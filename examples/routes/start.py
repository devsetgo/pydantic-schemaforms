"""Start here: login, registration, and the contact and feedback forms with their JSON APIs."""

import hmac
import secrets

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from examples.shared_models import (
    ContactForm,
    FeedbackForm,
    MinimalLoginForm,
    UserRegistrationForm,
)


from pydantic_schemaforms import (
    render_form_html_async,
)
from examples.fastapi_routes import (
    create_refer_path,
    templates,
)

router = APIRouter()


# Derive the API model once at module level.
# Same fields and validation rules; ui_* keys stripped so OpenAPI docs are clean.
ContactSchema = ContactForm.as_api_model()


# ge/le constraints (minimum/maximum) are preserved in the API schema.
FeedbackSchema = FeedbackForm.as_api_model()


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

    submitted_csrf_token = form_data.get('csrf_token')
    csrf_error = 'CSRF verification failed. Refresh the page and submit again.'
    if not verify_login_csrf_token(request, submitted_csrf_token):
        csrf_token = issue_login_csrf_token(request)

        form_html = await render_form_html_async(
            MinimalLoginForm,
            framework=style,
            form_data=form_data,
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

    validation = MinimalLoginForm.validate(
        form_data,
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

    submitted_csrf_token = form_data.get('csrf_token')
    csrf_error = 'CSRF verification failed. Refresh the page and submit again.'
    if not verify_register_csrf_token(request, submitted_csrf_token):
        csrf_token = issue_register_csrf_token(request)

        form_html = await render_form_html_async(
            UserRegistrationForm,
            framework=style,
            form_data=form_data,
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

    validation = UserRegistrationForm.validate(
        form_data,
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
    result = ContactForm.validate(raw, submit_url=f'/contact?style={style}', framework=style)
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
    result = FeedbackForm.validate(raw, submit_url=f'/feedback?style={style}', framework=style)
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
