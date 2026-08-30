#!/usr/bin/env python3
"""
FastAPI Example - Composition Root
===================================

Thin entrypoint: FastAPI() construction, session middleware, the static asset
mount, and the uvicorn runner. All routes/endpoints live in fastapi_routes.py
and are attached here via `app.include_router(router)` — see that module's
docstring for what the app actually demonstrates.

Run with:
    python examples/main.py
    # or, from within examples/:
    uvicorn main:app --port 8000 --reload
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.fastapi_routes import RequestTimingMiddleware, router
from examples.datatable_import_example import router as datatable_router
from examples.menu_order_example import router as menu_order_router
from pydantic_schemaforms import __version__ as _psf_version

from dsg_lib.common_functions.logging_config import config_log

if 'pytest' not in sys.modules:
    # config_log() reconfigures the *global* logging module (strips
    # handlers, flips propagate on every logger) -- tests import this
    # module (via examples.main.app) just to get a TestClient, and running
    # it under pytest would leak that reconfiguration into unrelated tests
    # in the same worker process.
    #
    # logging_directory is anchored to this file's own directory (not a
    # bare relative path) because config_log()'s SafeFileSink opens the log
    # file relative to the process's cwd, which varies by how this app is
    # started: `make ex-run` cd's into examples/ first, but the demo
    # Docker image runs `uvicorn examples.main:app` from /app -- a bare
    # 'logs' would then resolve to a directory that's never created.
    _logs_dir = Path(__file__).resolve().parent / 'logs'
    _logs_dir.mkdir(parents=True, exist_ok=True)
    config_log(
        logging_directory=str(_logs_dir),  # Directory for storing logs
        log_name='log',  # Base name for log files
        logging_level='DEBUG',  # Minimum logging level
        log_rotation='100 MB',  # Size threshold for log rotation
        log_retention='30 days',  # Duration to retain old log files
        enqueue=True,  # Enqueue log messages
        log_propagate=False,  # Control log propagation
    )


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
    {
        'name': 'CSV Import (DataTableLayout)',
        'description': 'DataTableLayout — a file input for CSV import paired with an HTML table, validated row-by-row against a Pydantic model and progressively enhanced by DataTables.js.',
    },
]

app = FastAPI(
    title='Pydantic SchemaForms - FastAPI Example',
    description='Comprehensive showcase of pydantic-schemaforms capabilities in async FastAPI',
    version=_psf_version,
    openapi_tags=_openapi_tags,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SCHEMAFORMS_EXAMPLE_SESSION_SECRET', 'dev-only-change-me'),
    same_site='lax',
    https_only=False,
)
# Added last so it's outermost -- times the whole request/response cycle,
# session middleware included, for every route.
app.add_middleware(RequestTimingMiddleware)

_base_dir = Path(__file__).resolve().parent

# Mount /static to serve images (for favicon, etc.)
app.mount('/static', StaticFiles(directory=_base_dir / 'img'), name='static')

app.include_router(router)
app.include_router(datatable_router)
app.include_router(menu_order_router)


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
    print('   uvicorn main:app --port 8000 --reload')
    print('=' * 60)
