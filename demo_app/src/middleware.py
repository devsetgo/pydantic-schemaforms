"""HTTP middleware: request/error logging, analytics recording, and an anti-scan tarpit.

Demo-app-only (no counterpart in lib-examples).
"""

import asyncio
import json
import logging
import os
import re
import time
from uuid import uuid4

from fastapi import Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from .analytics import extract_client_ip, extract_country, record_request

logger = logging.getLogger('schemaforms.demo')


def _analytics_capture_enabled() -> bool:
    raw = os.environ.get('ANALYTICS_CAPTURE_ENABLED')
    if raw is None:
        return False
    return raw.strip().lower() not in {'0', 'false', 'no', 'off'}


def _antihack_enabled() -> bool:
    raw = (os.environ.get('ANTISCAN_ENABLED') or '1').strip().lower()
    return raw not in {'0', 'false', 'no', 'off'}


def _antihack_redirect_url() -> str | None:
    raw = os.environ.get('ANTISCAN_REDIRECT_URL')
    if raw is None:
        return None
    raw = raw.strip()
    return raw or None


def _antihack_tarpit_seconds() -> float | None:
    raw = os.environ.get('ANTISCAN_TARPIT_SECONDS')
    if raw is None:
        return None
    try:
        v = float(raw)
    except Exception:
        return None
    if v <= 0:
        return None
    # Safety cap: holding connections open for too long can self-DoS.
    return min(v, 600.0)


def _antihack_max_inflight_per_ip() -> int:
    raw = os.environ.get('ANTISCAN_MAX_INFLIGHT_PER_IP')
    try:
        if raw is None:
            return 1
        return max(1, int(raw))
    except Exception:
        return 1


def _looks_like_scan_path(path: str) -> bool:
    p = (path or '/').strip()
    if not p.startswith('/'):
        p = '/' + p
    p_low = p.lower()

    # Keep false positives low: match known scanner probes.
    # Note: this app serves real assets under /vendor/, so that prefix is
    # intentionally excluded (unlike a typical PHP/Composer vendor-dir probe).
    prefixes = (
        '/.aws/',
        '/aws/',
        '/.git',
        '/.hg',
        '/.svn',
        '/.circleci/',
        '/.travis',
        '/.bitbucket/',
        '/.env',
        '/wp-',
        '/phpmyadmin',
        '/_profiler',
        '/app_dev.php',
        '/server-status',
        '/server-info',
        '/cgi-bin/',
        '/horizon/',
        '/storage/logs/',
        '/debug',
        '/manage/env',
    )
    if p_low.startswith(prefixes):
        return True

    # File probes.
    if p_low in {'/phpinfo', '/phpinfo.php', '/info.php', '/test.php', '/error.log', '/debug.log'}:
        return True

    # Common sensitive file extensions.
    if re.search(r'\.(?:php|asp|aspx|jsp|cgi|pl|sh|bak|old|swp)$', p_low):
        return True

    # Obvious secret/config filenames.
    if re.search(r'(?:secret|credential|config|settings)\.(?:ya?ml|json|ini|env)$', p_low):
        return True

    return False


# Simple in-memory tarpit/block for scanners.
# Note: per-process only (fine for a demo; use a reverse proxy/WAF for production).
_abuse_state: dict[str, dict[str, float]] = {}


def _abuse_key(request: Request) -> str:
    ip = extract_client_ip(dict(request.headers), getattr(request.client, 'host', None))
    ip = (ip or 'unknown').strip() or 'unknown'
    return ip


def _abuse_gc(now: float) -> None:
    # Best-effort cleanup: drop entries not seen in ~1h.
    try:
        for k in list(_abuse_state.keys()):
            if (now - float(_abuse_state[k].get('last', 0.0))) > 3600:
                _abuse_state.pop(k, None)
    except Exception:
        return


def _user_id_cookie_name() -> str:
    return (os.environ.get('USER_ID_COOKIE_NAME') or 'schemaforms_uid').strip() or 'schemaforms_uid'


def _user_id_cookie_max_age_seconds() -> int:
    raw = os.environ.get('USER_ID_COOKIE_MAX_AGE_SECONDS')
    try:
        if raw is None:
            # ~6 months
            return 180 * 24 * 60 * 60
        return max(60, int(raw))
    except Exception:
        return 180 * 24 * 60 * 60


def _get_or_create_request_id(request: Request) -> str:
    rid = (request.headers.get('x-request-id') or '').strip()
    return rid or uuid4().hex


def _get_or_create_user_id(request: Request) -> tuple[str, bool]:
    cookie_name = _user_id_cookie_name()
    existing = (request.cookies.get(cookie_name) or '').strip()
    if existing:
        return existing, False
    return uuid4().hex, True


def _request_log_context(request: Request) -> dict:
    client_ip = None
    if _analytics_capture_enabled():
        client_ip = extract_client_ip(dict(request.headers), getattr(request.client, 'host', None))
    return {
        'request_id': getattr(request.state, 'request_id', None),
        'user_id': getattr(request.state, 'user_id', None),
        'method': request.method,
        'path': request.url.path,
        'client_ip': client_ip,
        'user_agent': request.headers.get('user-agent'),
        'referer': request.headers.get('referer'),
    }


def _request_is_https(request: Request) -> bool:
    xf_proto = (request.headers.get('x-forwarded-proto') or '').strip().lower()
    if xf_proto:
        return xf_proto == 'https'
    return (request.url.scheme or '').lower() == 'https'


async def analytics_middleware(request: Request, call_next):
    start = time.perf_counter()
    capture_enabled = _analytics_capture_enabled()

    # Skip analytics for internal IP ranges (e.g., 10.*). These are
    # internal service calls that should not be recorded or tarpitted.
    try:
        _client_ip = extract_client_ip(dict(request.headers), getattr(request.client, 'host', None))
        if _client_ip:
            cip = (_client_ip or '').strip()
            if cip.startswith('10.') or cip == '10.42.0.1':
                return await call_next(request)
    except Exception:
        # Fall through to normal handling if anything goes wrong.
        pass

    request_id = _get_or_create_request_id(request)
    if capture_enabled:
        user_id, should_set_user_cookie = _get_or_create_user_id(request)
    else:
        user_id, should_set_user_cookie = None, False
    request.state.request_id = request_id
    request.state.user_id = user_id

    path = request.url.path
    # Keep noise down, and don't let the dashboard's own traffic (including its
    # polling of /api/analytics/*) pollute the stats it's showing.
    if (
        path.startswith('/static')
        or path.startswith('/vendor')
        or path.startswith('/dashboard')
        or path.startswith('/api/analytics')
        or path in {'/favicon.ico', '/central'}
    ):
        return await call_next(request)

    # Inconvenience obvious scanner probes without impacting legitimate 404s.
    if _antihack_enabled() and _looks_like_scan_path(path):
        now = time.time()
        key = _abuse_key(request)
        state = _abuse_state.get(key) or {'score': 0.0, 'last': now, 'blocked_until': 0.0}

        # Limit concurrent tarpits per IP to avoid tying up the server.
        inflight = int(float(state.get('inflight', 0.0) or 0.0))
        max_inflight = _antihack_max_inflight_per_ip()
        if inflight >= max_inflight:
            state.update({'last': now, 'inflight': float(inflight)})
            _abuse_state[key] = state
            _abuse_gc(now)
            return PlainTextResponse(
                content='Too Many Requests',
                status_code=429,
                headers={'Retry-After': '60'},
            )

        state['inflight'] = float(inflight + 1)
        _abuse_state[key] = state

        try:
            # Decay score over time to avoid permanent penalty.
            last = float(state.get('last', now))
            score = float(state.get('score', 0.0))
            score = max(0.0, score - (now - last) * 0.35)

            score += 2.0
            blocked_until = float(state.get('blocked_until', 0.0))
            if blocked_until and now < blocked_until:
                state.update({'score': score, 'last': now, 'blocked_until': blocked_until})
                _abuse_state[key] = state
                _abuse_gc(now)
                return PlainTextResponse(
                    content='Too Many Requests',
                    status_code=429,
                    headers={'Retry-After': str(int(max(1, blocked_until - now)))},
                )

            if score >= 14.0:
                blocked_until = now + 60 * 30
                state.update({'score': score, 'last': now, 'blocked_until': blocked_until})
                _abuse_state[key] = state
                _abuse_gc(now)
                return PlainTextResponse(
                    content='Too Many Requests',
                    status_code=429,
                    headers={'Retry-After': '1800'},
                )

            # Tarpit: either a configured long delay, or a small delay that grows with score.
            forced = _antihack_tarpit_seconds()
            delay = float(forced) if forced is not None else min(1.25, 0.05 * (score**1.35))

            state.update({'score': score, 'last': now, 'blocked_until': 0.0})
            _abuse_state[key] = state
            _abuse_gc(now)
            try:
                await asyncio.sleep(delay)
            except Exception:
                pass

            redirect_url = _antihack_redirect_url() or '/security'
            if redirect_url:
                try:
                    return RedirectResponse(url=redirect_url, status_code=302)
                except Exception:
                    pass

            return PlainTextResponse(content='Not Found', status_code=404)
        finally:
            try:
                s = _abuse_state.get(key) or state
                cur = int(float(s.get('inflight', 1.0) or 1.0))
                s['inflight'] = float(max(0, cur - 1))
                _abuse_state[key] = s
            except Exception:
                pass

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        client_ip = None
        country = None
        if capture_enabled:
            client_ip = extract_client_ip(
                dict(request.headers), getattr(request.client, 'host', None)
            )
            country = extract_country(dict(request.headers))

        logger.error(
            json.dumps(
                {
                    'event': 'request.error',
                    'status_code': 500,
                    'duration_ms': duration_ms,
                    **_request_log_context(request),
                    'kind': exc.__class__.__name__,
                    'message': str(exc) or exc.__class__.__name__,
                },
                default=str,
            )
        )

        if capture_enabled:
            record_request(
                request_id=request_id,
                user_id=user_id,
                method=request.method,
                path=path,
                status_code=500,
                duration_ms=duration_ms,
                client_ip=client_ip,
                country=country,
                user_agent=request.headers.get('user-agent'),
                referer=request.headers.get('referer'),
            )
        raise

    duration_ms = int((time.perf_counter() - start) * 1000)
    client_ip = None
    country = None
    if capture_enabled:
        client_ip = extract_client_ip(dict(request.headers), getattr(request.client, 'host', None))
        country = extract_country(dict(request.headers))

    # Attach IDs so they show up in browser devtools + downstream logs.
    try:
        response.headers['x-request-id'] = request_id
    except Exception:
        pass

    if should_set_user_cookie:
        try:
            response.set_cookie(
                key=_user_id_cookie_name(),
                value=user_id,
                max_age=_user_id_cookie_max_age_seconds(),
                httponly=True,
                samesite='lax',
                secure=_request_is_https(request),
                path='/',
            )
        except Exception:
            pass

    logger.info(
        json.dumps(
            {
                'event': 'request',
                'status_code': getattr(response, 'status_code', 200),
                'duration_ms': duration_ms,
                **_request_log_context(request),
            },
            default=str,
        )
    )

    if capture_enabled:
        record_request(
            request_id=request_id,
            user_id=user_id,
            method=request.method,
            path=path,
            status_code=getattr(response, 'status_code', 200),
            duration_ms=duration_ms,
            client_ip=client_ip,
            country=country,
            user_agent=request.headers.get('user-agent'),
            referer=request.headers.get('referer'),
        )
    return response
