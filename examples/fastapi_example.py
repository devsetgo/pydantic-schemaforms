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
"""

import os
import hmac
import secrets
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.shared_models import (  # Simple Form; Medium Form; Complex Form; Pet Forms; Layout Demonstration; Utility functions
    CompanyOrganizationForm,
    CompleteShowcaseForm,
    LayoutDemonstrationForm,
    MinimalLoginForm,
    PetRegistrationForm,
    UserRegistrationForm,
    create_sample_nested_data,
)
from examples.nested_forms_example import create_comprehensive_sample_data

from pydantic_schemaforms import __version__ as _psf_version
from pydantic_schemaforms import render_form_html_async
from pydantic_schemaforms.assets.runtime import bootstrap_icons_css_content
from pydantic_schemaforms.form_data import parse_nested_form_data
from pydantic_schemaforms import FormLayoutBase

app = FastAPI(
    title='Pydantic SchemaForms - FastAPI Example',
    description='Comprehensive showcase of pydantic-schemaforms capabilities in async FastAPI',
    version=_psf_version,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SCHEMAFORMS_EXAMPLE_SESSION_SECRET', 'dev-only-change-me'),
    same_site='lax',
    https_only=False,
)

LOGIN_CSRF_SESSION_KEY = 'login_csrf_token'
REGISTER_CSRF_SESSION_KEY = 'register_csrf_token'


def issue_login_csrf_token(request: Request) -> str:
    """Issue and persist a CSRF token for the login demo flow."""
    token = secrets.token_urlsafe(32)
    request.session[LOGIN_CSRF_SESSION_KEY] = token
    return token


def verify_login_csrf_token(request: Request, submitted_token) -> bool:
    """Verify a submitted token against the session token using constant-time compare."""
    expected_token = request.session.get(LOGIN_CSRF_SESSION_KEY)
    if not expected_token or not submitted_token:
        return False
    return hmac.compare_digest(str(expected_token), str(submitted_token))


def issue_register_csrf_token(request: Request) -> str:
    """Issue and persist a CSRF token for the registration demo flow."""
    token = secrets.token_urlsafe(32)
    request.session[REGISTER_CSRF_SESSION_KEY] = token
    return token


def verify_register_csrf_token(request: Request, submitted_token) -> bool:
    """Verify a submitted registration token using constant-time compare."""
    expected_token = request.session.get(REGISTER_CSRF_SESSION_KEY)
    if not expected_token or not submitted_token:
        return False
    return hmac.compare_digest(str(expected_token), str(submitted_token))


_base_dir = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=_base_dir / 'templates')


# Add custom JSON filter that handles date objects
def safe_json_filter(obj):
    """Custom JSON filter that handles date/datetime objects."""
    import json
    from datetime import date, datetime

    def json_serial(o):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        # Handle layout objects (TabbedLayout, VerticalLayout, etc.)
        elif isinstance(o, FormLayoutBase):
            layout_name = o.__class__.__name__
            tab_names = []
            if hasattr(o, '_get_layouts'):
                try:
                    tab_names = [name for name, _ in o._get_layouts()]
                except Exception:
                    tab_names = []
            payload = {
                'type': layout_name,
                'description': f'Layout object: {layout_name}',
            }
            if tab_names:
                payload['tabs'] = tab_names
            return payload
        # Handle other common non-serializable objects
        elif hasattr(o, '__dict__'):
            return str(o)
        raise TypeError(f'Object of type {type(o)} is not JSON serializable')

    return json.dumps(obj, indent=2, default=json_serial)


# Register the custom filter
templates.env.filters['safe_json'] = safe_json_filter


# Mount /static to serve images (for favicon, etc.)
app.mount('/static', StaticFiles(directory=_base_dir / 'img'), name='static')


@app.get('/vendor/bootstrap-icons.css')
async def vendor_bootstrap_icons_css():
    """Serve the vendored Bootstrap Icons CSS with the woff2 font embedded as a data URI."""
    css = bootstrap_icons_css_content()
    return Response(content=css, media_type='text/css')


def render_self_contained_demo_page(selected_style: str, form_html: str, renderer_name: str) -> str:
    """Build the self-contained demo page shared by GET/POST handlers."""
    escaped_form_html = form_html.replace('<', '&lt;').replace('>', '&gt;')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Self-Contained Form Demo</title>
</head>
<body style="max-width: 600px; margin: 50px auto; padding: 20px; font-family: system-ui;">
    <h1>Self-Contained Form Demo (FastAPI)</h1>
    <p><strong>This form includes ZERO external dependencies!</strong></p>
    <p><strong>Selected Style:</strong> <code>{selected_style}</code></p>
    <p>Everything needed is embedded in the form HTML below:</p>

    <div style="border: 2px solid #dee2e6; border-radius: 8px; padding: 20px; background: #f8f9fa;">
        {form_html}
    </div>

    <div style="margin-top: 30px; padding: 20px; background: #e7f3ff; border-radius: 8px;">
        <h3>What's Included:</h3>
        <ul>
            <li>Self-contained form HTML for style <code>{selected_style}</code></li>
            <li>JavaScript for interactions</li>
            <li>Form validation and styling</li>
            <li>No external CDN dependencies</li>
        </ul>
        <p><strong>Template Usage:</strong> <code>&lt;div&gt;{{{{ form_html | safe }}}}&lt;/div&gt;</code></p>
    </div>

    <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
        <h3>Raw HTML Source:</h3>
        <p>This is the complete HTML generated by <code>{renderer_name}</code>:</p>
        <details style="margin-top: 15px;">
            <summary style="cursor: pointer; font-weight: bold; padding: 10px; background: #fff; border: 1px solid #ddd; border-radius: 4px;">
                Click to view raw HTML source
            </summary>
            <pre style="background: #f8f9fa; padding: 15px; border: 1px solid #dee2e6; border-radius: 4px; overflow-x: auto; font-size: 12px; margin-top: 10px; white-space: pre-wrap; word-wrap: break-word;"><code>{escaped_form_html}</code></pre>
        </details>
    </div>

    <div style="text-align: center; margin-top: 30px;">
        <a href="/" style="color: #0066cc; text-decoration: none;">← Back to FastAPI Examples</a>
    </div>
</body>
</html>"""


# ================================
# HOME PAGE - ALL EXAMPLES
# ================================


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    """Home page showcasing all form examples."""
    return templates.TemplateResponse(
        request,
        'home.html',
        {
            'request': request,
            'framework': 'fastapi',
            'framework_name': 'FastAPI',
            'framework_type': 'async',
        },
    )


# ================================
# SIMPLE FORM - LOGIN
# ================================


@app.get('/login', response_class=HTMLResponse)
async def login_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Simple form example - Login form (GET)."""
    csrf_token = issue_login_csrf_token(request)

    # Parse optional pre-fill data or use demo data
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo or not data:
        # Add demo data for easier testing
        form_data = {'username': 'demo_user', 'password': 'demo_pass', 'remember_me': True}

    form_html = await render_form_html_async(
        MinimalLoginForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/login?style={style}',
        csrf_mode='required-provider',
        csrf_token_provider=csrf_token,
        csrf_field_name='csrf_token',
        debug=debug,
        show_timing=show_timing,
        enable_logging=False,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Login - Simple Form',
            'description': 'Demonstrates basic form fields, validation, and CSRF protection',
            'security_highlight': 'CSRF demo enabled: token is issued on GET and verified before validation on POST.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@app.post('/login', response_class=HTMLResponse)
async def login_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Simple form example - Login form submission (async)."""
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = dict(form_data)

    submitted_csrf_token = form_dict.pop('csrf_token', None)
    csrf_error = 'CSRF verification failed. Refresh the page and submit again.'
    if not verify_login_csrf_token(request, submitted_csrf_token):
        csrf_token = issue_login_csrf_token(request)
        parsed_data = parse_nested_form_data(form_dict)

        form_html = await render_form_html_async(
            MinimalLoginForm,
            framework=style,
            form_data=parsed_data,
            errors={'form': csrf_error},
            submit_url=f'/login?style={style}',
            csrf_mode='required-provider',
            csrf_token_provider=csrf_token,
            csrf_field_name='csrf_token',
            debug=debug,
            show_timing=show_timing,
            enable_logging=True,
        )

        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': 'Login - Simple Form',
                'description': 'Demonstrates basic form fields, validation, and CSRF protection',
                'security_highlight': 'CSRF demo enabled: token is issued on GET and verified before validation on POST.',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': {'form': csrf_error},
            },
            status_code=403,
        )

    parsed_data = parse_nested_form_data(form_dict)
    validation = MinimalLoginForm.validate(
        parsed_data,
        submit_url=f'/login?style={style}',
        framework=style,
        debug=debug,
        show_timing=show_timing,
        csrf_mode='required-provider',
        csrf_field_name='csrf_token',
    )

    full_referer_path = create_refer_path(request)
    if validation.is_valid:
        request.session.pop(LOGIN_CSRF_SESSION_KEY, None)
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Login Successful',
                'message': f'Welcome {validation.data["username"]}!',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )
    else:
        csrf_token = issue_login_csrf_token(request)
        form_html = await validation.render_with_errors_async(
            csrf_token_provider=csrf_token,
            enable_logging=True,
        )

        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': 'Login - Simple Form',
                'description': 'Demonstrates basic form fields, validation, and CSRF protection',
                'security_highlight': 'CSRF demo enabled: token is issued on GET and verified before validation on POST.',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': validation.errors,
            },
        )


# ================================
# MEDIUM FORM - USER REGISTRATION
# ================================


@app.get('/register', response_class=HTMLResponse)
async def register_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Medium complexity form - User registration (GET)."""
    csrf_token = issue_register_csrf_token(request)

    # Parse optional pre-fill data or use demo data
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo or not data:
        # Add demo data for easier testing
        form_data = {
            'username': 'alex_johnson',
            'email': 'alex.johnson@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'age': 28,
            'role': 'user',
        }

    form_html = await render_form_html_async(
        UserRegistrationForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/register?style={style}',
        csrf_mode='required-provider',
        csrf_token_provider=csrf_token,
        csrf_field_name='csrf_token',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'User Registration - Medium Form',
            'description': 'Demonstrates multiple field types, icons, validation, and CSRF protection',
            'security_highlight': 'CSRF demo enabled: token is issued on GET and verified before validation on POST.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


# Alias for /user route (used in templates)
@app.get('/user', response_class=HTMLResponse)
async def user_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Alias for user registration form."""
    return await register_get(request, style, data, demo, debug, show_timing)


@app.post('/register', response_class=HTMLResponse)
async def register_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Medium complexity form - User registration submission (async)."""
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = dict(form_data)

    submitted_csrf_token = form_dict.pop('csrf_token', None)
    csrf_error = 'CSRF verification failed. Refresh the page and submit again.'
    if not verify_register_csrf_token(request, submitted_csrf_token):
        csrf_token = issue_register_csrf_token(request)
        parsed_data = parse_nested_form_data(form_dict)

        form_html = await render_form_html_async(
            UserRegistrationForm,
            framework=style,
            form_data=parsed_data,
            errors={'form': csrf_error},
            submit_url=f'/register?style={style}',
            csrf_mode='required-provider',
            csrf_token_provider=csrf_token,
            csrf_field_name='csrf_token',
            debug=debug,
            show_timing=show_timing,
            enable_logging=True,
        )

        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': 'User Registration - Medium Form',
                'description': 'Demonstrates multiple field types, icons, validation, and CSRF protection',
                'security_highlight': 'CSRF demo enabled: token is issued on GET and verified before validation on POST.',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': {'form': csrf_error},
            },
            status_code=403,
        )

    parsed_data = parse_nested_form_data(form_dict)
    validation = UserRegistrationForm.validate(
        parsed_data,
        submit_url=f'/register?style={style}',
        framework=style,
        debug=debug,
        show_timing=show_timing,
        csrf_mode='required-provider',
        csrf_field_name='csrf_token',
    )

    full_referer_path = create_refer_path(request)
    if validation.is_valid:
        request.session.pop(REGISTER_CSRF_SESSION_KEY, None)
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Registration Successful',
                'message': f'Welcome {validation.data["username"]}! Your account has been created.',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )
    else:
        csrf_token = issue_register_csrf_token(request)
        form_html = await validation.render_with_errors_async(
            csrf_token_provider=csrf_token,
        )

        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': 'User Registration - Medium Form',
                'description': 'Demonstrates multiple field types, icons, validation, and CSRF protection',
                'security_highlight': 'CSRF demo enabled: token is issued on GET and verified before validation on POST.',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': validation.errors,
            },
        )


# ================================
# COMPLEX FORM - COMPLETE SHOWCASE
# ================================


@app.get('/showcase', response_class=HTMLResponse)
async def showcase_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Complex form example - All features and field types (GET)."""
    # Parse optional pre-fill data or use demo data
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo:
        # Add comprehensive demo data for all showcase features
        form_data = {
            'first_name': 'Demo',
            'last_name': 'Showcase User',
            'email': 'showcase@example.com',
            'bio': 'This is a demo biography showcasing the textarea field with rich content. It demonstrates how longer text content appears in the form.',
            'age': 32,
            'birth_date': '1991-08-15',
            'phone': '+1 (555) 123-4567',
            'country': 'US',
            'favorite_color': '#3498db',
            'experience_level': 'advanced',
            'newsletter_subscription': True,
            'newsletter': True,
        }

    form_html = await render_form_html_async(
        CompleteShowcaseForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/showcase?style={style}',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Complete Showcase - Complex Form',
            'description': 'Demonstrates ALL library features: model lists, sections, all input types',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@app.post('/showcase', response_class=HTMLResponse)
async def showcase_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Complex form example - All features submission (async)."""
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = dict(form_data)

    parsed_data = parse_nested_form_data(form_dict)
    validation = CompleteShowcaseForm.validate(
        parsed_data,
        submit_url=f'/showcase?style={style}',
        framework=style,
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    full_referer_path = create_refer_path(request)
    if validation.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Showcase Form Submitted Successfully',
                'message': 'All form data processed successfully!',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )
    else:
        form_html = await validation.render_with_errors_async()
        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': 'Complete Showcase - Complex Form',
                'description': 'Demonstrates ALL library features: model lists, sections, all input types',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': validation.errors,
            },
        )


# ================================
# SPECIAL DEMOS
# ================================


# Alias routes for template compatibility
@app.get('/pets', response_class=HTMLResponse)
async def pets_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Pet registration form - demonstrates dynamic lists and complex models."""
    # Parse optional pre-fill data or use demo data
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo:
        # Add demo data for pet registration
        form_data = {
            'owner_name': 'Sarah Thompson',
            'email': 'sarah.thompson@email.com',
            'address': '5 Marine Parade, ',
            'emergency_contact': 'Mike Thompson - (555) 123-4567',
            'pets': [
                {
                    'name': 'Tweety',
                    'species': 'bird',
                    'breed': 'Canary',
                    'age': 2,
                    'weight': 0.02,
                    'microchipped': False,
                    'last_vet_visit': '2024-11-01',
                    'special_needs': 'Requires daily singing practice and fresh seed mix',
                },
                {
                    'name': 'Buddy',
                    'species': 'dog',
                    'breed': 'Golden Retriever',
                    'age': 3,
                    'weight': 65.5,
                    'microchipped': True,
                    'last_vet_visit': '2024-10-15',
                    'special_needs': 'Needs daily medication for hip dysplasia',
                },
                {
                    'name': 'Whiskers',
                    'species': 'cat',
                    'breed': 'Maine Coon',
                    'age': 5,
                    'weight': 12.3,
                    'microchipped': True,
                    'last_vet_visit': '2024-09-20',
                    'special_needs': 'Indoor only, sensitive to loud noises',
                },
                {
                    'name': 'Nemo',
                    'species': 'fish',
                    'breed': 'Clownfish',
                    'age': 1,
                    'weight': 0.1,
                    'microchipped': False,
                    'last_vet_visit': '2024-08-12',
                    'special_needs': 'Saltwater aquarium with anemone, pH monitoring',
                },
                {
                    'name': 'Bunny',
                    'species': 'rabbit',
                    'breed': 'Holland Lop',
                    'age': 4,
                    'weight': 3.2,
                    'microchipped': True,
                    'last_vet_visit': '2024-09-05',
                    'special_needs': 'High-fiber diet, daily exercise in secure area',
                },
                {
                    'name': 'Peanut',
                    'species': 'hamster',
                    'breed': 'Syrian Hamster',
                    'age': 1,
                    'weight': 0.12,
                    'microchipped': False,
                    'last_vet_visit': '2024-07-22',
                    'special_needs': 'Nocturnal, needs quiet during day, wheel for exercise',
                },
                {
                    'name': 'Scales',
                    'species': 'reptile',
                    'breed': 'Bearded Dragon',
                    'age': 6,
                    'weight': 0.4,
                    'microchipped': False,
                    'last_vet_visit': '2024-10-30',
                    'special_needs': 'UV lighting, temperature gradient 75-105°F, live insects',
                },
                {
                    'name': 'Chester',
                    'species': 'other',
                    'breed': 'Chinchilla',
                    'age': 3,
                    'weight': 0.6,
                    'microchipped': False,
                    'last_vet_visit': '2024-09-18',
                    'special_needs': 'Dust baths only, no water baths, cool temperature',
                },
                {
                    'name': 'Coco',
                    'species': 'bird',
                    'breed': 'African Grey Parrot',
                    'age': 12,
                    'weight': 0.45,
                    'microchipped': True,
                    'is_vaccinated': True,
                    'last_vet_visit': '2024-11-10',
                    'special_needs': 'Highly intelligent, requires 4+ hours of interaction daily',
                },
                {
                    'name': 'Gizmo',
                    'species': 'other',
                    'breed': 'Ferret',
                    'age': 2,
                    'weight': 0.8,
                    'microchipped': True,
                    'is_vaccinated': True,
                    'last_vet_visit': '2024-10-22',
                    'special_needs': 'Annual distemper and rabies vaccines required; needs ferret-proofed play area',
                },
            ],
        }

    form_html = await render_form_html_async(
        PetRegistrationForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/pets?style={style}',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Pet Registration - Dynamic Lists',
            'description': 'Demonstrates pet registration with dynamic lists and owner information',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@app.post('/pets', response_class=HTMLResponse)
async def pets_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Pet registration form submission."""
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = dict(form_data)

    parsed_data = parse_nested_form_data(form_dict)
    validation = PetRegistrationForm.validate(
        parsed_data,
        submit_url=f'/pets?style={style}',
        framework=style,
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    full_referer_path = create_refer_path(request)
    if validation.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Pet Registration Successful',
                'message': f'Successfully registered pets for {validation.data["owner_name"]}!',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )
    else:
        form_html = await validation.render_with_errors_async()
        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': 'Pet Registration - Dynamic Lists',
                'description': 'Demonstrates pet registration with dynamic lists and owner information',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': validation.errors,
            },
        )


# All framework-specific endpoints removed in favor of cleaner style parameter approach
# Use: /pets?style=bootstrap, /login?style=material, etc.

# ================================
# STRESS TEST - DEEPLY NESTED FORMS
# ================================


@app.get('/organization', response_class=HTMLResponse)
async def organization_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = True,
    show_timing: bool = True,
):
    """
    Comprehensive Tabbed Interface with 6 tabs!

    Demonstrates the library's ability to handle:
    1. Organization Tab - 5 levels deep nested structure
    2. Kitchen Sink Tab - ALL input types in one place
    3. Contact Management Tab - Advanced contact forms
    4. Scheduling Tab - Date/time management with events
    5. Media & Files Tab - Color themes and preferences
    6. Settings Tab - Application settings and notifications

        Educational note:
        - This route intentionally uses the original `nested_forms_example` module,
            so users can explore the full end-to-end stress-test form.
        - A reusable organization-only variant is exposed at
            `/organization-shared` using models from `shared_models.py`.
    """
    # Parse optional pre-fill data or use demo data
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo:
        # Use comprehensive sample data for all tabs
        form_data = create_comprehensive_sample_data()

    # Import locally to keep this route explicitly tied to the full nested demo.
    # This makes it clear which module provides the comprehensive tabbed layout.
    from examples.nested_forms_example import ComprehensiveTabbedForm

    form_html = await render_form_html_async(
        ComprehensiveTabbedForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/organization?style={style}',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Comprehensive Tabbed Interface - 6 Tabs! 🚀',
            'description': 'Ultimate showcase: Organization (5 levels deep) + Kitchen Sink (ALL inputs) + Contacts + Scheduling + Media + Settings',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@app.post('/organization', response_class=HTMLResponse)
async def organization_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """
    Handle submission for the full 6-tab comprehensive nested example.

    The submission path demonstrates how raw HTML form payloads are validated
    against the tabbed root model and then rendered in success/error templates.
    """
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = dict(form_data)

    from examples.nested_forms_example import ComprehensiveTabbedForm

    parsed_data = parse_nested_form_data(form_dict)
    validation = ComprehensiveTabbedForm.validate(
        parsed_data,
        submit_url=f'/organization?style={style}',
        framework=style,
        debug=debug,
        show_timing=show_timing,
    )
    full_referer_path = create_refer_path(request)

    if validation.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Comprehensive Form Submitted Successfully! 🎉',
                'message': 'All 6 tabs of data have been successfully processed!',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )
    else:
        form_html = await validation.render_with_errors_async()
        return templates.TemplateResponse(
            request,
            'form.html',
            {
                'request': request,
                'title': 'Comprehensive Tabbed Interface - 6 Tabs! 🚀',
                'description': 'Ultimate showcase: Organization (5 levels deep) + Kitchen Sink (ALL inputs) + Contacts + Scheduling + Media + Settings',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': validation.errors,
            },
        )


@app.get('/organization-shared', response_class=HTMLResponse)
async def organization_shared_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = True,
    show_timing: bool = True,
):
    """
    Organization-only demo reusing shared models.

    This route is the reusable counterpart to `/organization` and shows how to
    render a deeply nested form directly from models in `shared_models.py`.
    """
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass
    elif demo:
        # Seed with realistic nested data so users can inspect structure quickly.
        form_data = create_sample_nested_data()

    form_html = await render_form_html_async(
        CompanyOrganizationForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/organization-shared?style={style}',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Organization (Shared Models) - 5 Levels Deep 🏢',
            'description': 'Reusable organization-only example powered by models in shared_models.py.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@app.post('/organization-shared', response_class=HTMLResponse)
async def organization_shared_post(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = True,
):
    """
    Handle organization-only shared form submission.

    Uses the shared `CompanyOrganizationForm` to demonstrate that the same
    model can power multiple framework routes and API endpoints.
    """
    form_data = await request.form()
    form_dict = dict(form_data)

    parsed_data = parse_nested_form_data(form_dict)
    validation = CompanyOrganizationForm.validate(
        parsed_data,
        submit_url=f'/organization-shared?style={style}',
        framework=style,
        debug=debug,
        show_timing=show_timing,
    )
    full_referer_path = create_refer_path(request)

    if validation.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Organization Shared Form Submitted Successfully! 🎉',
                'message': 'Organization hierarchy data has been successfully processed!',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )

    form_html = await validation.render_with_errors_async()
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Organization (Shared Models) - 5 Levels Deep 🏢',
            'description': 'Reusable organization-only example powered by models in shared_models.py.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
            'errors': validation.errors,
        },
    )


@app.get('/layouts', response_class=HTMLResponse)
async def layouts_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Comprehensive layout demonstration - single form showcasing all layout types."""
    # Parse optional pre-fill data or use demo data
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo or not data:
        # Add demo data for easier testing of all layout types
        form_data = {
            'vertical_tab': {
                'first_name': 'Alex',
                'last_name': 'Johnson',
                'email': 'alex.johnson@example.com',
                'birth_date': '1990-05-15',
            },
            'horizontal_tab': {
                'phone': '+1 (555) 987-6543',
                'address': '456 Demo Street',
                'city': 'San Francisco',
                'postal_code': '94102',
            },
            'tabbed_tab': {
                'notification_email': True,
                'notification_sms': False,
                'theme': 'dark',
                'language': 'en',
            },
            'list_tab': {
                'project_name': 'Demo Project',
                'tasks': [
                    {
                        'task_name': 'Complete project setup',
                        'priority': 'high',
                        'due_date': '2024-12-01',
                    },
                    {
                        'task_name': 'Write documentation',
                        'priority': 'medium',
                        'due_date': '2024-12-15',
                    },
                ],
            },
        }

    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.html_markers import wrap_with_schemaforms_markers

    renderer = EnhancedFormRenderer(framework=style)
    form_html = await renderer.render_form_from_model_async(
        LayoutDemonstrationForm,
        data=form_data,
        errors={},
        submit_url=f'/layouts?style={style}',
        include_submit_button=True,
        debug=debug,
        show_timing=show_timing,
    )
    form_html = wrap_with_schemaforms_markers(form_html)
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Layout Demonstration - All Types',
            'description': 'Single form showcasing Vertical, Horizontal, Tabbed, and List layouts',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@app.post('/layouts', response_class=HTMLResponse)
async def layouts_post(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = True,
):
    """Handle comprehensive layout demonstration form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    full_referer_path = create_refer_path(request)

    parsed_data = parse_nested_form_data(form_dict)
    validation = LayoutDemonstrationForm.validate(parsed_data)

    if validation.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Layout Demo Submitted Successfully',
                'message': 'All layout types processed successfully!',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )

    # Re-render the form with validation errors + user data.
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.html_markers import wrap_with_schemaforms_markers

    renderer = EnhancedFormRenderer(framework=style)
    form_html = await renderer.render_form_from_model_async(
        LayoutDemonstrationForm,
        data=parsed_data,
        errors=validation.errors,
        submit_url=f'/layouts?style={style}',
        include_submit_button=True,
        debug=debug,
        show_timing=show_timing,
    )
    form_html = wrap_with_schemaforms_markers(form_html)

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Layout Demonstration - Validation Errors',
            'description': 'Please fix the highlighted fields',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
            'errors': validation.errors,
        },
    )


@app.get('/self-contained', response_class=HTMLResponse)
async def self_contained(
    style: str = 'material',
    demo: bool = True,
    debug: bool = True,
    show_timing: bool = True,
):
    """
    Self-contained form demo with zero external dependencies.

    Important behavior for this example:
    - Uses the core renderer with `self_contained=True`.
    - Posts back to `/self-contained` so submissions work without extra routes.
    - Honors `style` for `bootstrap`, `material`, and `none` (plain HTML).
    """
    from pydantic_schemaforms.html_markers import wrap_with_schemaforms_markers

    selected_style = (style or 'material').lower()
    if selected_style not in {'bootstrap', 'material', 'none'}:
        selected_style = 'material'

    # Add demo data if requested
    form_data = {}
    if demo:
        form_data = {
            'username': 'self_contained_user',
            'email': 'selfcontained@example.com',
            'password': 'DemoPass123!',
            'confirm_password': 'DemoPass123!',
            'full_name': 'Self Contained Demo',
            'age': 25,
            'agree_terms': True,
            'newsletter': False,
        }

    form_html = await render_form_html_async(
        UserRegistrationForm,
        framework=selected_style,
        form_data=form_data,
        submit_url=f'/self-contained?style={selected_style}&demo=false&debug={str(debug).lower()}&show_timing={str(show_timing).lower()}',
        self_contained=True,
        debug=debug,
        show_timing=show_timing,
    )
    form_html = wrap_with_schemaforms_markers(form_html)
    renderer_name = 'EnhancedFormRenderer'
    return render_self_contained_demo_page(selected_style, form_html, renderer_name)


@app.post('/self-contained', response_class=HTMLResponse)
async def self_contained_post(
    request: Request,
    style: str = 'material',
    debug: bool = True,
    show_timing: bool = True,
):
    """
    Handle self-contained form submission.

    This mirrors the GET demo while ensuring form posts are validated against
    `UserRegistrationForm` and errors are rendered back into the same
    self-contained HTML output.
    """
    from pydantic_schemaforms.html_markers import wrap_with_schemaforms_markers

    selected_style = (style or 'material').lower()
    if selected_style not in {'bootstrap', 'material', 'none'}:
        selected_style = 'material'

    form_data = await request.form()
    form_dict = dict(form_data)
    parsed_data = parse_nested_form_data(form_dict)
    _submit_url = f'/self-contained?style={selected_style}&demo=false&debug={str(debug).lower()}&show_timing={str(show_timing).lower()}'
    validation = UserRegistrationForm.validate(
        parsed_data,
        submit_url=_submit_url,
        framework=selected_style,
        self_contained=True,
        debug=debug,
        show_timing=show_timing,
    )

    if validation.is_valid:
        full_referer_path = create_refer_path(request)
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Self-Contained Form Submitted Successfully',
                'message': 'Self-contained registration data processed successfully!',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )

    form_html = await validation.render_with_errors_async()
    form_html = wrap_with_schemaforms_markers(form_html)
    renderer_name = 'EnhancedFormRenderer'
    return render_self_contained_demo_page(selected_style, form_html, renderer_name)


# ================================
# API ENDPOINTS (JSON RESPONSES)
# ================================

# Central registry used by API endpoints below.
#
# Why keep this in one place?
# - It makes it easy for readers to add a new form example in one edit.
# - It guarantees schema/render/submit endpoints all expose the same form set.
# - It demonstrates a clean API-first pattern for SchemaForms integrations.
FORM_REGISTRY = {
    'login': MinimalLoginForm,
    'register': UserRegistrationForm,
    'pets': PetRegistrationForm,
    'showcase': CompleteShowcaseForm,
    'layouts': LayoutDemonstrationForm,
    'organization': CompanyOrganizationForm,
    'organization-shared': CompanyOrganizationForm,
}


@app.get('/api/forms/{form_type}/schema')
async def api_form_schema(form_type: str):
    """
    Return JSON Schema for a form model.

    This endpoint helps users understand how SchemaForms derives field
    definitions directly from Pydantic models.
    """

    if form_type not in FORM_REGISTRY:
        raise HTTPException(status_code=404, detail='Form type not found')

    form_class = FORM_REGISTRY[form_type]
    schema = form_class.model_json_schema()

    return {'form_type': form_type, 'schema': schema, 'framework': 'fastapi'}


@app.post('/api/forms/{form_type}/submit')
async def api_submit_form(form_type: str, request: Request):
    """
    Validate JSON form submissions against a selected Pydantic form model.

    This shows the API workflow behind the HTML examples:
    request payload -> model validation -> normalized data/errors response.
    """

    if form_type not in FORM_REGISTRY:
        raise HTTPException(status_code=404, detail='Form type not found')

    form_class = FORM_REGISTRY[form_type]

    json_data = await request.json()

    validation = form_class.validate(json_data)

    return {
        'success': validation.is_valid,
        'data': validation.data if validation.is_valid else None,
        'errors': validation.errors,
        'framework': 'fastapi',
    }


@app.get('/api/forms/{form_type}/render')
async def api_render_form(
    form_type: str, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """
    Render a form model as HTML and return the markup in JSON.

    Useful for embedding forms in non-templated clients or testing renderer
    output through API calls.
    """

    if form_type not in FORM_REGISTRY:
        raise HTTPException(status_code=404, detail='Form type not found')

    form_class = FORM_REGISTRY[form_type]
    form_html = await render_form_html_async(
        form_class,
        framework=style,
        submit_url=f'/api/forms/{form_type}/submit',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return {'form_type': form_type, 'style': style, 'html': form_html, 'framework': 'fastapi'}


# ================================
# HEALTH CHECK
# ================================


@app.get('/api/health')
async def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'framework': 'fastapi', 'version': _psf_version}


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
    print('   • Self-Contained: http://localhost:8000/self-contained')
    print('   • API Docs:       http://localhost:8000/docs')
    print('   • Home Page:      http://localhost:8000/')
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
