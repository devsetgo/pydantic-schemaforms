#!/usr/bin/env python3
"""
FastAPI Example - Routes
========================

All routes/endpoints for the FastAPI showcase app: forms, dual-use JSON APIs,
live validation, AI instructions, etc. App bootstrapping (FastAPI() construction,
session middleware, static mount, the uvicorn entrypoint) lives in main.py,
which mounts this module's `router` via `app.include_router(router)`.

This module is imported, never run directly — see main.py for the entrypoint
(`python examples/main.py` or `uvicorn main:app` from within examples/).

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

import hmac
import secrets
from pathlib import Path

import markdown as _markdown
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from examples.shared_models import (  # Simple Form; Medium Form; Complex Form; Pet Forms; Layout Demonstration; Utility functions
    SHOWCASE_CAPTCHA_SECRET,
    CompanyOrganizationForm,
    CompleteShowcaseForm,
    LayoutDemonstrationForm,
    MinimalLoginForm,
    PetRegistrationForm,
    UserRegistrationForm,
    WidgetGalleryForm,
    create_sample_nested_data,
)
from examples.nested_forms_example import create_comprehensive_sample_data
from examples.date_time_formats_example import (
    DateTimeFormatsShowcaseForm,
    create_sample_date_time_format_data,
)

from pydantic import EmailStr, field_validator

from pydantic_schemaforms import (
    __version__ as _psf_version,
    EnhancedFormRenderer,
    EmailDeliverabilityRule,
    EmailRule,
    Field,
    FieldValidator,
    FormLayoutBase,
    FormModel,
    HTMXValidationConfig,
    LiveValidator,
    MinLengthRule,
    RequiredRule,
    available_instruction_profiles,
    get_app_instructions,
    parse_nested_form_data,
    render_form_html_async,
    suggested_instruction_filename,
    verify_captcha,
)
from pydantic_schemaforms.assets.runtime import (
    bootstrap_icons_css_content,
    read_asset_text,
)
from pydantic_schemaforms.live_validation import validation_response_headers

router = APIRouter()


# ---------------------------------------------------------------------------
# Dual-use demo: one FormModel, two endpoints (HTML form + JSON API)
# ---------------------------------------------------------------------------


class ContactForm(FormModel):
    """Simple contact form that also serves as a typed JSON API body."""

    name: str = Field(
        ...,
        min_length=2,
        title='Full Name',
        description='Your full name',
        examples=['Alice Smith'],
        ui_element='text',
        ui_placeholder='Enter your full name',
    )
    email: EmailStr = Field(
        ...,
        title='Email Address',
        description='We will never share your email',
        examples=['alice@example.com'],
        ui_element='email',
    )
    message: str = Field(
        ...,
        min_length=10,
        title='Message',
        description='What would you like to say?',
        examples=['Hello, I would like to ask about...'],
        ui_element='textarea',
    )


# Derive the API model once at module level.
# Same fields and validation rules; ui_* keys stripped so OpenAPI docs are clean.
ContactSchema = ContactForm.as_api_model()


# ---------------------------------------------------------------------------
# Second dual-use demo: integer + select fields via as_api_model()
# ---------------------------------------------------------------------------


class FeedbackForm(FormModel):
    """Product feedback form that also serves as a typed JSON API body."""

    subject: str = Field(
        ...,
        title='Subject',
        description='What are you giving feedback on?',
        examples=['Documentation', 'Performance', 'New feature request'],
        ui_element='text',
        ui_placeholder='e.g. Documentation clarity',
    )
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        title='Rating (1–5)',
        description='1 = poor, 5 = excellent',
        examples=[4],
        ui_element='number',
    )
    comment: str = Field(
        '',
        title='Comment',
        description='Any additional details (optional)',
        examples=['Great library, very easy to integrate!'],
        ui_element='textarea',
    )


# ge/le constraints (minimum/maximum) are preserved in the API schema.
FeedbackSchema = FeedbackForm.as_api_model()

# ---------------------------------------------------------------------------
# Live-validation: field-level validators for the /live-validation demo
# ---------------------------------------------------------------------------

_contact_live_validator = LiveValidator(
    HTMXValidationConfig(validate_on_blur=True, validate_on_input=False, validate_on_change=False)
)

_nv = FieldValidator('name')
_nv.add_rule(MinLengthRule(2, message='Name must be at least 2 characters'))
_contact_live_validator.register_field_validator(_nv)

_ev = FieldValidator('email')
_ev.add_rule(RequiredRule(message='Email is required'))
_ev.add_rule(EmailRule())
_contact_live_validator.register_field_validator(_ev)

_mv = FieldValidator('message')
_mv.add_rule(MinLengthRule(10, message='Message must be at least 10 characters'))
_contact_live_validator.register_field_validator(_mv)

# "With vs without DNS/MX check" demo (/email-dns-validation): two fields
# registered on the same live validator/endpoint so the page can show, side
# by side, that a well-formed-but-nonexistent domain passes format-only
# checking (EmailRule) but fails once EmailDeliverabilityRule's real DNS/MX
# lookup is added.
_ev_format_only = FieldValidator('email_format_only')
_ev_format_only.add_rule(RequiredRule(message='Email is required'))
_ev_format_only.add_rule(EmailRule())
_contact_live_validator.register_field_validator(_ev_format_only)

_ev_with_dns = FieldValidator('email_with_dns')
_ev_with_dns.add_rule(RequiredRule(message='Email is required'))
_ev_with_dns.add_rule(EmailRule())
_ev_with_dns.add_rule(EmailDeliverabilityRule(timeout=5))
_contact_live_validator.register_field_validator(_ev_with_dns)

_LIVE_VALIDATOR_SCRIPT = _contact_live_validator.render_htmx_script()

_DNS_HX_ATTRS = {
    'hx-trigger': 'blur',
    'hx-swap': 'innerHTML',
    'data-validate-endpoint': 'true',
}


class EmailDnsComparisonForm(FormModel):
    """Two email fields, otherwise identical, that differ only in whether
    EmailDeliverabilityRule's DNS/MX lookup is enforced — for the
    /email-dns-validation "with vs. without" demo.

    ``ui_options`` attaches the same ``hx-post``/``hx-target`` attributes the
    hand-written /live-validation demo uses, so both fields validate on blur
    through the standard FormModel-rendered inputs (no custom HTML needed).
    The ``email_with_dns`` field_validator mirrors that check at submit time
    too, so a domain that fails the live DNS check also fails on submit
    rather than silently passing.
    """

    email_format_only: EmailStr = Field(
        ...,
        title='Without DNS/MX Check',
        description='EmailRule format check only.',
        examples=['someone@gmail.com'],
        ui_element='email',
        ui_options={
            **_DNS_HX_ATTRS,
            'hx-post': '/validate/email_format_only',
            'hx-target': '#email_format_only-feedback',
        },
    )
    email_with_dns: EmailStr = Field(
        ...,
        title='With DNS/MX Check',
        description="Format check, plus a real DNS lookup for the domain's MX records.",
        examples=['someone@gmail.com'],
        ui_element='email',
        ui_options={
            **_DNS_HX_ATTRS,
            'hx-post': '/validate/email_with_dns',
            'hx-target': '#email_with_dns-feedback',
        },
    )

    @field_validator('email_with_dns')
    @classmethod
    def _check_deliverability(cls, value: str) -> str:
        is_valid, error = EmailDeliverabilityRule().validate(value)
        if not is_valid:
            raise ValueError(error)
        return value


LOGIN_CSRF_SESSION_KEY = 'login_csrf_token'
REGISTER_CSRF_SESSION_KEY = 'register_csrf_token'


def _group_form_data(form_data) -> dict:
    """Build a dict from Starlette FormData without losing repeated keys.

    ``dict(form_data)`` keeps only the last value for a repeated key, which
    silently drops all but one selection from a native ``<select multiple>``
    or several checkboxes sharing one ``name``. Iterating
    ``form_data.multi_items()`` instead preserves every value, grouping
    repeats into a list so parse_nested_form_data() (and the schema-aware
    coercion in validate_form_data()) can turn a single selection back into
    a one-item list and a multi-selection into the full list.
    """
    grouped: dict = {}
    for key, value in form_data.multi_items():
        if key in grouped:
            existing = grouped[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                grouped[key] = [existing, value]
        else:
            grouped[key] = value
    return grouped


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


SHOWCASE_CSRF_SESSION_KEY = 'showcase_csrf_token'


def issue_showcase_csrf_token(request: Request) -> str:
    """Issue and persist a CSRF token for the showcase demo flow."""
    token = secrets.token_urlsafe(32)
    request.session[SHOWCASE_CSRF_SESSION_KEY] = token
    return token


def verify_showcase_csrf_token(request: Request, submitted_token) -> bool:
    """Verify a submitted showcase token using constant-time compare."""
    expected_token = request.session.get(SHOWCASE_CSRF_SESSION_KEY)
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


@router.get('/vendor/bootstrap-icons.css', tags=['System'])
async def vendor_bootstrap_icons_css():
    """Serve the vendored Bootstrap Icons CSS with the woff2 font embedded as a data URI."""
    css = bootstrap_icons_css_content()
    return Response(content=css, media_type='text/css')


@router.get('/vendor/htmx.min.js', tags=['System'])
async def vendor_htmx_js():
    """Serve the vendored HTMX JavaScript."""
    js = read_asset_text('assets/vendor/htmx/htmx.min.js')
    return Response(content=js, media_type='application/javascript')


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


@router.get('/', response_class=HTMLResponse, tags=['System'])
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


@router.get('/login', response_class=HTMLResponse, tags=['Simple Forms'])
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


@router.post('/login', response_class=HTMLResponse, tags=['Simple Forms'])
async def login_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Simple form example - Login form submission (async)."""
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = _group_form_data(form_data)

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


@router.get('/register', response_class=HTMLResponse, tags=['Registration'])
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
            'accept_terms': True,
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
@router.get('/user', response_class=HTMLResponse, include_in_schema=False)
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


@router.post('/register', response_class=HTMLResponse, tags=['Registration'])
async def register_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Medium complexity form - User registration submission (async)."""
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = _group_form_data(form_data)

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


@router.get('/showcase', response_class=HTMLResponse, tags=['Showcase'])
async def showcase_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Complex form example - All features and field types (GET)."""
    csrf_token = issue_showcase_csrf_token(request)

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
            'phone': '(555) 123-4567',
            'country': 'US',
            'favorite_color': '#3498db',
            'experience_level': 'advanced',
            'newsletter_subscription': True,
            'newsletter': True,
            'rating': 8,
            'ssn_field': '123-45-6789',
            'credit_card_field': '4111 1111 1111 1111',
            'currency_field': '$1,234.56',
            'tags_field': 'python,fastapi,pydantic',
            'percentage_field': 75.0,
            'decimal_field': 3.14159,
            'integer_only_field': 42,
            'quantity_field': 3,
            'score_field': 85,
            'star_rating_field': 4,
            'slider_field': 60,
            'temperature_field': 20.0,
            'combobox_field': 'New York',
            'shipping_speed': 'express',
            'checkbox_group_field': ['email', 'push'],
            'month_field': '2024-06',
            'week_field': '2024-W24',
        }

    form_html = await render_form_html_async(
        CompleteShowcaseForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/showcase?style={style}',
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
            'title': 'Complete Showcase - Complex Form',
            'description': 'Demonstrates ALL library features: model lists, sections, all input types',
            'security_highlight': 'CSRF, honeypot spam-trap, and a self-hosted CAPTCHA are all '
            'enabled on this form -- see showcase_post() for the verification logic.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@router.post('/showcase', response_class=HTMLResponse, tags=['Showcase'])
async def showcase_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Complex form example - All features submission (async)."""
    # CompleteShowcaseForm has genuinely multi-value fields (multiselect_field,
    # checkbox_group_field). _group_form_data() preserves repeated keys as a
    # list; validate_form_data()'s schema-aware coercion wraps a lone
    # selection back into a single-item list for any List[<scalar>] field,
    # so no per-field allowlist is needed here.
    form_data = await request.form()
    form_dict = _group_form_data(form_data)

    full_referer_path = create_refer_path(request)

    # Honeypot: real users never see or fill this field in (it's hidden and
    # styled off-screen). A non-empty value means a bot filled every input it
    # could find. Pretend success rather than revealing that it was caught.
    if form_dict.get('honeypot_field'):
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Showcase Form Submitted Successfully',
                'message': 'All form data processed successfully!',
                'data': {},
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )

    submitted_csrf_token = form_dict.pop('csrf_token', None)
    if not verify_showcase_csrf_token(request, submitted_csrf_token):
        csrf_error = 'CSRF verification failed. Refresh the page and submit again.'
        csrf_token = issue_showcase_csrf_token(request)
        parsed_data = parse_nested_form_data(form_dict)

        form_html = await render_form_html_async(
            CompleteShowcaseForm,
            framework=style,
            form_data=parsed_data,
            errors={'form': csrf_error},
            submit_url=f'/showcase?style={style}',
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
                'title': 'Complete Showcase - Complex Form',
                'description': 'Demonstrates ALL library features: model lists, sections, all input types',
                'form_html': form_html,
                'errors': {'form': csrf_error},
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
            },
            status_code=403,
        )

    # CAPTCHA: the visible answer field is 'captcha_answer'; CaptchaInput
    # names its companion hidden token '{field_name}_token' -- see
    # CaptchaInput's docstring for why this is checked here rather than via
    # a @model_validator (the token only exists in the raw POST body, never
    # as a declared model attribute).
    captcha_token = form_dict.pop('captcha_answer_token', None)
    if not verify_captcha(
        token=captcha_token,
        answer=form_dict.get('captcha_answer', ''),
        secret_key=SHOWCASE_CAPTCHA_SECRET,
    ):
        captcha_error = 'Incorrect answer to the verification question. Please try again.'
        csrf_token = issue_showcase_csrf_token(request)
        parsed_data = parse_nested_form_data(form_dict)

        form_html = await render_form_html_async(
            CompleteShowcaseForm,
            framework=style,
            form_data=parsed_data,
            errors={'captcha_answer': captcha_error},
            submit_url=f'/showcase?style={style}',
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
                'title': 'Complete Showcase - Complex Form',
                'description': 'Demonstrates ALL library features: model lists, sections, all input types',
                'form_html': form_html,
                'errors': {'captcha_answer': captcha_error},
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
            },
        )

    parsed_data = parse_nested_form_data(form_dict)
    validation = CompleteShowcaseForm.validate(
        parsed_data,
        submit_url=f'/showcase?style={style}',
        framework=style,
        csrf_mode='required-provider',
        csrf_field_name='csrf_token',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    if validation.is_valid:
        request.session.pop(SHOWCASE_CSRF_SESSION_KEY, None)
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
# WIDGET GALLERY - TABBED BY INPUT-TYPE CATEGORY
# ================================


@router.get('/gallery', response_class=HTMLResponse, tags=['Showcase'])
async def gallery_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Tabbed widget gallery - every input type grouped by category (GET).

    Demo data must be flat (no top-level 'gallery' key): WidgetGalleryForm has
    a single ui_element='layout' field, and supplying a dict under that exact
    field's own name would get accepted as the field's literal value (its
    Pydantic schema is deliberately permissive so layout classes can be used
    as field types at all) instead of the default WidgetGalleryTabs instance,
    breaking the isinstance(value, BaseLayout) check the renderer relies on.
    Flat keys let the renderer's own nested-data reconstruction find each
    tab's fields by name, the same way POST submissions are matched up.
    """
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo:
        # Rendering only ever pre-fills fields explicitly present here -- it
        # never falls back to a field's own Pydantic default for display (that's
        # true of every FormModel in this library, not specific to tabbed/layout
        # fields). Every field gets a value below so the demo doesn't mix
        # populated and blank-looking fields, which reads as broken/scrambled
        # data even though each field is rendering correctly on its own.
        form_data = {
            # Text Inputs
            'text_input': 'Hello, world!',
            'textarea_input': 'This textarea supports\nmultiple lines of text.',
            'password_input': 'demo-password',
            'email_input': 'demo@example.com',
            'search_input': 'pydantic schemaforms',
            'url_input': 'https://example.com',
            'tel_input': '5551234567',
            'phone_input': '(555) 123-4567',
            'ssn_input': '123-45-6789',
            'credit_card_input': '4111 1111 1111 1111',
            'currency_input': '$1,234.56',
            'tags_input': 'python,fastapi,pydantic',
            # Checkboxes & Toggles
            'checkbox_unchecked': False,
            'checkbox_checked': True,
            'toggle_off': False,
            'toggle_on': True,
            'checkbox_group_stacked': ['email', 'push'],
            'checkbox_group_buttons': ['sms'],
            # Numeric Inputs
            'number_input': 42,
            'range_input': 65,
            'percentage_input': 82.5,
            'decimal_input': 3.14,
            'integer_input': 7,
            'age_input': 34,
            'quantity_input': 3,
            'score_input': 91.0,
            'rating_input': 8,
            'star_rating_input': 4,
            'slider_input': 55,
            'temperature_input': 21.5,
            # Selection Inputs
            'select_input': 'medium',
            'multiselect_input': ['python', 'rust'],
            'radio_stacked': 'large',
            'radio_segmented': 'express',
            'combobox_input': 'New York',
            # Date & Time
            'date_input': '2024-06-15',
            'time_input': '14:30',
            'datetime_input': '2024-06-15T14:30',
            'month_input': '2024-06',
            'week_input': '2024-W24',
            'birthdate_input': '1990-01-01',
            # Files & Specialized
            'color_input': '#3498db',
            'hidden_input': 'hidden-demo-value',
        }

    form_html = await render_form_html_async(
        WidgetGalleryForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/gallery?style={style}',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Widget Gallery - Tabbed by Category',
            'description': 'Every input type grouped into tabs: Text, Checkboxes & Toggles, '
            'Numeric, Selection, Date & Time, and Files & Specialized',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@router.post('/gallery', response_class=HTMLResponse, tags=['Showcase'])
async def gallery_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Tabbed widget gallery submission (async)."""
    # Several tabs have genuinely multi-value fields (multiselect_input,
    # checkbox_group_stacked, checkbox_group_buttons). _group_form_data()
    # preserves repeated keys as a list; validate_form_data()'s schema-aware
    # coercion wraps a lone selection back into a single-item list for any
    # List[<scalar>] field, so no per-field allowlist is needed here.
    form_data = await request.form()
    form_dict = _group_form_data(form_data)

    parsed_data = parse_nested_form_data(form_dict)
    validation = WidgetGalleryForm.validate(
        parsed_data,
        submit_url=f'/gallery?style={style}',
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
                'title': 'Widget Gallery Submitted Successfully',
                'message': 'All tabs processed successfully!',
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
                'title': 'Widget Gallery - Tabbed by Category',
                'description': 'Every input type grouped into tabs by category',
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'framework_type': style,
                'form_html': form_html,
                'errors': validation.errors,
            },
        )


# ================================
# DATE/TIME FORMAT SHOWCASE
# ================================


@router.get('/date-time-formats', response_class=HTMLResponse, tags=['Showcase'])
async def date_time_formats_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Custom date/time/datetime display format showcase (GET).

    Demo data must be flat (no top-level 'formats' key) -- same reasoning as
    WidgetGalleryForm's demo route: DateTimeFormatsShowcaseForm has a single
    ui_element='layout' field, so flat keys let the renderer's own nested-data
    reconstruction find each tab's fields by name.
    """
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo:
        form_data = create_sample_date_time_format_data()

    form_html = await render_form_html_async(
        DateTimeFormatsShowcaseForm,
        framework=style,
        form_data=form_data,
        submit_url=f'/date-time-formats?style={style}',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Date/Time Format Showcase',
            'description': (
                'Custom date_format/time_format/datetime_format ui_options: USA, '
                'Europe, Asia, military (24-hour) time, and compact year-month-day '
                'shapes, grouped into Date/Time/Datetime tabs'
            ),
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@router.post('/date-time-formats', response_class=HTMLResponse, tags=['Showcase'])
async def date_time_formats_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Date/time/datetime format showcase submission (async)."""
    form_data = await request.form()
    form_dict = _group_form_data(form_data)

    parsed_data = parse_nested_form_data(form_dict)
    validation = DateTimeFormatsShowcaseForm.validate(
        parsed_data,
        submit_url=f'/date-time-formats?style={style}',
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
                'title': 'Date/Time Formats Submitted Successfully',
                'message': 'Every date/time/datetime format parsed and validated correctly!',
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
                'title': 'Date/Time Format Showcase',
                'description': 'Please fix the highlighted fields',
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
@router.get('/pets', response_class=HTMLResponse, tags=['Dynamic Lists'])
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


@router.post('/pets', response_class=HTMLResponse, tags=['Dynamic Lists'])
async def pets_post(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Pet registration form submission."""
    # Get form data asynchronously
    form_data = await request.form()
    form_dict = _group_form_data(form_data)

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


@router.get('/organization', response_class=HTMLResponse, tags=['Advanced Nested'])
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


@router.post('/organization', response_class=HTMLResponse, tags=['Advanced Nested'])
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
    form_dict = _group_form_data(form_data)

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


@router.get('/organization-shared', response_class=HTMLResponse, tags=['Advanced Nested'])
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


@router.post('/organization-shared', response_class=HTMLResponse, tags=['Advanced Nested'])
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
    form_dict = _group_form_data(form_data)

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


@router.get('/layouts', response_class=HTMLResponse, tags=['Showcase'])
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
            'personal_info': {
                'first_name': 'Alex',
                'last_name': 'Johnson',
                'email': 'alex.johnson@example.com',
                'birth_date': '1990-05-15',
            },
            'contact_info': {
                'phone': '+1 (555) 987-6543',
                'address': '456 Demo Street',
                'city': 'San Francisco',
                'postal_code': '94102',
            },
            'preferences': {
                'notification_email': True,
                'notification_sms': False,
                'theme': 'dark',
                'language': 'en',
            },
            'task_list': {
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


@router.post('/layouts', response_class=HTMLResponse, tags=['Showcase'])
async def layouts_post(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = True,
):
    """Handle comprehensive layout demonstration form submission."""
    form_data = await request.form()
    form_dict = _group_form_data(form_data)
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


@router.get('/self-contained', response_class=HTMLResponse, tags=['Self-Contained'])
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
            'accept_terms': True,
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


@router.post('/self-contained', response_class=HTMLResponse, tags=['Self-Contained'])
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
    form_dict = _group_form_data(form_data)
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


@router.get('/api/forms/{form_type}/schema', tags=['Generic Form API'])
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


@router.get('/api/forms/{form_type}/pydantic-schema', tags=['Generic Form API'])
async def api_form_pydantic_schema(form_type: str):
    """
    Return the standard, nested-aware JSON Schema for the form's underlying
    Pydantic model, via ``get_pydantic_json_schema()``.

    Unlike ``/schema`` above (a flattened, UI-oriented shape used for
    rendering), this includes real ``$defs``/``$ref`` for nested BaseModel
    and List[BaseModel] fields — e.g. try `form_type=organization` to see
    Department/Team/TeamMember/Certification each get their own `$defs`
    entry instead of being collapsed to a generic `string`/`object` type.
    """

    if form_type not in FORM_REGISTRY:
        raise HTTPException(status_code=404, detail='Form type not found')

    form_class = FORM_REGISTRY[form_type]
    schema = form_class.get_pydantic_json_schema()

    return {'form_type': form_type, 'schema': schema, 'framework': 'fastapi'}


@router.post('/api/forms/{form_type}/submit', tags=['Generic Form API'])
async def api_submit_form(form_type: str, request: Request, flatten: bool = False):
    """
    Validate JSON form submissions against a selected Pydantic form model.

    This shows the API workflow behind the HTML examples:
    request payload -> model validation -> normalized data/errors response.

    By default, nested models (e.g. the `organization` form's
    departments -> teams -> members) round-trip as nested JSON, matching the
    shape of the underlying Pydantic model. Pass ``?flatten=true`` to submit
    and receive bracket+dot flat keys instead (e.g.
    ``"departments[0].teams[0].members[0].name"``), which some form-building
    clients prefer.
    """

    if form_type not in FORM_REGISTRY:
        raise HTTPException(status_code=404, detail='Form type not found')

    form_class = FORM_REGISTRY[form_type]

    json_data = await request.json()

    validation = form_class.validate(json_data, flatten=flatten)

    return {
        'success': validation.is_valid,
        'data': validation.data if validation.is_valid else None,
        'errors': validation.errors,
        'framework': 'fastapi',
    }


@router.get('/api/forms/{form_type}/render', tags=['Generic Form API'])
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
# DUAL-USE: FORM + JSON API
# ================================
# One FormModel class serves both a browser form and a typed JSON endpoint.
# ContactForm renders to HTML; ContactSchema (= ContactForm.as_api_model())
# is the clean Pydantic model used by the JSON endpoint — ui_* keys stripped,
# all validation constraints and Field(examples=[...]) preserved.


@router.get('/contact', response_class=HTMLResponse, tags=['Dual-Use: Form + JSON API'])
async def contact_get(
    request: Request,
    style: str = 'bootstrap',
    demo: bool = False,
    debug: bool = False,
    show_timing: bool = False,
):
    """Render the contact form (HTML)."""
    form_data = (
        {
            'name': 'Alice Example',
            'email': 'alice@example.com',
            'message': 'Hello! I have a question about your library.',
        }
        if demo
        else {}
    )
    form_html = await ContactForm.render_form_async(
        submit_url=f'/contact?style={style}',
        framework=style,
        data=form_data,
        debug=debug,
        show_timing=show_timing,
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'title': 'Contact — HTML Form',
            'form_html': form_html,
            'refer_path': '/contact',
            'api_endpoint': '/api/contact',
            'api_schema_endpoint': '/api/contact/schema',
        },
    )


@router.post('/contact', response_class=HTMLResponse, tags=['Dual-Use: Form + JSON API'])
async def contact_post(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = False,
):
    """Accept and validate a browser form submission (multipart/form-data)."""
    raw = await request.form()
    data = parse_nested_form_data(raw.multi_items())
    result = ContactForm.validate(data, submit_url=f'/contact?style={style}', framework=style)
    if result.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'title': 'Message Sent!',
                'message': f'Thank you, {result.data.get("name", "")}! Your message was received.',
                'data': result.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': f'/contact?style={style}&demo=true&debug={debug}&show_timing={show_timing}',
            },
        )
    form_html = await result.render_with_errors_async(debug=debug, show_timing=show_timing)
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'title': 'Contact — HTML Form',
            'form_html': form_html,
            'refer_path': '/contact',
            'api_endpoint': '/api/contact',
            'api_schema_endpoint': '/api/contact/schema',
        },
    )


@router.post('/api/contact', response_model=ContactSchema, tags=['Dual-Use: Form + JSON API'])
async def api_contact(data: ContactSchema):
    """
    Accept a JSON body validated against the same model as the HTML form.

    FastAPI uses ContactSchema (ContactForm.as_api_model()) so the OpenAPI
    docs show a clean schema with no ui_* keys — identical to a hand-written
    Pydantic model, with Field examples and validation constraints intact.

    Try it:
        curl -X POST http://localhost:8000/api/contact \\
             -H 'Content-Type: application/json' \\
             -d '{"name":"Alice","email":"alice@example.com","message":"Hello there!"}'
    """
    return data


@router.get('/api/contact/schema', tags=['Dual-Use: Form + JSON API'])
async def api_contact_schema():
    """Return the clean JSON Schema used by the /api/contact endpoint."""
    return ContactSchema.model_json_schema()


# ================================
# FEEDBACK — second dual-use demo
# ================================


@router.get('/feedback', response_class=HTMLResponse, tags=['Dual-Use: Form + JSON API'])
async def feedback_get(
    request: Request,
    style: str = 'bootstrap',
    demo: bool = False,
    debug: bool = False,
    show_timing: bool = False,
):
    """Render the feedback form (HTML)."""
    form_data = (
        {
            'subject': 'Documentation',
            'rating': 4,
            'comment': 'Very clear examples — the dual-use pattern is especially handy!',
        }
        if demo
        else {}
    )
    form_html = await FeedbackForm.render_form_async(
        submit_url=f'/feedback?style={style}',
        framework=style,
        data=form_data,
        debug=debug,
        show_timing=show_timing,
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'title': 'Feedback — HTML Form',
            'form_html': form_html,
            'refer_path': '/feedback',
            'api_endpoint': '/api/feedback',
            'api_schema_endpoint': '/api/feedback/schema',
        },
    )


@router.post('/feedback', response_class=HTMLResponse, tags=['Dual-Use: Form + JSON API'])
async def feedback_post(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = False,
):
    """Accept and validate a browser feedback submission."""
    raw = await request.form()
    data = parse_nested_form_data(raw.multi_items())
    result = FeedbackForm.validate(data, submit_url=f'/feedback?style={style}', framework=style)
    if result.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'title': 'Feedback Received!',
                'message': f'Thanks for the {result.data.get("rating", "")}-star feedback!',
                'data': result.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': f'/feedback?style={style}&demo=true&debug={debug}&show_timing={show_timing}',
            },
        )
    form_html = await result.render_with_errors_async(debug=debug, show_timing=show_timing)
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'title': 'Feedback — HTML Form',
            'form_html': form_html,
            'refer_path': '/feedback',
            'api_endpoint': '/api/feedback',
            'api_schema_endpoint': '/api/feedback/schema',
        },
    )


@router.post('/api/feedback', response_model=FeedbackSchema, tags=['Dual-Use: Form + JSON API'])
async def api_feedback(data: FeedbackSchema):
    """
    Accept a JSON body validated against the same model as the HTML feedback form.

    FeedbackSchema is FeedbackForm.as_api_model(): integer rating with ge=1/le=5
    constraints (minimum/maximum in JSON Schema) and no ui_* keys in OpenAPI.

    Try it:
        curl -X POST http://localhost:8000/api/feedback \\
             -H 'Content-Type: application/json' \\
             -d '{"subject":"Documentation","rating":5,"comment":"Very clear!"}'
    """
    return data


@router.get('/api/feedback/schema', tags=['Dual-Use: Form + JSON API'])
async def api_feedback_schema():
    """Return the clean JSON Schema used by the /api/feedback endpoint."""
    return FeedbackSchema.model_json_schema()


# ================================
# LIVE HTMX VALIDATION DEMO
# ================================


@router.get('/live-validation', response_class=HTMLResponse, tags=['Live Validation'])
async def live_validation_get(request: Request, style: str = 'bootstrap'):
    """Demonstrate real-time HTMX field validation on blur."""
    return templates.TemplateResponse(
        request,
        'live_validation.html',
        {
            'request': request,
            'title': 'Live HTMX Validation',
            'description': 'Fields validate on blur via HTMX — no page reload required.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'validator_script': _LIVE_VALIDATOR_SCRIPT,
            'form_data': {},
            'errors': {},
        },
    )


@router.post('/live-validation', response_class=HTMLResponse, tags=['Live Validation'])
async def live_validation_post(request: Request, style: str = 'bootstrap'):
    """Handle contact form submission for the live-validation demo."""
    raw = await request.form()
    data = parse_nested_form_data(raw.multi_items())
    result = ContactForm.validate(
        data, submit_url=f'/live-validation?style={style}', framework=style
    )
    if result.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Message Sent!',
                'message': f'Thank you, {result.data.get("name", "")}! Your message was received.',
                'data': result.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': f'/live-validation?style={style}',
            },
        )
    return templates.TemplateResponse(
        request,
        'live_validation.html',
        {
            'request': request,
            'title': 'Live HTMX Validation',
            'description': 'Fields validate on blur via HTMX — no page reload required.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'validator_script': _LIVE_VALIDATOR_SCRIPT,
            'form_data': data,
            'errors': result.errors,
        },
    )


@router.post('/validate/{field_name}', response_class=HTMLResponse, tags=['Live Validation'])
async def htmx_validate_field(field_name: str, request: Request):
    """HTMX endpoint: validate a single contact form field and return feedback HTML."""
    raw = await request.form()
    value = raw.get(field_name, '')
    try:
        result = _contact_live_validator.validate_field(field_name, str(value))
    except ImportError as e:
        # EmailDeliverabilityRule's DNS/MX check needs the optional
        # email-validator package — surface that as feedback instead of a 500.
        feedback = f'<span class="text-warning small"><i class="bi bi-exclamation-triangle-fill me-1"></i>{e}</span>'
        headers = validation_response_headers(field_name, False)
        return HTMLResponse(feedback, headers=headers)
    if result.is_valid:
        feedback = '<span class="text-success small"><i class="bi bi-check-circle-fill me-1"></i>Looks good!</span>'
    else:
        error_text = '; '.join(result.errors)
        feedback = f'<span class="text-danger small"><i class="bi bi-exclamation-circle-fill me-1"></i>{error_text}</span>'
    headers = validation_response_headers(field_name, result.is_valid)
    return HTMLResponse(feedback, headers=headers)


@router.get('/email-dns-validation', response_class=HTMLResponse, tags=['Live Validation'])
async def email_dns_validation_get(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = True,
):
    """Side-by-side demo: email format validation with and without a DNS/MX check."""
    form_html = await render_form_html_async(
        EmailDnsComparisonForm,
        framework=style,
        submit_url=f'/email-dns-validation?style={style}',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    return templates.TemplateResponse(
        request,
        'email_dns_validation.html',
        {
            'request': request,
            'title': 'Email DNS/MX Validation',
            'description': 'Same field type, two rule sets: format-only vs. format + a real DNS/MX lookup.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
            'validator_script': _LIVE_VALIDATOR_SCRIPT,
        },
    )


@router.post('/email-dns-validation', response_class=HTMLResponse, tags=['Live Validation'])
async def email_dns_validation_post(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = True,
):
    """Submit-time validation for the DNS/MX comparison demo.

    email_with_dns's field_validator runs the same EmailDeliverabilityRule
    check the live HTMX endpoint uses, so a domain that fails on blur also
    fails here rather than silently passing on submit.
    """
    raw = await request.form()
    parsed_data = parse_nested_form_data(_group_form_data(raw))
    validation = EmailDnsComparisonForm.validate(
        parsed_data,
        submit_url=f'/email-dns-validation?style={style}',
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
                'title': 'Both Emails Passed Validation',
                'message': 'Both fields — including the DNS/MX check — passed.',
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )

    form_html = await validation.render_with_errors_async()
    return templates.TemplateResponse(
        request,
        'email_dns_validation.html',
        {
            'request': request,
            'title': 'Email DNS/MX Validation',
            'description': 'Same field type, two rule sets: format-only vs. format + a real DNS/MX lookup.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
            'validator_script': _LIVE_VALIDATOR_SCRIPT,
            'errors': validation.errors,
        },
    )


# ================================
# AI ASSISTANT INSTRUCTIONS
# ================================


@router.get('/ai-instructions', response_class=HTMLResponse, tags=['System'])
async def ai_instructions_page(request: Request):
    """Render the packaged AI-assistant instructions (one tab per profile)."""
    profiles = [
        {
            'id': profile,
            'label': profile.title(),
            'filename': suggested_instruction_filename(profile),
            'html': _markdown.markdown(
                get_app_instructions(profile),
                extensions=['fenced_code', 'tables', 'sane_lists'],
            ),
        }
        for profile in available_instruction_profiles()
    ]

    return templates.TemplateResponse(
        request,
        'ai_instructions.html',
        {
            'request': request,
            'title': 'AI Assistant Instructions',
            'profiles': profiles,
        },
    )


# ================================
# HEALTH CHECK
# ================================


@router.get('/api/health', tags=['System'])
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
