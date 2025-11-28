"""Reusable contract describing how a framework renders form chrome and assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from ..templates import FormTemplates, TemplateString
from .theme_assets import ACCORDION_COMPONENT_ASSETS, TAB_COMPONENT_ASSETS


@dataclass(frozen=True)
class FormStyleTemplates:
    """Template bundle used when rendering shared chrome."""

    form_wrapper: TemplateString = FormTemplates.FORM_WRAPPER
    tab_layout: TemplateString = FormTemplates.TAB_LAYOUT
    accordion_layout: TemplateString = FormTemplates.ACCORDION_LAYOUT


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
register_form_style(FormStyle(framework="material"))
register_form_style(FormStyle(framework="plain"))
