from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .analytics import get_db_path


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat()


def _parse_int(raw: str | None, default: int) -> int:
    try:
        if raw is None:
            return default
        return int(raw)
    except Exception:
        return default


def _mem_cache_ttl_seconds() -> int:
    return max(10, _parse_int(os.environ.get("IP_GEO_MEM_CACHE_TTL_SECONDS"), 30 * 60))


def _neg_cache_ttl_seconds() -> int:
    return max(5, _parse_int(os.environ.get("IP_GEO_NEG_CACHE_TTL_SECONDS"), 2 * 60))


def _enqueue_cache_ttl_seconds() -> int:
    return max(5, _parse_int(os.environ.get("IP_GEO_ENQUEUE_CACHE_TTL_SECONDS"), 60))


def _cache_ttl_days() -> int:
    return max(1, _parse_int(os.environ.get("IP_GEO_CACHE_TTL_DAYS"), 180))


def _provider_name() -> str:
    return (os.environ.get("IP_GEO_PROVIDER") or "iplocation.net").strip() or "iplocation.net"


def _connect() -> sqlite3.Connection:
    db_path = get_db_path()
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception:
        pass
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _tables_available(conn: sqlite3.Connection) -> bool:
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('ip_geo_cache','ip_geo_queue','ip_geo_leader_lock')"
        ).fetchall()
        names = {r["name"] for r in row}
        return {"ip_geo_cache", "ip_geo_queue", "ip_geo_leader_lock"}.issubset(names)
    except Exception:
        return False


@dataclass(frozen=True)
class GeoRow:
    country: str | None
    country_code: str | None
    region: str | None
    city: str | None
    latitude: float | None
    longitude: float | None


_mem_geo_cache: dict[str, tuple[float, GeoRow | None]] = {}
_mem_enqueue_cache: dict[str, float] = {}


def get_cached_geo(ip: str) -> GeoRow | None:
    """Return cached geo for an IP if present+fresh, else None.

    Never raises; failures behave like cache-miss.
    """

    ip = (ip or "").strip()
    if not ip:
        return None

    now_mono = time.monotonic()
    cached = _mem_geo_cache.get(ip)
    if cached:
        ts, value = cached
        ttl = _mem_cache_ttl_seconds() if value is not None else _neg_cache_ttl_seconds()
        if (now_mono - ts) <= ttl:
            return value

    try:
        now_iso = _iso(_utcnow())
        with _connect() as conn:
            if not _tables_available(conn):
                _mem_geo_cache[ip] = (now_mono, None)
                return None

            row = conn.execute(
                """
                SELECT country, country_code, region, city, lat, lon
                FROM ip_geo_cache
                WHERE ip = ? AND expires_at > ?
                """.strip(),
                (ip, now_iso),
            ).fetchone()

        if not row:
            _mem_geo_cache[ip] = (now_mono, None)
            return None

        value = GeoRow(
            country=row["country"],
            country_code=row["country_code"],
            region=row["region"],
            city=row["city"],
            latitude=row["lat"],
            longitude=row["lon"],
        )
        _mem_geo_cache[ip] = (now_mono, value)
        return value
    except sqlite3.OperationalError:
        _mem_geo_cache[ip] = (now_mono, None)
        return None
    except Exception:
        _mem_geo_cache[ip] = (now_mono, None)
        return None


def enqueue_ip(ip: str) -> None:
    """Idempotently queue an IP for lookup.

    Uses a small in-memory TTL to avoid repeated DB writes during bursts.
    Never raises.
    """

    ip = (ip or "").strip()
    if not ip:
        return

    now_mono = time.monotonic()
    last = _mem_enqueue_cache.get(ip)
    if last is not None and (now_mono - last) <= _enqueue_cache_ttl_seconds():
        return

    now = _utcnow()
    now_iso = _iso(now)

    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return

            conn.execute(
                """
                INSERT INTO ip_geo_queue(
                    ip, status, created_at, updated_at, attempt_count, next_attempt_at,
                    locked_by, locked_until, last_error
                ) VALUES (?, 'pending', ?, ?, 0, ?, NULL, NULL, NULL)
                ON CONFLICT(ip) DO UPDATE SET
                    status = CASE
                        WHEN ip_geo_queue.status = 'in_progress' THEN ip_geo_queue.status
                        WHEN ip_geo_queue.status = 'done' THEN ip_geo_queue.status
                        ELSE 'pending'
                    END,
                    updated_at = excluded.updated_at,
                    next_attempt_at = CASE
                        WHEN ip_geo_queue.status IN ('pending','error') THEN excluded.next_attempt_at
                        ELSE ip_geo_queue.next_attempt_at
                    END
                """.strip(),
                (ip, now_iso, now_iso, now_iso),
            )

        _mem_enqueue_cache[ip] = now_mono
    except Exception:
        return


def upsert_cache_success(
    *,
    ip: str,
    country: str | None,
    country_code: str | None,
    region: str | None,
    city: str | None,
    lat: float | None,
    lon: float | None,
    raw_json: str,
    status_code: int | None = None,
) -> None:
    ip = (ip or "").strip()
    if not ip:
        return

    now = _utcnow()
    fetched_at = _iso(now)
    expires_at = _iso(now + timedelta(days=_cache_ttl_days()))

    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return

            conn.execute(
                """
                INSERT INTO ip_geo_cache(
                    ip, provider, fetched_at, expires_at,
                    country, country_code, region, city, lat, lon,
                    raw_json, last_status_code, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(ip) DO UPDATE SET
                    provider=excluded.provider,
                    fetched_at=excluded.fetched_at,
                    expires_at=excluded.expires_at,
                    country=excluded.country,
                    country_code=excluded.country_code,
                    region=excluded.region,
                    city=excluded.city,
                    lat=excluded.lat,
                    lon=excluded.lon,
                    raw_json=excluded.raw_json,
                    last_status_code=excluded.last_status_code,
                    last_error=NULL
                """.strip(),
                (
                    ip,
                    _provider_name(),
                    fetched_at,
                    expires_at,
                    country,
                    country_code,
                    region,
                    city,
                    lat,
                    lon,
                    raw_json,
                    int(status_code) if status_code is not None else None,
                ),
            )

        # Warm in-memory cache immediately.
        _mem_geo_cache[ip] = (
            time.monotonic(),
            GeoRow(
                country=country,
                country_code=country_code,
                region=region,
                city=city,
                latitude=lat,
                longitude=lon,
            ),
        )
    except Exception:
        return


def upsert_cache_error(
    *, ip: str, raw_json: str | None, status_code: int | None, error: str
) -> None:
    ip = (ip or "").strip()
    if not ip:
        return

    # Store the raw JSON even for errors if we have it, for debugging.
    raw = raw_json if raw_json is not None else json.dumps({"error": error}, ensure_ascii=False)
    now = _utcnow()
    fetched_at = _iso(now)
    # Keep errors short-lived so we don't permanently poison the cache.
    expires_at = _iso(now + timedelta(minutes=15))

    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return

            conn.execute(
                """
                INSERT INTO ip_geo_cache(
                    ip, provider, fetched_at, expires_at,
                    country, country_code, region, city, lat, lon,
                    raw_json, last_status_code, last_error
                ) VALUES (?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, ?, ?, ?)
                ON CONFLICT(ip) DO UPDATE SET
                    provider=excluded.provider,
                    fetched_at=excluded.fetched_at,
                    expires_at=excluded.expires_at,
                    raw_json=excluded.raw_json,
                    last_status_code=excluded.last_status_code,
                    last_error=excluded.last_error
                """.strip(),
                (
                    ip,
                    _provider_name(),
                    fetched_at,
                    expires_at,
                    raw,
                    int(status_code) if status_code is not None else None,
                    error,
                ),
            )

        _mem_geo_cache[ip] = (time.monotonic(), None)
    except Exception:
        return


def try_acquire_leader(*, lock_key: str, locked_by: str, ttl_seconds: int) -> bool:
    """Attempt to become the single leader process for the geo worker."""

    now = _utcnow()
    now_iso = _iso(now)
    locked_until = _iso(now + timedelta(seconds=max(5, ttl_seconds)))

    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return False

            conn.execute("BEGIN IMMEDIATE")

            row = conn.execute(
                "SELECT lock_key, locked_by, locked_until FROM ip_geo_leader_lock WHERE lock_key = ?",
                (lock_key,),
            ).fetchone()

            if not row:
                conn.execute(
                    """
                    INSERT INTO ip_geo_leader_lock(lock_key, locked_by, locked_until, updated_at)
                    VALUES (?, ?, ?, ?)
                    """.strip(),
                    (lock_key, locked_by, locked_until, now_iso),
                )
                conn.execute("COMMIT")
                return True

            current_until = row["locked_until"]
            current_by = row["locked_by"]

            if current_by == locked_by:
                conn.execute(
                    """
                    UPDATE ip_geo_leader_lock
                    SET locked_until = ?, updated_at = ?
                    WHERE lock_key = ? AND locked_by = ?
                    """.strip(),
                    (locked_until, now_iso, lock_key, locked_by),
                )
                conn.execute("COMMIT")
                return True

            if current_until < now_iso:
                conn.execute(
                    """
                    UPDATE ip_geo_leader_lock
                    SET locked_by = ?, locked_until = ?, updated_at = ?
                    WHERE lock_key = ?
                    """.strip(),
                    (locked_by, locked_until, now_iso, lock_key),
                )
                conn.execute("COMMIT")
                return True

            conn.execute("COMMIT")
            return False
    except Exception:
        return False


def renew_leader(*, lock_key: str, locked_by: str, ttl_seconds: int) -> bool:
    now = _utcnow()
    now_iso = _iso(now)
    locked_until = _iso(now + timedelta(seconds=max(5, ttl_seconds)))

    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return False

            rowcount = conn.execute(
                """
                UPDATE ip_geo_leader_lock
                SET locked_until = ?, updated_at = ?
                WHERE lock_key = ? AND locked_by = ?
                """.strip(),
                (locked_until, now_iso, lock_key, locked_by),
            ).rowcount
        return bool(rowcount)
    except Exception:
        return False


def claim_next_job(*, locked_by: str, lock_seconds: int) -> str | None:
    now = _utcnow()
    now_iso = _iso(now)
    locked_until = _iso(now + timedelta(seconds=max(10, lock_seconds)))

    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return None

            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT ip
                FROM ip_geo_queue
                WHERE status IN ('pending','error')
                  AND next_attempt_at <= ?
                  AND (locked_until IS NULL OR locked_until < ?)
                ORDER BY next_attempt_at ASC
                LIMIT 1
                """.strip(),
                (now_iso, now_iso),
            ).fetchone()

            if not row:
                conn.execute("COMMIT")
                return None

            ip = row["ip"]

            updated = conn.execute(
                """
                UPDATE ip_geo_queue
                SET status='in_progress',
                    locked_by=?,
                    locked_until=?,
                    updated_at=?,
                    attempt_count=attempt_count+1
                WHERE ip=?
                  AND status IN ('pending','error')
                  AND (locked_until IS NULL OR locked_until < ?)
                """.strip(),
                (locked_by, locked_until, now_iso, ip, now_iso),
            ).rowcount

            conn.execute("COMMIT")
            return ip if updated else None
    except Exception:
        return None


def mark_job_done(*, ip: str, locked_by: str) -> None:
    now_iso = _iso(_utcnow())
    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return

            conn.execute(
                """
                UPDATE ip_geo_queue
                SET status='done',
                    updated_at=?,
                    locked_by=NULL,
                    locked_until=NULL,
                    last_error=NULL
                WHERE ip=? AND locked_by=?
                """.strip(),
                (now_iso, ip, locked_by),
            )
    except Exception:
        return


def mark_job_error(*, ip: str, locked_by: str, delay_seconds: int, error: str) -> None:
    now = _utcnow()
    now_iso = _iso(now)
    next_attempt_at = _iso(now + timedelta(seconds=max(5, delay_seconds)))

    try:
        with _connect() as conn:
            if not _tables_available(conn):
                return

            conn.execute(
                """
                UPDATE ip_geo_queue
                SET status='error',
                    updated_at=?,
                    next_attempt_at=?,
                    locked_by=NULL,
                    locked_until=NULL,
                    last_error=?
                WHERE ip=? AND locked_by=?
                """.strip(),
                (now_iso, next_attempt_at, error[:500], ip, locked_by),
            )
    except Exception:
        return
