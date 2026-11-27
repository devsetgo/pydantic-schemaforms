"""Validation: the validation showcase, live HTMX validation, and email DNS checking."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from examples.shared_models import (
    ContactForm,
    EmailDnsComparisonForm,
    LIVE_VALIDATION_DEBOUNCE_MS,  # Simple Form; Medium Form; Complex Form; Pet Forms; Layout Demonstration; Utility functions
    INVALID_VALIDATION_DEMO,
    PASSWORD_MISMATCH_DEMO,
    VALID_VALIDATION_DEMO,
    ValidationShowcaseForm,
    validation_showcase_rules,
)


from pydantic_schemaforms import (
    LiveValidator,
    render_form_html_async,
)
from pydantic_schemaforms import (
    html,
    validation_response_headers,
)
from examples.fastapi_routes import (
    create_refer_path,
    templates,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Live-validation for the /live-validation and /email-dns-validation demos.
# LiveValidator.for_model() derives every field's live check straight from
# each FormModel's own Field constraints/types (min_length, EmailStr,
# DeliverableEmailStr's DNS/MX lookup, ...) and checks as-you-type (debounced)
# rather than only on blur -- no separate FieldValidator to hand-write or
# keep in sync with the model.
# ---------------------------------------------------------------------------

_contact_live_validator = LiveValidator.for_model(
    ContactForm, EmailDnsComparisonForm, debounce_ms=LIVE_VALIDATION_DEBOUNCE_MS
)


# ================================
# LIVE HTMX VALIDATION DEMO
# ================================


# ================================
# VALIDATION SHOWCASE
# ================================

_VALIDATION_SCENARIOS = {
    'invalid': INVALID_VALIDATION_DEMO,
    'mismatch': PASSWORD_MISMATCH_DEMO,
    'valid': VALID_VALIDATION_DEMO,
}


async def _render_validation_page(
    request: Request, style: str, form_data: Any, errors: dict | None = None
) -> HTMLResponse:
    form_html = await render_form_html_async(
        ValidationShowcaseForm,
        form_data=form_data,
        errors=errors,
        framework=style,
        submit_url=f'/validation?style={style}',
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Validation Showcase',
            'description': 'Every kind of validation on one form: Pydantic Field constraints, '
            '@field_validator, @model_validator, sub-form and list-item errors, every '
            'built-in rule class, and a cross-field rule. Submit as-is to see them fail; '
            '?scenario=mismatch shows the form-wide @model_validator error, '
            '?scenario=valid a passing submission. As-you-type HTMX validation: '
            '/live-validation.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@router.get('/validation', response_class=HTMLResponse, tags=['Showcase'])
async def validation_get(request: Request, style: str = 'bootstrap', scenario: str = 'invalid'):
    """Every kind of validation, pre-filled so one Submit makes each of them fail."""
    return await _render_validation_page(
        request, style, _VALIDATION_SCENARIOS.get(scenario, INVALID_VALIDATION_DEMO)
    )


@router.post('/validation', response_class=HTMLResponse, tags=['Showcase'])
async def validation_post(request: Request, style: str = 'bootstrap'):
    """Validate with Pydantic and a rule-based FormValidator; merge both error sets."""
    form_data = await request.form()
    result = ValidationShowcaseForm.validate(form_data, submit_url=f'/validation?style={style}')
    # original_data is the decoded (nested) submission; the rule-based layer
    # validates its top-level fields.
    rules_ok, rule_errors = validation_showcase_rules().validate(result.original_data)
    if result.is_valid and rules_ok:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Validation Showcase Passed',
                'message': 'Every Pydantic constraint, validator, and rule passed.',
                'data': result.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': create_refer_path(request),
            },
        )
    # Both layers share one nested error tree; a field's message may be a list.
    errors = {**rule_errors, **result.errors}
    return await _render_validation_page(request, style, form_data, errors)


@router.get('/live-validation', response_class=HTMLResponse, tags=['Live Validation'])
async def live_validation_get(request: Request, style: str = 'bootstrap'):
    """Demonstrate real-time HTMX field validation as-you-type (debounced)."""
    return templates.TemplateResponse(
        request,
        'live_validation.html',
        {
            'request': request,
            'title': 'Live HTMX Validation',
            'description': 'Fields validate as you type (debounced) via HTMX — no page reload required.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'validator_script': _contact_live_validator.render_htmx_script(),
            'debounce_ms': LIVE_VALIDATION_DEBOUNCE_MS,
            'form_data': {},
            'errors': {},
        },
    )


@router.post('/live-validation', response_class=HTMLResponse, tags=['Live Validation'])
async def live_validation_post(request: Request, style: str = 'bootstrap'):
    """Handle contact form submission for the live-validation demo."""
    raw = await request.form()
    result = ContactForm.validate(
        raw, submit_url=f'/live-validation?style={style}', framework=style
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
            'description': 'Fields validate as you type (debounced) via HTMX — no page reload required.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'validator_script': _contact_live_validator.render_htmx_script(),
            'debounce_ms': LIVE_VALIDATION_DEBOUNCE_MS,
            'form_data': result.original_data,
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
        message = str(e)
        feedback = html(
            t'<span class="text-warning small"><i class="bi bi-exclamation-triangle-fill me-1"></i>{message}</span>'
        )
        headers = validation_response_headers(field_name, False)
        return HTMLResponse(str(feedback), headers=headers)
    if result.is_valid:
        feedback = html(
            t'<span class="text-success small"><i class="bi bi-check-circle-fill me-1"></i>Looks good!</span>'
        )
    else:
        # Validator messages can echo the submitted value, so let html() escape them.
        error_text = '; '.join(result.errors)
        feedback = html(
            t'<span class="text-danger small"><i class="bi bi-exclamation-circle-fill me-1"></i>{error_text}</span>'
        )
    headers = validation_response_headers(field_name, result.is_valid)
    return HTMLResponse(str(feedback), headers=headers)


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
            'description': 'Two field types, same demo: EmailStr (format-only) vs. DeliverableEmailStr (format + a real DNS/MX lookup).',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
            'validator_script': _contact_live_validator.render_htmx_script(),
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

    email_with_dns's DeliverableEmailStr type runs the same DNS/MX lookup the
    live HTMX endpoint uses, so a domain that fails on blur also fails here
    rather than silently passing on submit.
    """
    raw = await request.form()
    validation = EmailDnsComparisonForm.validate(
        raw,
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
            'description': 'Two field types, same demo: EmailStr (format-only) vs. DeliverableEmailStr (format + a real DNS/MX lookup).',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
            'validator_script': _contact_live_validator.render_htmx_script(),
            'errors': validation.errors,
        },
    )
