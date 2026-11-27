"""Layouts: layout switcher, field groups, confirm dialog, save-and-continue, and review pages."""

import hmac
import secrets
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from examples.shared_models import (
    AccountSettingsForm,
    LayoutDemonstrationForm,
    FieldGroupsForm,
    SaveAndContinueForm,
    CloseAccountForm,
    CLOSE_ACCOUNT_CONFIRM,
    WidgetGalleryForm,
)


from pydantic_schemaforms import (
    EnhancedFormRenderer,
    render_form_html_async,
)
from pydantic_schemaforms import (
    SafeHTML,
    html,
    wrap_with_schemaforms_markers,
)
from examples.fastapi_routes import (
    _material_variant,
    _variant_query,
    create_refer_path,
    templates,
)

router = APIRouter()


def _layout_demo_options(
    style: str,
    layout: str,
    linear: bool,
    progress: bool,
    labels: bool,
    variant: str | None = None,
    review: bool = False,
    count: bool = False,
    autosave: bool = False,
    warn: bool = False,
) -> dict:
    """Render kwargs for /layouts: the submit URL keeps every query option,
    and the wizard gets wizard_options built from them."""
    query = (
        f'style={style}&layout={layout}&linear={linear}&progress={progress}&labels={labels}'
        f'&review={review}&count={count}&autosave={autosave}&warn={warn}'
        f'{_variant_query(variant)}'
    )
    options: dict = {
        'submit_url': f'/layouts?{query}',
        'layout': layout,
        'progress': count,
        'autosave': autosave,
        'warn_unsaved': warn,
    }
    if layout == 'wizard':
        options['wizard_options'] = {'linear': linear, 'show_progress': progress}
        if labels:
            options['wizard_options'] |= {'back_label': 'Previous', 'next_label': 'Continue'}
        if review:
            options['wizard_options']['review_step'] = (
                {'title': 'Check your answers', 'edit_label': 'Change'} if labels else True
            )
    return options


_LAYOUT_CHOICES = [
    ('vertical', 'Vertical'),
    ('tabbed', 'Tabbed'),
    ('side-by-side', 'Side by side'),
    ('accordion', 'Accordion'),
    ('wizard', 'Step wizard'),
]


def _layout_switcher(
    style: str,
    layout: str,
    linear: bool,
    progress: bool,
    labels: bool,
    variant: str | None = None,
    review: bool = False,
    count: bool = False,
    autosave: bool = False,
    warn: bool = False,
) -> str:
    """Buttons to re-render /layouts with each layout, plus the wizard's options."""

    current_query = {
        'style': style,
        'layout': layout,
        'linear': str(linear).lower(),
        'progress': str(progress).lower(),
        'labels': str(labels).lower(),
        'review': str(review).lower(),
        'count': str(count).lower(),
        'autosave': str(autosave).lower(),
        'warn': str(warn).lower(),
    }

    def link(label: str, current: bool, *, toggle: bool = False, **query: object) -> SafeHTML:
        params = current_query | query
        href = '/layouts?' + '&'.join(f'{key}={value}' for key, value in params.items())
        href += _variant_query(variant)
        css = 'btn btn-sm ' + ('btn-primary' if current else 'btn-outline-primary')
        # aria-current shows the state to screen readers and to the Material shell,
        # which styles every .btn alike; a tick shows which options are on.
        _current = SafeHTML(' aria-current="true"' if current else '')  # NOSONAR
        _tick = SafeHTML(
            '<span aria-hidden="true">✓ </span>' if toggle and current else ''
        )  # NOSONAR
        return html(t'<a class="{css}" href="{href}"{_current}>{_tick}{label}</a>')

    layout_links = SafeHTML(
        ''.join(str(link(label, value == layout, layout=value)) for value, label in _LAYOUT_CHOICES)
    )
    # progress=True: a bar on every layout, ticks in the wizard's step header.
    form_toggles = SafeHTML(
        ''.join(
            str(link(label, active, toggle=True, **{key: str(not active).lower()}))
            for key, label, active in (
                ('count', 'Count required fields (progress)', count),
                ('autosave', 'Autosave a draft', autosave),
                ('warn', 'Warn before leaving (warn_unsaved)', warn),
            )
        )
    )
    wizard_row = SafeHTML('')
    if layout == 'wizard':
        toggles = SafeHTML(
            ''.join(
                str(link(label, active, toggle=True, **{key: str(not active).lower()}))
                for key, label, active in (
                    ('linear', 'Linear', linear),
                    ('progress', 'Progress header', progress),
                    ('labels', 'Custom labels', labels),
                    ('review', 'Review step', review),
                )
            )
        )
        save_steps_href = f'/layouts/save-steps?style={style}{_variant_query(variant)}'
        wizard_row = html(
            t'<div class="d-flex flex-wrap gap-2 align-items-center mt-2">'
            t'<span class="text-muted small">Wizard options:</span>{toggles}</div>'
            t'<p class="small text-muted mt-2 mb-0">Saving each step on the server is a '
            t'different flow: <a href="{save_steps_href}">see save_steps</a>.</p>'
        )
    return str(
        html(
            t'<div class="layout-switcher mb-4"><div class="d-flex flex-wrap gap-2 align-items-center">'
            t'<span class="text-muted small">Layout:</span>{layout_links}</div>'
            t'<div class="d-flex flex-wrap gap-2 align-items-center mt-2">'
            t'<span class="text-muted small">Form options:</span>{form_toggles}</div>{wizard_row}</div>'
        )
    )


# Demo values for /layouts and /layouts/review.
_LAYOUT_DEMO_DATA = {
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


@router.get('/layouts', response_class=HTMLResponse, tags=['Showcase'])
async def layouts_get(
    request: Request,
    style: str = 'bootstrap',
    variant: str | None = None,
    layout: str = 'tabbed',
    linear: bool = True,
    progress: bool = True,
    labels: bool = False,
    review: bool = False,
    count: bool = False,
    autosave: bool = False,
    warn: bool = False,
    data: str = None,
    demo: bool = True,
    debug: bool = False,
    show_timing: bool = True,
):
    """Four FormModels nested in one parent form, shown with any layout.

    Try ?layout=vertical, tabbed, side-by-side, accordion, or wizard -- the model is
    the same; only the presentation changes. Wizard options: &linear=false lets
    the step header jump anywhere, &progress=false hides it, &labels=true
    renames Back/Next, &review=true adds a review step before Submit.
    """
    # Parse optional pre-fill data or use demo data
    form_data = {}
    if data:
        try:
            import json

            form_data = json.loads(data)
        except Exception:
            pass  # Ignore invalid JSON
    elif demo or not data:
        form_data = _LAYOUT_DEMO_DATA

    renderer = EnhancedFormRenderer(framework=style, material_variant=_material_variant(variant))
    form_html = await renderer.render_form_from_model_async(
        LayoutDemonstrationForm,
        data=form_data,
        errors={},
        **_layout_demo_options(
            style, layout, linear, progress, labels, variant, review, count, autosave, warn
        ),
        include_submit_button=True,
        debug=debug,
        show_timing=show_timing,
    )
    form_html = wrap_with_schemaforms_markers(form_html)
    form_html = (
        _layout_switcher(
            style, layout, linear, progress, labels, variant, review, count, autosave, warn
        )
        + form_html
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Layout Demonstration - All Types',
            'description': 'Four FormModels nested in one form, shown with each layout. '
            'Pick a layout and, for the wizard, its options below.',
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
    variant: str | None = None,
    layout: str = 'tabbed',
    linear: bool = True,
    progress: bool = True,
    labels: bool = False,
    review: bool = False,
    count: bool = False,
    autosave: bool = False,
    warn: bool = False,
    debug: bool = False,
    show_timing: bool = True,
):
    """Handle comprehensive layout demonstration form submission."""
    form_data = await request.form()
    full_referer_path = create_refer_path(request)

    validation = LayoutDemonstrationForm.validate(form_data)

    if validation.is_valid:
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Layout Demo Submitted Successfully',
                'message': 'All layout types processed successfully!',
                'display_html': LayoutDemonstrationForm.render_display(
                    validation.data,
                    framework=style,
                    layout=layout,
                    material_variant=_material_variant(variant),
                ),
                'data': validation.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': full_referer_path,
            },
        )

    # Re-render the form with validation errors + user data.
    renderer = EnhancedFormRenderer(framework=style, material_variant=_material_variant(variant))
    form_html = await renderer.render_form_from_model_async(
        LayoutDemonstrationForm,
        data=form_data,
        errors=validation.errors,
        **_layout_demo_options(
            style, layout, linear, progress, labels, variant, review, count, autosave, warn
        ),
        include_submit_button=True,
        debug=debug,
        show_timing=show_timing,
    )
    form_html = wrap_with_schemaforms_markers(form_html)
    form_html = (
        _layout_switcher(
            style, layout, linear, progress, labels, variant, review, count, autosave, warn
        )
        + form_html
    )

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


_FIELD_GROUPS_DESCRIPTION = (
    'One flat model arranged with ui_group and ui_cols, so result.data has no nesting. A group '
    'can be a section, tab, panel or wizard step.'
)


async def _render_field_groups_page(
    request: Request,
    style: str,
    variant: str | None,
    layout: str,
    data: dict | None = None,
    errors: dict | None = None,
):
    if layout not in dict(_LAYOUT_CHOICES):
        layout = 'vertical'
    query = f'style={style}&layout={layout}{_variant_query(variant)}'

    def link(value: str, label: str) -> str:
        css = 'btn btn-sm ' + ('btn-primary' if value == layout else 'btn-outline-primary')
        href = f'/layouts/field-groups?style={style}&layout={value}{_variant_query(variant)}'
        return str(html(t'<a class="{css}" href="{href}">{label}</a>'))

    links = SafeHTML(''.join(link(value, label) for value, label in _LAYOUT_CHOICES))
    renderer = EnhancedFormRenderer(framework=style, material_variant=_material_variant(variant))
    form_html = await renderer.render_form_from_model_async(
        FieldGroupsForm,
        data=data,
        errors=errors or {},
        submit_url=f'/layouts/field-groups?{query}',
        layout=layout,
    )
    page_html = html(
        t'<div class="d-flex flex-wrap gap-2 align-items-center mb-4">'
        t'<span class="text-muted small">Layout:</span>{links}</div>{SafeHTML(form_html)}'
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Field Groups and Grid Widths',
            'description': _FIELD_GROUPS_DESCRIPTION,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'hide_api_info': True,
            'form_html': wrap_with_schemaforms_markers(str(page_html)),
            'errors': errors,
        },
    )


@router.get('/layouts/field-groups', response_class=HTMLResponse, tags=['Showcase'])
async def field_groups_get(
    request: Request,
    style: str = 'bootstrap',
    variant: str | None = None,
    layout: str = 'vertical',
):
    """ui_group and ui_cols on a flat model, shown with any layout."""
    return await _render_field_groups_page(request, style, variant, layout)


@router.post('/layouts/field-groups', response_class=HTMLResponse, tags=['Showcase'])
async def field_groups_post(
    request: Request,
    style: str = 'bootstrap',
    variant: str | None = None,
    layout: str = 'vertical',
):
    form_data = await request.form()
    validation = FieldGroupsForm.validate(form_data)
    if not validation.is_valid:
        return await _render_field_groups_page(
            request, style, variant, layout, data=form_data, errors=validation.errors
        )
    return templates.TemplateResponse(
        request,
        'success.html',
        {
            'request': request,
            'title': 'Field Groups Submitted',
            'message': 'The groups were only presentation: the data below is flat.',
            'display_html': FieldGroupsForm.render_display(
                validation.data,
                framework=style,
                layout=layout,
                material_variant=_material_variant(variant),
            ),
            'data': validation.data,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'try_again_url': create_refer_path(request),
        },
    )


# --- confirm=: ask before a destructive submit -------------------------------
_CLOSE_ACCOUNT_DESCRIPTION = (
    'confirm= opens a dialog before the form submits, for actions that are hard to undo. '
    'Cancel has focus first, and Escape closes it. Without JavaScript the form submits '
    'as usual.'
)


def _close_account_options(style: str, variant: str | None) -> dict[str, Any]:
    return {
        'submit_url': f'/confirm?style={style}{_variant_query(variant)}',
        'framework': style,
        'material_variant': _material_variant(variant),
        'confirm': CLOSE_ACCOUNT_CONFIRM,
    }


def _close_account_page(request: Request, style: str, form_html: str):
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Close Your Account',
            'description': _CLOSE_ACCOUNT_DESCRIPTION,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'hide_api_info': True,
            'form_html': form_html,
        },
    )


@router.get('/confirm', response_class=HTMLResponse, tags=['Showcase'])
async def confirm_get(request: Request, style: str = 'bootstrap', variant: str | None = None):
    """A destructive form that asks before it submits."""
    form_html = await render_form_html_async(
        CloseAccountForm, **_close_account_options(style, variant)
    )
    return _close_account_page(request, style, form_html)


@router.post('/confirm', response_class=HTMLResponse, tags=['Showcase'])
async def confirm_post(request: Request, style: str = 'bootstrap', variant: str | None = None):
    result = CloseAccountForm.validate(
        await request.form(), **_close_account_options(style, variant)
    )
    if not result.is_valid:
        return _close_account_page(request, style, await result.render_with_errors_async())
    return templates.TemplateResponse(
        request,
        'success.html',
        {
            'request': request,
            'title': 'Account Closed',
            'message': 'This is a demo: nothing was deleted.',
            'data': result.data,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'try_again_url': f'/confirm?style={style}{_variant_query(variant)}',
        },
    )


# --- Save and continue: wizard_options={'save_steps': True} -------------------
# The app stores the wizard's draft; here it's a signed cookie, and uploaded
# files sit in memory under a ref (a real app would use a database and file store).
_SAVE_STEPS_COOKIE = 'sf_save_steps_draft'


_SAVE_STEPS_KEY = secrets.token_bytes(32)


_SAVED_UPLOADS: dict[str, bytes] = {}


_CITY_BY_ZIP_PREFIX = {'100': 'New York', '787': 'Austin', '981': 'Seattle'}


_SAVE_STEPS_DESCRIPTION = (
    "wizard_options={'save_steps': True}: each step is its own page and POST, checked "
    'on the server and saved before the next one shows. Leave and come back: the draft '
    'is kept in a cookie. The ZIP code on step 1 fills in the city on step 3.'
)


def _save_steps_options(style: str, variant: str | None) -> dict[str, Any]:
    return {
        'submit_url': f'/layouts/save-steps?style={style}{_variant_query(variant)}',
        'framework': style,
        'material_variant': _material_variant(variant),
        'layout': 'wizard',
        'wizard_options': {
            'save_steps': True,
            'next_label': 'Save and continue',
            'review_step': {'title': 'Check and submit'},
        },
        'progress': True,
    }


def _load_save_steps_draft(request: Request, cookie: str = _SAVE_STEPS_COOKIE) -> dict | None:
    import base64
    import json

    raw = request.cookies.get(cookie, '')
    payload, _, signature = raw.partition('.')
    expected = hmac.new(_SAVE_STEPS_KEY, payload.encode(), 'sha256').hexdigest()
    if not payload or not hmac.compare_digest(signature, expected):
        return None
    return json.loads(base64.urlsafe_b64decode(payload))


def _store_save_steps_draft(
    response: Response, draft: dict, cookie: str = _SAVE_STEPS_COOKIE
) -> None:
    import base64
    import json

    payload = base64.urlsafe_b64encode(json.dumps(draft).encode()).decode()
    signature = hmac.new(_SAVE_STEPS_KEY, payload.encode(), 'sha256').hexdigest()
    response.set_cookie(cookie, f'{payload}.{signature}', httponly=True, samesite='lax')


def _prefill_city(data: dict) -> None:
    zip_code = str((data.get('applicant') or {}).get('zip_code') or '')
    availability = data.setdefault('availability', {})
    if availability.get('city'):
        return
    for prefix, city in _CITY_BY_ZIP_PREFIX.items():
        if zip_code.startswith(prefix):
            availability['city'] = city
            return


def _save_steps_page(request: Request, style: str, form_html: str):
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Save and Continue Wizard',
            'description': _SAVE_STEPS_DESCRIPTION,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'hide_api_info': True,
            'form_html': form_html,
        },
    )


@router.get('/layouts/save-steps', response_class=HTMLResponse, tags=['Showcase'])
async def save_steps_get(request: Request, style: str = 'bootstrap', variant: str | None = None):
    """A wizard that saves each step on the server; resumes from the saved draft."""
    form_html = await render_form_html_async(
        SaveAndContinueForm,
        draft=_load_save_steps_draft(request),
        **_save_steps_options(style, variant),
    )
    return _save_steps_page(request, style, form_html)


@router.post('/layouts/save-steps', response_class=HTMLResponse, tags=['Showcase'])
async def save_steps_post(request: Request, style: str = 'bootstrap', variant: str | None = None):
    result = SaveAndContinueForm.validate_step(
        await request.form(),
        draft=_load_save_steps_draft(request),
        **_save_steps_options(style, variant),
    )
    if result.is_complete:
        response = templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Application Saved and Submitted',
                'message': 'Every step was saved on the server, then checked together.',
                'display_html': SaveAndContinueForm.render_display(
                    result.data, framework=style, material_variant=_material_variant(variant)
                ),
                'data': result.data,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': f'/layouts/save-steps?style={style}{_variant_query(variant)}',
            },
        )
        response.delete_cookie(_SAVE_STEPS_COOKIE)
        return response
    if result.is_valid:
        for upload in result.files:
            upload.ref = secrets.token_hex(8)
            _SAVED_UPLOADS[upload.ref] = upload.read()
        _prefill_city(result.data)
    response = _save_steps_page(request, style, await result.render_async())
    if result.is_valid:
        _store_save_steps_draft(response, result.draft)
    return response


@router.get('/layouts/review', response_class=HTMLResponse, tags=['Showcase'])
async def layouts_review(
    request: Request,
    style: str = 'bootstrap',
    variant: str | None = None,
    layout: str = 'vertical',
):
    """The same demo values read-only, through FormModel.render_display()."""
    if layout not in dict(_LAYOUT_CHOICES):
        layout = 'vertical'

    def link(value: str, label: str) -> str:
        css = 'btn btn-sm ' + ('btn-primary' if value == layout else 'btn-outline-primary')
        href = f'/layouts/review?style={style}&layout={value}{_variant_query(variant)}'
        return str(html(t'<a class="{css}" href="{href}">{label}</a>'))

    links = SafeHTML(''.join(link(value, label) for value, label in _LAYOUT_CHOICES))
    edit_url = f'/layouts?style={style}&layout=vertical{_variant_query(variant)}'
    display_html = LayoutDemonstrationForm.render_display(
        _LAYOUT_DEMO_DATA,
        framework=style,
        layout=layout,
        edit_urls={'personal_info': edit_url, 'task_list': edit_url},
        material_variant=_material_variant(variant),
    )
    page_html = html(
        t'<div class="d-flex flex-wrap gap-2 align-items-center mb-4">'
        t'<span class="text-muted small">Layout:</span>{links}</div>{SafeHTML(display_html)}'
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Read-Only Review',
            'description': "A validated model shown with the form's labels and sections, not "
            'inputs. Select fields show their label, booleans Yes or No, lists a table.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'hide_api_info': True,
            'form_html': str(page_html),
        },
    )


@router.get('/gallery/review', response_class=HTMLResponse, tags=['Showcase'])
async def gallery_review(request: Request, style: str = 'bootstrap', variant: str | None = None):
    """Every input type in display mode, using the gallery's own demo values."""
    # Every gallery field has a default, and those defaults are its demo values.
    demo_values = {name: info.annotation() for name, info in WidgetGalleryForm.model_fields.items()}
    display_html = WidgetGalleryForm.render_display(
        demo_values,
        framework=style,
        layout='tabbed',
        material_variant=_material_variant(variant),
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Every Input, Read-Only',
            'description': 'How each input type reads in display mode. Passwords are masked; '
            'card and social security numbers show only their last four digits.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'hide_api_info': True,
            'form_html': display_html,
        },
    )


_TWO_FORMS_LAYOUTS = [('tabbed', 'Tabbed'), ('accordion', 'Accordion'), ('wizard', 'Step wizard')]


@router.get('/layouts/two-forms', response_class=HTMLResponse, tags=['Showcase'])
async def layouts_two_forms(request: Request, style: str = 'bootstrap', layout: str = 'tabbed'):
    """Two grouped forms on one page: each form's tabs, sections and steps
    control only that form."""
    if layout not in dict(_TWO_FORMS_LAYOUTS):
        layout = 'tabbed'
    renderer = EnhancedFormRenderer(framework=style)
    forms = []
    for heading, model in (
        ('Form 1: layout demo', LayoutDemonstrationForm),
        ('Form 2: account settings', AccountSettingsForm),
    ):
        form_html = await renderer.render_form_from_model_async(
            model, data={}, errors={}, layout=layout, include_submit_button=False
        )
        forms.append(html(t'<h4 class="mt-4">{heading}</h4>{SafeHTML(form_html)}'))

    def link(value: str, label: str) -> str:
        css = 'btn btn-sm ' + ('btn-primary' if value == layout else 'btn-outline-primary')
        href = f'/layouts/two-forms?style={style}&layout={value}'
        return str(html(t'<a class="{css}" href="{href}">{label}</a>'))

    links = SafeHTML(''.join(link(value, label) for value, label in _TWO_FORMS_LAYOUTS))
    page_html = html(
        t'<div class="d-flex flex-wrap gap-2 align-items-center mb-2">'
        t'<span class="text-muted small">Layout:</span>{links}</div>'
        t'{SafeHTML("".join(str(form) for form in forms))}'
    )
    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': 'Two Grouped Forms on One Page',
            'description': 'Switching a tab, section or step in one form leaves the other alone.',
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': wrap_with_schemaforms_markers(str(page_html)),
        },
    )
