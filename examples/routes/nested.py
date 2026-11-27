"""Nested forms: the complete showcase, pet registration, and organization forms."""

import hmac
import secrets

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from examples.shared_models import (
    SHOWCASE_CAPTCHA_SECRET,
    CompanyOrganizationForm,
    CompleteShowcaseForm,
    PetRegistrationForm,
    create_sample_nested_data,
)
from examples.nested_forms_example import create_comprehensive_sample_data


from pydantic_schemaforms import (
    render_form_html_async,
    verify_captcha,
)
from examples.fastapi_routes import (
    create_refer_path,
    templates,
)

router = APIRouter()


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
    form_data = await request.form()

    full_referer_path = create_refer_path(request)

    # Honeypot: real users never see or fill this field in (it's hidden and
    # styled off-screen). A non-empty value means a bot filled every input it
    # could find. Pretend success rather than revealing that it was caught.
    if form_data.get('honeypot_field'):
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

    submitted_csrf_token = form_data.get('csrf_token')
    if not verify_showcase_csrf_token(request, submitted_csrf_token):
        csrf_error = 'CSRF verification failed. Refresh the page and submit again.'
        csrf_token = issue_showcase_csrf_token(request)

        form_html = await render_form_html_async(
            CompleteShowcaseForm,
            framework=style,
            form_data=form_data,
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
    captcha_token = form_data.get('captcha_answer_token')
    if not verify_captcha(
        token=captcha_token,
        answer=form_data.get('captcha_answer', ''),
        secret_key=SHOWCASE_CAPTCHA_SECRET,
    ):
        captcha_error = 'Incorrect answer to the verification question. Please try again.'
        csrf_token = issue_showcase_csrf_token(request)

        form_html = await render_form_html_async(
            CompleteShowcaseForm,
            framework=style,
            form_data=form_data,
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

    validation = CompleteShowcaseForm.validate(
        form_data,
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
        csrf_token = issue_showcase_csrf_token(request)
        form_html = await validation.render_with_errors_async(csrf_token_provider=csrf_token)
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

    validation = PetRegistrationForm.validate(
        form_data,
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
        layout='tabbed',
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
    # Every nested list item's inputs are separate fields: the demo data is
    # ~500, so a few added departments pass Starlette's default max_fields=1000.
    form_data = await request.form(max_fields=10_000)

    from examples.nested_forms_example import ComprehensiveTabbedForm

    validation = ComprehensiveTabbedForm.validate(
        form_data,
        layout='tabbed',
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

    validation = CompanyOrganizationForm.validate(
        form_data,
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
