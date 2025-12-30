"""Tests for rendering/layout_engine.py to improve coverage."""


from pydantic_forms.rendering.layout_engine import (
    HorizontalLayout,
    VerticalLayout,
    TabLayout,
    LayoutEngine,
)
from pydantic_forms.rendering.context import RenderContext
from pydantic_forms.enhanced_renderer import EnhancedFormRenderer


class TestHorizontalLayout:
    """Test HorizontalLayout class."""

    def test_horizontal_layout_basic(self):
        """Test basic horizontal layout."""
        layout = HorizontalLayout(content=["Item 1", "Item 2"])

        html = layout.render()

        assert "horizontal-layout" in html
        assert "flex-direction: row" in html
        assert "Item 1" in html
        assert "Item 2" in html

    def test_horizontal_layout_with_gap(self):
        """Test horizontal layout with custom gap."""
        layout = HorizontalLayout(content=["A", "B"], gap="2rem")

        html = layout.render()

        assert "gap: 2rem" in html

    def test_horizontal_layout_with_alignment(self):
        """Test horizontal layout with custom alignment."""
        layout = HorizontalLayout(
            content=["X"],
            align_items="center",
            justify_content="space-between"
        )

        html = layout.render()

        assert "align-items: center" in html
        assert "justify-content: space-between" in html

    def test_horizontal_layout_none_content(self):
        """Test horizontal layout with None content."""
        layout = HorizontalLayout(content=None)

        html = layout.render()

        assert "horizontal-layout" in html


class TestVerticalLayout:
    """Test VerticalLayout class."""

    def test_vertical_layout_basic(self):
        """Test basic vertical layout."""
        layout = VerticalLayout(content=["Item 1", "Item 2"])

        html = layout.render()

        assert "vertical-layout" in html
        assert "flex-direction: column" in html
        assert "Item 1" in html
        assert "Item 2" in html

    def test_vertical_layout_with_gap(self):
        """Test vertical layout with custom gap."""
        layout = VerticalLayout(content=["A", "B"], gap="0.5rem")

        html = layout.render()

        assert "gap: 0.5rem" in html

    def test_vertical_layout_with_alignment(self):
        """Test vertical layout with custom align_items."""
        layout = VerticalLayout(content=["X"], align_items="flex-start")

        html = layout.render()

        assert "align-items: flex-start" in html


class TestTabLayout:
    """Test TabLayout class."""

    def test_tab_layout_basic(self):
        """Test basic tab layout."""
        tabs = [
            {"title": "Tab 1", "content": "<p>Content 1</p>"},
            {"title": "Tab 2", "content": "<p>Content 2</p>"},
        ]

        layout = TabLayout(tabs=tabs)

        html = layout.render(framework='bootstrap')

        assert "Tab 1" in html
        assert "Tab 2" in html

    def test_tab_layout_with_renderer(self):
        """Test tab layout with renderer."""
        tabs = [{"title": "Info", "content": "<div>Info content</div>"}]

        renderer = EnhancedFormRenderer(framework='bootstrap')
        layout = TabLayout(tabs=tabs)

        html = layout.render(framework='bootstrap', renderer=renderer)

        assert "Info" in html
        assert "Info content" in html


class TestLayoutEngine:
    """Test LayoutEngine class."""

    def test_layout_engine_init(self):
        """Test LayoutEngine initialization."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        engine = LayoutEngine(renderer)

        assert engine._renderer == renderer

    def test_render_layout_fields_as_tabs_empty(self):
        """Test rendering layout fields as tabs with empty list."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        engine = LayoutEngine(renderer)
        context = RenderContext(form_data={}, schema_defs={})

        result = engine.render_layout_fields_as_tabs(
            layout_fields=[],
            data={},
            errors={},
            required_fields=[],
            context=context
        )

        assert result == []

    def test_group_fields_into_tabs(self):
        """Test grouping fields into tabs."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        engine = LayoutEngine(renderer)

        fields = [
            ('name', {'ui': {'tab': 'Personal'}}),
            ('email', {'ui': {'tab': 'Personal'}}),
            ('company', {'ui': {'tab': 'Professional'}}),
        ]

        tabs = engine._group_fields_into_tabs(fields)

        assert len(tabs) >= 1  # Should group by tab
        # tabs is a list of (tab_name, fields) tuples
        for tab_name, tab_fields in tabs:
            assert isinstance(tab_name, str)
            assert isinstance(tab_fields, list)
