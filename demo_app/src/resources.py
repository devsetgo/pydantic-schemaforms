"""App lifecycle: startup/shutdown resource management.

Owns the analytics DB init/seed and the background IP-geo worker task. This is
demo-app-only (no counterpart in lib-examples) and has no bearing on the
library's own example routes.
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .analytics import init_db, seed_local_ip_examples
from .ip_geo_worker import ip_geo_enabled, ip_geo_worker_enabled, run_ip_geo_worker


def _truthy_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {'0', 'false', 'no', 'off'}


def _is_local_mode() -> bool:
    for key in ('APP_ENV', 'ENVIRONMENT', 'ENV'):
        raw = (os.environ.get(key) or '').strip().lower()
        if raw in {'local', 'dev', 'development'}:
            return True
    return _truthy_env('LOCAL_MODE', default=False)


def _analytics_capture_enabled() -> bool:
    return _truthy_env('ANALYTICS_CAPTURE_ENABLED', default=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _analytics_capture_enabled():
        try:
            init_db()

            if _is_local_mode() and _truthy_env('ANALYTICS_SEED_LOCAL_IPS', default=True):
                # One-time local seed for dashboard demo data.
                seed_local_ip_examples(force=False)
        except Exception:
            # Analytics must never prevent the app from starting.
            pass

        # IP geo lookup runs as a background task (single-leader across workers).
        try:
            if ip_geo_enabled() and ip_geo_worker_enabled():
                stop_event = asyncio.Event()
                task = asyncio.create_task(run_ip_geo_worker(stop_event=stop_event))
                app.state.ip_geo_stop_event = stop_event
                app.state.ip_geo_task = task
        except Exception:
            # Never block startup for this optional feature.
            pass

    yield

    try:
        stop_event = getattr(app.state, 'ip_geo_stop_event', None)
        task = getattr(app.state, 'ip_geo_task', None)
        if stop_event is not None:
            try:
                stop_event.set()
            except Exception:
                pass
        if task is not None:
            try:
                task.cancel()
            except Exception:
                pass
    except Exception:
        pass
