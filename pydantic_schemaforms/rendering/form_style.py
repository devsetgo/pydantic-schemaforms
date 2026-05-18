"""Reusable contract describing how a framework renders form chrome and assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from pydantic_schemaforms.templates import FormTemplates, TemplateString
from pydantic_schemaforms.tstring import SafeHTML, html
from .theme_assets import ACCORDION_COMPONENT_ASSETS, TAB_COMPONENT_ASSETS

# ---------------------------------------------------------------------------
# Default (Bootstrap-compatible) templates
# ---------------------------------------------------------------------------


def _default_layout_section(
    *, title: str = '', help_html: str = '', body_html: str = '', **_: Any
) -> SafeHTML:
    return html(t"""
<section class="layout-field-section card shadow-sm mb-4">
    <div class="card-header bg-body-tertiary">
        <h3 class="card-title h5 mb-0">{title}</h3>
    </div>
    <div class="card-body">
        {SafeHTML(help_html)}
        <div class="layout-field-content">
            {SafeHTML(body_html)}
        </div>
    </div>
</section>
""")


DEFAULT_LAYOUT_SECTION_TEMPLATE = TemplateString(_default_layout_section)


def _default_layout_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<p class="text-muted mb-2 layout-field-help">{help_text}</p>')


DEFAULT_LAYOUT_HELP_TEMPLATE = TemplateString(_default_layout_help)


def _default_model_list_container(
    *,
    field_name: str = '',
    min_items: str = '',
    max_items: str = '',
    label: str = '',
    required_indicator: str = '',
    items_id: str = '',
    items_html: str = '',
    add_button_label: str = '',
    help_html: str = '',
    error_html: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="mb-3 model-list-block" data-field-name="{field_name}" data-min-items="{min_items}" data-max-items="{max_items}">
    <label class="form-label fw-bold">{label}{SafeHTML(required_indicator)}</label>
    <div class="model-list-container" data-field-name="{field_name}" data-min-items="{min_items}" data-max-items="{max_items}">
        <div class="model-list-items" id="{items_id}">{SafeHTML(items_html)}</div>
        <div class="model-list-controls mt-2">
            <button type="button" class="btn btn-outline-primary btn-sm add-item-btn" data-target="{field_name}">
                <i class="bi bi-plus-circle"></i> {add_button_label}
            </button>
        </div>
    </div>
    {SafeHTML(help_html)}
    {SafeHTML(error_html)}
</div>
''')


DEFAULT_MODEL_LIST_CONTAINER_TEMPLATE = TemplateString(_default_model_list_container)


def _default_model_list_item(
    *,
    index: str = '',
    field_name: str = '',
    model_label: str = '',
    display_index: str = '',
    remove_button_aria_label: str = '',
    body_html: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="model-list-item border rounded p-3 mb-2 bg-light" data-index="{index}" data-field-name="{field_name}">
    <div class="d-flex justify-content-between align-items-start mb-2">
        <h6 class="mb-0 text-primary">
            <i class="bi bi-card-list"></i>
            {model_label} #{display_index}
        </h6>
        <button type="button" class="btn btn-outline-danger btn-sm remove-item-btn" data-index="{index}" aria-label="{remove_button_aria_label}">
            <i class="bi bi-trash"></i>
        </button>
    </div>
    {SafeHTML(body_html)}
</div>
''')


DEFAULT_MODEL_LIST_ITEM_TEMPLATE = TemplateString(_default_model_list_item)


def _default_model_list_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<div class="form-text text-muted model-list-help">{help_text}</div>')


DEFAULT_MODEL_LIST_HELP_TEMPLATE = TemplateString(_default_model_list_help)


def _default_model_list_error(*, error_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<div class="invalid-feedback d-block model-list-error">{error_text}</div>')


DEFAULT_MODEL_LIST_ERROR_TEMPLATE = TemplateString(_default_model_list_error)


def _default_submit_button(
    *, button_class: str = 'btn btn-primary', submit_label: str = 'Submit', **_: Any
) -> SafeHTML:
    return html(t'<button type="submit" class="{button_class}">{submit_label}</button>')


DEFAULT_SUBMIT_BUTTON_TEMPLATE = TemplateString(_default_submit_button)


def _default_field_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<small class="form-text text-muted d-block mt-1 field-help">{help_text}</small>')


DEFAULT_FIELD_HELP_TEMPLATE = TemplateString(_default_field_help)


def _default_field_error(*, error_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<div class="invalid-feedback d-block field-error">{error_text}</div>')


DEFAULT_FIELD_ERROR_TEMPLATE = TemplateString(_default_field_error)


# ---------------------------------------------------------------------------
# Plain (no-framework) templates
# ---------------------------------------------------------------------------


def _plain_layout_section(
    *, title: str = '', help_html: str = '', body_html: str = '', **_: Any
) -> SafeHTML:
    return html(t"""
<section class="layout-field-section">
    <h3 class="layout-field-title">{title}</h3>
    {SafeHTML(help_html)}
    <div class="layout-field-content">
        {SafeHTML(body_html)}
    </div>
</section>
""")


PLAIN_LAYOUT_SECTION_TEMPLATE = TemplateString(_plain_layout_section)


def _plain_layout_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<p class="layout-field-help">{help_text}</p>')


PLAIN_LAYOUT_HELP_TEMPLATE = TemplateString(_plain_layout_help)


def _plain_model_list_container(
    *,
    field_name: str = '',
    min_items: str = '',
    max_items: str = '',
    items_id: str = '',
    items_html: str = '',
    add_button_label: str = '',
    help_html: str = '',
    error_html: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="model-list-block" data-field-name="{field_name}" data-min-items="{min_items}" data-max-items="{max_items}">
    <div class="model-list-items" id="{items_id}">{SafeHTML(items_html)}</div>
    <button type="button" class="add-item-btn" data-target="{field_name}">{add_button_label}</button>
    {SafeHTML(help_html)}
    {SafeHTML(error_html)}
</div>
''')


PLAIN_MODEL_LIST_CONTAINER_TEMPLATE = TemplateString(_plain_model_list_container)


def _plain_model_list_item(
    *,
    index: str = '',
    field_name: str = '',
    model_label: str = '',
    display_index: str = '',
    remove_button_aria_label: str = '',
    body_html: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="model-list-item" data-index="{index}" data-field-name="{field_name}">
    <div class="model-list-header">
        <span>{model_label} #{display_index}</span>
        <button type="button" class="remove-item-btn" data-index="{index}" aria-label="{remove_button_aria_label}">Remove</button>
    </div>
    {SafeHTML(body_html)}
</div>
''')


PLAIN_MODEL_LIST_ITEM_TEMPLATE = TemplateString(_plain_model_list_item)


def _plain_model_list_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<div class="model-list-help">{help_text}</div>')


PLAIN_MODEL_LIST_HELP_TEMPLATE = TemplateString(_plain_model_list_help)


def _plain_model_list_error(*, error_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<div class="model-list-error">{error_text}</div>')


PLAIN_MODEL_LIST_ERROR_TEMPLATE = TemplateString(_plain_model_list_error)


def _plain_field_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<small class="field-help">{help_text}</small>')


PLAIN_FIELD_HELP_TEMPLATE = TemplateString(_plain_field_help)


def _plain_field_error(*, error_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<div class="field-error">{error_text}</div>')


PLAIN_FIELD_ERROR_TEMPLATE = TemplateString(_plain_field_error)


def _plain_submit_button(*, submit_label: str = 'Submit', **_: Any) -> SafeHTML:
    return html(t'<button type="submit">{submit_label}</button>')


PLAIN_SUBMIT_BUTTON_TEMPLATE = TemplateString(_plain_submit_button)


# ---------------------------------------------------------------------------
# Material Design templates
# ---------------------------------------------------------------------------


def _material_layout_section(
    *, title: str = '', help_html: str = '', body_html: str = '', **_: Any
) -> SafeHTML:
    return html(t"""
<section class="md-layout-card">
    <header class="md-layout-card__header">
        <span class="md-layout-card__title">{title}</span>
    </header>
    <div class="md-layout-card__body">
        {SafeHTML(help_html)}
        <div class="md-layout-card__content">
            {SafeHTML(body_html)}
        </div>
    </div>
</section>
""")


MATERIAL_LAYOUT_SECTION_TEMPLATE = TemplateString(_material_layout_section)


def _material_layout_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<p class="md-layout-card__help">{help_text}</p>')


MATERIAL_LAYOUT_HELP_TEMPLATE = TemplateString(_material_layout_help)


# ---------------------------------------------------------------------------
# Bootstrap tab / accordion templates
# ---------------------------------------------------------------------------


def _bootstrap_tab_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    tab_buttons: str = '',
    tab_panels: str = '',
    component_assets: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="tab-layout nav-tabs-wrapper {layout_class}" style="{layout_style}">
    <ul class="nav nav-tabs" role="tablist">
        {SafeHTML(tab_buttons)}
    </ul>
    <div class="tab-content">
        {SafeHTML(tab_panels)}
    </div>
</div>
{SafeHTML(component_assets)}
''')


BOOTSTRAP_TAB_LAYOUT_TEMPLATE = TemplateString(_bootstrap_tab_layout)


def _bootstrap_tab_button(
    *,
    tab_id: str = '',
    title: str = '',
    active_class: str = '',
    aria_selected: str = 'false',
    **_: Any,
) -> SafeHTML:
    _active_class = SafeHTML(active_class)
    return html(t'''
<li class="nav-item" role="presentation">
    <button class="nav-link{_active_class}"
            id="{tab_id}-tab"
            data-bs-toggle="tab"
            data-bs-target="#{tab_id}"
            type="button"
            role="tab"
            aria-controls="{tab_id}"
            aria-selected="{aria_selected}">
        {title}
    </button>
</li>
''')


BOOTSTRAP_TAB_BUTTON_TEMPLATE = TemplateString(_bootstrap_tab_button)


def _bootstrap_tab_panel(
    *, tab_id: str = '', content: str = '', active_class: str = '', **_: Any
) -> SafeHTML:
    _active_class = SafeHTML(active_class)
    return html(t'''
<div class="tab-pane fade{_active_class}"
     id="{tab_id}"
     role="tabpanel"
     aria-labelledby="{tab_id}-tab">
    {SafeHTML(content)}
</div>
''')


BOOTSTRAP_TAB_PANEL_TEMPLATE = TemplateString(_bootstrap_tab_panel)


def _bootstrap_accordion_layout(
    *,
    layout_class: str = '',
    layout_id: str = '',
    layout_style: str = '',
    sections: str = '',
    component_assets: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="accordion {layout_class}" id="{layout_id}" style="{layout_style}">
    {SafeHTML(sections)}
</div>
{SafeHTML(component_assets)}
''')


BOOTSTRAP_ACCORDION_LAYOUT_TEMPLATE = TemplateString(_bootstrap_accordion_layout)


def _bootstrap_accordion_section(
    *,
    section_id: str = '',
    title: str = '',
    content: str = '',
    expanded_class: str = '',
    aria_expanded: str = 'false',
    **_: Any,
) -> SafeHTML:
    _expanded_class = SafeHTML(expanded_class)
    return html(t'''
<div class="accordion-item">
    <h2 class="accordion-header" id="{section_id}-header">
        <button class="accordion-button{_expanded_class}" type="button" data-bs-toggle="collapse" data-bs-target="#{section_id}"
            aria-expanded="{aria_expanded}" aria-controls="{section_id}">
            {title}
        </button>
    </h2>
    <div id="{section_id}" class="accordion-collapse collapse{_expanded_class}" aria-labelledby="{section_id}-header">
        <div class="accordion-body">{SafeHTML(content)}</div>
    </div>
</div>
''')


BOOTSTRAP_ACCORDION_SECTION_TEMPLATE = TemplateString(_bootstrap_accordion_section)


# ---------------------------------------------------------------------------
# Plain tab / accordion templates
# ---------------------------------------------------------------------------


def _plain_tab_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    tab_buttons: str = '',
    tab_panels: str = '',
    component_assets: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="tab-layout {layout_class}" style="{layout_style}">
    <div class="tab-navigation" role="tablist">{SafeHTML(tab_buttons)}</div>
    <div class="tab-content">{SafeHTML(tab_panels)}</div>
</div>
{SafeHTML(component_assets)}
''')


PLAIN_TAB_LAYOUT_TEMPLATE = TemplateString(_plain_tab_layout)

PLAIN_TAB_BUTTON_TEMPLATE = FormTemplates.TAB_BUTTON
PLAIN_TAB_PANEL_TEMPLATE = FormTemplates.TAB_PANEL


def _plain_accordion_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    sections: str = '',
    component_assets: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="accordion-layout {layout_class}" style="{layout_style}">
    {SafeHTML(sections)}
</div>
{SafeHTML(component_assets)}
''')


PLAIN_ACCORDION_LAYOUT_TEMPLATE = TemplateString(_plain_accordion_layout)

PLAIN_ACCORDION_SECTION_TEMPLATE = FormTemplates.ACCORDION_SECTION


# ---------------------------------------------------------------------------
# Material tab / accordion templates
# ---------------------------------------------------------------------------


def _material_tab_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    tab_buttons: str = '',
    tab_panels: str = '',
    component_assets: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="tab-layout md-tab-layout {layout_class}" style="{layout_style}">
    <div class="tab-navigation md-tab-navigation" role="tablist">{SafeHTML(tab_buttons)}</div>
    <div class="tab-content md-tab-content">{SafeHTML(tab_panels)}</div>
</div>
{SafeHTML(component_assets)}
''')


MATERIAL_TAB_LAYOUT_TEMPLATE = TemplateString(_material_tab_layout)


def _material_tab_button(
    *,
    tab_id: str = '',
    title: str = '',
    active_class: str = '',
    aria_selected: str = 'false',
    **_: Any,
) -> SafeHTML:
    _active_class = SafeHTML(active_class)
    return html(t'''
<button class="tab-button md-tab-button{_active_class}" type="button" role="tab"
        aria-selected="{aria_selected}" aria-controls="{tab_id}" onclick="switchTab(&#39;{tab_id}&#39;, this)">
    {title}
</button>
''')


MATERIAL_TAB_BUTTON_TEMPLATE = TemplateString(_material_tab_button)

MATERIAL_TAB_PANEL_TEMPLATE = FormTemplates.TAB_PANEL


def _material_accordion_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    sections: str = '',
    component_assets: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<div class="md-accordion-layout {layout_class}" style="{layout_style}">
    {SafeHTML(sections)}
</div>
{SafeHTML(component_assets)}
''')


MATERIAL_ACCORDION_LAYOUT_TEMPLATE = TemplateString(_material_accordion_layout)


def _material_accordion_section(
    *,
    section_id: str = '',
    title: str = '',
    content: str = '',
    expanded_class: str = '',
    aria_expanded: str = 'false',
    display_style: str = 'none',
    **_: Any,
) -> SafeHTML:
    _expanded_class = SafeHTML(expanded_class)
    return html(t'''
<div class="md-accordion-section">
    <button class="md-accordion-header{_expanded_class}" aria-expanded="{aria_expanded}"
            aria-controls="{section_id}" onclick="toggleAccordion(&#39;{section_id}&#39;, this)">
        {title}
    </button>
    <div id="{section_id}" class="md-accordion-content" style="display: {display_style};">
        {SafeHTML(content)}
    </div>
</div>
''')


MATERIAL_ACCORDION_SECTION_TEMPLATE = TemplateString(_material_accordion_section)


def _material_model_list_container(
    *,
    field_name: str = '',
    min_items: str = '',
    max_items: str = '',
    label: str = '',
    required_indicator: str = '',
    items_id: str = '',
    items_html: str = '',
    add_button_label: str = '',
    help_html: str = '',
    error_html: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<section class="md-model-list-wrapper" data-field-name="{field_name}" data-min-items="{min_items}" data-max-items="{max_items}">
    <label class="md-field-label">{label}{SafeHTML(required_indicator)}</label>
    <div class="model-list-container md-model-list-container" data-field-name="{field_name}" data-min-items="{min_items}" data-max-items="{max_items}">
        <div class="model-list-items md-model-list-items" id="{items_id}">{SafeHTML(items_html)}</div>
        <div class="md-model-list-actions">
            <button type="button" class="md-button md-button-tonal add-item-btn" data-target="{field_name}">
                <span class="material-icons md-button__icon">add</span>
                <span class="md-button__label">{add_button_label}</span>
            </button>
        </div>
    </div>
    {SafeHTML(help_html)}
    {SafeHTML(error_html)}
</section>
''')


MATERIAL_MODEL_LIST_CONTAINER_TEMPLATE = TemplateString(_material_model_list_container)


def _material_model_list_item(
    *,
    index: str = '',
    field_name: str = '',
    model_label: str = '',
    display_index: str = '',
    remove_button_aria_label: str = '',
    body_html: str = '',
    **_: Any,
) -> SafeHTML:
    return html(t'''
<section class="model-list-item md-model-card mdc-card mdc-card--outlined" data-index="{index}" data-field-name="{field_name}">
    <div class="mdc-card__primary-action">
        <header class="md-model-card__header">
            <h6 class="mdc-typography--subtitle2 mb-0">{model_label} #{display_index}</h6>
            <button type="button" class="md-icon-button mdc-icon-button remove-item-btn" data-index="{index}" aria-label="{remove_button_aria_label}">
                <span class="material-icons">delete</span>
            </button>
        </header>
        <div class="md-model-card__body">{SafeHTML(body_html)}</div>
    </div>
</section>
''')


MATERIAL_MODEL_LIST_ITEM_TEMPLATE = TemplateString(_material_model_list_item)


def _material_model_list_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<p class="md-help-text">{help_text}</p>')


MATERIAL_MODEL_LIST_HELP_TEMPLATE = TemplateString(_material_model_list_help)


def _material_model_list_error(*, error_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<p class="md-error-text">{error_text}</p>')


MATERIAL_MODEL_LIST_ERROR_TEMPLATE = TemplateString(_material_model_list_error)


def _material_field_help(*, help_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<p class="md-field-help-text">{help_text}</p>')


MATERIAL_FIELD_HELP_TEMPLATE = TemplateString(_material_field_help)


def _material_field_error(*, error_text: str = '', **_: Any) -> SafeHTML:
    return html(t'<p class="md-field-error-text">{error_text}</p>')


MATERIAL_FIELD_ERROR_TEMPLATE = TemplateString(_material_field_error)


def _material_submit_button(*, submit_label: str = 'Submit', **_: Any) -> SafeHTML:
    return html(t'<button type="submit" class="md-button md-button-filled">{submit_label}</button>')


MATERIAL_SUBMIT_BUTTON_TEMPLATE = TemplateString(_material_submit_button)


# ---------------------------------------------------------------------------
# FormStyleTemplates dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FormStyleTemplates:
    """Template bundle used when rendering shared chrome."""

    form_wrapper: TemplateString = FormTemplates.FORM_WRAPPER
    tab_layout: TemplateString = FormTemplates.TAB_LAYOUT
    tab_button: TemplateString = FormTemplates.TAB_BUTTON
    tab_panel: TemplateString = FormTemplates.TAB_PANEL
    accordion_layout: TemplateString = FormTemplates.ACCORDION_LAYOUT
    accordion_section: TemplateString = FormTemplates.ACCORDION_SECTION
    layout_section: TemplateString = DEFAULT_LAYOUT_SECTION_TEMPLATE
    layout_help: TemplateString = DEFAULT_LAYOUT_HELP_TEMPLATE
    model_list_container: TemplateString = DEFAULT_MODEL_LIST_CONTAINER_TEMPLATE
    model_list_item: TemplateString = DEFAULT_MODEL_LIST_ITEM_TEMPLATE
    model_list_help: TemplateString = DEFAULT_MODEL_LIST_HELP_TEMPLATE
    model_list_error: TemplateString = DEFAULT_MODEL_LIST_ERROR_TEMPLATE
    field_help: TemplateString = DEFAULT_FIELD_HELP_TEMPLATE
    field_error: TemplateString = DEFAULT_FIELD_ERROR_TEMPLATE
    submit_button: TemplateString = DEFAULT_SUBMIT_BUTTON_TEMPLATE


@dataclass(frozen=True)
class FormStyleAssets:
    """Declarative collection of renderer asset snippets."""

    before_form: str = ''
    after_form: str = ''
    tab_assets: str = TAB_COMPONENT_ASSETS
    accordion_assets: str = ACCORDION_COMPONENT_ASSETS


@dataclass(frozen=True)
class FormStyle:
    """Descriptor that ties a framework + variant to templates/assets."""

    framework: str
    variant: str = 'default'
    name: str | None = None
    templates: FormStyleTemplates = FormStyleTemplates()
    assets: FormStyleAssets = FormStyleAssets()

    def key(self) -> Tuple[str, str]:
        return (self.framework, self.variant)


_FORM_STYLE_REGISTRY: Dict[Tuple[str, str], FormStyle] = {}


def _parse_framework_variant(framework: str, variant: str | None = None) -> Tuple[str, str]:
    """Normalize framework/variant inputs, supporting descriptor syntax like 'bootstrap:5'."""
    if variant:
        return framework, variant
    if ':' in framework:
        base, version = framework.split(':', 1)
        return base, version
    return framework, 'default'


def register_form_style(style: FormStyle) -> None:
    """Register or override a FormStyle for a framework/variant pair."""
    _FORM_STYLE_REGISTRY[style.key()] = style


def get_form_style(framework: str, variant: str | None = None) -> FormStyle:
    """Return the registered style for a framework/variant pair."""
    key = _parse_framework_variant(framework, variant)
    if key in _FORM_STYLE_REGISTRY:
        return _FORM_STYLE_REGISTRY[key]
    base_framework, _ = key
    base_key = (base_framework, 'default')
    if base_key in _FORM_STYLE_REGISTRY:
        return _FORM_STYLE_REGISTRY[base_key]
    fallback = ('default', 'default')
    if fallback in _FORM_STYLE_REGISTRY:
        return _FORM_STYLE_REGISTRY[fallback]
    raise KeyError(f'No form style registered for framework={framework!r} variant={variant!r}')


# ---------------------------------------------------------------------------
# Register built-in styles
# ---------------------------------------------------------------------------

register_form_style(FormStyle(framework='default', variant='default'))

register_form_style(
    FormStyle(
        framework='bootstrap',
        templates=FormStyleTemplates(
            tab_layout=BOOTSTRAP_TAB_LAYOUT_TEMPLATE,
            tab_button=BOOTSTRAP_TAB_BUTTON_TEMPLATE,
            tab_panel=BOOTSTRAP_TAB_PANEL_TEMPLATE,
            accordion_layout=BOOTSTRAP_ACCORDION_LAYOUT_TEMPLATE,
            accordion_section=BOOTSTRAP_ACCORDION_SECTION_TEMPLATE,
            field_help=DEFAULT_FIELD_HELP_TEMPLATE,
            field_error=DEFAULT_FIELD_ERROR_TEMPLATE,
        ),
    )
)

register_form_style(
    FormStyle(
        framework='bootstrap',
        variant='5',
        templates=FormStyleTemplates(
            tab_layout=BOOTSTRAP_TAB_LAYOUT_TEMPLATE,
            tab_button=BOOTSTRAP_TAB_BUTTON_TEMPLATE,
            tab_panel=BOOTSTRAP_TAB_PANEL_TEMPLATE,
            accordion_layout=BOOTSTRAP_ACCORDION_LAYOUT_TEMPLATE,
            accordion_section=BOOTSTRAP_ACCORDION_SECTION_TEMPLATE,
            field_help=DEFAULT_FIELD_HELP_TEMPLATE,
            field_error=DEFAULT_FIELD_ERROR_TEMPLATE,
        ),
    )
)

register_form_style(
    FormStyle(
        framework='plain',
        templates=FormStyleTemplates(
            layout_section=PLAIN_LAYOUT_SECTION_TEMPLATE,
            layout_help=PLAIN_LAYOUT_HELP_TEMPLATE,
            tab_layout=PLAIN_TAB_LAYOUT_TEMPLATE,
            tab_button=PLAIN_TAB_BUTTON_TEMPLATE,
            tab_panel=PLAIN_TAB_PANEL_TEMPLATE,
            accordion_layout=PLAIN_ACCORDION_LAYOUT_TEMPLATE,
            accordion_section=PLAIN_ACCORDION_SECTION_TEMPLATE,
            model_list_container=PLAIN_MODEL_LIST_CONTAINER_TEMPLATE,
            model_list_item=PLAIN_MODEL_LIST_ITEM_TEMPLATE,
            model_list_help=PLAIN_MODEL_LIST_HELP_TEMPLATE,
            model_list_error=PLAIN_MODEL_LIST_ERROR_TEMPLATE,
            field_help=PLAIN_FIELD_HELP_TEMPLATE,
            field_error=PLAIN_FIELD_ERROR_TEMPLATE,
            submit_button=PLAIN_SUBMIT_BUTTON_TEMPLATE,
        ),
    )
)

_MATERIAL_TEMPLATES = FormStyleTemplates(
    layout_section=MATERIAL_LAYOUT_SECTION_TEMPLATE,
    layout_help=MATERIAL_LAYOUT_HELP_TEMPLATE,
    tab_layout=MATERIAL_TAB_LAYOUT_TEMPLATE,
    tab_button=MATERIAL_TAB_BUTTON_TEMPLATE,
    tab_panel=MATERIAL_TAB_PANEL_TEMPLATE,
    accordion_layout=MATERIAL_ACCORDION_LAYOUT_TEMPLATE,
    accordion_section=MATERIAL_ACCORDION_SECTION_TEMPLATE,
    model_list_container=MATERIAL_MODEL_LIST_CONTAINER_TEMPLATE,
    model_list_item=MATERIAL_MODEL_LIST_ITEM_TEMPLATE,
    model_list_help=MATERIAL_MODEL_LIST_HELP_TEMPLATE,
    model_list_error=MATERIAL_MODEL_LIST_ERROR_TEMPLATE,
    field_help=MATERIAL_FIELD_HELP_TEMPLATE,
    field_error=MATERIAL_FIELD_ERROR_TEMPLATE,
    submit_button=MATERIAL_SUBMIT_BUTTON_TEMPLATE,
)

register_form_style(FormStyle(framework='material', templates=_MATERIAL_TEMPLATES))
register_form_style(FormStyle(framework='material', variant='3', templates=_MATERIAL_TEMPLATES))
register_form_style(FormStyle(framework='material-embedded', templates=_MATERIAL_TEMPLATES))
