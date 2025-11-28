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


@dataclass(frozen=True)
class FormStyleTemplates:
    """Template bundle used when rendering shared chrome."""

    form_wrapper: TemplateString = FormTemplates.FORM_WRAPPER
    tab_layout: TemplateString = FormTemplates.TAB_LAYOUT
    accordion_layout: TemplateString = FormTemplates.ACCORDION_LAYOUT
    layout_section: TemplateString = DEFAULT_LAYOUT_SECTION_TEMPLATE
    layout_help: TemplateString = DEFAULT_LAYOUT_HELP_TEMPLATE


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


def register_form_style(style: FormStyle) -> None:
    """Register or override a `FormStyle` for a framework/variant pair."""

    _FORM_STYLE_REGISTRY[style.key()] = style


def get_form_style(framework: str, variant: str | None = None) -> FormStyle:
    """Return the registered style for a framework/variant pair."""

    key = (framework, variant or "default")
    if key in _FORM_STYLE_REGISTRY:
        return _FORM_STYLE_REGISTRY[key]

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
register_form_style(FormStyle(framework="bootstrap"))

register_form_style(
    FormStyle(
        framework="plain",
        templates=FormStyleTemplates(
            layout_section=PLAIN_LAYOUT_SECTION_TEMPLATE,
            layout_help=PLAIN_LAYOUT_HELP_TEMPLATE,
        ),
    )
)

_MATERIAL_TEMPLATES = FormStyleTemplates(
    layout_section=MATERIAL_LAYOUT_SECTION_TEMPLATE,
    layout_help=MATERIAL_LAYOUT_HELP_TEMPLATE,
)

register_form_style(
    FormStyle(
        framework="material",
        templates=_MATERIAL_TEMPLATES,
    )
)
register_form_style(
    FormStyle(
        framework="material-embedded",
        templates=_MATERIAL_TEMPLATES,
    )
)
