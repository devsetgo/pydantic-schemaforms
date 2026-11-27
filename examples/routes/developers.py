"""Developers: the generic form API, AI instructions, and the health check."""

import markdown as _markdown
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from examples.shared_models import (
    CompanyOrganizationForm,
    CompleteShowcaseForm,
    LayoutDemonstrationForm,
    MinimalLoginForm,
    PetRegistrationForm,
    UserRegistrationForm,
    ValidationShowcaseForm,
    WidgetGalleryForm,
)


from pydantic_schemaforms import (
    __version__ as _psf_version,
    available_instruction_profiles,
    get_app_instructions,
    render_form_html_async,
    suggested_instruction_filename,
)
from examples.fastapi_routes import (
    templates,
)

router = APIRouter()


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
    'gallery': WidgetGalleryForm,
    'validation': ValidationShowcaseForm,
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
async def api_submit_form(form_type: str, request: Request):
    """
    Validate JSON form submissions against a selected Pydantic form model.

    This shows the API workflow behind the HTML examples:
    request payload -> model validation -> data/errors response.

    Input and output are nested JSON matching the model, e.g. the
    `organization` form's departments -> teams -> members. ``errors`` has the
    same shape as ``data`` (list items keyed by index), so
    ``errors["departments"]["0"]["name"]`` sits where ``data["departments"][0]["name"]`` does.
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
