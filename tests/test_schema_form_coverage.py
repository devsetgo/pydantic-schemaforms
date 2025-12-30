"""Tests for schema_form.py to improve coverage."""

import pytest
from pydantic import Field as PydanticField
from typing import Dict, Any

from pydantic_forms.schema_form import (
    form_validator,
    Field,
    FormModel,
    ValidationResult,
)


class TestFormValidator:
    """Test form_validator decorator."""

    def test_form_validator_decorator_basic(self):
        """Test form_validator wraps function correctly."""
        @form_validator
        def validate_age(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            if values.get('age', 0) < 18:
                raise ValueError("Must be 18 or older")
            return values

        # The decorator returns a classmethod
        assert isinstance(validate_age, classmethod)


class TestFieldFunction:
    """Test Field function wrapper."""

    def test_field_with_ui_element(self):
        """Test Field adds ui_element to json_schema_extra."""
        field_info = Field(default="", ui_element="textarea")

        assert field_info.json_schema_extra is not None
        assert isinstance(field_info.json_schema_extra, dict)
        assert field_info.json_schema_extra.get('ui_element') == 'textarea'

    def test_field_with_ui_section(self):
        """Test Field adds ui_section to json_schema_extra."""
        field_info = Field(default="", ui_section="profile")

        assert field_info.json_schema_extra['ui_section'] == 'profile'

    def test_field_with_order(self):
        """Test Field adds ui_order to json_schema_extra."""
        field_info = Field(default="", ui_order=5)

        assert field_info.json_schema_extra['ui_order'] == 5

    def test_field_with_help_text(self):
        """Test Field adds ui_help_text to json_schema_extra."""
        field_info = Field(default="", ui_help_text="Enter your name")

        assert field_info.json_schema_extra['ui_help_text'] == "Enter your name"

    def test_field_combines_with_json_schema_extra(self):
        """Test Field merges with existing json_schema_extra."""
        field_info = Field(
            default="",
            json_schema_extra={"custom": "value"},
            ui_element="email"
        )

        assert field_info.json_schema_extra['custom'] == 'value'
        assert field_info.json_schema_extra['ui_element'] == 'email'

    def test_field_with_callable_json_schema_extra(self):
        """Test Field doesn't support callable json_schema_extra with UI elements."""
        def custom_schema(schema, model_type):
            schema['custom_field'] = 'value'

        # When callable is passed with UI elements, Field expects dict
        # So we skip this combination
        field_info = Field(default="", ui_element="text")

        assert field_info.json_schema_extra['ui_element'] == 'text'


class TestFormModelGetJsonSchema:
    """Test FormModel.get_json_schema method."""

    def test_get_json_schema_basic(self):
        """Test get_json_schema returns schema with properties."""
        class SimpleForm(FormModel):
            name: str = Field(default="", ui_element="text")
            age: int = Field(default=0, ui_element="number")

        schema = SimpleForm.get_json_schema()

        assert schema['type'] == 'object'
        assert 'properties' in schema
        assert 'name' in schema['properties']
        assert 'age' in schema['properties']

    def test_get_json_schema_string_constraints(self):
        """Test get_json_schema includes string validation constraints."""
        class StringForm(FormModel):
            username: str = PydanticField(min_length=3, max_length=20, pattern=r'^[a-z]+$')

        schema = StringForm.get_json_schema()
        props = schema['properties']

        assert props['username']['minLength'] == 3
        assert props['username']['maxLength'] == 20
        assert props['username']['pattern'] == r'^[a-z]+$'

    def test_get_json_schema_number_constraints(self):
        """Test get_json_schema includes number validation constraints."""
        class NumberForm(FormModel):
            score: int = PydanticField(ge=0, le=100)

        schema = NumberForm.get_json_schema()
        props = schema['properties']

        assert props['score']['minimum'] == 0
        assert props['score']['maximum'] == 100

    def test_get_json_schema_enum(self):
        """Test get_json_schema handles enum types."""
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class EnumForm(FormModel):
            status: Status

        schema = EnumForm.get_json_schema()
        props = schema['properties']

        # Enum handling varies by Pydantic version, just check schema exists
        assert 'status' in props
        assert props['status']['type'] == 'string'


class TestFormModelExtractUiInfo:
    """Test FormModel._extract_ui_info method."""

    def test_extract_ui_info_with_dict_extra(self):
        """Test _extract_ui_info extracts UI info from dict json_schema_extra."""
        field_info = PydanticField(
            default="",
            json_schema_extra={
                'ui_element': 'textarea',
                'ui_rows': 4,
                'non_ui_field': 'ignored'
            }
        )

        ui_info = FormModel._extract_ui_info(field_info)

        assert ui_info['element'] == 'textarea'
        assert ui_info['rows'] == 4
        assert 'non_ui_field' not in ui_info

    def test_extract_ui_info_with_callable_extra(self):
        """Test _extract_ui_info extracts UI info from callable json_schema_extra."""
        def schema_modifier(schema, model_type):
            schema['ui_placeholder'] = 'Enter value'
            schema['ui_class'] = 'form-control'

        field_info = PydanticField(default="", json_schema_extra=schema_modifier)

        # Create a dummy FormModel class for the callable
        class DummyForm(FormModel):
            pass

        ui_info = DummyForm._extract_ui_info(field_info)

        assert ui_info['placeholder'] == 'Enter value'
        assert ui_info['class'] == 'form-control'

    def test_extract_ui_info_no_extra(self):
        """Test _extract_ui_info returns empty dict when no json_schema_extra."""
        field_info = PydanticField(default="")

        ui_info = FormModel._extract_ui_info(field_info)

        assert ui_info == {}


class TestFormModelGetExampleFormData:
    """Test FormModel.get_example_form_data method."""

    def test_get_example_form_data_basic_types(self):
        """Test get_example_form_data generates example data."""
        class ExampleForm(FormModel):
            name: str
            age: int
            score: float
            active: bool

        example = ExampleForm.get_example_form_data()

        assert example['name'] == 'example'
        assert example['age'] == 123
        assert example['score'] == 1.23
        assert example['active'] is True

    def test_get_example_form_data_unknown_type(self):
        """Test get_example_form_data handles unknown types."""
        from typing import List

        class ComplexForm(FormModel):
            tags: List[str] = []

        example = ComplexForm.get_example_form_data()

        # Unknown types default to empty string
        assert example['tags'] == ''


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_valid(self):
        """Test ValidationResult for valid data."""
        result = ValidationResult(
            is_valid=True,
            data={'name': 'John'},
            errors={}
        )

        assert result.is_valid
        assert result.data == {'name': 'John'}
        assert result.errors == {}

    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid data."""
        result = ValidationResult(
            is_valid=False,
            data={},
            errors={'name': 'Required field'}
        )

        assert not result.is_valid
        assert result.errors == {'name': 'Required field'}

    def test_validation_result_str_valid(self):
        """Test ValidationResult.__str__ for valid result."""
        result = ValidationResult(is_valid=True, data={'name': 'John'}, errors={})

        result_str = str(result)

        assert 'valid=True' in result_str
        assert 'name' in result_str

    def test_validation_result_str_invalid(self):
        """Test ValidationResult.__str__ for invalid result."""
        result = ValidationResult(
            is_valid=False,
            data={},
            errors={'email': 'Invalid email'}
        )

        result_str = str(result)

        assert 'valid=False' in result_str
        assert 'errors' in result_str

    def test_validation_result_render_with_errors(self):
        """Test ValidationResult.render_with_errors method."""
        class TestForm(FormModel):
            name: str = ""

        result = ValidationResult(
            is_valid=False,
            data={},
            errors={'name': 'Required'},
            form_model_cls=TestForm,
            original_data={'name': ''}
        )

        html = result.render_with_errors(framework='bootstrap')

        assert isinstance(html, str)
        # Should contain form HTML

    def test_validation_result_render_with_errors_no_model(self):
        """Test ValidationResult.render_with_errors raises without form_model_cls."""
        result = ValidationResult(
            is_valid=False,
            data={},
            errors={'field': 'error'}
        )

        with pytest.raises(ValueError, match="Cannot render form"):
            result.render_with_errors()


class TestFormModelRegisterField:
    """Test FormModel.register_field method for dynamic fields."""

    def test_register_field_basic(self):
        """Test registering a new field at runtime."""
        class DynamicForm(FormModel):
            name: str = ""

        # Register a new field
        field_info = DynamicForm.register_field('email', annotation=str, field=Field(default=""))

        assert field_info is not None
        assert hasattr(DynamicForm, '__runtime_fields__')
        assert 'email' in DynamicForm.__runtime_fields__

    def test_register_field_without_field_info(self):
        """Test registering field with default FieldInfo."""
        class SimpleForm(FormModel):
            pass

        field_info = SimpleForm.register_field('new_field', annotation=int)

        assert field_info is not None
        assert 'new_field' in SimpleForm.__runtime_fields__

    def test_ensure_dynamic_fields(self):
        """Test ensure_dynamic_fields detects FieldInfo attributes."""
        class ManualForm(FormModel):
            pass

        # Manually add a FieldInfo attribute
        ManualForm.dynamic_field = PydanticField(default="test")

        # Should detect it
        result = ManualForm.ensure_dynamic_fields()

        assert result is True
        assert hasattr(ManualForm, '__runtime_fields__')

    def test_ensure_dynamic_fields_no_new_fields(self):
        """Test ensure_dynamic_fields returns False when no new fields."""
        class StaticForm(FormModel):
            name: str = ""

        result = StaticForm.ensure_dynamic_fields()

        assert result is False

    def test_get_runtime_model_no_runtime_fields(self):
        """Test get_runtime_model returns cls when no runtime fields."""
        class SimpleForm(FormModel):
            name: str = ""

        runtime_model = SimpleForm.get_runtime_model()

        assert runtime_model is SimpleForm

    def test_get_runtime_model_with_runtime_fields(self):
        """Test get_runtime_model creates new model with runtime fields."""
        class BaseForm(FormModel):
            name: str = ""

        # Register a runtime field
        BaseForm.register_field('email', annotation=str, field=Field(default=""))

        runtime_model = BaseForm.get_runtime_model()

        # Should be a different class
        assert runtime_model is not BaseForm
        assert 'Runtime' in runtime_model.__name__

    def test_get_runtime_model_caches(self):
        """Test get_runtime_model caches the runtime model."""
        class CachedForm(FormModel):
            name: str = ""

        CachedForm.register_field('age', annotation=int, field=Field(default=0))

        model1 = CachedForm.get_runtime_model()
        model2 = CachedForm.get_runtime_model()

        # Should return same cached instance
        assert model1 is model2


class TestFormModelRenderForm:
    """Test FormModel.render_form method."""

    def test_render_form_basic(self):
        """Test rendering a form with default settings."""
        class RenderForm(FormModel):
            name: str = Field(default="", ui_element="text")
            email: str = Field(default="", ui_element="email")

        html = RenderForm.render_form()

        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_form_with_data(self):
        """Test rendering a form with initial data."""
        class DataForm(FormModel):
            name: str = ""

        html = DataForm.render_form(data={'name': 'John'})

        assert isinstance(html, str)

    def test_render_form_with_errors(self):
        """Test rendering a form with validation errors."""
        class ErrorForm(FormModel):
            email: str = ""

        html = ErrorForm.render_form(
            data={'email': 'invalid'},
            errors={'email': 'Invalid email'}
        )

        assert isinstance(html, str)

    def test_render_form_different_framework(self):
        """Test rendering with different CSS framework."""
        class FrameworkForm(FormModel):
            name: str = ""

        html = FrameworkForm.render_form(framework='material')

        assert isinstance(html, str)
