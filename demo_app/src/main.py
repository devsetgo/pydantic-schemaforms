#!/usr/bin/env python3
"""
FastAPI Example - Async Implementation
=====================================

This example demonstrates ALL Pydantic SchemaForms capabilities in an asynchronous FastAPI application.
It showcases simple, medium, and complex forms with various layouts.

Forms demonstrated:
- Simple: MinimalLoginForm (basic fields, validation)
- Medium: UserRegistrationForm (multiple field types, icons, validation)
- Complex: CompleteShowcaseForm (model lists, dynamic fields, sections, all input types)

Layouts demonstrated:
- Bootstrap styling with external icons
- Material Design 3 styling with external icons
- Self-contained forms (zero dependencies)
- Dynamic list layouts with add/remove functionality
- Sectioned forms with collapsible sections
- All input types (text, email, password, select, number, date, color, range, etc.)
- API-first design with JSON schemas and OpenAPI documentation

Module layout
-------------
- `examples_routes.py` — the library showcase routes (kept in sync with
  lib-examples/fastapi_example.py per CLAUDE.md).
- `app_routes.py` — demo-app-only routes (analytics dashboard, robots/security).
- `middleware.py` — the analytics/anti-scan HTTP middleware.
- `resources.py` — startup/shutdown lifecycle (analytics DB, IP-geo worker).

This file is just the composition root: it creates the app, wires the
middleware/lifespan, and includes the routers above.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import __version__ as _demo_version

from . import app_routes, examples_routes
from .middleware import analytics_middleware
from .resources import lifespan

_openapi_tags = [
    {
        'name': 'Simple Forms',
        'description': 'Minimal login form — basic fields, CSRF protection, and two CSS frameworks.',
    },
    {
        'name': 'Registration',
        'description': 'Medium-complexity registration form with role selection and responsive design.',
    },
    {
        'name': 'Dynamic Lists',
        'description': 'Pet registration — repeating sub-forms (model-list fields) with add/remove controls.',
    },
    {
        'name': 'Showcase',
        'description': 'Complete field showcase and complex layout compositions (tabs, accordions, grids).',
    },
    {
        'name': 'Advanced Nested',
        'description': 'Five-level nested organization hierarchy — the stress test for the rendering engine.',
    },
    {
        'name': 'Self-Contained',
        'description': 'Forms rendered with inline Bootstrap assets — no CDN required.',
    },
    {
        'name': 'Dual-Use: Form + JSON API',
        'description': (
            'One `FormModel` serves both an HTML browser form and a typed JSON endpoint. '
            '`as_api_model()` strips `ui_*` keys so the schema here looks hand-written, '
            'with all validation constraints intact.'
        ),
    },
    {
        'name': 'Generic Form API',
        'description': 'JSON endpoints for schema introspection, server-side rendering, and headless submission.',
    },
    {
        'name': 'System',
        'description': 'Health check and static asset endpoints.',
    },
]


def _load_dotenv_if_present() -> None:
    """Load a local .env file if present.

    This demo intentionally avoids adding dependencies. We only set env vars that
    are not already set in the process environment.
    """
    env_path = Path(__file__).resolve().parents[1] / '.env'
    if not env_path.exists():
        return

    try:
        for raw_line in env_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        # Never fail app startup for a bad .env.
        return


_load_dotenv_if_present()


def _configure_logging() -> logging.Logger:
    """Configure app logging (stdout + optional rotating file).

    Uvicorn will configure its own loggers when run via `uvicorn ...`.
    This config is for running the module directly or in minimal setups.
    """
    level_name = (os.environ.get('LOG_LEVEL') or 'INFO').strip().upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger('schemaforms.demo')
    logger.setLevel(level)

    # Avoid duplicate handlers on reload/import.
    if logger.handlers:
        return logger

    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    log_path = (os.environ.get('LOG_PATH') or '').strip()
    if log_path:
        fh = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    logger.propagate = False
    return logger


logger = _configure_logging()


app = FastAPI(
    title='Pydantic SchemaForms - FastAPI Example',
    description='Comprehensive showcase of pydantic-schemaforms capabilities in async FastAPI',
    version=_demo_version,
    openapi_tags=_openapi_tags,
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SCHEMAFORMS_EXAMPLE_SESSION_SECRET', 'dev-only-change-me'),
    same_site='lax',
    https_only=False,
)

# Analytics/anti-scan middleware (src/middleware.py) — demo-app-only.
app.middleware('http')(analytics_middleware)

_base_dir = Path(__file__).resolve().parent

# Mount /static to serve images (for favicon, etc.)
app.mount('/static', StaticFiles(directory=_base_dir / 'static'), name='static')

app.include_router(examples_routes.router)
app.include_router(app_routes.router)

# Demo-only: the "Demo v..." badge in shared_base.html is guarded by
# `{% if demo_version %}`, so it silently disappears if this template is
# copied into the library's own lib-examples app (which never sets this).
examples_routes.templates.env.globals['demo_version'] = _demo_version
app_routes.templates.env.globals['demo_version'] = _demo_version

app.add_exception_handler(404, app_routes.not_found_handler)
app.add_exception_handler(500, app_routes.server_error_handler)
app.add_exception_handler(Exception, app_routes.unhandled_exception_handler)


# ================================
# RUN APPLICATION
# ================================

if __name__ == '__main__':
    print('🚀 Starting FastAPI Example (Async)')
    print('=' * 60)
    print('📋 Available Examples:')
    print('   • Simple:    http://localhost:8000/login')
    print('   • Medium:    http://localhost:8000/register')
    print('   • Complex:   http://localhost:8000/showcase')
    print('   • Layouts:   http://localhost:8000/layouts')
    print('   • 🚀 STRESS TEST (5 levels deep!): http://localhost:8000/organization')
    print('   • 🏢 Reusable Organization:         http://localhost:8000/organization-shared')
    print('')
    print('🎨 Style Variants (add ?style= to any form):')
    print('   • Bootstrap:       ?style=bootstrap')
    print('   • Material Design: ?style=material')
    print('   • Plain HTML:      ?style=none')
    print('   • Debug Panel:     add ?debug=1')
    print('   • Show Timing:     add ?show_timing=1')
    print('')
    print('🎯 Special Demos:')
    print('   • Live HTMX Validation: http://localhost:8000/live-validation')
    print('   • Self-Contained:       http://localhost:8000/self-contained')
    print('   • API Docs:             http://localhost:8000/docs')
    print('   • Home Page:            http://localhost:8000/')
    print('')
    print('🔗 Dual-Use Demos (form + JSON API from one FormModel):')
    print('   Contact form (str fields):')
    print('   • HTML Form:  http://localhost:8000/contact')
    print('   • JSON API:   POST http://localhost:8000/api/contact')
    print('   • API Schema: http://localhost:8000/api/contact/schema')
    print('   Feedback form (int rating with ge/le constraints):')
    print('   • HTML Form:  http://localhost:8000/feedback')
    print('   • JSON API:   POST http://localhost:8000/api/feedback')
    print('   • API Schema: http://localhost:8000/api/feedback/schema')
    print('')
    print('🔧 API Endpoints:')
    print('   • Schema:              http://localhost:8000/api/forms/register/schema')
    print('   • Pet Schema:          http://localhost:8000/api/forms/pets/schema')
    print('   • Layout Schema:       http://localhost:8000/api/forms/layouts/schema')
    print('   • Organization Schema: http://localhost:8000/api/forms/organization/schema')
    print('   • Org Shared Schema:   http://localhost:8000/api/forms/organization-shared/schema')
    print('   • Render:              http://localhost:8000/api/forms/register/render')
    print('   • Pet Render:          http://localhost:8000/api/forms/pets/render')
    print('   • Layout Render:       http://localhost:8000/api/forms/layouts/render')
    print('   • Organization Render: http://localhost:8000/api/forms/organization/render')
    print('   • Org Shared Render:   http://localhost:8000/api/forms/organization-shared/render')
    print('   • Submit:              POST http://localhost:8000/api/forms/register/submit')
    print('   • Health:              http://localhost:8000/api/health')
    print('=' * 60)
    print('💡 To run this example:')
    print('   make ex-run')
    print('   # OR')
    print('   uvicorn fastapi_example:app --port 8000 --reload')
    print('=' * 60)
