"""
Tests for layouts module - form layout and organization components.

Consolidated from:
- test_layouts.py (original base)
- test_layout_engine_coverage.py
- test_layout_templates.py
- test_e2e_layouts_async.py
- test_layout_demo_smoke.py
- test_layout_form_validation.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import examples.fastapi_routes as fastapi_routes
from examples.main import app
from examples.shared_models import LayoutDemonstrationForm
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.layout_base import BaseLayout
from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.form_style import FormStyle, FormStyleTemplates
from pydantic_schemaforms.rendering.layout_engine import (
    AccordionLayout,
    CardLayout,
    GridLayout,
    HorizontalLayout,
    Layout,
    LayoutEngine,
    LayoutFactory,
    ModalLayout,
    ResponsiveGridLayout,
    TabLayout,
    VerticalLayout,
    _extract_existing_field_data,
    _extract_fallback_mapped_data,
    _extract_layout_nested_data,
    _safe_layout_tabs,
    _tab_payload_from_main_data,
    get_nested_form_data,
)
from pydantic_schemaforms.templates import TemplateString
from pydantic_schemaforms.tstring import SafeHTML, html as thtml
from pydantic_schemaforms.validation import validate_form_data


# ===========================================================================
# From test_layouts.py (original base)
# ===========================================================================


class TestBaseLayout:
    """Test the BaseLayout class."""

    def test_base_layout_creation(self):
        """Test basic BaseLayout creation."""
        layout = BaseLayout('Test content')
        assert layout is not None
        assert hasattr(layout, 'render')
        assert layout.content == 'Test content'

    def test_base_layout_render(self):
        """Test BaseLayout render method."""
        layout = BaseLayout('Hello World')
        html = layout.render()
        assert isinstance(html, str)
        assert 'Hello World' in html

    def test_base_layout_with_attributes(self):
        """Test BaseLayout with attributes."""
        layout = BaseLayout('Content', class_='test-class')
        html = layout.render(style='color: red;')
        assert isinstance(html, str)
        assert len(html) > 0

    def test_base_layout_with_list_content(self):
        """Test BaseLayout with list content."""
        layout = BaseLayout(['Item 1', 'Item 2', 'Item 3'])
        html = layout.render()
        assert isinstance(html, str)
        assert 'Item 1' in html
        assert 'Item 2' in html
        assert 'Item 3' in html


class TestHorizontalLayout:
    """Test the HorizontalLayout class (from original test_layouts.py)."""

    def test_horizontal_layout_creation(self):
        """Test basic HorizontalLayout creation."""
        layout = HorizontalLayout('Content here')
        assert layout is not None
        assert hasattr(layout, 'render')
        assert layout.content == 'Content here'

    def test_horizontal_layout_render(self):
        """Test HorizontalLayout HTML rendering."""
        layout = HorizontalLayout('Test content')
        html = layout.render()
        assert isinstance(html, str)
        assert 'horizontal-layout' in html
        assert 'flex-direction: row' in html
        assert 'Test content' in html

    def test_horizontal_layout_with_gap(self):
        """Test HorizontalLayout with custom gap."""
        layout = HorizontalLayout('Content', gap='2rem')
        html = layout.render()
        assert 'gap: 2rem' in html

    def test_horizontal_layout_with_alignment(self):
        """Test HorizontalLayout with custom alignment."""
        layout = HorizontalLayout('Content', align_items='center', justify_content='space-between')
        html = layout.render()
        assert 'align-items: center' in html
        assert 'justify-content: space-between' in html

    def test_horizontal_layout_multiple_items(self):
        """Test HorizontalLayout with multiple content items."""
        layout = HorizontalLayout(['Item 1', 'Item 2', 'Item 3'])
        html = layout.render()
        assert 'Item 1' in html
        assert 'Item 2' in html
        assert 'Item 3' in html


class TestHorizontalLayoutEngine:
    """Test HorizontalLayout class (from test_layout_engine_coverage.py)."""

    def test_horizontal_layout_basic(self):
        """Test basic horizontal layout."""
        layout = HorizontalLayout(content=['Item 1', 'Item 2'])

        html = layout.render()

        assert 'horizontal-layout' in html
        assert 'flex-direction: row' in html
        assert 'Item 1' in html
        assert 'Item 2' in html

    def test_horizontal_layout_with_gap(self):
        """Test horizontal layout with custom gap."""
        layout = HorizontalLayout(content=['A', 'B'], gap='2rem')

        html = layout.render()

        assert 'gap: 2rem' in html

    def test_horizontal_layout_with_alignment(self):
        """Test horizontal layout with custom alignment."""
        layout = HorizontalLayout(
            content=['X'], align_items='center', justify_content='space-between'
        )

        html = layout.render()

        assert 'align-items: center' in html
        assert 'justify-content: space-between' in html

    def test_horizontal_layout_none_content(self):
        """Test horizontal layout with None content."""
        layout = HorizontalLayout(content=None)

        html = layout.render()

        assert 'horizontal-layout' in html


class TestVerticalLayout:
    """Test the VerticalLayout class (from original test_layouts.py)."""

    def test_vertical_layout_creation(self):
        """Test basic VerticalLayout creation."""
        layout = VerticalLayout('Content here')
        assert layout is not None
        assert hasattr(layout, 'render')

    def test_vertical_layout_render(self):
        """Test VerticalLayout HTML rendering."""
        layout = VerticalLayout('Test content')
        html = layout.render()
        assert isinstance(html, str)
        assert 'vertical-layout' in html
        assert 'flex-direction: column' in html
        assert 'Test content' in html

    def test_vertical_layout_with_gap(self):
        """Test VerticalLayout with custom gap."""
        layout = VerticalLayout('Content', gap='1.5rem')
        html = layout.render()
        assert 'gap: 1.5rem' in html

    def test_vertical_layout_with_alignment(self):
        """Test VerticalLayout with custom alignment."""
        layout = VerticalLayout('Content', align_items='center')
        html = layout.render()
        assert 'align-items: center' in html

    def test_vertical_layout_multiple_items(self):
        """Test VerticalLayout with multiple content items."""
        layout = VerticalLayout(['<div>Item 1</div>', '<div>Item 2</div>', '<div>Item 3</div>'])
        html = layout.render()
        assert 'Item 1' in html
        assert 'Item 2' in html
        assert 'Item 3' in html


class TestVerticalLayoutEngine:
    """Test VerticalLayout class (from test_layout_engine_coverage.py)."""

    def test_vertical_layout_basic(self):
        """Test basic vertical layout."""
        layout = VerticalLayout(content=['Item 1', 'Item 2'])

        html = layout.render()

        assert 'vertical-layout' in html
        assert 'flex-direction: column' in html
        assert 'Item 1' in html
        assert 'Item 2' in html

    def test_vertical_layout_with_gap(self):
        """Test vertical layout with custom gap."""
        layout = VerticalLayout(content=['A', 'B'], gap='0.5rem')

        html = layout.render()

        assert 'gap: 0.5rem' in html

    def test_vertical_layout_with_alignment(self):
        """Test vertical layout with custom align_items."""
        layout = VerticalLayout(content=['X'], align_items='flex-start')

        html = layout.render()

        assert 'align-items: flex-start' in html


class TestGridLayout:
    """Test the GridLayout class."""

    def test_grid_layout_creation(self):
        """Test basic GridLayout creation."""
        layout = GridLayout('Grid content')
        assert layout is not None
        assert hasattr(layout, 'render')

    def test_grid_layout_render(self):
        """Test GridLayout HTML rendering."""
        layout = GridLayout('Test content')
        html = layout.render()
        assert isinstance(html, str)
        assert 'grid-layout' in html
        assert 'display: grid' in html
        assert 'Test content' in html

    def test_grid_layout_with_columns(self):
        """Test GridLayout with custom columns."""
        layout = GridLayout('Content', columns='1fr 2fr 1fr')
        html = layout.render()
        assert 'grid-template-columns: 1fr 2fr 1fr' in html

    def test_grid_layout_with_rows(self):
        """Test GridLayout with custom rows."""
        layout = GridLayout('Content', columns='1fr 1fr', rows='auto auto', gap='2rem')
        html = layout.render()
        assert 'grid-template-rows: auto auto' in html
        assert 'gap: 2rem' in html

    def test_grid_layout_multiple_items(self):
        """Test GridLayout with multiple grid items."""
        items = ['<div>Item 1</div>', '<div>Item 2</div>', '<div>Item 3</div>', '<div>Item 4</div>']
        layout = GridLayout(items, columns='1fr 1fr')
        html = layout.render()

        for item in ['Item 1', 'Item 2', 'Item 3', 'Item 4']:
            assert item in html


class TestResponsiveGridLayout:
    """Test the ResponsiveGridLayout class."""

    def test_responsive_grid_creation(self):
        """Test basic ResponsiveGridLayout creation."""
        layout = ResponsiveGridLayout('Responsive content')
        assert layout is not None
        assert hasattr(layout, 'render')

    def test_responsive_grid_render(self):
        """Test ResponsiveGridLayout HTML rendering."""
        layout = ResponsiveGridLayout('Test content')
        html = layout.render()
        assert isinstance(html, str)
        assert 'grid-layout' in html
        assert 'repeat(auto-fit, minmax' in html
        assert 'Test content' in html

    def test_responsive_grid_with_min_width(self):
        """Test ResponsiveGridLayout with custom minimum width."""
        layout = ResponsiveGridLayout('Content', min_column_width='250px')
        html = layout.render()
        assert 'minmax(250px' in html

    def test_responsive_grid_multiple_items(self):
        """Test ResponsiveGridLayout with multiple items."""
        items = [f'<div>Card {i}</div>' for i in range(1, 7)]
        layout = ResponsiveGridLayout(items, min_column_width='200px', gap='1rem')
        html = layout.render()

        for i in range(1, 7):
            assert f'Card {i}' in html
        assert 'gap: 1rem' in html


class TestTabLayout:
    """Test the TabLayout class (merged from test_layouts.py and test_layout_engine_coverage.py)."""

    def test_tab_layout_creation(self):
        """Test basic TabLayout creation."""
        tabs = [
            {'title': 'Tab 1', 'content': 'Content 1'},
            {'title': 'Tab 2', 'content': 'Content 2'},
        ]
        layout = TabLayout(tabs)
        assert layout is not None
        assert hasattr(layout, 'render')
        assert layout.tabs == tabs

    def test_tab_layout_render(self):
        """Test TabLayout HTML rendering."""
        tabs = [
            {'title': 'Home', 'content': '<p>Welcome home!</p>'},
            {'title': 'About', 'content': '<p>About us</p>'},
            {'title': 'Contact', 'content': '<p>Contact info</p>'},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        assert isinstance(html, str)
        assert 'tab-layout' in html
        assert 'tab-navigation' in html
        assert 'tab-content' in html

        # Check tab titles
        assert 'Home' in html
        assert 'About' in html
        assert 'Contact' in html

        # Check tab content
        assert 'Welcome home!' in html
        assert 'About us' in html
        assert 'Contact info' in html

    def test_tab_layout_with_attributes(self):
        """Test TabLayout with custom attributes."""
        tabs = [{'title': 'Test', 'content': 'Test content'}]
        layout = TabLayout(tabs, class_='custom-tabs')
        html = layout.render(style='margin: 1rem;')

        assert 'custom-tabs' in html
        assert 'margin: 1rem' in html

    def test_tab_layout_javascript_functionality(self):
        """Test TabLayout includes JavaScript functionality."""
        tabs = [
            {'title': 'Tab 1', 'content': 'Content 1'},
            {'title': 'Tab 2', 'content': 'Content 2'},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        assert 'switchTab' in html
        assert 'onclick=' in html
        assert 'role=' in html  # Accessibility
        assert 'aria-' in html  # Accessibility

    def test_tab_layout_basic(self):
        """Test basic tab layout."""
        tabs = [
            {'title': 'Tab 1', 'content': '<p>Content 1</p>'},
            {'title': 'Tab 2', 'content': '<p>Content 2</p>'},
        ]

        layout = TabLayout(tabs=tabs)

        html = layout.render(framework='bootstrap')

        assert 'Tab 1' in html
        assert 'Tab 2' in html

    def test_tab_layout_with_renderer(self):
        """Test tab layout with renderer."""
        tabs = [{'title': 'Info', 'content': '<div>Info content</div>'}]

        renderer = EnhancedFormRenderer(framework='bootstrap')
        layout = TabLayout(tabs=tabs)

        html = layout.render(framework='bootstrap', renderer=renderer)

        assert 'Info' in html
        assert 'Info content' in html


class TestAccordionLayout:
    """Test the AccordionLayout class."""

    def test_accordion_layout_creation(self):
        """Test basic AccordionLayout creation."""
        sections = [
            {'title': 'Section 1', 'content': 'Content 1'},
            {'title': 'Section 2', 'content': 'Content 2'},
        ]
        layout = AccordionLayout(sections)
        assert layout is not None
        assert hasattr(layout, 'render')
        assert layout.sections == sections

    def test_accordion_layout_render(self):
        """Test AccordionLayout HTML rendering."""
        sections = [
            {'title': 'FAQ 1', 'content': '<p>Answer 1</p>'},
            {'title': 'FAQ 2', 'content': '<p>Answer 2</p>'},
            {'title': 'FAQ 3', 'content': '<p>Answer 3</p>'},
        ]
        layout = AccordionLayout(sections)
        html = layout.render()

        assert isinstance(html, str)
        assert 'accordion-layout' in html
        assert 'accordion-section' in html

        # Check section titles
        assert 'FAQ 1' in html
        assert 'FAQ 2' in html
        assert 'FAQ 3' in html

        # Check section content
        assert 'Answer 1' in html
        assert 'Answer 2' in html
        assert 'Answer 3' in html

    def test_accordion_layout_expanded_sections(self):
        """Test AccordionLayout with expanded sections."""
        sections = [
            {'title': 'Section 1', 'content': 'Content 1', 'expanded': True},
            {'title': 'Section 2', 'content': 'Content 2', 'expanded': False},
        ]
        layout = AccordionLayout(sections)
        html = layout.render()

        assert 'aria-expanded="true"' in html
        assert 'aria-expanded="false"' in html

    def test_accordion_layout_javascript_functionality(self):
        """Test AccordionLayout includes JavaScript functionality."""
        sections = [{'title': 'Test', 'content': 'Test content'}]
        layout = AccordionLayout(sections)
        html = layout.render()

        assert 'toggleAccordion' in html
        assert 'onclick=' in html
        assert 'aria-expanded' in html


class TestModalLayout:
    """Test the ModalLayout class."""

    def test_modal_layout_creation(self):
        """Test basic ModalLayout creation."""
        layout = ModalLayout('test-modal', 'Test Title', 'Test content')
        assert layout is not None
        assert hasattr(layout, 'render')
        assert layout.modal_id == 'test-modal'
        assert layout.title == 'Test Title'
        assert layout.content == 'Test content'

    def test_modal_layout_render(self):
        """Test ModalLayout HTML rendering."""
        layout = ModalLayout(
            'my-modal',
            'Confirmation',
            '<p>Are you sure?</p>',
            footer='<button>Cancel</button><button>OK</button>',
        )
        html = layout.render()

        assert isinstance(html, str)
        assert 'modal-overlay' in html
        assert 'my-modal' in html
        assert 'Confirmation' in html
        assert 'Are you sure?' in html
        assert 'Cancel' in html
        assert 'OK' in html

    def test_modal_layout_default_footer(self):
        """Test ModalLayout with default footer."""
        layout = ModalLayout('test-modal', 'Test', 'Content')
        html = layout.render()

        assert 'Close' in html  # Default close button

    def test_modal_layout_javascript_functionality(self):
        """Test ModalLayout includes JavaScript functionality."""
        layout = ModalLayout('test-modal', 'Test', 'Content')
        html = layout.render()

        assert 'openModal' in html
        assert 'closeModal' in html
        assert 'onclick=' in html


class TestCardLayout:
    """Test the CardLayout class."""

    def test_card_layout_creation(self):
        """Test basic CardLayout creation."""
        layout = CardLayout('Card Title', 'Card content here')
        assert layout is not None
        assert hasattr(layout, 'render')
        assert layout.title == 'Card Title'
        assert layout.content == 'Card content here'

    def test_card_layout_render(self):
        """Test CardLayout HTML rendering."""
        layout = CardLayout(
            'User Profile', '<p>User details go here</p>', footer='<button>Edit</button>'
        )
        html = layout.render()

        assert isinstance(html, str)
        assert 'card-layout' in html
        assert 'card-header' in html
        assert 'card-body' in html
        assert 'card-footer' in html
        assert 'User Profile' in html
        assert 'User details go here' in html
        assert 'Edit' in html

    def test_card_layout_without_footer(self):
        """Test CardLayout without footer."""
        layout = CardLayout('Simple Card', 'Just content')
        html = layout.render()

        assert 'card-header' in html
        assert 'card-body' in html
        assert 'Simple Card' in html
        assert 'Just content' in html

    def test_card_layout_with_attributes(self):
        """Test CardLayout with custom attributes."""
        layout = CardLayout('Test Card', 'Content', class_='custom-card')
        html = layout.render(style='border: 2px solid red;')

        assert 'custom-card' in html
        assert 'border: 2px solid red' in html


class TestLayoutFactory:
    """Test the LayoutFactory class."""

    def test_layout_factory_horizontal(self):
        """Test LayoutFactory horizontal method."""
        layout = LayoutFactory.create_horizontal('Item 1', 'Item 2', gap='2rem')
        assert isinstance(layout, HorizontalLayout)

        html = layout.render()
        assert 'horizontal-layout' in html
        assert 'Item 1' in html
        assert 'Item 2' in html
        assert 'gap: 2rem' in html

    def test_layout_factory_vertical(self):
        """Test LayoutFactory vertical method."""
        layout = LayoutFactory.create_vertical('Item 1', 'Item 2', gap='1rem')
        assert isinstance(layout, VerticalLayout)

        html = layout.render()
        assert 'vertical-layout' in html
        assert 'Item 1' in html
        assert 'Item 2' in html

    def test_layout_factory_grid(self):
        """Test LayoutFactory grid method."""
        layout = LayoutFactory.create_grid('Item 1', 'Item 2', columns='1fr 2fr')
        assert isinstance(layout, GridLayout)

        html = layout.render()
        assert 'grid-layout' in html
        assert '1fr 2fr' in html

    def test_layout_factory_responsive_grid(self):
        """Test LayoutFactory responsive_grid method."""
        layout = LayoutFactory.responsive_grid('Item 1', 'Item 2', min_width='250px')
        assert isinstance(layout, ResponsiveGridLayout)

        html = layout.render()
        assert 'minmax(250px' in html

    def test_layout_factory_tabs(self):
        """Test LayoutFactory tabs method."""
        tabs = [{'title': 'Tab 1', 'content': 'Content 1'}]
        layout = LayoutFactory.create_tabs(tabs)
        assert isinstance(layout, TabLayout)

        html = layout.render()
        assert 'tab-layout' in html

    def test_layout_factory_accordion(self):
        """Test LayoutFactory accordion method."""
        sections = [{'title': 'Section 1', 'content': 'Content 1'}]
        layout = LayoutFactory.create_accordion(sections)
        assert isinstance(layout, AccordionLayout)

        html = layout.render()
        assert 'accordion-layout' in html

    def test_layout_factory_modal(self):
        """Test LayoutFactory modal method."""
        layout = LayoutFactory.create_modal('test-modal', 'Title', 'Content')
        assert isinstance(layout, ModalLayout)

        html = layout.render()
        assert 'modal-overlay' in html
        assert 'test-modal' in html

    def test_layout_factory_card(self):
        """Test LayoutFactory card method."""
        layout = LayoutFactory.create_card('Title', 'Content')
        assert isinstance(layout, CardLayout)

        html = layout.render()
        assert 'card-layout' in html
        assert 'Title' in html


class TestLayoutAlias:
    """Test the Layout alias for LayoutFactory."""

    def test_layout_alias_works(self):
        """Test that Layout is an alias for LayoutFactory."""
        assert Layout is LayoutFactory

    def test_layout_alias_horizontal(self):
        """Test Layout.create_horizontal works."""
        layout = Layout.create_horizontal('Test content')
        assert isinstance(layout, HorizontalLayout)

        html = layout.render()
        assert 'Test content' in html

    def test_layout_alias_card(self):
        """Test Layout.create_card works."""
        layout = Layout.create_card('Test Title', 'Test content')
        assert isinstance(layout, CardLayout)

        html = layout.render()
        assert 'Test Title' in html
        assert 'Test content' in html


class TestLayoutIntegration:
    """Test layouts working together and with forms."""

    def test_nested_layouts(self):
        """Test nesting layouts within each other."""
        inner_horizontal = HorizontalLayout(['Left', 'Right'])
        inner_html = inner_horizontal.render()

        outer_vertical = VerticalLayout(['Header', inner_html, 'Footer'])
        html = outer_vertical.render()

        assert 'Header' in html
        assert 'Left' in html
        assert 'Right' in html
        assert 'Footer' in html
        assert 'horizontal-layout' in html
        assert 'vertical-layout' in html

    def test_card_with_form_content(self):
        """Test CardLayout with form-like content."""
        form_content = """
        <div class="form-group">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name">
        </div>
        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email">
        </div>
        """

        card = CardLayout(
            'User Registration', form_content, footer="<button type='submit'>Submit</button>"
        )
        html = card.render()

        assert 'User Registration' in html
        assert 'Name:' in html
        assert 'Email:' in html
        assert 'Submit' in html

    def test_tabs_with_different_layout_content(self):
        """Test TabLayout with different layout types in tabs."""
        horizontal_content = HorizontalLayout(['Col 1', 'Col 2']).render()
        grid_content = GridLayout(
            ['Item 1', 'Item 2', 'Item 3', 'Item 4'], columns='1fr 1fr'
        ).render()

        tabs = [
            {'title': 'Horizontal', 'content': horizontal_content},
            {'title': 'Grid', 'content': grid_content},
        ]

        tab_layout = TabLayout(tabs)
        html = tab_layout.render()

        assert 'Horizontal' in html
        assert 'Grid' in html
        assert 'horizontal-layout' in html
        assert 'grid-layout' in html


class TestFormStyleLayoutSections:
    """Ensure layout sections honor FormStyle templates."""

    def test_layout_card_uses_custom_form_style_template(self):
        def _section(*, title: str = '', help_html: str = '', body_html: str = '', **_):
            return thtml(
                t'<section class="custom-layout" data-title="{title}">{SafeHTML(help_html)}<div class="custom-body">{SafeHTML(body_html)}</div></section>'
            )

        def _help(*, help_text: str = '', **_):
            return thtml(t'<aside class="custom-help">{help_text}</aside>')

        section_template = TemplateString(_section)
        help_template = TemplateString(_help)

        custom_style = FormStyle(
            framework='custom',
            templates=FormStyleTemplates(
                layout_section=section_template,
                layout_help=help_template,
            ),
        )

        class DummyTheme:
            def __init__(self, style):
                self.form_style = style

            def render_layout_section(self, *_args, **_kwargs):  # pragma: no cover - simple stub
                return ''

        renderer = SimpleNamespace(theme=DummyTheme(custom_style), framework='custom')
        engine = LayoutEngine(renderer)

        html = engine._render_layout_card(
            'Section Title', '<div>Body</div>', 'Needs <script>alert(1)</script>'
        )

        assert 'custom-layout' in html
        assert 'custom-body' in html
        assert 'custom-help' in html
        assert 'Needs &lt;script&gt;alert(1)&lt;/script&gt;' in html


# ===========================================================================
# From test_layout_engine_coverage.py
# ===========================================================================


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

        result = engine.render_layout_fields_as_tabs(layout_fields=[], data={}, context=context)

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


@pytest.fixture(autouse=True)
def _reset_layout_renderers():
    yield
    LayoutEngine.reset_layout_renderers()


def _context(form_data=None):
    return RenderContext(form_data=form_data or {}, schema_defs={})


def test_render_tabbed_layout_and_side_by_side_layout():
    renderer = EnhancedFormRenderer(framework='bootstrap')
    engine = LayoutEngine(renderer)
    context = _context({'name': 'A', 'email': 'a@example.com', 'city': 'Boston'})

    fields = [
        ('name', {'type': 'string', 'title': 'Name'}),
        ('email', {'type': 'string', 'title': 'Email'}),
        ('city', {'type': 'string', 'title': 'City'}),
    ]

    tabbed_html_parts = engine.render_tabbed_layout(
        fields=fields,
        data=context.form_data,
        errors={},
        required_fields=['name'],
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
    assert 'tabbed-layout' in tabbed_html_parts[0]
    assert 'Name' in tabbed_html_parts[0]
    assert len(side_by_side_parts) == 2
    assert all('side-by-side-row' in part for part in side_by_side_parts)


def test_render_layout_fields_as_tabs_and_layout_field_wrapper():
    renderer = EnhancedFormRenderer(framework='bootstrap')
    engine = LayoutEngine(renderer)
    context = _context({'misc': 'value'})

    tabs = engine.render_layout_fields_as_tabs(
        layout_fields=[
            (
                'unknown_layout',
                {
                    'title': 'Unknown Layout',
                    'ui': {'help_text': 'fallback help'},
                },
            )
        ],
        data=context.form_data,
        context=context,
    )

    direct = engine.render_layout_field(
        'unknown_layout',
        {'title': 'Unknown Layout'},
        None,
        {'help_text': 'wrapper help'},
        context,
    )

    assert len(tabs) == 1
    assert 'layout-tabbed-section' in tabs[0]
    assert 'Unknown layout field type' in tabs[0]
    assert 'wrapper help' in direct


def test_render_layout_field_content_fallback_success_error_and_unknown(monkeypatch):
    renderer = EnhancedFormRenderer(framework='bootstrap')
    engine = LayoutEngine(renderer)
    context = _context({'first_name': 'Ada', 'last_name': 'Lovelace'})

    monkeypatch.setattr(
        EnhancedFormRenderer,
        'render_form_fields_only',
        lambda self, *_args, **_kwargs: '<div>nested-content-ok</div>',
    )
    success = engine.render_layout_field_content_fallback(
        'vertical_tab',
        {'help_text': 'vertical help'},
        context,
    )

    def _raise_render(*_args, **_kwargs):
        raise RuntimeError('fallback boom')

    monkeypatch.setattr(EnhancedFormRenderer, 'render_form_fields_only', _raise_render)
    failed = engine.render_layout_field_content_fallback(
        'vertical_tab',
        {'help_text': 'vertical help'},
        context,
    )

    unknown = engine.render_layout_field_content_fallback(
        'unknown_layout',
        {'help_text': 'unknown help'},
        context,
    )

    assert 'nested-content-ok' in success
    assert 'Could not render: fallback boom' in failed
    assert 'Unknown layout field type' in unknown
    assert 'unknown help' in unknown


def test_render_layout_field_fallback_success_error_and_unknown(monkeypatch):
    renderer = EnhancedFormRenderer(framework='bootstrap')
    engine = LayoutEngine(renderer)
    context = _context({'first_name': 'Grace'})

    monkeypatch.setattr(
        renderer, 'render_form_fields_only', lambda *_args, **_kwargs: '<div>ok</div>'
    )
    success = engine.render_layout_field_fallback(
        'vertical_tab',
        {'help_text': 'vertical help'},
        context,
    )

    monkeypatch.setattr(
        renderer,
        'render_form_fields_only',
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError('render exploded')),
    )
    failed = engine.render_layout_field_fallback(
        'vertical_tab',
        {'help_text': 'help <b>unsafe</b>'},
        context,
    )

    unknown = engine.render_layout_field_fallback(
        'no_mapping',
        {'help_text': 'plain unknown'},
        context,
    )

    assert '<div>ok</div>' in success
    assert 'Layout demonstration: PersonalInfoForm' in failed
    assert 'render exploded' in failed
    assert 'help &lt;b&gt;unsafe&lt;/b&gt;' in failed
    assert 'Unknown layout field type' in unknown


def test_build_layout_body_error_message_via_custom_handler():
    renderer = EnhancedFormRenderer(framework='bootstrap')
    engine = LayoutEngine(renderer)

    def broken_handler(*_args, **_kwargs):
        raise RuntimeError('custom handler failed')

    LayoutEngine.register_layout_renderer('broken_layout', broken_handler)
    output = engine.render_layout_field(
        'layout_sample',
        {'title': 'Layout Sample'},
        None,
        {'layout_handler': 'broken_layout', 'help_text': 'show me'},
        _context(),
    )

    assert 'Error rendering layout field "Layout Sample": custom handler failed' in output
    assert 'show me' in output


def test_render_layout_card_theme_short_circuit_and_template_fallbacks():
    renderer = EnhancedFormRenderer(framework='bootstrap')
    engine = LayoutEngine(renderer)

    class ThemeShortCircuit:
        form_style = None

        def render_layout_section(self, *_args, **_kwargs):
            return '<section>from-theme</section>'

    renderer._theme = ThemeShortCircuit()
    themed = engine._render_layout_card('T', '<p>B</p>', 'H')

    class ThemeWithEmptyTemplates:
        form_style = SimpleNamespace(
            templates=SimpleNamespace(layout_section=None, layout_help=None)
        )

        def render_layout_section(self, *_args, **_kwargs):
            return ''

    renderer._theme = ThemeWithEmptyTemplates()
    defaulted = engine._render_layout_card('Title', '<p>Body</p>', 'help <script>x</script>')

    assert themed == '<section>from-theme</section>'
    assert 'Title' in defaulted
    assert 'help &lt;script&gt;x&lt;/script&gt;' in defaulted
    assert '<p>Body</p>' in defaulted


def test_helper_extractors_cover_success_and_exception_paths():
    class GoodTabLayout:
        @staticmethod
        def _get_forms():
            class FormA:
                model_fields = {'alpha': object(), 'beta': object()}

            return [FormA]

    class BrokenTabLayout:
        @staticmethod
        def _get_forms():
            raise RuntimeError('broken forms')

    class LayoutWithTabs(BaseLayout):
        @staticmethod
        def _get_layouts():
            return [('profile', GoodTabLayout()), ('broken', BrokenTabLayout())]

    class LayoutWithBrokenTabs(BaseLayout):
        @staticmethod
        def _get_layouts():
            raise RuntimeError('broken tabs')

    assert _extract_existing_field_data('profile', {'profile': {'x': 1}}) == {'x': 1}
    assert _extract_existing_field_data('profile', {'profile': 'not a dict'}) is None

    assert _safe_layout_tabs(object()) == []
    assert _safe_layout_tabs(LayoutWithBrokenTabs(content='')) == []

    main_data = {
        'profile': {'pre': 'nested'},
        'alpha': 1,
        'beta': 2,
        'first_name': 'Ada',
        'email': 'ada@example.com',
    }
    assert _tab_payload_from_main_data(GoodTabLayout(), main_data) == {'alpha': 1, 'beta': 2}
    assert _tab_payload_from_main_data(BrokenTabLayout(), main_data) == {}
    assert _tab_payload_from_main_data(object(), main_data) == {}

    nested_from_layout = _extract_layout_nested_data(LayoutWithTabs(content=''), main_data)
    assert nested_from_layout['profile'] == {'pre': 'nested'}
    assert 'broken' not in nested_from_layout

    fallback = _extract_fallback_mapped_data('vertical_tab', main_data)
    assert fallback == {'first_name': 'Ada', 'email': 'ada@example.com'}

    assert get_nested_form_data('profile', main_data) == {'pre': 'nested'}
    assert get_nested_form_data('tabs', {'alpha': 1, 'beta': 2}, LayoutWithTabs(content='')) == {
        'profile': {'alpha': 1, 'beta': 2}
    }
    assert get_nested_form_data('vertical_tab', main_data, None) == fallback


# ===========================================================================
# From test_layout_templates.py
# ===========================================================================


def test_tab_layout_uses_template_markup() -> None:
    layout = TabLayout(
        [
            {'title': 'General', 'content': '<p>One</p>'},
            {'title': 'Advanced', 'content': '<p>Two</p>'},
        ],
        class_='custom-tab',
        style='margin: 1rem',
    )

    html = layout.render()

    assert 'class="tab-layout custom-tab"' in html
    assert 'role="tablist"' in html
    assert html.count('class="tab-button') == 2
    assert html.count('class="tab-panel') == 2


def test_accordion_layout_uses_template_markup() -> None:
    layout = AccordionLayout(
        [
            {'title': 'Section A', 'content': '<p>A</p>', 'expanded': True},
            {'title': 'Section B', 'content': '<p>B</p>', 'expanded': False},
        ],
        class_='custom-accordion',
    )

    html = layout.render()

    assert 'class="accordion-layout custom-accordion"' in html
    assert html.count('class="accordion-section"') == 2
    assert 'aria-expanded="true"' in html
    assert 'aria-expanded="false"' in html


# ===========================================================================
# From test_e2e_layouts_async.py
# ===========================================================================


class TestTabLayoutStructure:
    """Unit tests for TabLayout DOM structure and attributes."""

    def test_tab_buttons_have_aria_attributes(self):
        """Verify tab buttons include accessibility attributes."""
        tabs = [
            {'title': 'Settings', 'content': 'Settings content'},
            {'title': 'Profile', 'content': 'Profile content'},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        # Verify aria-selected and role attributes
        assert 'role="tablist"' in html
        assert 'aria-selected="true"' in html  # First tab active
        assert 'aria-selected="false"' in html  # Second tab inactive

    def test_tab_panels_have_aria_hidden_attribute(self):
        """Verify tab panels include aria-hidden for accessibility."""
        tabs = [
            {'title': 'Tab A', 'content': 'Content A'},
            {'title': 'Tab B', 'content': 'Content B'},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        # First panel visible, second hidden
        assert 'aria-hidden="false"' in html
        assert 'aria-hidden="true"' in html

    def test_tab_content_initial_display_style(self):
        """Verify first tab content is displayed, others hidden."""
        tabs = [
            {'title': 'First', 'content': 'First content'},
            {'title': 'Second', 'content': 'Second content'},
            {'title': 'Third', 'content': 'Third content'},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        # Check display styles in content
        assert 'display: block' in html or 'display:block' in html  # First visible
        assert 'display: none' in html or 'display:none' in html  # Others hidden

    def test_accordion_sections_have_expanded_attributes(self):
        """Verify accordion sections include expanded/collapse state."""
        sections = [
            {'title': 'Expandable 1', 'content': 'Content 1', 'expanded': True},
            {'title': 'Expandable 2', 'content': 'Content 2', 'expanded': False},
        ]
        layout = AccordionLayout(sections)
        html = layout.render()

        # Count expanded attributes
        expanded_count = html.count('aria-expanded="true"')
        collapsed_count = html.count('aria-expanded="false"')

        assert expanded_count >= 1
        assert collapsed_count >= 1

    def test_accordion_section_ids_are_unique(self):
        """Verify each accordion section has unique ID."""
        sections = [{'title': f'Section {i}', 'content': f'Content {i}'} for i in range(5)]
        layout = AccordionLayout(sections)
        html = layout.render()

        # Count unique section IDs
        section_ids = []
        for i in range(5):
            section_id = f'accordion-{i}'
            if section_id in html:
                section_ids.append(section_id)

        assert len(section_ids) == 5


class TestTabLayoutBootstrapMaterial:
    """Unit tests verifying Bootstrap/Material theme-specific rendering."""

    def test_tab_layout_bootstrap_theme(self):
        """Verify TabLayout respects Bootstrap theme."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        tabs = [
            {'title': 'Tab 1', 'content': 'Content 1'},
            {'title': 'Tab 2', 'content': 'Content 2'},
        ]
        layout = TabLayout(tabs)
        html = layout.render(renderer=renderer, framework='bootstrap')

        # Bootstrap-specific elements
        assert 'tab-layout' in html or 'tabbed-layout' in html

    def test_tab_layout_material_theme(self):
        """Verify TabLayout respects Material theme via EnhancedFormRenderer(framework='material')."""
        from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

        renderer = EnhancedFormRenderer(framework='material')
        tabs = [
            {'title': 'Tab 1', 'content': 'Content 1'},
            {'title': 'Tab 2', 'content': 'Content 2'},
        ]
        layout = TabLayout(tabs)
        html = layout.render(renderer=renderer, framework='material')

        # Material theme should also render tabs
        assert 'Tab 1' in html
        assert 'Tab 2' in html


class TestLayoutDemonstrationFormRendering:
    """Integration tests for LayoutDemonstrationForm with all layout types."""

    def test_layout_form_renders_all_tabs(self):
        """Verify layout form renders all tab sections."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        form_data = {
            'vertical_tab': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'birth_date': '1990-01-01',
            },
            'horizontal_tab': {
                'phone': '+1-555-0000',
                'address': '123 Main St',
                'city': 'Springfield',
                'postal_code': '12345',
            },
            'tabbed_tab': {
                'notification_email': True,
                'notification_sms': False,
                'theme': 'light',
                'language': 'en',
            },
            'list_tab': {
                'project_name': 'Demo',
                'tasks': [
                    {
                        'task_name': 'Task 1',
                        'priority': 'high',
                        'due_date': '2024-12-01',
                    }
                ],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url='/submit',
        )

        # All layout field titles should be present
        assert 'Personal Info' in html
        assert 'Contact Info' in html
        assert 'Preferences' in html
        assert 'Task List' in html

    def test_layout_form_includes_nested_field_content(self):
        """Verify nested form content renders in layout fields."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        form_data = {
            'vertical_tab': {
                'first_name': 'Alice',
                'last_name': 'Smith',
                'email': 'alice@example.com',
            },
            'horizontal_tab': {
                'address': '456 Oak Ave',
                'city': 'Metropolis',
            },
            'tabbed_tab': {
                'notification_email': True,
                'theme': 'dark',
            },
            'list_tab': {
                'project_name': 'Project X',
                'tasks': [],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url='/submit',
        )

        # Check that nested field values appear
        assert 'Alice' in html
        assert 'Smith' in html
        assert 'alice@example.com' in html
        assert '456 Oak Ave' in html
        assert 'Metropolis' in html

        # Preferences tab should render nested fields (and not the empty-layout warning)
        assert 'Email Notifications' in html
        assert 'No layouts found in tabbed layout' not in html

    def test_layout_form_renders_model_list_in_task_field(self):
        """Verify model_list field renders correctly within layout."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        form_data = {
            'vertical_tab': {
                'first_name': 'Bob',
                'last_name': 'Builder',
                'email': 'bob@example.com',
            },
            'horizontal_tab': {
                'address': '789 Work St',
                'city': 'Construction City',
            },
            'tabbed_tab': {'theme': 'light'},
            'list_tab': {
                'project_name': 'Build It',
                'tasks': [
                    {
                        'task_name': 'Lay foundation',
                        'priority': 'high',
                        'due_date': '2024-12-05',
                        'completed': False,
                    },
                    {
                        'task_name': 'Frame walls',
                        'priority': 'medium',
                        'due_date': '2024-12-15',
                        'completed': False,
                    },
                ],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url='/submit',
        )

        # Verify model list content in task field
        assert 'Build It' in html  # project_name
        assert 'Lay foundation' in html
        assert 'Frame walls' in html
        assert 'remove-item-btn' in html  # Remove button for list items


class TestTabLayoutIntegration:
    """Integration tests for tab rendering in form contexts."""

    def test_tabbed_form_renders_tabs_and_content(self):
        """Verify tabbed form renders all tab buttons and content."""
        renderer = EnhancedFormRenderer(framework='bootstrap')

        form_data = {
            'vertical_tab': {
                'first_name': 'Tab',
                'last_name': 'Tester',
                'email': 'tabs@example.com',
            },
            'horizontal_tab': {
                'address': 'Tab Street',
                'city': 'Tabville',
            },
            'tabbed_tab': {
                'notification_email': True,
                'notification_sms': True,
                'theme': 'auto',
                'language': 'es',
            },
            'list_tab': {
                'project_name': 'Tab Project',
                'tasks': [
                    {
                        'task_name': 'Tab task',
                        'priority': 'low',
                        'due_date': None,
                    }
                ],
            },
        }

        html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url='/submit',
        )

        # Verify both bootstrap tab structure and content are rendered
        assert 'tab-layout' in html or 'tabbed' in html.lower()


class TestAsyncFormRendering:
    """Tests for async renderer paths."""

    @pytest.mark.asyncio
    async def test_async_render_returns_same_html_as_sync(self):
        """Verify async rendering produces identical output to sync."""
        renderer = EnhancedFormRenderer(framework='bootstrap')
        form_data = {
            'vertical_tab': {
                'first_name': 'Async',
                'last_name': 'Test',
                'email': 'async@example.com',
            },
            'horizontal_tab': {
                'address': '123 Async St',
                'city': 'Asyncville',
            },
            'tabbed_tab': {'theme': 'light'},
            'list_tab': {
                'project_name': 'Async Project',
                'tasks': [
                    {
                        'task_name': 'Async task',
                        'priority': 'high',
                        'due_date': '2024-12-10',
                    }
                ],
            },
        }

        # Render synchronously
        sync_html = renderer.render_form_from_model(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url='/submit',
        )

        # Render asynchronously
        async_html = await renderer.render_form_from_model_async(
            LayoutDemonstrationForm,
            data=form_data,
            submit_url='/submit',
        )

        # Both should produce equivalent content
        assert sync_html == async_html
        assert 'Async' in async_html
        assert 'async@example.com' in async_html

    @pytest.mark.asyncio
    async def test_async_render_with_errors(self):
        """Verify async rendering handles validation errors."""
        renderer = EnhancedFormRenderer(framework='bootstrap')

        # Invalid data: empty tasks list (min_length=1)
        invalid_data = {
            'vertical_tab': {
                'first_name': 'Invalid',
                'last_name': 'User',
                'email': 'invalid@example.com',
            },
            'horizontal_tab': {
                'address': 'Bad St',
                'city': 'Badville',
            },
            'tabbed_tab': {'theme': 'dark'},
            'list_tab': {
                'project_name': 'Bad Project',
                'tasks': [],  # Invalid: min_length=1 required
            },
        }

        # Async render should not raise; let renderer handle errors gracefully
        try:
            html = await renderer.render_form_from_model_async(
                LayoutDemonstrationForm,
                data=invalid_data,
                errors={},
                submit_url='/submit',
            )
            # Rendering completes even with data issues
            assert isinstance(html, str)
        except ValidationError:
            # Validation may occur; that's acceptable
            pass

    @pytest.mark.asyncio
    async def test_multiple_async_renders_concurrent(self):
        """Verify multiple async renders can run concurrently."""
        renderer = EnhancedFormRenderer(framework='bootstrap')

        async def render_form_variant(name: str, theme: str):
            data = {
                'vertical_tab': {
                    'first_name': name,
                    'last_name': 'Concurrent',
                    'email': f'{name}@example.com',
                },
                'horizontal_tab': {
                    'address': 'Concurrent St',
                    'city': 'CityC',
                },
                'tabbed_tab': {'theme': theme},
                'list_tab': {
                    'project_name': f'{name} Project',
                    'tasks': [
                        {
                            'task_name': f'{name} Task',
                            'priority': 'medium',
                            'due_date': '2024-12-20',
                        }
                    ],
                },
            }
            return await renderer.render_form_from_model_async(
                LayoutDemonstrationForm,
                data=data,
                submit_url='/submit',
            )

        # Run 3 async renders concurrently
        results = await asyncio.gather(
            render_form_variant('Alice', 'light'),
            render_form_variant('Bob', 'dark'),
            render_form_variant('Charlie', 'auto'),
        )

        # All should complete without error
        assert len(results) == 3
        assert all(isinstance(html, str) for html in results)
        assert 'Alice' in results[0]
        assert 'Bob' in results[1]
        assert 'Charlie' in results[2]


# ===========================================================================
# From test_layout_demo_smoke.py
# ===========================================================================


def _patch_templates_to_repo_root() -> None:
    """Ensure templates resolve when running tests from repo root."""

    base_dir = Path(fastapi_routes.__file__).resolve().parent
    fastapi_routes.templates = Jinja2Templates(directory=base_dir / 'templates')


def _client() -> TestClient:
    _patch_templates_to_repo_root()
    return TestClient(app)


def test_layout_demo_bootstrap_initial_tab_renders():
    client = _client()
    resp = client.get('/layouts?style=bootstrap')
    assert resp.status_code == 200

    body = resp.text
    # Bootstrap tab pane should render first tab as show active
    assert 'tab-pane fade show active' in body
    # Personal info content should be present immediately
    assert 'Alex' in body  # demo data
    assert 'Personal Info' in body


def test_layout_demo_material_initial_tab_renders():
    client = _client()
    resp = client.get('/layouts?style=material')
    assert resp.status_code == 200

    body = resp.text
    # Material tabs use shared tab-panel with active class and display:block on first
    assert 'tab-panel active' in body or 'tab-panel  active' in body
    # Tab buttons should have generic tab-button class for JS-less toggling
    assert 'tab-button' in body
    assert 'Alex' in body
    assert 'Personal Info' in body


def test_layout_demo_tab_buttons_present():
    client = _client()
    resp = client.get('/layouts?style=bootstrap')
    assert resp.status_code == 200
    body = resp.text
    # Tab buttons should include all four sections
    for label in ['Personal Info', 'Contact Info', 'Preferences', 'Task List']:
        assert label in body


# ===========================================================================
# From test_layout_form_validation.py
# ===========================================================================


def test_layout_form_rejects_blank_first_name():
    data = {
        # Vertical tab (PersonalInfoForm)
        'first_name': '',
        'last_name': 'Johnson',
        'email': 'alex.johnson@example.com',
        # Horizontal tab (ContactInfoForm)
        'address': '456 Demo Street',
        'city': 'San Francisco',
        # Tabbed tab (PreferencesForm)
        'notification_email': True,
        'notification_sms': False,
        'theme': 'dark',
        'language': 'en',
        # List tab (TaskListForm)
        'project_name': 'Demo Project',
        'tasks': [
            {
                'task_name': 'Complete project setup',
                'priority': 'high',
                'due_date': '2024-12-01',
            }
        ],
    }

    result = validate_form_data(LayoutDemonstrationForm, data)
    assert result.is_valid is False
    assert 'first_name' in result.errors


def test_layout_form_rejects_missing_first_name():
    data = {
        # Vertical tab (PersonalInfoForm)
        'last_name': 'Johnson',
        'email': 'alex.johnson@example.com',
        # Horizontal tab (ContactInfoForm)
        'address': '456 Demo Street',
        'city': 'San Francisco',
        # List tab (TaskListForm)
        'project_name': 'Demo Project',
        'tasks': [
            {
                'task_name': 'Write documentation',
                'priority': 'medium',
                'due_date': '2024-12-15',
            }
        ],
    }

    result = validate_form_data(LayoutDemonstrationForm, data)
    assert result.is_valid is False
    assert 'first_name' in result.errors
