"""Demo-app-only routes: robots/security notices and the analytics dashboard.

None of this has a counterpart in lib-examples; it must never be overwritten
by a library sync (see CLAUDE.md).
"""

import json
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pydantic_schemaforms import __version__ as _psf_version

from .analytics import (
    extract_client_ip,
    get_db_path,
    get_ip_geo_queue_status,
    get_recent_errors,
    get_recent_requests,
    get_summary,
    purge_all,
    record_error,
)
from .middleware import _request_is_https, _request_log_context, logger

router = APIRouter()

_base_dir = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=_base_dir / 'templates')


def _analytics_capture_enabled() -> bool:
    raw = os.environ.get('ANALYTICS_CAPTURE_ENABLED')
    if raw is None:
        return False
    return raw.strip().lower() not in {'0', 'false', 'no', 'off'}


def _analytics_dashboard_enabled() -> bool:
    raw = os.environ.get('ANALYTICS_DASHBOARD_ENABLED')
    if raw is None:
        return False
    return raw.strip().lower() not in {'0', 'false', 'no', 'off'}


@router.get('/robots.txt', response_class=PlainTextResponse, include_in_schema=False)
async def robots_txt(request: Request) -> PlainTextResponse:
    base = str(request.base_url).rstrip('/')
    body = '\n'.join(
        [
            'User-agent: *',
            'Disallow: /api/',
            'Disallow: /docs',
            'Disallow: /openapi.json',
            'Disallow: /dashboard',
            'Disallow: /central',
            'Disallow: /static/',
            'Allow: /',
            '',
            f'# Host: {base}',
        ]
    )
    return PlainTextResponse(content=body, media_type='text/plain; charset=utf-8')


@router.get('/security', response_class=PlainTextResponse, include_in_schema=False)
async def security_notice() -> PlainTextResponse:
    body = '\n'.join(
        [
            'Nothing to see here.',
            '',
            'If you are scanning for exposed logs/.env/credentials: this demo app does not store them under the web root.',
            'Please stop probing random paths.',
            '',
            '(Legit issue? Contact the site owner.)',
        ]
    )
    return PlainTextResponse(content=body, media_type='text/plain; charset=utf-8')


def _dashboard_token_required() -> str:
    """Return the required dashboard token.

    Security posture: fail closed.
    - If DASHBOARD_TOKEN is not configured, dashboards/APIs must not be public.
    """
    if not _analytics_dashboard_enabled():
        raise HTTPException(status_code=404, detail='Not Found')

    token = (os.environ.get('DASHBOARD_TOKEN') or '').strip()
    if not token:
        raise HTTPException(status_code=503, detail='DASHBOARD_TOKEN must be set')
    return token


def _dashboard_cookie_name() -> str:
    return 'schemaforms_dashboard_token'


def _dashboard_cookie_ttl_seconds() -> int:
    # Default to 30 minutes; can be overridden if desired.
    raw = os.environ.get('DASHBOARD_COOKIE_TTL_SECONDS')
    try:
        if raw is None:
            return 30 * 60
        return max(60, int(raw))
    except Exception:
        return 30 * 60


_dashboard_ip_modal_registry: dict[str, dict[str, Any]] = {}


def _dashboard_ip_modal_prune(now: float | None = None) -> None:
    ts = now if now is not None else time.time()
    try:
        for key in list(_dashboard_ip_modal_registry.keys()):
            meta = _dashboard_ip_modal_registry.get(key) or {}
            if float(meta.get('expires_at', 0.0)) <= ts:
                _dashboard_ip_modal_registry.pop(key, None)
    except Exception:
        return


def _dashboard_ip_modal_store(request: Request, payload: dict[str, Any]) -> str:
    now = time.time()
    _dashboard_ip_modal_prune(now)

    key = uuid4().hex
    _dashboard_ip_modal_registry[key] = {
        'payload': payload,
        'user_id': getattr(request.state, 'user_id', None),
        'expires_at': now + float(_dashboard_cookie_ttl_seconds()),
    }
    return key


def _dashboard_ip_modal_lookup(request: Request, lookup_id: str) -> dict[str, Any] | None:
    # Only accept canonical UUID-ish values.
    try:
        UUID(str(lookup_id))
    except Exception:
        return None

    now = time.time()
    _dashboard_ip_modal_prune(now)

    meta = _dashboard_ip_modal_registry.get(str(lookup_id))
    if not meta:
        return None

    expires_at = float(meta.get('expires_at', 0.0))
    if expires_at <= now:
        _dashboard_ip_modal_registry.pop(str(lookup_id), None)
        return None

    expected_user_id = meta.get('user_id')
    current_user_id = getattr(request.state, 'user_id', None)
    if expected_user_id and current_user_id and expected_user_id != current_user_id:
        return None

    payload = meta.get('payload')
    if isinstance(payload, dict):
        return payload
    return None


def _token_from_request(request: Request) -> str:
    header_token = (request.headers.get('x-dashboard-token') or '').strip()
    if header_token:
        return header_token
    return (request.query_params.get('token') or '').strip()


def _maybe_set_dashboard_cookie_from_token(request: Request, response: Response) -> None:
    if not _analytics_dashboard_enabled():
        return

    try:
        required = _dashboard_token_required()
    except HTTPException:
        return

    presented = _token_from_request(request)
    if not presented:
        return

    if presented != required:
        return

    response.set_cookie(
        key=_dashboard_cookie_name(),
        value=required,
        max_age=_dashboard_cookie_ttl_seconds(),
        httponly=True,
        samesite='lax',
        secure=_request_is_https(request),
        path='/',
    )


def _require_dashboard_auth(request: Request) -> None:
    if not _analytics_dashboard_enabled():
        raise HTTPException(status_code=404, detail='Not Found')

    required = _dashboard_token_required()

    # Allow either header auth, query param, or an HttpOnly cookie.
    presented = _token_from_request(request)
    if presented == required:
        return

    cookie_val = (request.cookies.get(_dashboard_cookie_name()) or '').strip()
    if cookie_val == required:
        return
    raise HTTPException(status_code=401, detail='Dashboard token required')


# =========================================================================
# ANALYTICS DASHBOARD
# =========================================================================


@router.get('/api/analytics/summary', tags=['Analytics'], include_in_schema=False)
async def api_analytics_summary(request: Request, days: int = 1, top_n: int = 10):
    _require_dashboard_auth(request)
    summary = get_summary(days=days, top_n=top_n)
    return {
        'since': summary.since_iso,
        'total_requests': summary.total_requests,
        'unique_ips': summary.unique_ips,
        'avg_duration_ms': summary.avg_duration_ms,
        'top_paths': summary.top_paths,
        'status_counts': summary.status_counts,
        'browser_counts': summary.browser_counts,
    }


@router.get('/api/analytics/requests', tags=['Analytics'], include_in_schema=False)
async def api_analytics_requests(request: Request, limit: int = 200):
    _require_dashboard_auth(request)
    return {'requests': get_recent_requests(limit=min(max(limit, 1), 1000))}


@router.get('/api/analytics/errors', tags=['Analytics'], include_in_schema=False)
async def api_analytics_errors(request: Request, limit: int = 200):
    _require_dashboard_auth(request)
    return {'errors': get_recent_errors(limit=min(max(limit, 1), 1000))}


@router.get('/api/analytics/ip-geo', tags=['Analytics'], include_in_schema=False)
async def api_analytics_ip_geo(request: Request):
    _require_dashboard_auth(request)
    return {'ip_geo': get_ip_geo_queue_status()}


@router.post('/api/analytics/purge', tags=['Analytics'], include_in_schema=False)
async def api_analytics_purge(request: Request):
    _require_dashboard_auth(request)
    purge_all()
    return {'status': 'ok'}


@router.get('/central', response_class=HTMLResponse, tags=['Analytics'], include_in_schema=False)
async def central_dashboard(request: Request):
    # Same token-to-cookie flow as /dashboard. Only a query-param token triggers
    # the redirect-and-strip flow; header auth renders directly (no URL to clean).
    required = _dashboard_token_required()
    presented = (request.query_params.get('token') or '').strip()
    if presented:
        if presented != required:
            raise HTTPException(status_code=401, detail='Dashboard token required')

        params = dict(request.query_params)
        params.pop('token', None)
        query = '&'.join(f'{k}={v}' for k, v in params.items() if v is not None and v != '')
        url = '/central' + (f'?{query}' if query else '')

        resp = RedirectResponse(url=url, status_code=303)
        _maybe_set_dashboard_cookie_from_token(request, resp)
        return resp

    _require_dashboard_auth(request)

    ip_geo = get_ip_geo_queue_status()
    token_required = True
    ttl_min = int(_dashboard_cookie_ttl_seconds() / 60)

    def _env(name: str, default: str) -> str:
        val = os.environ.get(name)
        if val is None:
            return default
        return val

    def _env_int(name: str, default: int) -> int:
        try:
            return int(os.environ.get(name) or default)
        except Exception:
            return default

    health = {
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': _psf_version,
    }

    return templates.TemplateResponse(
        request,
        'central_dashboard.html',
        {
            'request': request,
            'app_name': request.app.title,
            'app_version': request.app.version,
            'health': health,
            'ip_geo': ip_geo,
            'ip_geo_enabled': _env('IP_GEO_ENABLED', '0'),
            'ip_geo_worker_enabled': _env('IP_GEO_WORKER_ENABLED', '0'),
            'ip_geo_rate_limit_per_min': _env_int('IP_GEO_RATE_LIMIT_PER_MIN', 40),
            'ip_geo_cache_ttl_days': _env_int('IP_GEO_CACHE_TTL_DAYS', 180),
            'analytics_db_path': get_db_path(),
            'token_required': token_required,
            'ttl_min': ttl_min,
        },
    )


@router.get('/dashboard', response_class=HTMLResponse, tags=['Analytics'], include_in_schema=False)
async def dashboard(request: Request, days: int = 1, limit: int = 50):
    # If a valid token is presented via query param, set/refresh a 30-min cookie
    # and redirect to a clean URL (so the token doesn't stay in the address bar).
    # Header auth renders directly since there's no URL to clean up.
    required = _dashboard_token_required()
    presented = (request.query_params.get('token') or '').strip()
    if presented:
        if presented != required:
            raise HTTPException(status_code=401, detail='Dashboard token required')

        params = dict(request.query_params)
        params.pop('token', None)
        query = '&'.join(f'{k}={v}' for k, v in params.items() if v is not None and v != '')
        url = '/dashboard' + (f'?{query}' if query else '')

        resp = RedirectResponse(url=url, status_code=303)
        _maybe_set_dashboard_cookie_from_token(request, resp)
        return resp

    _require_dashboard_auth(request)

    summary = get_summary(days=days, top_n=10)
    recent = get_recent_requests(limit=min(max(limit, 1), 500))

    # Build per-row UUID lookups so HTMX details fetches don't expose raw IP query params.
    for row in recent:
        try:
            payload = {
                'ts': row.get('ts'),
                'request_id': row.get('request_id'),
                'path': row.get('path'),
                'method': row.get('method'),
                'status_code': row.get('status_code'),
                'client_ip': row.get('client_ip'),
                'location': row.get('location'),
                'country': row.get('country'),
                'country_code': row.get('country_code'),
                'region': row.get('region'),
                'city': row.get('city'),
                'latitude': row.get('latitude'),
                'longitude': row.get('longitude'),
                'ip_geo_provider': row.get('ip_geo_provider'),
                'ip_geo_fetched_at': row.get('ip_geo_fetched_at'),
                'ip_geo_expires_at': row.get('ip_geo_expires_at'),
                'ip_geo_raw_json': row.get('ip_geo_raw_json'),
                'ip_geo_tooltip': row.get('ip_geo_tooltip'),
            }
            row['ip_lookup_id'] = _dashboard_ip_modal_store(request, payload)
        except Exception:
            row['ip_lookup_id'] = None

    recent_errors = get_recent_errors(limit=50)
    ip_geo = get_ip_geo_queue_status()

    token_required = True
    ttl_min = int(_dashboard_cookie_ttl_seconds() / 60)

    return templates.TemplateResponse(
        request,
        'dashboard.html',
        {
            'request': request,
            'summary': summary,
            'recent': recent,
            'recent_errors': recent_errors,
            'ip_geo': ip_geo,
            'token_required': token_required,
            'ttl_min': ttl_min,
        },
    )


@router.get(
    '/dashboard/ip-modal/{lookup_id}',
    response_class=HTMLResponse,
    tags=['Analytics'],
    include_in_schema=False,
)
async def dashboard_ip_modal(request: Request, lookup_id: str):
    _require_dashboard_auth(request)

    payload = _dashboard_ip_modal_lookup(request, lookup_id)
    if not payload:
        raise HTTPException(status_code=404, detail='IP detail lookup not found')

    return templates.TemplateResponse(
        request,
        'ip_modal.html',
        {
            'request': request,
            'row': payload,
        },
    )


@router.get('/dashboard/logout', tags=['Analytics'], include_in_schema=False)
async def dashboard_logout(request: Request):
    resp = RedirectResponse(url='/', status_code=303)
    resp.delete_cookie(key=_dashboard_cookie_name(), path='/')
    return resp


# ============================================================================
# ERROR HANDLERS
# ============================================================================


async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return templates.TemplateResponse(
        request, '404.html', {'request': request, 'framework': 'fastapi'}, status_code=404
    )


async def server_error_handler(request: Request, exc):
    """Handle 500 errors."""
    return templates.TemplateResponse(
        request,
        '500.html',
        {'request': request, 'framework': 'fastapi', 'error': str(exc)},
        status_code=500,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Capture unhandled exceptions for the dashboard."""
    client_ip = extract_client_ip(dict(request.headers), getattr(request.client, 'host', None))

    logger.exception(
        json.dumps(
            {
                'event': 'unhandled_exception',
                **_request_log_context(request),
                'kind': exc.__class__.__name__,
                'message': str(exc) or exc.__class__.__name__,
            },
            default=str,
        )
    )

    if _analytics_capture_enabled():
        record_error(
            request_id=getattr(request.state, 'request_id', None),
            user_id=getattr(request.state, 'user_id', None),
            kind=exc.__class__.__name__,
            message=str(exc) or exc.__class__.__name__,
            detail=traceback.format_exc(),
            path=request.url.path,
            method=request.method,
            status_code=500,
            client_ip=client_ip,
            user_agent=request.headers.get('user-agent'),
        )

    return templates.TemplateResponse(
        request,
        '500.html',
        {'request': request, 'framework': 'fastapi', 'error': str(exc)},
        status_code=500,
    )
