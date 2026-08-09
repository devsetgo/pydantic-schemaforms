from __future__ import annotations

import asyncio
import os
import socket
import time

from .analytics import _is_public_ip, _normalize_ip
from .ip_geo_service import GeoLookupError, fetch_ip_api
from .ip_geo_store import (
    claim_next_job,
    mark_job_done,
    mark_job_error,
    renew_leader,
    try_acquire_leader,
    upsert_cache_error,
    upsert_cache_success,
)


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


def ip_geo_enabled() -> bool:
    return _truthy_env("IP_GEO_ENABLED", default=False)


def ip_geo_worker_enabled() -> bool:
    return _truthy_env("IP_GEO_WORKER_ENABLED", default=False)


def _parse_int(raw: str | None, default: int) -> int:
    try:
        if raw is None:
            return default
        return int(raw)
    except Exception:
        return default


def _rate_limit_per_minute() -> int:
    return max(1, _parse_int(os.environ.get("IP_GEO_RATE_LIMIT_PER_MIN"), 40))


def _instance_id() -> str:
    host = socket.gethostname()
    pid = os.getpid()
    return f"{host}:{pid}"


async def run_ip_geo_worker(*, stop_event: asyncio.Event) -> None:
    if not ip_geo_enabled() or not ip_geo_worker_enabled():
        return

    leader_key = "ip_geo_worker"
    me = _instance_id()
    leader_ttl = 30

    # Acquire leader lock (single global worker across all Uvicorn processes).
    if not try_acquire_leader(lock_key=leader_key, locked_by=me, ttl_seconds=leader_ttl):
        return

    min_interval = 60.0 / float(_rate_limit_per_minute())
    next_allowed = time.monotonic()

    while not stop_event.is_set():
        # Renew leader lease.
        if not renew_leader(lock_key=leader_key, locked_by=me, ttl_seconds=leader_ttl):
            # Lost leadership; stop doing work.
            return

        ip = await asyncio.to_thread(claim_next_job, locked_by=me, lock_seconds=90)
        if not ip:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=2.0)
            except TimeoutError:
                pass
            continue

        normalized = _normalize_ip(ip)
        if not normalized or not _is_public_ip(normalized):
            await asyncio.to_thread(mark_job_done, ip=ip, locked_by=me)
            continue

        # Global rate limiting.
        wait = max(0.0, next_allowed - time.monotonic())
        if wait:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=wait)
                # stop_event set
                return
            except TimeoutError:
                pass

        next_allowed = time.monotonic() + min_interval

        try:
            result = await fetch_ip_api(normalized)
            await asyncio.to_thread(
                upsert_cache_success,
                ip=normalized,
                country=result.country,
                country_code=result.country_code,
                region=result.region,
                city=result.city,
                lat=result.lat,
                lon=result.lon,
                raw_json=result.raw_json,
                status_code=200,
            )
            await asyncio.to_thread(mark_job_done, ip=ip, locked_by=me)
        except GeoLookupError as ex:
            delay = 60 if ex.status_code == 429 else min(60 * 15, 10 + 2**6)
            await asyncio.to_thread(
                upsert_cache_error,
                ip=normalized,
                raw_json=getattr(ex, "raw_json", None),
                status_code=getattr(ex, "status_code", None),
                error=str(ex) or "lookup_error",
            )
            await asyncio.to_thread(
                mark_job_error,
                ip=ip,
                locked_by=me,
                delay_seconds=delay,
                error=str(ex) or "lookup_error",
            )
        except Exception as ex:
            await asyncio.to_thread(
                upsert_cache_error,
                ip=normalized,
                raw_json=None,
                status_code=None,
                error=str(ex) or ex.__class__.__name__,
            )
            await asyncio.to_thread(
                mark_job_error,
                ip=ip,
                locked_by=me,
                delay_seconds=60,
                error=str(ex) or ex.__class__.__name__,
            )
