"""Minimal self-hosted analytics + error capture.

Goals:
- Zero external services
- Minimal dependencies (stdlib only)
- Reasonable behavior behind a reverse proxy (e.g., Traefik)

Storage:
- SQLite file (path configurable via env var)
- Short retention window (configurable via env var)

This is intentionally lightweight: it is *not* a full observability stack.
"""

from __future__ import annotations

import os
import re
import sqlite3
import time
import json
import ipaddress
import urllib.request
from uuid import uuid4
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_int(value: str | None, default: int) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def get_db_path() -> str:
    # Default to a durable local path.
    # Docker sets ANALYTICS_DB_PATH to /data/... via scripts/docker_entrypoint.sh.
    return os.environ.get("ANALYTICS_DB_PATH", "./data/schemaforms_analytics.db")


def get_retention_days() -> int:
    return max(1, _parse_int(os.environ.get("ANALYTICS_RETENTION_DAYS"), 7))


def get_max_rows() -> int:
    # Additional safety valve: if traffic spikes, keep DB bounded.
    return max(1_000, _parse_int(os.environ.get("ANALYTICS_MAX_ROWS"), 200_000))


def _connect() -> sqlite3.Connection:
    db_path = get_db_path()
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # Wait a bit for locks instead of failing fast (common on multi-worker startup).
    try:
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception:
        pass
    # Improve concurrency with multiple workers.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    # Multiple workers can race on first-time initialization.
    # Retry a few times rather than failing startup.
    for attempt in range(10):
        try:
            with _connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS request_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ts TEXT NOT NULL,
                        request_id TEXT,
                        user_id TEXT,
                        method TEXT NOT NULL,
                        path TEXT NOT NULL,
                        status_code INTEGER NOT NULL,
                        duration_ms INTEGER NOT NULL,
                        client_ip TEXT,
                        country TEXT,
                        country_code TEXT,
                        region TEXT,
                        city TEXT,
                        latitude REAL,
                        longitude REAL,
                        user_agent TEXT,
                        browser TEXT,
                        referer TEXT
                    )
                    """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_log_ts ON request_log(ts)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_request_log_path ON request_log(path)")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_request_log_status ON request_log(status_code)"
                )

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS error_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ts TEXT NOT NULL,
                        request_id TEXT,
                        user_id TEXT,
                        kind TEXT NOT NULL,
                        message TEXT NOT NULL,
                        detail TEXT,
                        path TEXT,
                        method TEXT,
                        status_code INTEGER,
                        client_ip TEXT,
                        user_agent TEXT
                    )
                    """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_error_log_ts ON error_log(ts)")

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """)

                # Lightweight migrations for existing DBs.
                _ensure_column(conn, "request_log", "request_id", "TEXT")
                _ensure_column(conn, "request_log", "user_id", "TEXT")
                _ensure_column(conn, "request_log", "country_code", "TEXT")
                _ensure_column(conn, "request_log", "region", "TEXT")
                _ensure_column(conn, "request_log", "city", "TEXT")
                _ensure_column(conn, "request_log", "latitude", "REAL")
                _ensure_column(conn, "request_log", "longitude", "REAL")

                _ensure_column(conn, "error_log", "request_id", "TEXT")
                _ensure_column(conn, "error_log", "user_id", "TEXT")
            return
        except sqlite3.OperationalError as ex:
            if "database is locked" not in str(ex).lower():
                return
            time.sleep(0.05 * (attempt + 1))
        except Exception:
            return


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl_type: str) -> None:
    try:
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column in existing:
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")
    except Exception:
        # Never block startup for analytics migrations.
        return


def _browser_family(user_agent: str | None) -> str:
    ua = (user_agent or "").lower()
    if not ua:
        return "unknown"
    # Order matters.
    if "edg/" in ua or "edge/" in ua:
        return "edge"
    if "chrome/" in ua and "chromium" not in ua and "edg/" not in ua:
        return "chrome"
    if "firefox/" in ua:
        return "firefox"
    if "safari/" in ua and "chrome/" not in ua:
        return "safari"
    if "curl/" in ua or "wget/" in ua or "httpie" in ua:
        return "cli"
    return "other"


_ip_re = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3})$")


def extract_client_ip(headers: dict[str, str], fallback: str | None = None) -> str | None:
    # Cloudflare sits in front of Traefik in this deployment: CF-Connecting-IP is
    # Cloudflare's authoritative single-value header for the real visitor IP, so
    # prefer it over X-Forwarded-For (which requires trusting the whole chain).
    cf_ip = headers.get("cf-connecting-ip")
    if cf_ip:
        cf_ip = cf_ip.strip()
        if cf_ip:
            return cf_ip

    # Prefer X-Forwarded-For (first IP is the original client).
    xff = headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first

    xri = headers.get("x-real-ip")
    if xri:
        return xri.strip() or fallback

    return fallback


def extract_country(headers: dict[str, str]) -> str | None:
    # Optional: if you later configure Traefik / upstream to provide a country header.
    for key in ("cf-ipcountry", "x-country", "x-forwarded-country", "x-geo-country"):
        value = headers.get(key)
        if value:
            value = value.strip()
            if value:
                return value
    return None


def _truthy_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    raw = raw.strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _flag_emoji(country_code: str | None) -> str:
    code = (country_code or "").strip().upper()
    if len(code) != 2 or not code.isalpha():
        return ""
    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)


def _normalize_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    s = ip.strip()
    if not s:
        return None
    # Common case: IPv4 with port (e.g. "1.2.3.4:12345")
    if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d+$", s):
        s = s.split(":", 1)[0]
    # Bracketed IPv6 with port: "[2001:db8::1]:1234"
    if s.startswith("[") and "]:" in s:
        s = s[1 : s.index("]")]
    return s


def _is_public_ip(ip: str | None) -> bool:
    s = _normalize_ip(ip)
    if not s:
        return False
    try:
        obj = ipaddress.ip_address(s)
    except Exception:
        return False
    # Skip private/loopback/link-local/etc.
    return bool(getattr(obj, "is_global", False))


_geoip_cache: dict[str, tuple[float, dict[str, Any] | None]] = {}


_LOCAL_SAMPLE_IPS = [
    "34.136.250.113",
    "47.202.132.163",
    "44.207.207.36",
    "54.162.53.446.101.115.83",  # invalid on purpose in provided list; skipped safely
    "44.195.201.244",
    "74.7.230.41",
    "16.144.17.106",
    "146.70.185.32",
    "34.170.116.95",
]


def _geoip_cache_ttl_seconds() -> int:
    raw = os.environ.get("ANALYTICS_GEOIP_CACHE_TTL_SECONDS")
    try:
        if raw is None:
            return 24 * 60 * 60
        return max(60, int(raw))
    except Exception:
        return 24 * 60 * 60


def _geoip_timeout_seconds() -> float:
    raw = os.environ.get("ANALYTICS_GEOIP_TIMEOUT_SECONDS")
    try:
        if raw is None:
            return 1.5
        return max(0.2, float(raw))
    except Exception:
        return 1.5


def _geoip_enabled() -> bool:
    # Opt-in only: external IP → location lookup.
    return _truthy_env("ANALYTICS_GEOIP_ENABLED", default=False)


def _geoip_lookup_ipapi_co(ip: str) -> dict[str, Any] | None:
    url = f"https://ipapi.co/{ip}/json/"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "schemaforms-analytics/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_geoip_timeout_seconds()) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        if data.get("error"):
            return None
        return {
            "country_code": data.get("country_code"),
            "country": data.get("country_name"),
            "region": data.get("region"),
            "city": data.get("city"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
        }
    except Exception:
        return None


def geoip_enrich(client_ip: str | None) -> dict[str, Any] | None:
    if not _geoip_enabled():
        return None
    ip = _normalize_ip(client_ip)
    if not ip or not _is_public_ip(ip):
        return None

    now = time.time()
    cached = _geoip_cache.get(ip)
    if cached:
        ts, value = cached
        if (now - ts) <= _geoip_cache_ttl_seconds():
            return value

    value = _geoip_lookup_ipapi_co(ip)
    _geoip_cache[ip] = (now, value)
    # Prevent unbounded growth.
    if len(_geoip_cache) > 10_000:
        try:
            for k in list(_geoip_cache.keys())[:2_000]:
                _geoip_cache.pop(k, None)
        except Exception:
            _geoip_cache.clear()
    return value


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat()


def _should_prune(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT value FROM meta WHERE key='last_prune_ts'").fetchone()
    if not row:
        return True
    try:
        last = datetime.fromisoformat(row["value"])
    except Exception:
        return True
    return (_utcnow() - last) > timedelta(minutes=10)


def _set_last_prune(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('last_prune_ts', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (_iso(_utcnow()),),
    )


def _meta_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    if not row:
        return None
    return str(row["value"])


def _meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def _sample_geo_for_ip(ip: str) -> dict[str, Any]:
    # Deterministic pseudo-geo for local demos; no external calls needed.
    zones = [
        ("United States", "US", "Virginia", "Ashburn", 39.0438, -77.4874),
        ("United States", "US", "Texas", "Dallas", 32.7767, -96.7970),
        ("Canada", "CA", "Ontario", "Toronto", 43.6532, -79.3832),
        ("United Kingdom", "GB", "England", "London", 51.5072, -0.1276),
        ("Germany", "DE", "Hesse", "Frankfurt", 50.1109, 8.6821),
    ]
    bucket = sum(ord(c) for c in ip) % len(zones)
    country, country_code, region, city, lat, lon = zones[bucket]
    return {
        "country": country,
        "country_code": country_code,
        "region": region,
        "city": city,
        "lat": lat,
        "lon": lon,
        "provider": "local-seed",
    }


def seed_local_ip_examples(*, force: bool = False) -> dict[str, int]:
    """Insert sample request + geo rows for local dashboard demos.

    The seed is idempotent and tracked in `meta` unless `force=True`.
    """

    inserted = 0
    skipped = 0
    marker_key = "local_sample_ips_seeded_v1"

    try:
        with _connect() as conn:
            if not force and _meta_get(conn, marker_key):
                return {"inserted": 0, "skipped": 0}

            now_iso = _iso(_utcnow())

            for idx, raw_ip in enumerate(_LOCAL_SAMPLE_IPS):
                ip = _normalize_ip(raw_ip)
                if not ip or not _is_public_ip(ip):
                    skipped += 1
                    continue

                geo = _sample_geo_for_ip(ip)
                raw_geo_json = json.dumps(
                    {
                        "provider": geo["provider"],
                        "query": ip,
                        "country": geo["country"],
                        "countryCode": geo["country_code"],
                        "regionName": geo["region"],
                        "city": geo["city"],
                        "lat": geo["lat"],
                        "lon": geo["lon"],
                        "seeded": True,
                    },
                    ensure_ascii=False,
                )

                # Best effort: also seed ip_geo_cache for richer dashboard tooltip/modal data.
                try:
                    from .ip_geo_store import upsert_cache_success

                    upsert_cache_success(
                        ip=ip,
                        country=geo["country"],
                        country_code=geo["country_code"],
                        region=geo["region"],
                        city=geo["city"],
                        lat=geo["lat"],
                        lon=geo["lon"],
                        raw_json=raw_geo_json,
                        status_code=200,
                    )
                except Exception:
                    pass

                conn.execute(
                    """
                    INSERT INTO request_log(
                        ts, request_id, user_id, method, path, status_code, duration_ms,
                        client_ip, country, country_code, region, city, latitude, longitude,
                        user_agent, browser, referer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """.strip(),
                    (
                        now_iso,
                        uuid4().hex,
                        "local-seed-user",
                        "GET",
                        "/seed/local-ip-demo",
                        200,
                        12 + idx,
                        ip,
                        geo["country"],
                        geo["country_code"],
                        geo["region"],
                        geo["city"],
                        geo["lat"],
                        geo["lon"],
                        "local-seed/1.0",
                        "other",
                        "local://seed",
                    ),
                )
                inserted += 1

            _meta_set(conn, marker_key, now_iso)
    except Exception:
        return {"inserted": 0, "skipped": 0}

    return {"inserted": inserted, "skipped": skipped}


def _prune(conn: sqlite3.Connection) -> None:
    cutoff = _utcnow() - timedelta(days=get_retention_days())
    cutoff_iso = _iso(cutoff)

    conn.execute("DELETE FROM request_log WHERE ts < ?", (cutoff_iso,))
    conn.execute("DELETE FROM error_log WHERE ts < ?", (cutoff_iso,))

    max_rows = get_max_rows()
    # If still too big, trim oldest rows.
    row = conn.execute("SELECT COUNT(*) AS c FROM request_log").fetchone()
    if row and int(row["c"]) > max_rows:
        to_delete = int(row["c"]) - max_rows
        conn.execute(
            "DELETE FROM request_log WHERE id IN (SELECT id FROM request_log ORDER BY id ASC LIMIT ?)",
            (to_delete,),
        )

    row = conn.execute("SELECT COUNT(*) AS c FROM error_log").fetchone()
    if row and int(row["c"]) > max_rows:
        to_delete = int(row["c"]) - max_rows
        conn.execute(
            "DELETE FROM error_log WHERE id IN (SELECT id FROM error_log ORDER BY id ASC LIMIT ?)",
            (to_delete,),
        )


def record_request(
    *,
    request_id: str | None = None,
    user_id: str | None = None,
    method: str,
    path: str,
    status_code: int,
    duration_ms: int,
    client_ip: str | None,
    country: str | None,
    user_agent: str | None,
    referer: str | None,
) -> None:
    try:
        normalized_ip = _normalize_ip(client_ip)

        # Best-effort: convert a 2-letter country header into a country_code.
        country_code = None
        if country and isinstance(country, str):
            maybe = country.strip().upper()
            if len(maybe) == 2 and maybe.isalpha():
                country_code = maybe

        # GeoIP is now async + queued (never block requests on external I/O).
        # Best-effort: read from DB cache; if missing, enqueue for background lookup.
        region = None
        city = None
        latitude = None
        longitude = None
        try:
            if not _truthy_env("IP_GEO_ENABLED", default=False):
                raise RuntimeError("ip_geo_disabled")

            from .ip_geo_store import enqueue_ip, get_cached_geo

            geo_row = get_cached_geo(normalized_ip or "") if normalized_ip else None
            if geo_row:
                country = (geo_row.country or country) or None
                country_code = (geo_row.country_code or country_code) or None
                region = geo_row.region
                city = geo_row.city
                latitude = geo_row.latitude
                longitude = geo_row.longitude
            else:
                # Only queue lookups for public/global IPs.
                if normalized_ip and _is_public_ip(normalized_ip):
                    enqueue_ip(normalized_ip)
        except Exception:
            # Never break the request path.
            pass

        with _connect() as conn:
            if _should_prune(conn):
                _prune(conn)
                _set_last_prune(conn)

            conn.execute(
                """
                INSERT INTO request_log(
                    ts, request_id, user_id, method, path, status_code, duration_ms,
                    client_ip, country, country_code, region, city, latitude, longitude,
                    user_agent, browser, referer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """.strip(),
                (
                    _iso(_utcnow()),
                    request_id,
                    user_id,
                    method,
                    path,
                    int(status_code),
                    int(duration_ms),
                    normalized_ip,
                    country,
                    country_code,
                    region,
                    city,
                    latitude,
                    longitude,
                    user_agent,
                    _browser_family(user_agent),
                    referer,
                ),
            )
    except Exception:
        # Analytics must never break the app.
        return


def record_error(
    *,
    request_id: str | None = None,
    user_id: str | None = None,
    kind: str,
    message: str,
    detail: str | None = None,
    path: str | None = None,
    method: str | None = None,
    status_code: int | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    try:
        with _connect() as conn:
            if _should_prune(conn):
                _prune(conn)
                _set_last_prune(conn)

            conn.execute(
                """
                INSERT INTO error_log(
                    ts, request_id, user_id, kind, message, detail,
                    path, method, status_code, client_ip, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """.strip(),
                (
                    _iso(_utcnow()),
                    request_id,
                    user_id,
                    kind,
                    message,
                    detail,
                    path,
                    method,
                    int(status_code) if status_code is not None else None,
                    client_ip,
                    user_agent,
                ),
            )
    except Exception:
        return


@dataclass(frozen=True)
class AnalyticsSummary:
    since_iso: str
    total_requests: int
    unique_ips: int
    avg_duration_ms: int
    top_paths: list[dict[str, Any]]
    status_counts: list[dict[str, Any]]
    browser_counts: list[dict[str, Any]]


def _since_iso(days: int) -> str:
    since = _utcnow() - timedelta(days=max(0, days))
    return _iso(since)


def get_summary(*, days: int = 1, top_n: int = 10) -> AnalyticsSummary:
    since = _since_iso(days)
    with _connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM request_log WHERE ts >= ?",
            (since,),
        ).fetchone()["c"]

        unique_ips = conn.execute(
            "SELECT COUNT(DISTINCT client_ip) AS c FROM request_log WHERE ts >= ? AND client_ip IS NOT NULL",
            (since,),
        ).fetchone()["c"]

        avg_dur = conn.execute(
            "SELECT COALESCE(AVG(duration_ms), 0) AS v FROM request_log WHERE ts >= ?",
            (since,),
        ).fetchone()["v"]

        top_paths = [
            dict(r)
            for r in conn.execute(
                """
                SELECT path, COUNT(*) AS count
                FROM request_log
                WHERE ts >= ?
                GROUP BY path
                ORDER BY count DESC
                LIMIT ?
                """.strip(),
                (since, int(top_n)),
            ).fetchall()
        ]

        status_counts = [
            dict(r)
            for r in conn.execute(
                """
                SELECT status_code, COUNT(*) AS count
                FROM request_log
                WHERE ts >= ?
                GROUP BY status_code
                ORDER BY count DESC
                """.strip(),
                (since,),
            ).fetchall()
        ]

        browser_counts = [
            dict(r)
            for r in conn.execute(
                """
                SELECT browser, COUNT(*) AS count
                FROM request_log
                WHERE ts >= ?
                GROUP BY browser
                ORDER BY count DESC
                """.strip(),
                (since,),
            ).fetchall()
        ]

    return AnalyticsSummary(
        since_iso=since,
        total_requests=int(total),
        unique_ips=int(unique_ips),
        avg_duration_ms=int(avg_dur or 0),
        top_paths=top_paths,
        status_counts=status_counts,
        browser_counts=browser_counts,
    )


def get_recent_requests(*, limit: int = 200) -> list[dict[str, Any]]:
    with _connect() as conn:
        try:
            # Prefer geo data from the persistent cache if available.
            now_iso = _iso(_utcnow())
            rows = conn.execute(
                """
                SELECT rl.ts, rl.request_id, rl.user_id, rl.method, rl.path, rl.status_code, rl.duration_ms,
                       rl.client_ip,
                       COALESCE(rl.country, ig.country) AS country,
                       COALESCE(rl.country_code, ig.country_code) AS country_code,
                       COALESCE(rl.region, ig.region) AS region,
                       COALESCE(rl.city, ig.city) AS city,
                       COALESCE(rl.latitude, ig.lat) AS latitude,
                       COALESCE(rl.longitude, ig.lon) AS longitude,
                       ig.fetched_at AS ip_geo_fetched_at,
                       ig.expires_at AS ip_geo_expires_at,
                       ig.provider AS ip_geo_provider,
                       ig.raw_json AS ip_geo_raw_json,
                       rl.browser, rl.referer
                FROM request_log AS rl
                LEFT JOIN ip_geo_cache AS ig
                  ON ig.ip = rl.client_ip AND ig.expires_at > ?
                ORDER BY rl.id DESC
                LIMIT ?
                """.strip(),
                (now_iso, int(limit)),
            ).fetchall()
        except Exception:
            # Fallback if ip_geo_cache isn't present yet.
            rows = conn.execute(
                """
                SELECT ts, request_id, user_id, method, path, status_code, duration_ms,
                       client_ip, country, country_code, region, city, latitude, longitude,
                       browser, referer
                FROM request_log
                ORDER BY id DESC
                LIMIT ?
                """.strip(),
                (int(limit),),
            ).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        cc = (d.get("country_code") or "").strip() or None
        d["flag"] = _flag_emoji(cc)

        parts: list[str] = []
        city = (d.get("city") or "").strip()
        region = (d.get("region") or "").strip()
        country = (d.get("country") or "").strip()
        if city:
            parts.append(city)
        if region and region not in parts:
            parts.append(region)
        if country:
            parts.append(country)
        if cc and cc not in parts and cc != country:
            parts.append(cc)
        d["location"] = ", ".join(parts)

        # Tooltip shown on IP hover in the dashboard.
        try:
            raw = (d.get("ip_geo_raw_json") or "").strip()
            # Keep tooltips reasonable.
            if len(raw) > 800:
                raw = raw[:800] + "…"

            tooltip_parts: list[str] = []
            if d.get("ip_geo_provider"):
                tooltip_parts.append(f"provider={d.get('ip_geo_provider')}")
            if d.get("ip_geo_fetched_at"):
                tooltip_parts.append(f"fetched_at={d.get('ip_geo_fetched_at')}")
            if d.get("ip_geo_expires_at"):
                tooltip_parts.append(f"expires_at={d.get('ip_geo_expires_at')}")
            if d.get("location"):
                tooltip_parts.append(f"location={d.get('location')}")
            if raw:
                tooltip_parts.append(f"raw_json={raw}")

            d["ip_geo_tooltip"] = " | ".join(str(p) for p in tooltip_parts if p)
        except Exception:
            d["ip_geo_tooltip"] = ""

        out.append(d)
    return out


def get_recent_errors(*, limit: int = 200) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT ts, request_id, user_id, kind, message, detail, path, method, status_code, client_ip
            FROM error_log
            ORDER BY id DESC
            LIMIT ?
            """.strip(),
            (int(limit),),
        ).fetchall()
    return [dict(r) for r in rows]


def purge_all() -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM request_log")
        conn.execute("DELETE FROM error_log")
        conn.execute("DELETE FROM meta")


def get_ip_geo_queue_status() -> dict[str, Any]:
    """Best-effort view of the IP geo queue/worker state.

    This is used by the dashboard and must never raise.
    """

    try:
        now_iso = _iso(_utcnow())
        with _connect() as conn:
            # If tables don't exist yet (migrations not applied), just return empty.
            existing = {
                r["name"]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ip_geo_%'"
                ).fetchall()
            }
            if "ip_geo_queue" not in existing:
                return {
                    "available": False,
                    "pending": 0,
                    "in_progress": 0,
                    "error": 0,
                    "done": 0,
                    "due_now": 0,
                    "leader": None,
                }

            counts = {r["status"]: int(r["count"]) for r in conn.execute("""
                    SELECT status, COUNT(*) AS count
                    FROM ip_geo_queue
                    GROUP BY status
                    """.strip()).fetchall()}

            due_now = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM ip_geo_queue
                WHERE status IN ('pending','error') AND next_attempt_at <= ?
                """.strip(),
                (now_iso,),
            ).fetchone()

            leader = None
            if "ip_geo_leader_lock" in existing:
                row = conn.execute("""
                    SELECT lock_key, locked_by, locked_until, updated_at
                    FROM ip_geo_leader_lock
                    WHERE lock_key='ip_geo_worker'
                    """.strip()).fetchone()
                if row:
                    leader = {
                        "locked_by": row["locked_by"],
                        "locked_until": row["locked_until"],
                        "updated_at": row["updated_at"],
                        "expired": bool(row["locked_until"] < now_iso),
                    }

        return {
            "available": True,
            "pending": int(counts.get("pending", 0)),
            "in_progress": int(counts.get("in_progress", 0)),
            "error": int(counts.get("error", 0)),
            "done": int(counts.get("done", 0)),
            "due_now": int(due_now["c"] if due_now else 0),
            "leader": leader,
        }
    except Exception:
        return {
            "available": False,
            "pending": 0,
            "in_progress": 0,
            "error": 0,
            "done": 0,
            "due_now": 0,
            "leader": None,
        }
