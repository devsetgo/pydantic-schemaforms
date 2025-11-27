"""Tests for theme-specific hooks that power tabs, accordions, and model lists."""

from typing import Dict, Optional, Type

from pydantic_forms.model_list import ModelListRenderer
from pydantic_forms.rendering.layout_engine import AccordionLayout, TabLayout
from pydantic_forms.rendering.themes import RendererTheme
from pydantic_forms.schema_form import FormModel


class _StubTheme(RendererTheme):
    """Theme that exposes unique markers for assertions."""

    def tab_component_assets(self) -> str:  # type: ignore[override]
        return "<style>.custom-tab-asset{color:red;}</style>"

    def accordion_component_assets(self) -> str:  # type: ignore[override]
        return "<style>.custom-accordion-asset{color:blue;}</style>"

    def render_model_list_container(  # type: ignore[override]
        self,
        *,
        field_name: str,
        label: str,
        is_required: bool,
        min_items: int,
        max_items: int,
        items_html: str,
        help_text: Optional[str],
        error: Optional[str],
        add_button_label: str,
    ) -> str:
        return (
            f"<section class='custom-model-list' data-field='{field_name}'>"
            f"<header>{label}</header>"
            f"<div class='items'>{items_html}</div>"
            f"<footer>{add_button_label}</footer>"
            "</section>"
        )

    def render_model_list_item(  # type: ignore[override]
        self,
        *,
        field_name: str,
        model_label: str,
        index: int,
        body_html: str,
        remove_button_aria_label: str,
    ) -> str:
        return (
            f"<article class='custom-item' data-field='{field_name}' data-index='{index}'>"
            f"<h6>{model_label}</h6>"
            f"<div class='body'>{body_html}</div>"
            f"<button aria-label='{remove_button_aria_label}'>x</button>"
            "</article>"
        )


class _StubRenderer:
    def __init__(self, theme: RendererTheme) -> None:
        self.theme = theme


class _StubModel(FormModel):
    name: str


def test_tab_layout_uses_theme_assets() -> None:
    layout = TabLayout([
        {"title": "General", "content": "<p>Info</p>"},
    ])
    stub_renderer = _StubRenderer(_StubTheme())

    html = layout.render(renderer=stub_renderer, framework="bootstrap")

    assert ".custom-tab-asset" in html


def test_accordion_layout_uses_theme_assets() -> None:
    layout = AccordionLayout([
        {"title": "FAQ", "content": "Answer"},
    ])
    stub_renderer = _StubRenderer(_StubTheme())

    html = layout.render(renderer=stub_renderer, framework="bootstrap")

    assert ".custom-accordion-asset" in html


def test_model_list_renderer_delegates_container_to_theme() -> None:
    class _StubListRenderer(ModelListRenderer):
        def __init__(self) -> None:
            super().__init__(framework="bootstrap")
            self._theme = _StubTheme()

        def _resolve_theme(self) -> RendererTheme:  # type: ignore[override]
            return self._theme

        def _render_item_body(  # type: ignore[override]
            self,
            field_name: str,
            model_class: Type[FormModel],
            index: int,
            item_data: Dict[str, str],
            nested_errors: Optional[Dict[str, str]] = None,
        ) -> str:
            return f"<div class='item-body' data-index='{index}'>Body</div>"

    renderer = _StubListRenderer()

    html = renderer.render_model_list(
        field_name="pets",
        label="Pets",
        model_class=_StubModel,
        values=[{"name": "Rex"}],
        min_items=0,
        max_items=5,
    )

    assert "custom-model-list" in html
    assert "Add Pets" in html  # comes from add_button_label argument
    assert "custom-item" in html
    assert "item-body" in html
