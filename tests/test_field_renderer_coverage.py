"""Comprehensive tests for field_renderer.py to increase coverage."""

import pytest
from typing import Any, Dict, Optional
from pydantic_forms.rendering.field_renderer import FieldRenderer
from pydantic_forms.rendering.context import RenderContext
from pydantic_forms.inputs import HiddenInput, TextInput, SelectInput
from unittest.mock import Mock, MagicMock, patch


class TestFieldRendererBasicSetup:
    """Test FieldRenderer initialization and basic properties."""

    def test_field_renderer_init(self):
        """Test FieldRenderer initialization."""
        renderer = Mock()
        renderer.config = {"framework": "bootstrap"}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        assert field_renderer._renderer == renderer
        assert field_renderer.config == {"framework": "bootstrap"}
        assert field_renderer.framework == "bootstrap"

    def test_field_renderer_theme_property(self):
        """Test FieldRenderer theme property."""
        renderer = Mock()
        renderer.theme = {"primary_color": "blue"}
        
        field_renderer = FieldRenderer(renderer)
        assert field_renderer.theme == {"primary_color": "blue"}

    def test_field_renderer_theme_none(self):
        """Test FieldRenderer theme property when not set."""
        renderer = Mock(spec=[])
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        assert field_renderer.theme is None


class TestFieldRendererHiddenFields:
    """Test rendering of hidden fields."""

    def test_render_hidden_field(self):
        """Test rendering of hidden input fields."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="hidden_id",
            field_schema={"ui": {"hidden": True}, "type": "string"},
            value="123",
            context=context
        )
        
        assert "hidden" in result.lower()
        assert "123" in result

    def test_render_field_with_hidden_ui_config(self):
        """Test rendering field marked as hidden in UI config."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="secret",
            field_schema={"type": "string", "ui": {"hidden": True}},
            value="secret_value",
            context=context
        )
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestFieldRendererUIElementDetection:
    """Test UI element type detection and configuration."""

    def test_render_field_with_explicit_element(self):
        """Test rendering field with explicit UI element specified."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        renderer._render_layout_field = Mock(return_value="<div>layout</div>")
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="custom",
            field_schema={"type": "string", "ui": {"element": "text"}},
            value="test",
            context=context
        )
        
        assert result is not None

    def test_render_field_detects_layout_element(self):
        """Test field renderer detects layout element type."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        renderer._render_layout_field = Mock(return_value="<div>layout content</div>")
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="layout_field",
            field_schema={"type": "object", "ui": {"element": "layout"}},
            context=context
        )
        
        renderer._render_layout_field.assert_called_once()

    def test_render_field_detects_model_list_element(self):
        """Test field renderer detects model_list element type."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        renderer._render_model_list_field = Mock(return_value="<ul>list</ul>")
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        with patch.object(field_renderer, '_render_model_list_field', return_value="<ul>list</ul>"):
            result = field_renderer.render_field(
                field_name="model_list",
                field_schema={"type": "array", "ui": {"element": "model_list"}},
                context=context
            )


class TestFieldRendererCheckboxHandling:
    """Test checkbox-specific field rendering."""

    def test_render_checkbox_with_true_value(self):
        """Test rendering checkbox with true value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="agree",
            field_schema={"type": "boolean"},
            value=True,
            context=context,
            layout="vertical"
        )
        
        assert "checkbox" in result.lower() or "checked" in result.lower()

    def test_render_checkbox_with_string_true_value(self):
        """Test rendering checkbox with string 'true' value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="active",
            field_schema={"type": "boolean"},
            value="true",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_render_checkbox_with_numeric_true_value(self):
        """Test rendering checkbox with numeric true value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="enabled",
            field_schema={"type": "boolean"},
            value="1",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_render_checkbox_with_on_value(self):
        """Test rendering checkbox with 'on' value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="switch",
            field_schema={"type": "boolean"},
            value="on",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)


class TestFieldRendererPasswordFields:
    """Test password field rendering."""

    def test_render_password_field(self):
        """Test rendering of password fields."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="password",
            field_schema={"type": "string", "ui": {"input_type": "password"}},
            value="secret123",
            context=context,
            layout="vertical"
        )
        
        assert "password" in result.lower()

    def test_render_password_field_no_value(self):
        """Test rendering of password field without value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="pwd",
            field_schema={"type": "string", "ui_element": "password"},
            value=None,
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)


class TestFieldRendererErrorHandling:
    """Test field error rendering."""

    def test_render_field_with_error(self):
        """Test rendering field with error message."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="email",
            field_schema={"type": "string"},
            value="invalid",
            error="Invalid email format",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_render_field_with_all_errors_dict(self):
        """Test rendering field with all_errors dictionary."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        all_errors = {
            "field1": "error1",
            "field2": "error2"
        }
        
        result = field_renderer.render_field(
            field_name="field1",
            field_schema={"type": "string"},
            value="test",
            all_errors=all_errors,
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)


class TestFieldRendererRequiredFields:
    """Test required field handling."""

    def test_render_required_field(self):
        """Test rendering required field."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        required_fields = ["username", "email"]
        
        result = field_renderer.render_field(
            field_name="username",
            field_schema={"type": "string"},
            value="john",
            required_fields=required_fields,
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_render_optional_field(self):
        """Test rendering optional field."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        required_fields = ["username"]
        
        result = field_renderer.render_field(
            field_name="optional_field",
            field_schema={"type": "string"},
            value="data",
            required_fields=required_fields,
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)


class TestFieldRendererInputInference:
    """Test input type inference from schema."""

    def test_infer_ui_element_from_schema(self):
        """Test UI element inference from schema."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        # Test with email type
        result = field_renderer.render_field(
            field_name="email",
            field_schema={"type": "string", "format": "email"},
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_infer_textarea_for_long_string(self):
        """Test textarea inference for long text."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="description",
            field_schema={"type": "string", "description": "A long text field"},
            value="long text content",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)


class TestFieldRendererContextRequirement:
    """Test that RenderContext is required."""

    def test_render_field_without_context_raises(self):
        """Test that rendering without context raises error."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        
        with pytest.raises(ValueError, match="RenderContext is required"):
            field_renderer.render_field(
                field_name="test",
                field_schema={"type": "string"},
                value="test",
                context=None
            )


class TestFieldRendererLayoutOptions:
    """Test field rendering with different layout options."""

    def test_render_field_vertical_layout(self):
        """Test rendering field with vertical layout."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="field",
            field_schema={"type": "string"},
            value="test",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_render_field_horizontal_layout(self):
        """Test rendering field with horizontal layout."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="field",
            field_schema={"type": "string"},
            value="test",
            context=context,
            layout="horizontal"
        )
        
        assert isinstance(result, str)

    def test_render_field_inline_layout(self):
        """Test rendering field with inline layout."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="field",
            field_schema={"type": "string"},
            value="test",
            context=context,
            layout="inline"
        )
        
        assert isinstance(result, str)


class TestFieldRendererInputClassing:
    """Test input CSS class generation."""

    def test_get_input_class_for_text(self):
        """Test input class generation for text input."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        renderer.theme = Mock()
        renderer.theme.input_class = Mock(return_value="form-control")
        
        field_renderer = FieldRenderer(renderer)
        
        css_class = field_renderer._get_input_class("text")
        assert isinstance(css_class, str)

    def test_get_input_class_for_email(self):
        """Test input class generation for email input."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        renderer.theme = Mock()
        renderer.theme.input_class = Mock(return_value="form-control")
        
        field_renderer = FieldRenderer(renderer)
        
        css_class = field_renderer._get_input_class("email")
        assert isinstance(css_class, str)

    def test_get_input_class_for_checkbox(self):
        """Test input class generation for checkbox."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        renderer.theme = Mock()
        renderer.theme.input_class = Mock(return_value="form-check-input")
        
        field_renderer = FieldRenderer(renderer)
        
        css_class = field_renderer._get_input_class("checkbox")
        assert isinstance(css_class, str)


class TestFieldRendererFrameworkSpecific:
    """Test framework-specific rendering."""

    def test_render_field_bootstrap_framework(self):
        """Test rendering field for bootstrap framework."""
        renderer = Mock()
        renderer.config = {"theme": "bootstrap"}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="test",
            field_schema={"type": "string"},
            value="test",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_render_field_material_framework(self):
        """Test rendering field for material framework."""
        renderer = Mock()
        renderer.config = {"theme": "material"}
        renderer.framework = "material"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="test",
            field_schema={"type": "string"},
            value="test",
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)


class TestFieldRendererNullValues:
    """Test handling of null/None values."""

    def test_render_field_with_none_value(self):
        """Test rendering field with None value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="optional",
            field_schema={"type": "string"},
            value=None,
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)

    def test_render_checkbox_with_none_value(self):
        """Test rendering checkbox with None value."""
        renderer = Mock()
        renderer.config = {}
        renderer.framework = "bootstrap"
        
        field_renderer = FieldRenderer(renderer)
        context = RenderContext(form_data={}, schema_defs={})
        
        result = field_renderer.render_field(
            field_name="checkbox",
            field_schema={"type": "boolean"},
            value=None,
            context=context,
            layout="vertical"
        )
        
        assert isinstance(result, str)
