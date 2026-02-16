"""Targeted branch coverage tests for rendering/layout_engine.py."""

from types import SimpleNamespace

import pytest

from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.layout_base import BaseLayout
from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.layout_engine import (
    LayoutEngine,
    _extract_existing_field_data,
    _extract_fallback_mapped_data,
    _extract_layout_nested_data,
    _safe_layout_tabs,
    _tab_payload_from_main_data,
    get_nested_form_data,
)


@pytest.fixture(autouse=True)
def _reset_layout_renderers():
    yield
    LayoutEngine.reset_layout_renderers()


def _context(form_data=None):
    return RenderContext(form_data=form_data or {}, schema_defs={})


def test_render_tabbed_layout_and_side_by_side_layout():
    renderer = EnhancedFormRenderer(framework="bootstrap")
    engine = LayoutEngine(renderer)
    context = _context({"name": "A", "email": "a@example.com", "city": "Boston"})

    fields = [
        ("name", {"type": "string", "title": "Name"}),
        ("email", {"type": "string", "title": "Email"}),
        ("city", {"type": "string", "title": "City"}),
    ]

    tabbed_html_parts = engine.render_tabbed_layout(
        fields=fields,
        data=context.form_data,
        errors={},
        required_fields=["name"],
        context=context,
    )
    side_by_side_parts = engine.render_side_by_side_layout(
        fields=fields,
        data=context.form_data,
        errors={},
        required_fields=[],
        context=context,
    )

    assert len(tabbed_html_parts) == 1
    assert "tabbed-layout" in tabbed_html_parts[0]
    assert "Name" in tabbed_html_parts[0]
    assert len(side_by_side_parts) == 2
    assert all("side-by-side-row" in part for part in side_by_side_parts)


def test_render_layout_fields_as_tabs_and_layout_field_wrapper():
    renderer = EnhancedFormRenderer(framework="bootstrap")
    engine = LayoutEngine(renderer)
    context = _context({"misc": "value"})

    tabs = engine.render_layout_fields_as_tabs(
        layout_fields=[
            (
                "unknown_layout",
                {
                    "title": "Unknown Layout",
                    "ui": {"help_text": "fallback help"},
                },
            )
        ],
        data=context.form_data,
        errors={},
        required_fields=[],
        context=context,
    )

    direct = engine.render_layout_field(
        "unknown_layout",
        {"title": "Unknown Layout"},
        None,
        None,
        {"help_text": "wrapper help"},
        context,
    )

    assert len(tabs) == 1
    assert "layout-tabbed-section" in tabs[0]
    assert "Unknown layout field type" in tabs[0]
    assert "wrapper help" in direct


def test_render_layout_field_content_fallback_success_error_and_unknown(monkeypatch):
    renderer = EnhancedFormRenderer(framework="bootstrap")
    engine = LayoutEngine(renderer)
    context = _context({"first_name": "Ada", "last_name": "Lovelace"})

    monkeypatch.setattr(
        EnhancedFormRenderer,
        "render_form_fields_only",
        lambda self, *_args, **_kwargs: "<div>nested-content-ok</div>",
    )
    success = engine.render_layout_field_content_fallback(
        "vertical_tab",
        {},
        {"help_text": "vertical help"},
        context,
    )

    def _raise_render(*_args, **_kwargs):
        raise RuntimeError("fallback boom")

    monkeypatch.setattr(EnhancedFormRenderer, "render_form_fields_only", _raise_render)
    failed = engine.render_layout_field_content_fallback(
        "vertical_tab",
        {},
        {"help_text": "vertical help"},
        context,
    )

    unknown = engine.render_layout_field_content_fallback(
        "unknown_layout",
        {},
        {"help_text": "unknown help"},
        context,
    )

    assert "nested-content-ok" in success
    assert "Could not render: fallback boom" in failed
    assert "Unknown layout field type" in unknown
    assert "unknown help" in unknown


def test_render_layout_field_fallback_success_error_and_unknown(monkeypatch):
    renderer = EnhancedFormRenderer(framework="bootstrap")
    engine = LayoutEngine(renderer)
    context = _context({"first_name": "Grace"})

    monkeypatch.setattr(renderer, "render_form_fields_only", lambda *_args, **_kwargs: "<div>ok</div>")
    success = engine.render_layout_field_fallback(
        "vertical_tab",
        {},
        {"help_text": "vertical help"},
        context,
    )

    monkeypatch.setattr(
        renderer,
        "render_form_fields_only",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("render exploded")),
    )
    failed = engine.render_layout_field_fallback(
        "vertical_tab",
        {},
        {"help_text": "help <b>unsafe</b>"},
        context,
    )

    unknown = engine.render_layout_field_fallback(
        "no_mapping",
        {},
        {"help_text": "plain unknown"},
        context,
    )

    assert "<div>ok</div>" in success
    assert "Layout demonstration: PersonalInfoForm" in failed
    assert "render exploded" in failed
    assert "help &lt;b&gt;unsafe&lt;/b&gt;" in failed
    assert "Unknown layout field type" in unknown


def test_build_layout_body_error_message_via_custom_handler():
    renderer = EnhancedFormRenderer(framework="bootstrap")
    engine = LayoutEngine(renderer)

    def broken_handler(*_args, **_kwargs):
        raise RuntimeError("custom handler failed")

    LayoutEngine.register_layout_renderer("broken_layout", broken_handler)
    output = engine.render_layout_field(
        "layout_sample",
        {"title": "Layout Sample"},
        None,
        None,
        {"layout_handler": "broken_layout", "help_text": "show me"},
        _context(),
    )

    assert "Error rendering layout field \"Layout Sample\": custom handler failed" in output
    assert "show me" in output


def test_render_layout_card_theme_short_circuit_and_template_fallbacks():
    renderer = EnhancedFormRenderer(framework="bootstrap")
    engine = LayoutEngine(renderer)

    class ThemeShortCircuit:
        form_style = None

        def render_layout_section(self, *_args, **_kwargs):
            return "<section>from-theme</section>"

    renderer._theme = ThemeShortCircuit()
    themed = engine._render_layout_card("T", "<p>B</p>", "H")

    class ThemeWithEmptyTemplates:
        form_style = SimpleNamespace(templates=SimpleNamespace(layout_section=None, layout_help=None))

        def render_layout_section(self, *_args, **_kwargs):
            return ""

    renderer._theme = ThemeWithEmptyTemplates()
    defaulted = engine._render_layout_card("Title", "<p>Body</p>", "help <script>x</script>")

    assert themed == "<section>from-theme</section>"
    assert "Title" in defaulted
    assert "help &lt;script&gt;x&lt;/script&gt;" in defaulted
    assert "<p>Body</p>" in defaulted


def test_helper_extractors_cover_success_and_exception_paths():
    class GoodTabLayout:
        @staticmethod
        def _get_forms():
            class FormA:
                model_fields = {"alpha": object(), "beta": object()}

            return [FormA]

    class BrokenTabLayout:
        @staticmethod
        def _get_forms():
            raise RuntimeError("broken forms")

    class LayoutWithTabs(BaseLayout):
        @staticmethod
        def _get_layouts():
            return [("profile", GoodTabLayout()), ("broken", BrokenTabLayout())]

    class LayoutWithBrokenTabs(BaseLayout):
        @staticmethod
        def _get_layouts():
            raise RuntimeError("broken tabs")

    assert _extract_existing_field_data("profile", {"profile": {"x": 1}}) == {"x": 1}
    assert _extract_existing_field_data("profile", {"profile": "not a dict"}) is None

    assert _safe_layout_tabs(object()) == []
    assert _safe_layout_tabs(LayoutWithBrokenTabs(content="")) == []

    main_data = {
        "profile": {"pre": "nested"},
        "alpha": 1,
        "beta": 2,
        "first_name": "Ada",
        "email": "ada@example.com",
    }
    assert _tab_payload_from_main_data(GoodTabLayout(), main_data) == {"alpha": 1, "beta": 2}
    assert _tab_payload_from_main_data(BrokenTabLayout(), main_data) == {}
    assert _tab_payload_from_main_data(object(), main_data) == {}

    nested_from_layout = _extract_layout_nested_data(LayoutWithTabs(content=""), main_data)
    assert nested_from_layout["profile"] == {"pre": "nested"}
    assert "broken" not in nested_from_layout

    fallback = _extract_fallback_mapped_data("vertical_tab", main_data)
    assert fallback == {"first_name": "Ada", "email": "ada@example.com"}

    assert get_nested_form_data("profile", main_data) == {"pre": "nested"}
    assert get_nested_form_data("tabs", {"alpha": 1, "beta": 2}, LayoutWithTabs(content="")) == {
        "profile": {"alpha": 1, "beta": 2}
    }
    assert get_nested_form_data("vertical_tab", main_data, None) == fallback
