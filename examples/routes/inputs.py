"""Inputs: the widget gallery, date and time formats, and the input-type reference."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from examples.shared_models import (
    WidgetGalleryForm,
)
from examples.date_time_formats_example import (
    DateTimeFormatsShowcaseForm,
    create_sample_date_time_format_data,
)
from examples.input_type_reference import INPUT_TYPE_CATEGORIES


from pydantic_schemaforms import (
    render_form_html_async,
)
from examples.fastapi_routes import (
    _material_variant,
    _variant_query,
    create_refer_path,
    templates,
)

router = APIRouter()


@router.get('/gallery', response_class=HTMLResponse, tags=['Showcase'])
async def gallery_get(
    request: Request,
    style: str = 'bootstrap',
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
    variant: str | None = None,
):
    """Tabbed widget gallery - every input type grouped by category (GET).

    Demo data is every field's default, nested one dict per tab -- the same
    shape validate() returns.
    """
    # No form_data renders a fresh form from the field defaults, which are the
    # gallery's demo values; an empty dict renders it blank.
    form_data = None if demo else {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON

    form_html = await render_form_html_async(
        WidgetGalleryForm,
        layout='tabbed',
        framework=style,
        form_data=form_data,
        submit_url=f'/gallery?style={style}{_variant_query(variant)}',
        material_variant=_material_variant(variant),
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
    )

    # model_list and DataTableLayout are composition mechanisms, not discrete
    # widgets (see WidgetGalleryForm's docstring), so they're cross-linked
    # here rather than embedded as gallery fields.
    form_html += (
        '<div class="alert alert-info mt-4">'
        '<strong>Looking for repeating sub-forms or CSV-import tables?</strong> '
        'Those are composition mechanisms, not discrete widgets — see '
        '<a href="/pets">/pets</a> (model_list) and '
        '<a href="/employees/import">/employees/import</a> (DataTableLayout).'
        '</div>'
    )

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Widget Gallery - Tabbed by Category',
            'description': 'Every input type, alias, and widget option, grouped into tabs: '
            'Text, Checkboxes & Toggles, Numeric, Selection, Date & Time, '
            'Content & Consent, Files & Specialized, and Field Options',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@router.post('/gallery', response_class=HTMLResponse, tags=['Showcase'])
async def gallery_post(
    request: Request,
    style: str = 'bootstrap',
    debug: bool = False,
    show_timing: bool = True,
    variant: str | None = None,
):
    """Tabbed widget gallery submission (async)."""
    form_data = await request.form()

    validation = WidgetGalleryForm.validate(
        form_data,
        layout='tabbed',
        submit_url=f'/gallery?style={style}{_variant_query(variant)}',
        framework=style,
        material_variant=_material_variant(variant),
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

    Demo data is nested one dict per tab (dates/times/datetimes), mirroring
    DateTimeFormatsShowcaseForm's nested sub-form fields.
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
        layout='tabbed',
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

    validation = DateTimeFormatsShowcaseForm.validate(
        form_data,
        layout='tabbed',
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
# INPUT TYPE REFERENCE
# ================================


@router.get('/input-types', response_class=HTMLResponse, tags=['System'])
async def input_type_reference_page(request: Request):
    """Plain documentation page: every ui_element with a code example.

    Static reference data only -- nothing here goes through the form
    renderer. See /gallery for the live-rendered version.
    """
    return templates.TemplateResponse(
        request,
        'input_type_reference.html',
        {
            'request': request,
            'title': 'Input Type Reference',
            'categories': INPUT_TYPE_CATEGORIES,
        },
    )
