#!/usr/bin/env python3
"""
FastAPI Example - Shared Core
=============================

The pieces every example route module shares: the `router` for the home page and
`/vendor/*` assets, the Jinja2 `templates` environment, the style and CSP
middleware, `log_timing`, and the `_material_variant`/`_variant_query`/
`create_refer_path` helpers. The routes themselves live in examples/routes/, one
module per catalog section (see examples/catalog.py).

App bootstrapping (FastAPI() construction, session middleware, static mount, the
uvicorn entrypoint) lives in main.py, which mounts this module's `router` and
each examples/routes/ router via `app.include_router(...)`.

This module is imported, never run directly — see main.py for the entrypoint
(`python examples/main.py` or `uvicorn main:app` from within examples/).
"""

import os
import secrets
import time
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


from pydantic_schemaforms import (
    __version__ as _psf_version,
    UploadedFile,
)
from pydantic_schemaforms import (
    bootstrap_icons_css_content,
    csp_nonces,
    read_asset_text,
)

router = APIRouter()


_base_dir = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=_base_dir / 'templates')


@contextmanager
def log_timing(label: str, **context: object):
    """Log how long the wrapped block took -- used to narrow down which
    step of a slow request (form render, CSV parsing, template render, ...)
    is actually the bottleneck, rather than guessing from total request time."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        suffix = ' '.join(f'{key}={value}' for key, value in context.items())
        logger.info(f'{label} took {elapsed_ms:.1f}ms' + (f' ({suffix})' if suffix else ''))


_FORM_STYLES = ('bootstrap', 'material', 'none')


class PreferredStyleMiddleware:
    """Apply the site header's style choice (the sf-style cookie) to any page
    whose URL doesn't name a style, so the choice follows you around the demo."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http' and scope['method'] == 'GET':
            request = Request(scope)
            style = request.cookies.get('sf-style')
            if style in _FORM_STYLES and 'style' not in request.query_params:
                query = scope['query_string']
                joiner = b'&' if query else b''
                scope['query_string'] = query + joiner + f'style={style}'.encode()
        await self.app(scope, receive, send)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Logs total wall-clock time for every request/response -- covers every
    route (including ones nobody hand-wrapped in log_timing, like /vendor/*
    or a page we haven't gotten to yet), so "how long did this page take"
    always has an answer without needing per-route instrumentation."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f'{request.method} {request.url.path} -> {response.status_code} in {elapsed_ms:.1f}ms'
        )
        return response


_CSP_EXEMPT_PATHS = ('/docs', '/redoc')  # FastAPI's own pages load inline scripts from a CDN.


def content_security_policy(nonce: str) -> str:
    return '; '.join(
        [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' https://plausible.devsetgo.com",
            f"style-src 'self' 'nonce-{nonce}'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            "connect-src 'self' https://plausible.devsetgo.com",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'self'",
        ]
    )


class ContentSecurityPolicyMiddleware:
    """Serve every page under a strict policy: no 'unsafe-inline' for scripts or styles.

    One nonce per request goes in the header, in ``request.state.csp_nonce`` for
    the templates' own tags, and to the library through ``csp_nonces``, so every
    render and validate call in the request picks it up without passing it.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'].startswith(_CSP_EXEMPT_PATHS):
            await self.app(scope, receive, send)
            return
        nonce = secrets.token_urlsafe(16)
        scope.setdefault('state', {})['csp_nonce'] = nonce
        policy = content_security_policy(nonce).encode()

        async def send_with_policy(message):
            if message['type'] == 'http.response.start':
                headers = [
                    h for h in message.get('headers', []) if h[0] != b'content-security-policy'
                ]
                message = {**message, 'headers': [*headers, (b'content-security-policy', policy)]}
            await send(message)

        with csp_nonces(script_nonce=nonce, style_nonce=nonce):
            await self.app(scope, receive, send_with_policy)


# Add custom JSON filter that handles date objects
def safe_json_filter(obj):
    """Custom JSON filter that handles date/datetime objects."""
    import json
    from datetime import date, datetime
    from datetime import time as dt_time

    def json_serial(o):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(o, (datetime, date, dt_time)):
            return o.isoformat()
        if isinstance(o, UploadedFile):
            return o.filename
        # Values of Pydantic types (Color, Coordinate, ...) in their JSON form.
        try:
            from pydantic_core import to_jsonable_python

            return to_jsonable_python(o)
        except Exception:  # noqa: BLE001 -- the demo shows anything else as text
            return str(o)

    return json.dumps(obj, indent=2, default=json_serial)


# Register the custom filter
templates.env.filters['safe_json'] = safe_json_filter
templates.env.globals['library_version'] = _psf_version
templates.env.globals['container_version'] = os.getenv('SCHEMAFORMS_DEMO_IMAGE_VERSION', 'dev')


@router.get('/vendor/bootstrap-icons.css', tags=['System'])
async def vendor_bootstrap_icons_css():
    """Serve the vendored Bootstrap Icons CSS with the woff2 font embedded as a data URI."""
    css = bootstrap_icons_css_content()
    return Response(content=css, media_type='text/css')


@router.get('/vendor/md3-tokens.css', tags=['System'])
async def vendor_md3_tokens_css():
    """The Material tokens, for material_base.html's page shell."""
    css = read_asset_text('assets/material/md3-tokens.css')
    return Response(content=css, media_type='text/css')


@router.get('/vendor/htmx.min.js', tags=['System'])
async def vendor_htmx_js():
    """Serve the vendored HTMX JavaScript."""
    js = read_asset_text('assets/vendor/htmx/htmx.min.js')
    return Response(content=js, media_type='application/javascript')


@router.get('/vendor/bootstrap.min.css', tags=['System'])
async def vendor_bootstrap_css():
    """Serve the vendored Bootstrap CSS -- shared_base.html used to pull this
    from cdn.jsdelivr.net as a render-blocking <link>, which added several
    seconds per page load whenever the CDN was slow to reach (e.g. from a
    devcontainer's forwarded browser). Same fix as bootstrap-icons above."""
    css = read_asset_text('assets/vendor/bootstrap/bootstrap.min.css')
    return Response(content=css, media_type='text/css')


@router.get('/vendor/bootstrap.bundle.min.js', tags=['System'])
async def vendor_bootstrap_js():
    """Serve the vendored Bootstrap JS bundle (see vendor_bootstrap_css)."""
    js = read_asset_text('assets/vendor/bootstrap/bootstrap.bundle.min.js')
    return Response(content=js, media_type='application/javascript')


# ================================
# HOME PAGE - ALL EXAMPLES
# ================================


@router.get('/', response_class=HTMLResponse, tags=['System'])
async def home(request: Request):
    """Home page showcasing all form examples."""
    return templates.TemplateResponse(
        request,
        'home.html',
        {
            'request': request,
            'title': 'Forms from Pydantic models',
            'framework': 'fastapi',
            'framework_name': 'FastAPI',
            'framework_type': 'async',
        },
    )


# ================================
# WIDGET GALLERY - TABBED BY INPUT-TYPE CATEGORY
# ================================


def _material_variant(variant: str | None) -> str | None:
    return variant if variant in ('outlined', 'filled') else None


def _variant_query(variant: str | None) -> str:
    return f'&variant={variant}' if _material_variant(variant) else ''


def create_refer_path(request: Request) -> str:
    """Helper function to create referer path with query parameters."""
    referer = request.headers.get('referer', '')
    if referer:
        from urllib.parse import urlparse

        parsed_referer = urlparse(referer)
        referer_path = parsed_referer.path
        referer_query = parsed_referer.query
        full_referer_path = f'{referer_path}?{referer_query}' if referer_query else referer_path
        return full_referer_path
    return '/'
