"""
Tests for layouts module - form layout and organization components.
"""

from types import SimpleNamespace

from pydantic_forms.layout_base import BaseLayout
from pydantic_forms.rendering.form_style import FormStyle, FormStyleTemplates
from pydantic_forms.rendering.layout_engine import (
    AccordionLayout,
    CardLayout,
    GridLayout,
    HorizontalLayout,
    LayoutEngine,
    Layout,
    LayoutFactory,
    ModalLayout,
    ResponsiveGridLayout,
    TabLayout,
    VerticalLayout,
)
from pydantic_forms.templates import TemplateString


class TestBaseLayout:
    """Test the BaseLayout class."""

    def test_base_layout_creation(self):
        """Test basic BaseLayout creation."""
        layout = BaseLayout("Test content")
        assert layout is not None
        assert hasattr(layout, "render")
        assert layout.content == "Test content"

    def test_base_layout_render(self):
        """Test BaseLayout render method."""
        layout = BaseLayout("Hello World")
        html = layout.render()
        assert isinstance(html, str)
        assert "Hello World" in html

    def test_base_layout_with_attributes(self):
        """Test BaseLayout with attributes."""
        layout = BaseLayout("Content", class_="test-class")
        html = layout.render(style="color: red;")
        assert isinstance(html, str)
        assert len(html) > 0

    def test_base_layout_with_list_content(self):
        """Test BaseLayout with list content."""
        layout = BaseLayout(["Item 1", "Item 2", "Item 3"])
        html = layout.render()
        assert isinstance(html, str)
        assert "Item 1" in html
        assert "Item 2" in html
        assert "Item 3" in html


class TestHorizontalLayout:
    """Test the HorizontalLayout class."""

    def test_horizontal_layout_creation(self):
        """Test basic HorizontalLayout creation."""
        layout = HorizontalLayout("Content here")
        assert layout is not None
        assert hasattr(layout, "render")
        assert layout.content == "Content here"

    def test_horizontal_layout_render(self):
        """Test HorizontalLayout HTML rendering."""
        layout = HorizontalLayout("Test content")
        html = layout.render()
        assert isinstance(html, str)
        assert "horizontal-layout" in html
        assert "flex-direction: row" in html
        assert "Test content" in html

    def test_horizontal_layout_with_gap(self):
        """Test HorizontalLayout with custom gap."""
        layout = HorizontalLayout("Content", gap="2rem")
        html = layout.render()
        assert "gap: 2rem" in html

    def test_horizontal_layout_with_alignment(self):
        """Test HorizontalLayout with custom alignment."""
        layout = HorizontalLayout("Content", align_items="center", justify_content="space-between")
        html = layout.render()
        assert "align-items: center" in html
        assert "justify-content: space-between" in html

    def test_horizontal_layout_multiple_items(self):
        """Test HorizontalLayout with multiple content items."""
        layout = HorizontalLayout(["Item 1", "Item 2", "Item 3"])
        html = layout.render()
        assert "Item 1" in html
        assert "Item 2" in html
        assert "Item 3" in html


class TestVerticalLayout:
    """Test the VerticalLayout class."""

    def test_vertical_layout_creation(self):
        """Test basic VerticalLayout creation."""
        layout = VerticalLayout("Content here")
        assert layout is not None
        assert hasattr(layout, "render")

    def test_vertical_layout_render(self):
        """Test VerticalLayout HTML rendering."""
        layout = VerticalLayout("Test content")
        html = layout.render()
        assert isinstance(html, str)
        assert "vertical-layout" in html
        assert "flex-direction: column" in html
        assert "Test content" in html

    def test_vertical_layout_with_gap(self):
        """Test VerticalLayout with custom gap."""
        layout = VerticalLayout("Content", gap="1.5rem")
        html = layout.render()
        assert "gap: 1.5rem" in html

    def test_vertical_layout_with_alignment(self):
        """Test VerticalLayout with custom alignment."""
        layout = VerticalLayout("Content", align_items="center")
        html = layout.render()
        assert "align-items: center" in html

    def test_vertical_layout_multiple_items(self):
        """Test VerticalLayout with multiple content items."""
        layout = VerticalLayout(["<div>Item 1</div>", "<div>Item 2</div>", "<div>Item 3</div>"])
        html = layout.render()
        assert "Item 1" in html
        assert "Item 2" in html
        assert "Item 3" in html


class TestGridLayout:
    """Test the GridLayout class."""

    def test_grid_layout_creation(self):
        """Test basic GridLayout creation."""
        layout = GridLayout("Grid content")
        assert layout is not None
        assert hasattr(layout, "render")

    def test_grid_layout_render(self):
        """Test GridLayout HTML rendering."""
        layout = GridLayout("Test content")
        html = layout.render()
        assert isinstance(html, str)
        assert "grid-layout" in html
        assert "display: grid" in html
        assert "Test content" in html

    def test_grid_layout_with_columns(self):
        """Test GridLayout with custom columns."""
        layout = GridLayout("Content", columns="1fr 2fr 1fr")
        html = layout.render()
        assert "grid-template-columns: 1fr 2fr 1fr" in html

    def test_grid_layout_with_rows(self):
        """Test GridLayout with custom rows."""
        layout = GridLayout("Content", columns="1fr 1fr", rows="auto auto", gap="2rem")
        html = layout.render()
        assert "grid-template-rows: auto auto" in html
        assert "gap: 2rem" in html

    def test_grid_layout_multiple_items(self):
        """Test GridLayout with multiple grid items."""
        items = ["<div>Item 1</div>", "<div>Item 2</div>", "<div>Item 3</div>", "<div>Item 4</div>"]
        layout = GridLayout(items, columns="1fr 1fr")
        html = layout.render()

        for item in ["Item 1", "Item 2", "Item 3", "Item 4"]:
            assert item in html


class TestResponsiveGridLayout:
    """Test the ResponsiveGridLayout class."""

    def test_responsive_grid_creation(self):
        """Test basic ResponsiveGridLayout creation."""
        layout = ResponsiveGridLayout("Responsive content")
        assert layout is not None
        assert hasattr(layout, "render")

    def test_responsive_grid_render(self):
        """Test ResponsiveGridLayout HTML rendering."""
        layout = ResponsiveGridLayout("Test content")
        html = layout.render()
        assert isinstance(html, str)
        assert "grid-layout" in html
        assert "repeat(auto-fit, minmax" in html
        assert "Test content" in html

    def test_responsive_grid_with_min_width(self):
        """Test ResponsiveGridLayout with custom minimum width."""
        layout = ResponsiveGridLayout("Content", min_column_width="250px")
        html = layout.render()
        assert "minmax(250px" in html

    def test_responsive_grid_multiple_items(self):
        """Test ResponsiveGridLayout with multiple items."""
        items = [f"<div>Card {i}</div>" for i in range(1, 7)]
        layout = ResponsiveGridLayout(items, min_column_width="200px", gap="1rem")
        html = layout.render()

        for i in range(1, 7):
            assert f"Card {i}" in html
        assert "gap: 1rem" in html


class TestTabLayout:
    """Test the TabLayout class."""

    def test_tab_layout_creation(self):
        """Test basic TabLayout creation."""
        tabs = [
            {"title": "Tab 1", "content": "Content 1"},
            {"title": "Tab 2", "content": "Content 2"},
        ]
        layout = TabLayout(tabs)
        assert layout is not None
        assert hasattr(layout, "render")
        assert layout.tabs == tabs

    def test_tab_layout_render(self):
        """Test TabLayout HTML rendering."""
        tabs = [
            {"title": "Home", "content": "<p>Welcome home!</p>"},
            {"title": "About", "content": "<p>About us</p>"},
            {"title": "Contact", "content": "<p>Contact info</p>"},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        assert isinstance(html, str)
        assert "tab-layout" in html
        assert "tab-navigation" in html
        assert "tab-content" in html

        # Check tab titles
        assert "Home" in html
        assert "About" in html
        assert "Contact" in html

        # Check tab content
        assert "Welcome home!" in html
        assert "About us" in html
        assert "Contact info" in html

    def test_tab_layout_with_attributes(self):
        """Test TabLayout with custom attributes."""
        tabs = [{"title": "Test", "content": "Test content"}]
        layout = TabLayout(tabs, class_="custom-tabs")
        html = layout.render(style="margin: 1rem;")

        assert "custom-tabs" in html
        assert "margin: 1rem" in html

    def test_tab_layout_javascript_functionality(self):
        """Test TabLayout includes JavaScript functionality."""
        tabs = [
            {"title": "Tab 1", "content": "Content 1"},
            {"title": "Tab 2", "content": "Content 2"},
        ]
        layout = TabLayout(tabs)
        html = layout.render()

        assert "switchTab" in html
        assert "onclick=" in html
        assert "role=" in html  # Accessibility
        assert "aria-" in html  # Accessibility


class TestAccordionLayout:
    """Test the AccordionLayout class."""

    def test_accordion_layout_creation(self):
        """Test basic AccordionLayout creation."""
        sections = [
            {"title": "Section 1", "content": "Content 1"},
            {"title": "Section 2", "content": "Content 2"},
        ]
        layout = AccordionLayout(sections)
        assert layout is not None
        assert hasattr(layout, "render")
        assert layout.sections == sections

    def test_accordion_layout_render(self):
        """Test AccordionLayout HTML rendering."""
        sections = [
            {"title": "FAQ 1", "content": "<p>Answer 1</p>"},
            {"title": "FAQ 2", "content": "<p>Answer 2</p>"},
            {"title": "FAQ 3", "content": "<p>Answer 3</p>"},
        ]
        layout = AccordionLayout(sections)
        html = layout.render()

        assert isinstance(html, str)
        assert "accordion-layout" in html
        assert "accordion-section" in html

        # Check section titles
        assert "FAQ 1" in html
        assert "FAQ 2" in html
        assert "FAQ 3" in html

        # Check section content
        assert "Answer 1" in html
        assert "Answer 2" in html
        assert "Answer 3" in html

    def test_accordion_layout_expanded_sections(self):
        """Test AccordionLayout with expanded sections."""
        sections = [
            {"title": "Section 1", "content": "Content 1", "expanded": True},
            {"title": "Section 2", "content": "Content 2", "expanded": False},
        ]
        layout = AccordionLayout(sections)
        html = layout.render()

        assert 'aria-expanded="true"' in html
        assert 'aria-expanded="false"' in html

    def test_accordion_layout_javascript_functionality(self):
        """Test AccordionLayout includes JavaScript functionality."""
        sections = [{"title": "Test", "content": "Test content"}]
        layout = AccordionLayout(sections)
        html = layout.render()

        assert "toggleAccordion" in html
        assert "onclick=" in html
        assert "aria-expanded" in html


class TestModalLayout:
    """Test the ModalLayout class."""

    def test_modal_layout_creation(self):
        """Test basic ModalLayout creation."""
        layout = ModalLayout("test-modal", "Test Title", "Test content")
        assert layout is not None
        assert hasattr(layout, "render")
        assert layout.modal_id == "test-modal"
        assert layout.title == "Test Title"
        assert layout.content == "Test content"

    def test_modal_layout_render(self):
        """Test ModalLayout HTML rendering."""
        layout = ModalLayout(
            "my-modal",
            "Confirmation",
            "<p>Are you sure?</p>",
            footer="<button>Cancel</button><button>OK</button>",
        )
        html = layout.render()

        assert isinstance(html, str)
        assert "modal-overlay" in html
        assert "my-modal" in html
        assert "Confirmation" in html
        assert "Are you sure?" in html
        assert "Cancel" in html
        assert "OK" in html

    def test_modal_layout_default_footer(self):
        """Test ModalLayout with default footer."""
        layout = ModalLayout("test-modal", "Test", "Content")
        html = layout.render()

        assert "Close" in html  # Default close button

    def test_modal_layout_javascript_functionality(self):
        """Test ModalLayout includes JavaScript functionality."""
        layout = ModalLayout("test-modal", "Test", "Content")
        html = layout.render()

        assert "openModal" in html
        assert "closeModal" in html
        assert "onclick=" in html


class TestCardLayout:
    """Test the CardLayout class."""

    def test_card_layout_creation(self):
        """Test basic CardLayout creation."""
        layout = CardLayout("Card Title", "Card content here")
        assert layout is not None
        assert hasattr(layout, "render")
        assert layout.title == "Card Title"
        assert layout.content == "Card content here"

    def test_card_layout_render(self):
        """Test CardLayout HTML rendering."""
        layout = CardLayout(
            "User Profile", "<p>User details go here</p>", footer="<button>Edit</button>"
        )
        html = layout.render()

        assert isinstance(html, str)
        assert "card-layout" in html
        assert "card-header" in html
        assert "card-body" in html
        assert "card-footer" in html
        assert "User Profile" in html
        assert "User details go here" in html
        assert "Edit" in html

    def test_card_layout_without_footer(self):
        """Test CardLayout without footer."""
        layout = CardLayout("Simple Card", "Just content")
        html = layout.render()

        assert "card-header" in html
        assert "card-body" in html
        assert "Simple Card" in html
        assert "Just content" in html

    def test_card_layout_with_attributes(self):
        """Test CardLayout with custom attributes."""
        layout = CardLayout("Test Card", "Content", class_="custom-card")
        html = layout.render(style="border: 2px solid red;")

        assert "custom-card" in html
        assert "border: 2px solid red" in html


class TestLayoutFactory:
    """Test the LayoutFactory class."""

    def test_layout_factory_horizontal(self):
        """Test LayoutFactory horizontal method."""
        layout = LayoutFactory.horizontal("Item 1", "Item 2", gap="2rem")
        assert isinstance(layout, HorizontalLayout)

        html = layout.render()
        assert "horizontal-layout" in html
        assert "Item 1" in html
        assert "Item 2" in html
        assert "gap: 2rem" in html

    def test_layout_factory_vertical(self):
        """Test LayoutFactory vertical method."""
        layout = LayoutFactory.vertical("Item 1", "Item 2", gap="1rem")
        assert isinstance(layout, VerticalLayout)

        html = layout.render()
        assert "vertical-layout" in html
        assert "Item 1" in html
        assert "Item 2" in html

    def test_layout_factory_grid(self):
        """Test LayoutFactory grid method."""
        layout = LayoutFactory.grid("Item 1", "Item 2", columns="1fr 2fr")
        assert isinstance(layout, GridLayout)

        html = layout.render()
        assert "grid-layout" in html
        assert "1fr 2fr" in html

    def test_layout_factory_responsive_grid(self):
        """Test LayoutFactory responsive_grid method."""
        layout = LayoutFactory.responsive_grid("Item 1", "Item 2", min_width="250px")
        assert isinstance(layout, ResponsiveGridLayout)

        html = layout.render()
        assert "minmax(250px" in html

    def test_layout_factory_tabs(self):
        """Test LayoutFactory tabs method."""
        tabs = [{"title": "Tab 1", "content": "Content 1"}]
        layout = LayoutFactory.tabs(tabs)
        assert isinstance(layout, TabLayout)

        html = layout.render()
        assert "tab-layout" in html

    def test_layout_factory_accordion(self):
        """Test LayoutFactory accordion method."""
        sections = [{"title": "Section 1", "content": "Content 1"}]
        layout = LayoutFactory.accordion(sections)
        assert isinstance(layout, AccordionLayout)

        html = layout.render()
        assert "accordion-layout" in html

    def test_layout_factory_modal(self):
        """Test LayoutFactory modal method."""
        layout = LayoutFactory.modal("test-modal", "Title", "Content")
        assert isinstance(layout, ModalLayout)

        html = layout.render()
        assert "modal-overlay" in html
        assert "test-modal" in html

    def test_layout_factory_card(self):
        """Test LayoutFactory card method."""
        layout = LayoutFactory.card("Title", "Content")
        assert isinstance(layout, CardLayout)

        html = layout.render()
        assert "card-layout" in html
        assert "Title" in html


class TestLayoutAlias:
    """Test the Layout alias for LayoutFactory."""

    def test_layout_alias_works(self):
        """Test that Layout is an alias for LayoutFactory."""
        assert Layout is LayoutFactory

    def test_layout_alias_horizontal(self):
        """Test Layout.horizontal works."""
        layout = Layout.horizontal("Test content")
        assert isinstance(layout, HorizontalLayout)

        html = layout.render()
        assert "Test content" in html

    def test_layout_alias_card(self):
        """Test Layout.card works."""
        layout = Layout.card("Test Title", "Test content")
        assert isinstance(layout, CardLayout)

        html = layout.render()
        assert "Test Title" in html
        assert "Test content" in html


class TestLayoutIntegration:
    """Test layouts working together and with forms."""

    def test_nested_layouts(self):
        """Test nesting layouts within each other."""
        inner_horizontal = HorizontalLayout(["Left", "Right"])
        inner_html = inner_horizontal.render()

        outer_vertical = VerticalLayout(["Header", inner_html, "Footer"])
        html = outer_vertical.render()

        assert "Header" in html
        assert "Left" in html
        assert "Right" in html
        assert "Footer" in html
        assert "horizontal-layout" in html
        assert "vertical-layout" in html

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
            "User Registration", form_content, footer="<button type='submit'>Submit</button>"
        )
        html = card.render()

        assert "User Registration" in html
        assert "Name:" in html
        assert "Email:" in html
        assert "Submit" in html

    def test_tabs_with_different_layout_content(self):
        """Test TabLayout with different layout types in tabs."""
        horizontal_content = HorizontalLayout(["Col 1", "Col 2"]).render()
        grid_content = GridLayout(
            ["Item 1", "Item 2", "Item 3", "Item 4"], columns="1fr 1fr"
        ).render()

        tabs = [
            {"title": "Horizontal", "content": horizontal_content},
            {"title": "Grid", "content": grid_content},
        ]

        tab_layout = TabLayout(tabs)
        html = tab_layout.render()

        assert "Horizontal" in html
        assert "Grid" in html
        assert "horizontal-layout" in html
        assert "grid-layout" in html


class TestFormStyleLayoutSections:
    """Ensure layout sections honor FormStyle templates."""

    def test_layout_card_uses_custom_form_style_template(self):
        section_template = TemplateString(
            """
<section class="custom-layout" data-title="${title}">
    ${help_html}
    <div class="custom-body">${body_html}</div>
</section>
"""
        )
        help_template = TemplateString(
            """
<aside class="custom-help">${help_text}</aside>
"""
        )

        custom_style = FormStyle(
            framework="custom",
            templates=FormStyleTemplates(
                layout_section=section_template,
                layout_help=help_template,
            ),
        )

        class DummyTheme:
            def __init__(self, style):
                self.form_style = style

            def render_layout_section(self, *_args, **_kwargs):  # pragma: no cover - simple stub
                return ""

        renderer = SimpleNamespace(theme=DummyTheme(custom_style), framework="custom")
        engine = LayoutEngine(renderer)

        html = engine._render_layout_card("Section Title", "<div>Body</div>", "Needs <script>alert(1)</script>")

        assert "custom-layout" in html
        assert "custom-body" in html
        assert "custom-help" in html
        assert "Needs &lt;script&gt;alert(1)&lt;/script&gt;" in html
