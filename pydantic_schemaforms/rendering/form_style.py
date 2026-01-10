"""Reusable contract describing how a framework renders form chrome and assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from ..templates import FormTemplates, TemplateString
from .theme_assets import ACCORDION_COMPONENT_ASSETS, TAB_COMPONENT_ASSETS

DEFAULT_LAYOUT_SECTION_TEMPLATE = TemplateString(
    """
<section class="layout-field-section card shadow-sm mb-4">
    <div class="card-header bg-body-tertiary">
        <h3 class="card-title h5 mb-0">${title}</h3>
    </div>
    <div class="card-body">
        ${help_html}
        <div class="layout-field-content">
            ${body_html}
        </div>
    </div>
</section>
"""
)

DEFAULT_LAYOUT_HELP_TEMPLATE = TemplateString(
    """
<p class="text-muted mb-2 layout-field-help">${help_text}</p>
"""
)

DEFAULT_MODEL_LIST_CONTAINER_TEMPLATE = TemplateString(
    """
<div class="mb-3 model-list-block" data-field-name="${field_name}" data-min-items="${min_items}" data-max-items="${max_items}">
    <label class="form-label fw-bold">${label}${required_indicator}</label>
    <div class="model-list-container" data-field-name="${field_name}" data-min-items="${min_items}" data-max-items="${max_items}">
        <div class="model-list-items" id="${items_id}">${items_html}</div>
        <div class="model-list-controls mt-2">
            <button type="button" class="btn btn-outline-primary btn-sm add-item-btn" data-target="${field_name}">
                <i class="bi bi-plus-circle"></i> ${add_button_label}
            </button>
        </div>
    </div>
    ${help_html}
    ${error_html}
</div>
"""
)

DEFAULT_MODEL_LIST_ITEM_TEMPLATE = TemplateString(
    """
<div class="model-list-item border rounded p-3 mb-2 bg-light" data-index="${index}" data-field-name="${field_name}">
    <div class="d-flex justify-content-between align-items-start mb-2">
        <h6 class="mb-0 text-primary">
            <i class="bi bi-card-list"></i>
            ${model_label} #${display_index}
        </h6>
        <button type="button" class="btn btn-outline-danger btn-sm remove-item-btn" data-index="${index}" aria-label="${remove_button_aria_label}">
            <i class="bi bi-trash"></i>
        </button>
    </div>
    ${body_html}
</div>
"""
)

DEFAULT_MODEL_LIST_HELP_TEMPLATE = TemplateString(
    """
<div class="form-text text-muted model-list-help">${help_text}</div>
"""
)

DEFAULT_MODEL_LIST_ERROR_TEMPLATE = TemplateString(
    """
<div class="invalid-feedback d-block model-list-error">${error_text}</div>
"""
)

DEFAULT_SUBMIT_BUTTON_TEMPLATE = TemplateString(
    """
<button type="submit" class="${button_class}">${submit_label}</button>
"""
)

DEFAULT_FIELD_HELP_TEMPLATE = TemplateString(
    """
<small class="form-text text-muted d-block mt-1 field-help">${help_text}</small>
"""
)

DEFAULT_FIELD_ERROR_TEMPLATE = TemplateString(
    """
<div class="invalid-feedback d-block field-error">${error_text}</div>
"""
)

PLAIN_LAYOUT_SECTION_TEMPLATE = TemplateString(
    """
<section class="layout-field-section">
    <h3 class="layout-field-title">${title}</h3>
    ${help_html}
    <div class="layout-field-content">
        ${body_html}
    </div>
</section>
"""
)

PLAIN_LAYOUT_HELP_TEMPLATE = TemplateString(
    """
<p class="layout-field-help">${help_text}</p>
"""
)

PLAIN_MODEL_LIST_CONTAINER_TEMPLATE = TemplateString(
    """
<div class="model-list-block" data-field-name="${field_name}" data-min-items="${min_items}" data-max-items="${max_items}">
    <div class="model-list-items" id="${items_id}">${items_html}</div>
    <button type="button" class="add-item-btn" data-target="${field_name}">${add_button_label}</button>
    ${help_html}
    ${error_html}
</div>
"""
)

PLAIN_MODEL_LIST_ITEM_TEMPLATE = TemplateString(
    """
<div class="model-list-item" data-index="${index}" data-field-name="${field_name}">
    <div class="model-list-header">
        <span>${model_label} #${display_index}</span>
        <button type="button" class="remove-item-btn" data-index="${index}" aria-label="${remove_button_aria_label}">Remove</button>
    </div>
    ${body_html}
</div>
"""
)

PLAIN_MODEL_LIST_HELP_TEMPLATE = TemplateString(
    """
<div class="model-list-help">${help_text}</div>
"""
)

PLAIN_MODEL_LIST_ERROR_TEMPLATE = TemplateString(
    """
<div class="model-list-error">${error_text}</div>
"""
)

PLAIN_FIELD_HELP_TEMPLATE = TemplateString(
    """
<small class="field-help">${help_text}</small>
"""
)

PLAIN_FIELD_ERROR_TEMPLATE = TemplateString(
    """
<div class="field-error">${error_text}</div>
"""
)

PLAIN_SUBMIT_BUTTON_TEMPLATE = TemplateString(
    """
<button type="submit">${submit_label}</button>
"""
)

MATERIAL_LAYOUT_SECTION_TEMPLATE = TemplateString(
    """
<section class="md-layout-card">
    <header class="md-layout-card__header">
        <span class="md-layout-card__title">${title}</span>
    </header>
    <div class="md-layout-card__body">
        ${help_html}
        <div class="md-layout-card__content">
            ${body_html}
        </div>
    </div>
</section>
"""
)

MATERIAL_LAYOUT_HELP_TEMPLATE = TemplateString(
    """
<p class="md-layout-card__help">${help_text}</p>
"""
)

# Framework-specific tab/accordion templates
BOOTSTRAP_TAB_LAYOUT_TEMPLATE = TemplateString(
    """
<div class="tab-layout nav-tabs-wrapper ${layout_class}" style="${layout_style}">
    <ul class="nav nav-tabs" role="tablist">
        ${tab_buttons}
    </ul>
    <div class="tab-content">
        ${tab_panels}
    </div>
</div>
${component_assets}
"""
)

BOOTSTRAP_TAB_BUTTON_TEMPLATE = TemplateString(
    """
<li class="nav-item" role="presentation">
    <button class="nav-link${active_class}"
            id="${tab_id}-tab"
            data-bs-toggle="tab"
            data-bs-target="#${tab_id}"
            type="button"
            role="tab"
            aria-controls="${tab_id}"
            aria-selected="${aria_selected}">
        ${title}
    </button>
</li>
"""
)

BOOTSTRAP_TAB_PANEL_TEMPLATE = TemplateString(
    """
<div class="tab-pane fade${active_class}"
     id="${tab_id}"
     role="tabpanel"
     aria-labelledby="${tab_id}-tab">
    ${content}
</div>
"""
)

BOOTSTRAP_ACCORDION_LAYOUT_TEMPLATE = TemplateString(
    """
<div class="accordion ${layout_class}" id="${layout_id}" style="${layout_style}">
    ${sections}
</div>
${component_assets}
"""
)

BOOTSTRAP_ACCORDION_SECTION_TEMPLATE = TemplateString(
    """
<div class="accordion-item">
    <h2 class="accordion-header" id="${section_id}-header">
        <button class="accordion-button${expanded_class}" type="button" data-bs-toggle="collapse" data-bs-target="#${section_id}"
            aria-expanded="${aria_expanded}" aria-controls="${section_id}">
            ${title}
        </button>
    </h2>
    <div id="${section_id}" class="accordion-collapse collapse${expanded_class}" aria-labelledby="${section_id}-header">
        <div class="accordion-body">${content}</div>
    </div>
</div>
"""
)

PLAIN_TAB_LAYOUT_TEMPLATE = TemplateString(
    """
<div class="tab-layout ${layout_class}" style="${layout_style}">
    <div class="tab-navigation" role="tablist">${tab_buttons}</div>
    <div class="tab-content">${tab_panels}</div>
</div>
${component_assets}
"""
)

PLAIN_TAB_BUTTON_TEMPLATE = FormTemplates.TAB_BUTTON
PLAIN_TAB_PANEL_TEMPLATE = FormTemplates.TAB_PANEL

PLAIN_ACCORDION_LAYOUT_TEMPLATE = TemplateString(
    """
<div class="accordion-layout ${layout_class}" style="${layout_style}">
    ${sections}
</div>
${component_assets}
"""
)

PLAIN_ACCORDION_SECTION_TEMPLATE = FormTemplates.ACCORDION_SECTION

MATERIAL_TAB_LAYOUT_TEMPLATE = TemplateString(
    """
<div class="tab-layout md-tab-layout ${layout_class}" style="${layout_style}">
    <div class="tab-navigation md-tab-navigation" role="tablist">${tab_buttons}</div>
    <div class="tab-content md-tab-content">${tab_panels}</div>
</div>
${component_assets}
"""
)

MATERIAL_TAB_BUTTON_TEMPLATE = TemplateString(
    """
<button class="tab-button md-tab-button${active_class}" type="button" role="tab"
        aria-selected="${aria_selected}" aria-controls="${tab_id}" onclick="switchTab('${tab_id}', this)">
    ${title}
</button>
"""
)

MATERIAL_TAB_PANEL_TEMPLATE = FormTemplates.TAB_PANEL

MATERIAL_ACCORDION_LAYOUT_TEMPLATE = TemplateString(
    """
<div class="md-accordion-layout ${layout_class}" style="${layout_style}">
    ${sections}
</div>
${component_assets}
"""
)

MATERIAL_ACCORDION_SECTION_TEMPLATE = TemplateString(
    """
<div class="md-accordion-section">
    <button class="md-accordion-header${expanded_class}" aria-expanded="${aria_expanded}"
            aria-controls="${section_id}" onclick="toggleAccordion('${section_id}', this)">
        ${title}
    </button>
    <div id="${section_id}" class="md-accordion-content" style="display: ${display_style};">
        ${content}
    </div>
</div>
"""
)

MATERIAL_MODEL_LIST_CONTAINER_TEMPLATE = TemplateString(
        """
<section class="md-model-list-wrapper" data-field-name="${field_name}" data-min-items="${min_items}" data-max-items="${max_items}">
    <label class="md-field-label">${label}${required_indicator}</label>
    <div class="model-list-container md-model-list-container" data-field-name="${field_name}" data-min-items="${min_items}" data-max-items="${max_items}">
        <div class="model-list-items md-model-list-items" id="${items_id}">${items_html}</div>
        <div class="md-model-list-actions">
            <button type="button" class="md-button md-button-tonal add-item-btn" data-target="${field_name}">
                <span class="material-icons md-button__icon">add</span>
                <span class="md-button__label">${add_button_label}</span>
            </button>
        </div>
    </div>
    ${help_html}
    ${error_html}
</section>
"""
)

MATERIAL_MODEL_LIST_ITEM_TEMPLATE = TemplateString(
        """
<section class="model-list-item md-model-card mdc-card mdc-card--outlined" data-index="${index}" data-field-name="${field_name}">
    <div class="mdc-card__primary-action">
        <header class="md-model-card__header">
            <h6 class="mdc-typography--subtitle2 mb-0">${model_label} #${display_index}</h6>
            <button type="button" class="md-icon-button mdc-icon-button remove-item-btn" data-index="${index}" aria-label="${remove_button_aria_label}">
                <span class="material-icons">delete</span>
            </button>
        </header>
        <div class="md-model-card__body">${body_html}</div>
    </div>
</section>
"""
)

MATERIAL_MODEL_LIST_HELP_TEMPLATE = TemplateString(
        """
<p class="md-help-text">${help_text}</p>
"""
)

MATERIAL_MODEL_LIST_ERROR_TEMPLATE = TemplateString(
        """
<p class="md-error-text">${error_text}</p>
"""
)

MATERIAL_FIELD_HELP_TEMPLATE = TemplateString(
        """
<p class="md-field-help-text">${help_text}</p>
"""
)

MATERIAL_FIELD_ERROR_TEMPLATE = TemplateString(
        """
<p class="md-field-error-text">${error_text}</p>
"""
)

MATERIAL_SUBMIT_BUTTON_TEMPLATE = TemplateString(
        """
<button type="submit" class="md-button md-button-filled">${submit_label}</button>
"""
)


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

    before_form: str = ""
    after_form: str = ""
    tab_assets: str = TAB_COMPONENT_ASSETS
    accordion_assets: str = ACCORDION_COMPONENT_ASSETS


@dataclass(frozen=True)
class FormStyle:
    """Descriptor that ties a framework + variant to templates/assets."""

    framework: str
    variant: str = "default"
    name: str | None = None
    templates: FormStyleTemplates = FormStyleTemplates()
    assets: FormStyleAssets = FormStyleAssets()

    def key(self) -> Tuple[str, str]:
        return (self.framework, self.variant)


_FORM_STYLE_REGISTRY: Dict[Tuple[str, str], FormStyle] = {}


def _parse_framework_variant(framework: str, variant: str | None = None) -> Tuple[str, str]:
    """Normalize framework/variant inputs, supporting descriptor syntax like "bootstrap:5".

    Accepts either:
    - framework="bootstrap", variant="5"
    - framework="bootstrap:5", variant=None
    - framework="bootstrap", variant=None (falls back to "default")
    """

    if variant:
        return framework, variant

    if ":" in framework:
        base, version = framework.split(":", 1)
        return base, version

    return framework, "default"


def register_form_style(style: FormStyle) -> None:
    """Register or override a `FormStyle` for a framework/variant pair."""

    _FORM_STYLE_REGISTRY[style.key()] = style


def get_form_style(framework: str, variant: str | None = None) -> FormStyle:
    """Return the registered style for a framework/variant pair."""

    # First try the normalized descriptor (supports "framework:version" shortcuts)
    key = _parse_framework_variant(framework, variant)
    if key in _FORM_STYLE_REGISTRY:
        return _FORM_STYLE_REGISTRY[key]

    # Fallback to the base framework with default variant (e.g., "bootstrap" -> ("bootstrap", "default"))
    base_framework, _ = key
    base_key = (base_framework, "default")
    if base_key in _FORM_STYLE_REGISTRY:
        return _FORM_STYLE_REGISTRY[base_key]

    # Final fallback to the global default style
    fallback = ("default", "default")
    if fallback in _FORM_STYLE_REGISTRY:
        return _FORM_STYLE_REGISTRY[fallback]

    raise KeyError(f"No form style registered for framework={framework!r} variant={variant!r}")


# Register the default (bootstrap/plain) style eagerly.
_DEFAULT_STYLE = FormStyle(
    framework="default",
    variant="default",
)

register_form_style(_DEFAULT_STYLE)
register_form_style(
    FormStyle(
        framework="bootstrap",
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

# Bootstrap v5 alias (descriptor access: "bootstrap:5")
register_form_style(
    FormStyle(
        framework="bootstrap",
        variant="5",
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
        framework="plain",
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

register_form_style(
    FormStyle(
        framework="material",
        templates=_MATERIAL_TEMPLATES,
    )
)

# Material Design v3 alias (descriptor access: "material:3")
register_form_style(
    FormStyle(
        framework="material",
        variant="3",
        templates=_MATERIAL_TEMPLATES,
    )
)
register_form_style(
    FormStyle(
        framework="material-embedded",
        templates=_MATERIAL_TEMPLATES,
    )
)
