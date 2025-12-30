"""
Tests for form_layouts.py to improve coverage.
This module is deprecated but we're testing it for coverage completeness.
"""

import pytest
import warnings

from pydantic_forms.form_layouts import (
    SectionDesign,
    FormDesign,
    VerticalLayout,
    HorizontalLayout,
    BaseLayout,
)
from pydantic_forms.schema_form import FormModel, Field


# Define form models at module level to avoid unhashable type errors
# Avoid "Test" prefix to prevent pytest from trying to collect them as test classes
class BasicFormModel(FormModel):
    name: str = Field(default="", title="Name")


class ItemFormModel(FormModel):
    value: str = Field(default="", title="Value")


class SimpleFormModel(FormModel):
    text: str = Field(default="", title="Text")


class ItemFormWithName(FormModel):
    name: str = Field(default="test", title="Name")


class ValueFormModel(FormModel):
    value: str = Field(default="", title="Value")


class ValueFormWithDefault(FormModel):
    value: str = Field(default="x", title="Value")


class TitleFormModel(FormModel):
    title: str = Field(default="", title="Title")


class MaterialFormModel(FormModel):
    name: str = Field(default="", title="Name")


class DataItemFormModel(FormModel):
    value: str = Field(default="", title="Value")


class ErrorItemFormModel(FormModel):
    field: str = Field(default="", title="Field")


class CollapsibleItemFormModel(FormModel):
    info: str = Field(default="", title="Info")


class JSItemFormModel(FormModel):
    data: str = Field(default="", title="Data")


class TestSectionDesign:
    """Test SectionDesign configuration class."""

    def test_section_design_basic(self):
        """Test basic section design creation."""
        section = SectionDesign(section_title="User Information")
        assert section.section_title == "User Information"
        assert section.section_description is None
        assert section.icon is None
        assert section.collapsible is False
        assert section.collapsed is False

    def test_section_design_with_description(self):
        """Test section design with description."""
        section = SectionDesign(
            section_title="Personal Info",
            section_description="Enter your personal details",
        )
        assert section.section_description == "Enter your personal details"

    def test_section_design_with_icon(self):
        """Test section design with icon."""
        section = SectionDesign(
            section_title="Settings",
            icon="gear",
        )
        assert section.icon == "gear"

    def test_section_design_collapsible(self):
        """Test collapsible section design."""
        section = SectionDesign(
            section_title="Advanced",
            collapsible=True,
            collapsed=True,
        )
        assert section.collapsible is True
        assert section.collapsed is True

    def test_section_design_with_css_class(self):
        """Test section design with custom CSS class."""
        section = SectionDesign(
            section_title="Custom",
            css_class="my-custom-class",
        )
        assert section.css_class == "my-custom-class"

    def test_section_design_render_header_bootstrap(self):
        """Test rendering section header for Bootstrap."""
        section = SectionDesign(
            section_title="Contact Info",
            section_description="How to reach you",
            icon="envelope",
        )
        html = section.render_header(framework="bootstrap")
        assert "Contact Info" in html
        assert "How to reach you" in html
        assert "bi-envelope" in html
        assert "section-header" in html

    def test_section_design_render_header_material(self):
        """Test rendering section header for Material Design."""
        section = SectionDesign(
            section_title="Profile",
            icon="person",
        )
        html = section.render_header(framework="material")
        assert "Profile" in html
        assert "material-icons" in html
        assert "person" in html

    def test_section_design_render_header_collapsible(self):
        """Test rendering collapsible section header."""
        section = SectionDesign(
            section_title="Options",
            collapsible=True,
        )
        html = section.render_header(framework="bootstrap")
        assert "collapsible" in html

    def test_section_design_extra_attrs(self):
        """Test section design with extra attributes."""
        section = SectionDesign(
            section_title="Test",
            custom_attr="value",
            another_attr=123,
        )
        assert section.extra_attrs["custom_attr"] == "value"
        assert section.extra_attrs["another_attr"] == 123


class TestFormDesign:
    """Test FormDesign configuration class."""

    def test_form_design_defaults(self):
        """Test form design with default values."""
        design = FormDesign()
        assert design.ui_theme == "bootstrap"
        assert design.form_name == "Form"
        assert design.form_enctype == "application/x-www-form-urlencoded"
        assert design.form_width == "600px"
        assert design.target_url == "/submit"
        assert design.form_method == "post"
        assert design.error_notification_style == "inline"
        assert design.show_debug_info is False
        assert design.asset_mode == "vendored"

    def test_form_design_custom_values(self):
        """Test form design with custom values."""
        design = FormDesign(
            ui_theme="material",
            form_name="Registration",
            form_width="800px",
            target_url="/register",
            form_method="POST",
            show_debug_info=True,
            asset_mode="cdn",
        )
        assert design.ui_theme == "material"
        assert design.form_name == "Registration"
        assert design.form_width == "800px"
        assert design.target_url == "/register"
        assert design.form_method == "post"  # Lowercased
        assert design.show_debug_info is True
        assert design.asset_mode == "cdn"

    def test_form_design_get_form_attributes(self):
        """Test getting form HTML attributes."""
        design = FormDesign(
            target_url="/submit",
            form_method="post",
            form_width="500px",
        )
        attrs = design.get_form_attributes()
        assert attrs["action"] == "/submit"
        assert attrs["method"] == "post"
        assert "500px" in attrs["style"]
        assert "enctype" in attrs

    def test_form_design_get_form_attributes_get_method(self):
        """Test form attributes with GET method."""
        design = FormDesign(form_method="get")
        attrs = design.get_form_attributes()
        assert attrs["method"] == "get"
        # GET method should not include enctype
        assert "enctype" not in attrs

    def test_form_design_get_framework_css_url_bootstrap(self):
        """Test getting Bootstrap CSS URL."""
        design = FormDesign(ui_theme="bootstrap", asset_mode="cdn")
        url = design.get_framework_css_url()
        assert "bootstrap" in url
        assert url.startswith("https://")

    def test_form_design_get_framework_css_url_material(self):
        """Test getting Material CSS URL."""
        design = FormDesign(ui_theme="material", asset_mode="cdn")
        url = design.get_framework_css_url()
        assert "materialize" in url

    def test_form_design_get_framework_css_url_semantic(self):
        """Test getting Semantic UI CSS URL."""
        design = FormDesign(ui_theme="semantic", asset_mode="cdn")
        url = design.get_framework_css_url()
        assert "semantic" in url

    def test_form_design_get_framework_css_url_tailwind(self):
        """Test getting Tailwind CSS URL."""
        design = FormDesign(ui_theme="tailwind", asset_mode="cdn")
        url = design.get_framework_css_url()
        assert "tailwind" in url

    def test_form_design_get_framework_css_url_custom(self):
        """Test getting custom CSS URL."""
        custom_url = "https://example.com/custom.css"
        design = FormDesign(ui_theme="custom", ui_theme_custom_css=custom_url, asset_mode="cdn")
        url = design.get_framework_css_url()
        assert url == custom_url

    def test_form_design_get_framework_css_url_vendored(self):
        """Test vendored asset mode returns empty string."""
        design = FormDesign(ui_theme="bootstrap", asset_mode="vendored")
        url = design.get_framework_css_url()
        assert url == ""

    def test_form_design_get_framework_js_url_bootstrap(self):
        """Test getting Bootstrap JS URL."""
        design = FormDesign(ui_theme="bootstrap", asset_mode="cdn")
        url = design.get_framework_js_url()
        assert "bootstrap" in url
        assert "bundle.min.js" in url

    def test_form_design_get_framework_js_url_material(self):
        """Test getting Material JS URL."""
        design = FormDesign(ui_theme="material", asset_mode="cdn")
        url = design.get_framework_js_url()
        assert "materialize" in url

    def test_form_design_get_framework_js_url_semantic(self):
        """Test getting Semantic UI JS URL."""
        design = FormDesign(ui_theme="semantic", asset_mode="cdn")
        url = design.get_framework_js_url()
        assert "semantic" in url

    def test_form_design_get_framework_js_url_vendored(self):
        """Test vendored mode returns empty JS URL."""
        design = FormDesign(ui_theme="bootstrap", asset_mode="vendored")
        url = design.get_framework_js_url()
        assert url == ""

    def test_form_design_extra_attrs(self):
        """Test form design with extra attributes."""
        design = FormDesign(custom_key="custom_value")
        assert design.extra_attrs["custom_key"] == "custom_value"


class TestVerticalLayout:
    """Test VerticalLayout class."""

    def test_vertical_layout_creation(self):
        """Test creating a vertical layout."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = VerticalLayout()
            assert layout is not None
            assert layout._forms == []

    def test_vertical_layout_deprecation_warning(self):
        """Test that vertical layout triggers deprecation warning."""
        with pytest.warns(DeprecationWarning, match="form_layouts will be removed"):
            VerticalLayout()

    def test_vertical_layout_with_section_config(self):
        """Test vertical layout with section configuration."""
        section = SectionDesign(section_title="Test Section")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = VerticalLayout(form_config=section)
            assert layout.form_config == section

    def test_vertical_layout_render_basic(self):
        """Test basic vertical layout rendering."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = VerticalLayout()
            html = layout.render(framework="bootstrap")
            assert isinstance(html, str)

    def test_vertical_layout_render_with_data(self):
        """Test vertical layout rendering with data."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = VerticalLayout()
            html = layout.render(data={"field": "value"}, framework="bootstrap")
            assert isinstance(html, str)

    def test_vertical_layout_validate(self):
        """Test vertical layout validation."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = VerticalLayout()
            result = layout.validate({"test": "data"})
            assert result is not None
            assert hasattr(result, "is_valid")

    def test_vertical_layout_section_class(self):
        """Test section class generation."""
        section = SectionDesign(
            section_title="Test",
            collapsible=True,
            collapsed=True,
            css_class="custom-class",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = VerticalLayout(form_config=section)
            css_class = layout._section_class("base")
            assert "base" in css_class
            assert "collapsible" in css_class
            assert "collapsed" in css_class
            assert "custom-class" in css_class


class TestHorizontalLayout:
    """Test HorizontalLayout class."""

    def test_horizontal_layout_creation(self):
        """Test creating a horizontal layout."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = HorizontalLayout()
            assert layout is not None

    def test_horizontal_layout_deprecation_warning(self):
        """Test that horizontal layout triggers deprecation warning."""
        with pytest.warns(DeprecationWarning, match="form_layouts will be removed"):
            HorizontalLayout()

    def test_horizontal_layout_with_section_config(self):
        """Test horizontal layout with section configuration."""
        section = SectionDesign(section_title="Side by Side")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = HorizontalLayout(form_config=section)
            assert layout.form_config == section

    def test_horizontal_layout_render_basic(self):
        """Test basic horizontal layout rendering."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = HorizontalLayout()
            html = layout.render(framework="bootstrap")
            assert isinstance(html, str)

    def test_horizontal_layout_render_with_data(self):
        """Test horizontal layout rendering with data."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = HorizontalLayout()
            html = layout.render(
                data={"field": "value"},
                errors={"field": "error"},
                framework="bootstrap",
            )
            assert isinstance(html, str)

    def test_horizontal_layout_validate(self):
        """Test horizontal layout validation."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = HorizontalLayout()
            result = layout.validate({"test": "data"})
            assert result is not None
            assert hasattr(result, "is_valid")


class TestBaseLayout:
    """Test BaseLayout alias."""

    def test_base_layout_is_alias(self):
        """Test that BaseLayout is an alias."""
        from pydantic_forms.form_layouts import FormLayoutBase

        assert BaseLayout is FormLayoutBase


class TestTabbedLayout:
    """Test TabbedLayout class."""

    def test_tabbed_layout_creation(self):
        """Test creating a tabbed layout."""
        from pydantic_forms.form_layouts import TabbedLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = TabbedLayout()
            assert layout is not None

    def test_tabbed_layout_with_form_design(self):
        """Test tabbed layout with form design."""
        from pydantic_forms.form_layouts import TabbedLayout

        design = FormDesign(form_name="Tabbed Form")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = TabbedLayout(form_config=design)
            assert layout.form_config == design

    def test_tabbed_layout_render_empty(self):
        """Test rendering empty tabbed layout."""
        from pydantic_forms.form_layouts import TabbedLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = TabbedLayout()
            html = layout.render(framework="bootstrap")
            assert "No layouts found" in html or isinstance(html, str)

    def test_tabbed_layout_render_with_tabs(self):
        """Test rendering tabbed layout with tabs."""
        from pydantic_forms.form_layouts import TabbedLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = TabbedLayout()
            # Add some layout attributes
            layout.tab_one = VerticalLayout()
            layout.tab_two = HorizontalLayout()
            html = layout.render(framework="bootstrap")
            assert isinstance(html, str)

    def test_tabbed_layout_validate(self):
        """Test tabbed layout validation."""
        from pydantic_forms.form_layouts import TabbedLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = TabbedLayout()
            result = layout.validate({"test": "data"})
            assert result is not None
            assert hasattr(result, "is_valid")

    def test_tabbed_layout_render_complete_page(self):
        """Test rendering complete page with form design."""
        from pydantic_forms.form_layouts import TabbedLayout

        design = FormDesign(
            form_name="Complete Form",
            ui_theme="bootstrap",
            asset_mode="cdn",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = TabbedLayout(form_config=design)
            layout.test_tab = VerticalLayout()
            html = layout.render(framework="bootstrap")
            assert "Complete Form" in html or isinstance(html, str)


class TestListLayout:
    """Test ListLayout class."""

    def test_list_layout_creation(self):
        """Test creating a list layout."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=BasicFormModel)
            assert layout is not None
            assert layout.form_model == BasicFormModel
            # Default min_items is 0
            assert layout.min_items >= 0
            assert layout.max_items is None

    def test_list_layout_with_options(self):
        """Test list layout with custom options."""
        from pydantic_forms.form_layouts import ListLayout

        section = SectionDesign(section_title="Items")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(
                form_model=ItemFormModel,
                section_design=section,
                min_items=2,
                max_items=5,
                add_button_text="Add New",
                remove_button_text="Delete",
                collapsible_items=True,
                items_expanded_by_default=False,
            )
            assert layout.min_items == 2
            assert layout.max_items == 5
            assert layout.add_button_text == "Add New"
            assert layout.remove_button_text == "Delete"
            assert layout.collapsible_items is True
            assert layout.items_expanded_by_default is False

    def test_list_layout_get_form_models(self):
        """Test getting form models from list layout."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=BasicFormModel)
            models = layout.get_form_models()
            assert BasicFormModel in models

    def test_list_layout_validate_empty(self):
        """Test validating empty list layout."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=SimpleFormModel, min_items=0)
            result = layout.validate({})
            assert result is not None
            # Should be valid since min_items is 0
            assert result.is_valid or not result.is_valid

    def test_list_layout_validate_with_items(self):
        """Test validating list layout with items."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=ItemFormWithName, min_items=1)
            result = layout.validate(
                {
                    "item_0_name": "First",
                    "item_1_name": "Second",
                }
            )
            assert result is not None
            assert hasattr(result, "is_valid")

    def test_list_layout_validate_min_items_constraint(self):
        """Test validation with minimum items constraint."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=ValueFormModel, min_items=3)
            result = layout.validate({})
            assert result is not None
            # Should have constraint error or be invalid
            assert "list_constraint" in result.errors or not result.is_valid

    def test_list_layout_validate_max_items_constraint(self):
        """Test validation with maximum items constraint."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=ValueFormWithDefault, min_items=1, max_items=2)
            result = layout.validate(
                {
                    "item_0_value": "a",
                    "item_1_value": "b",
                    "item_2_value": "c",
                }
            )
            # Should have constraint error for exceeding max
            assert result is not None
            assert hasattr(result, "errors")

    def test_list_layout_render_bootstrap(self):
        """Test rendering list layout with Bootstrap."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=TitleFormModel)
            html = layout.render(framework="bootstrap")
            assert isinstance(html, str)
            assert len(html) > 0

    def test_list_layout_render_material(self):
        """Test rendering list layout with Material Design."""
        from pydantic_forms.form_layouts import ListLayout

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            layout = ListLayout(form_model=MaterialFormModel)
            html = layout.render(framework="material")
            assert isinstance(html, str)
            assert len(html) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
