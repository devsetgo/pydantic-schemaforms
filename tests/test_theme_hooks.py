"""Tests for theme-specific hooks that power tabs, accordions, and model lists."""

from typing import Dict, Optional, Type

from pydantic_schemaforms.model_list import ModelListRenderer
from pydantic_schemaforms.rendering.form_style import FormStyle, FormStyleTemplates, register_form_style
from pydantic_schemaforms.rendering.layout_engine import AccordionLayout, TabLayout
from pydantic_schemaforms.rendering.themes import MaterialEmbeddedTheme, RendererTheme
from pydantic_schemaforms.schema_form import FormModel
from pydantic_schemaforms.templates import TemplateString


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


def test_model_list_uses_form_style_templates() -> None:
    renderer = ModelListRenderer(framework="bootstrap")

    html = renderer.render_model_list(
        field_name="pets",
        label="Pets",
        model_class=_StubModel,
        values=[{"name": "Rex"}],
        min_items=0,
        max_items=5,
    )

    assert "model-list-block" in html
    assert "model-list-items" in html
    assert "add-item-btn" in html


def test_model_list_respects_custom_form_style_templates() -> None:
    custom_templates = FormStyleTemplates(
        model_list_container=TemplateString(
            "<div class='mlc' data-name='${field_name}'>${items_html}${help_html}${error_html}</div>"
        ),
        model_list_item=TemplateString(
            "<div class='mli' data-idx='${index}'>${body_html}</div>"
        ),
        model_list_help=TemplateString("<span class='ml-help'>${help_text}</span>"),
        model_list_error=TemplateString("<span class='ml-err'>${error_text}</span>"),
        submit_button=TemplateString("<button class='custom-submit'>${submit_label}</button>"),
        # inherit defaults for other templates
    )

    register_form_style(
        FormStyle(
            framework="custom-style",
            templates=custom_templates,
        )
    )

    class _CustomTheme(RendererTheme):
        name = "custom-style"

    class _CustomListRenderer(ModelListRenderer):
        def __init__(self) -> None:
            super().__init__(framework="custom-style")
            self._theme = _CustomTheme()

        def _resolve_theme(self) -> RendererTheme:  # type: ignore[override]
            return self._theme

    renderer = _CustomListRenderer()

    html = renderer.render_model_list(
        field_name="pets",
        label="Pets",
        model_class=_StubModel,
        values=[{"name": "Rex"}],
        help_text="Helpful",
        error="Oops",
        min_items=0,
        max_items=5,
    )

    assert "mlc" in html
    assert "mli" in html
    assert "ml-help" in html
    assert "ml-err" in html

    button_html = renderer._theme.render_submit_button("ignored-class")
    assert "custom-submit" in button_html


def test_tab_layout_uses_form_style_templates() -> None:
    custom_templates = FormStyleTemplates(
        tab_layout=TemplateString("<div class='custom-tab-layout'>${tab_buttons}${tab_panels}</div>"),
        tab_button=TemplateString("<button class='custom-tab-btn'>${title}</button>"),
        tab_panel=TemplateString("<section class='custom-tab-panel'>${content}</section>"),
    )

    register_form_style(FormStyle(framework="tab-test", templates=custom_templates))

    class _TabTheme(RendererTheme):
        name = "tab-test"

    stub_renderer = _StubRenderer(_TabTheme())
    layout = TabLayout([
        {"title": "A", "content": "Alpha"},
        {"title": "B", "content": "Beta"},
    ])

    html = layout.render(renderer=stub_renderer, framework="bootstrap")

    assert "custom-tab-layout" in html
    assert "custom-tab-btn" in html
    assert "custom-tab-panel" in html


def test_accordion_layout_uses_form_style_templates() -> None:
    custom_templates = FormStyleTemplates(
        accordion_layout=TemplateString("<div class='custom-accordion'>${sections}</div>"),
        accordion_section=TemplateString("<article class='custom-acc-section'>${title}${content}</article>"),
    )

    register_form_style(FormStyle(framework="acc-test", templates=custom_templates))

    class _AccTheme(RendererTheme):
        name = "acc-test"

    stub_renderer = _StubRenderer(_AccTheme())
    layout = AccordionLayout([
        {"title": "Q1", "content": "A1"},
        {"title": "Q2", "content": "A2"},
    ])

    html = layout.render(renderer=stub_renderer, framework="bootstrap")

    assert "custom-accordion" in html
    assert "custom-acc-section" in html


def test_material_embedded_theme_includes_error_summary_styles() -> None:
    css = MaterialEmbeddedTheme._build_css()

    assert ".md-error-summary" in css
    assert ".md-error-summary__title" in css
    assert ".md-error-summary__list" in css
