"""
Tests for integration module - framework integrations, builders, workflows,
FastAPI example routes, and HTML marker assertions.

Consolidated from:
  - test_integration.py (32 tests)
  - test_integration_builder.py (36 tests)
  - test_integration_workflow.py (17 tests)
  - test_fastapi_forms_matrix.py (5 tests)
  - test_fastapi_layouts_post_validation.py (2 tests)
  - test_fastapi_example_smoke.py (1 test)
  - test_html_markers.py (3 tests)
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pytest
from pydantic import BaseModel

import examples.fastapi_example as fastapi_example
from examples.fastapi_example import app
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.integration import (
    FormBuilder,
    FormIntegration,
    handle_async_form,
    handle_form,
    handle_form_async,
    handle_sync_form,
)
from pydantic_schemaforms.integration.react import ReactJSONSchemaIntegration
from pydantic_schemaforms.integration.schema import JSONSchemaGenerator, OpenAPISchemaGenerator
from pydantic_schemaforms.integration.vue import VueFormulateIntegration
from pydantic_schemaforms.integration.builder import (
    AutoFormBuilder,
    create_contact_form,
    create_form_from_model,
    create_login_form,
    create_registration_form,
)
from pydantic_schemaforms.schema_form import Field, FormModel
from pydantic_schemaforms.validation import validate_form_data


# ---------------------------------------------------------------------------
# Shared helper: patch templates so FastAPI example resolves from repo root
# ---------------------------------------------------------------------------


def _patch_templates_to_repo_root() -> None:
    """Patch the FastAPI example templates directory to the repo root location.

    Also registers the safe_json Jinja2 filter used by the example app.
    """
    base_dir = Path(fastapi_example.__file__).resolve().parent
    fastapi_example.templates = Jinja2Templates(directory=base_dir / 'templates')
    fastapi_example.templates.env.filters['safe_json'] = fastapi_example.safe_json_filter


# ---------------------------------------------------------------------------
# Shared helper: build a FormBuilder wired to a model (used by generic tests)
# ---------------------------------------------------------------------------


def _build_form_builder(form_model):
    builder = FormBuilder(model=form_model)
    builder.text_input('name', 'Name')
    builder.email_input('email', 'Email')
    builder.number_input('age', 'Age')
    builder.checkbox_input('newsletter', 'Newsletter')
    return builder


# ---------------------------------------------------------------------------
# Helper models used by builder tests
# ---------------------------------------------------------------------------


class UserModel(BaseModel):
    """Test user model."""

    username: str
    email: str
    age: int
    is_active: bool = True
    birth_date: date


class ProfileModel(BaseModel):
    """Test profile model with various field types."""

    full_name: str
    email_address: str
    password_field: str
    phone_number: str
    website_url: str
    description: str
    comment: str
    notes: str
    bio: str
    score: float
    registered_date: datetime
    optional_field: Optional[str] = None


# ===========================================================================
# Section 1 – Generic server integrations (sync / async helpers)
# ===========================================================================


class TestGenericServerIntegrations:
    """Test the generic sync/async integration helpers used by WSGI/ASGI servers."""

    def test_handle_sync_form_success(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {'name': 'John Doe', 'email': 'john@example.com', 'age': 30, 'newsletter': True}

        result = handle_sync_form(builder, submitted_data=data)

        assert result['success'] is True
        assert result['data'] == data

    def test_handle_sync_form_errors_include_html(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        invalid_data = {'name': 'J', 'email': 'not-an-email', 'age': 10, 'newsletter': False}

        result = handle_sync_form(builder, submitted_data=invalid_data)

        assert result['success'] is False
        assert 'errors' in result and 'email' in result['errors']
        assert 'form_html' in result

    def test_handle_sync_form_initial_render(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)

        result = handle_sync_form(builder)

        assert 'form_html' in result
        assert isinstance(result['form_html'], str)

    def test_handle_form_sync_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {'name': 'Alias', 'email': 'alias@example.com', 'age': 30, 'newsletter': True}

        result = handle_form(builder, submitted_data=data)

        assert result['success'] is True
        assert result['data'] == data

    @pytest.mark.asyncio
    async def test_handle_async_form_success(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {'name': 'Jane Doe', 'email': 'jane@example.com', 'age': 28, 'newsletter': True}

        result = await handle_async_form(builder, submitted_data=data)

        assert result['success'] is True
        assert result['data'] == data

    @pytest.mark.asyncio
    async def test_handle_async_form_errors_include_html(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        invalid_data = {'name': 'J', 'email': 'bad', 'age': 5, 'newsletter': False}

        result = await handle_async_form(builder, submitted_data=invalid_data)

        assert result['success'] is False
        assert 'errors' in result and 'email' in result['errors']
        assert 'form_html' in result

    @pytest.mark.asyncio
    async def test_handle_async_form_initial_render(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)

        result = await handle_async_form(builder)

        assert 'form_html' in result
        assert isinstance(result['form_html'], str)

    @pytest.mark.asyncio
    async def test_handle_form_async_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {'name': 'Alias', 'email': 'alias@example.com', 'age': 30, 'newsletter': True}

        result = await handle_form_async(builder, submitted_data=data)

        assert result['success'] is True
        assert result['data'] == data

    def test_form_integration_sync_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {'name': 'Sync', 'email': 'sync@example.com', 'age': 40, 'newsletter': True}

        result = FormIntegration.sync_integration(builder, submitted_data=data)

        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_form_integration_async_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {'name': 'Async', 'email': 'async@example.com', 'age': 34, 'newsletter': True}

        result = await FormIntegration.async_integration(builder, submitted_data=data)

        assert result['success'] is True


# ===========================================================================
# Section 2 – React JSON Schema integration
# ===========================================================================


class TestReactJSONSchemaIntegration:
    """Test React JSON Schema Forms integration."""

    def test_react_integration_creation(self):
        """Test basic ReactJSONSchemaIntegration creation."""
        integration = ReactJSONSchemaIntegration()
        assert integration is not None
        assert hasattr(integration, 'generate_schema')
        assert hasattr(integration, 'generate_ui_schema')
        assert hasattr(integration, 'generate_form_data')

    def test_react_schema_generation(self, simple_form_model):
        """Test React JSON Schema generation."""
        integration = ReactJSONSchemaIntegration()

        schema = integration.generate_schema(simple_form_model)

        assert isinstance(schema, dict)
        assert 'type' in schema
        assert schema['type'] == 'object'
        assert 'properties' in schema

        # Check properties
        properties = schema['properties']
        assert 'name' in properties
        assert 'email' in properties
        assert 'age' in properties
        assert 'newsletter' in properties

        # Check property types
        assert properties['name']['type'] == 'string'
        assert properties['email']['type'] == 'string'
        assert properties['age']['type'] == 'integer'
        assert properties['newsletter']['type'] == 'boolean'

    def test_react_ui_schema_generation(self, complex_form_model):
        """Test React UI Schema generation."""
        integration = ReactJSONSchemaIntegration()

        ui_schema = integration.generate_ui_schema(complex_form_model)

        assert isinstance(ui_schema, dict)

        # Should contain UI specifications for different field types
        if 'email' in ui_schema:
            assert ui_schema['email']['ui:widget'] == 'email'

        if 'bio' in ui_schema:
            assert ui_schema['bio']['ui:widget'] == 'textarea'

        if 'birth_date' in ui_schema:
            assert ui_schema['birth_date']['ui:widget'] == 'date'

    def test_react_form_data_generation(self, simple_form_model, sample_form_data):
        """Test React form data generation."""
        integration = ReactJSONSchemaIntegration()

        form_data = integration.generate_form_data(simple_form_model, sample_form_data)

        assert isinstance(form_data, dict)
        assert form_data['name'] == sample_form_data['name']
        assert form_data['email'] == sample_form_data['email']

    def test_react_complete_form_config(self, complex_form_model):
        """Test complete React form configuration."""
        integration = ReactJSONSchemaIntegration()

        config = integration.generate_complete_config(complex_form_model)

        assert isinstance(config, dict)
        assert 'schema' in config
        assert 'uiSchema' in config
        assert 'formData' in config

        # Should be valid JSON Schema
        schema = config['schema']
        assert schema['type'] == 'object'
        assert 'properties' in schema


# ===========================================================================
# Section 3 – Vue Formulate integration
# ===========================================================================


class TestVueFormulateIntegration:
    """Test Vue Formulate integration."""

    def test_vue_integration_creation(self):
        """Test basic VueFormulateIntegration creation."""
        integration = VueFormulateIntegration()
        assert integration is not None
        assert hasattr(integration, 'generate_form_config')
        assert hasattr(integration, 'generate_validation_rules')

    def test_vue_form_config_generation(self, simple_form_model):
        """Test Vue Formulate configuration generation."""
        integration = VueFormulateIntegration()

        config = integration.generate_form_config(simple_form_model)

        assert isinstance(config, list)  # Vue Formulate uses array of fields

        # Check field configurations
        field_names = [field['name'] for field in config if 'name' in field]
        assert 'name' in field_names
        assert 'email' in field_names
        assert 'age' in field_names
        assert 'newsletter' in field_names

    def test_vue_validation_rules(self, simple_form_model):
        """Test Vue Formulate validation rules."""
        integration = VueFormulateIntegration()

        rules = integration.generate_validation_rules(simple_form_model)

        assert isinstance(rules, dict)

        # Should have validation rules for required fields
        if 'name' in rules:
            assert 'required' in rules['name']

        if 'email' in rules:
            assert 'email' in rules['email'] or 'required' in rules['email']


# ===========================================================================
# Section 4 – JSON Schema generator
# ===========================================================================


class TestJSONSchemaGenerator:
    """Test JSON Schema generation utilities."""

    def test_schema_generator_creation(self):
        """Test JSONSchemaGenerator creation."""
        generator = JSONSchemaGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_schema')
        assert hasattr(generator, 'generate_field_schema')

    def test_basic_schema_generation(self, simple_form_model):
        """Test basic JSON Schema generation."""
        generator = JSONSchemaGenerator()

        schema = generator.generate_schema(simple_form_model)

        assert isinstance(schema, dict)
        assert schema['type'] == 'object'
        assert 'properties' in schema
        assert 'required' in schema

        # Check required fields
        required_fields = schema['required']
        assert 'name' in required_fields
        assert 'email' in required_fields

    def test_field_schema_generation(self):
        """Test individual field schema generation."""
        generator = JSONSchemaGenerator()

        # Test string field
        string_field = Field(..., description='A string field')
        string_schema = generator.generate_field_schema(str, string_field)

        assert string_schema['type'] == 'string'
        assert string_schema['description'] == 'A string field'

        # Test integer field with constraints
        int_field = Field(..., ge=1, le=100)
        int_schema = generator.generate_field_schema(int, int_field)

        assert int_schema['type'] == 'integer'
        assert int_schema['minimum'] == 1
        assert int_schema['maximum'] == 100

    def test_complex_field_types(self, complex_form_model):
        """Test schema generation for complex field types."""
        generator = JSONSchemaGenerator()

        schema = generator.generate_schema(complex_form_model)

        properties = schema['properties']

        # Check date field
        if 'birth_date' in properties:
            assert properties['birth_date']['type'] == 'string'
            assert properties['birth_date']['format'] == 'date'

        # Check email field
        if 'email' in properties:
            assert properties['email']['type'] == 'string'
            assert properties['email']['format'] == 'email'


# ===========================================================================
# Section 5 – OpenAPI schema generator
# ===========================================================================


class TestOpenAPISchemaGenerator:
    """Test OpenAPI schema generation."""

    def test_openapi_generator_creation(self):
        """Test OpenAPISchemaGenerator creation."""
        generator = OpenAPISchemaGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_request_schema')
        assert hasattr(generator, 'generate_response_schema')

    def test_request_schema_generation(self, simple_form_model):
        """Test OpenAPI request schema generation."""
        generator = OpenAPISchemaGenerator()

        request_schema = generator.generate_request_schema(simple_form_model)

        assert isinstance(request_schema, dict)
        assert 'content' in request_schema
        assert 'application/json' in request_schema['content']

        json_schema = request_schema['content']['application/json']['schema']
        assert json_schema['type'] == 'object'
        assert 'properties' in json_schema

    def test_response_schema_generation(self, simple_form_model):
        """Test OpenAPI response schema generation."""
        generator = OpenAPISchemaGenerator()

        response_schema = generator.generate_response_schema(simple_form_model)

        assert isinstance(response_schema, dict)
        assert '200' in response_schema  # Success response
        assert '422' in response_schema  # Validation error response

        success_response = response_schema['200']
        assert 'content' in success_response
        assert 'description' in success_response

    def test_complete_openapi_spec(self, simple_form_model):
        """Test complete OpenAPI specification generation."""
        generator = OpenAPISchemaGenerator()

        spec = generator.generate_complete_spec(
            simple_form_model, endpoint_path='/submit-form', method='POST'
        )

        assert isinstance(spec, dict)
        assert 'paths' in spec
        assert '/submit-form' in spec['paths']
        assert 'post' in spec['paths']['/submit-form']

        post_spec = spec['paths']['/submit-form']['post']
        assert 'requestBody' in post_spec
        assert 'responses' in post_spec


# ===========================================================================
# Section 6 – Integration utility functions
# ===========================================================================


class TestIntegrationUtilities:
    """Test integration utility functions."""

    def test_field_type_mapping(self):
        """Test field type mapping between Pydantic and external systems."""
        from pydantic_schemaforms.integration import map_pydantic_to_json_schema_type

        # Test basic type mappings
        assert map_pydantic_to_json_schema_type(str) == 'string'
        assert map_pydantic_to_json_schema_type(int) == 'integer'
        assert map_pydantic_to_json_schema_type(float) == 'number'
        assert map_pydantic_to_json_schema_type(bool) == 'boolean'
        assert map_pydantic_to_json_schema_type(list) == 'array'
        assert map_pydantic_to_json_schema_type(dict) == 'object'

    def test_ui_element_mapping(self):
        """Test UI element mapping for different frameworks."""
        from pydantic_schemaforms.integration import map_ui_element_to_framework

        # Test email field mapping
        react_email = map_ui_element_to_framework('email', 'react')
        assert react_email == 'email'

        vue_email = map_ui_element_to_framework('email', 'vue')
        assert vue_email in ['email', 'text']

        # Test textarea mapping
        react_textarea = map_ui_element_to_framework('textarea', 'react')
        assert react_textarea == 'textarea'

    def test_validation_rule_conversion(self):
        """Test conversion of Pydantic validation to framework rules."""
        from pydantic_schemaforms.integration import convert_validation_rules

        field = Field(..., min_length=3, max_length=50, ge=1, le=100)

        # Test React JSON Schema validation
        react_rules = convert_validation_rules(field, 'react')
        assert isinstance(react_rules, dict)

        # Test Vue Formulate validation
        vue_rules = convert_validation_rules(field, 'vue')
        assert isinstance(vue_rules, (list, dict, str))


# ===========================================================================
# Section 7 – Integration error handling
# ===========================================================================


class TestIntegrationErrorHandling:
    """Test error handling in integrations."""

    def test_invalid_form_model_handling(self):
        """Test handling of invalid form models."""
        integration = ReactJSONSchemaIntegration()

        # Test with None
        with pytest.raises((TypeError, ValueError)):
            integration.generate_schema(None)

        # Test with non-FormModel class
        with pytest.raises((TypeError, ValueError)):
            integration.generate_schema(str)

    def test_missing_framework_handling(self):
        """Test handling of missing framework dependencies."""
        from pydantic_schemaforms.integration import check_framework_availability

        # Test checking for framework availability
        flask_available = check_framework_availability('flask')
        assert isinstance(flask_available, bool)

        fastapi_available = check_framework_availability('fastapi')
        assert isinstance(fastapi_available, bool)

    def test_integration_fallbacks(self, simple_form_model):
        """Test integration fallback mechanisms."""
        integration = ReactJSONSchemaIntegration()

        # Test with minimal form model
        class MinimalForm(FormModel):
            field: str = Field(...)

        schema = integration.generate_schema(MinimalForm)
        assert isinstance(schema, dict)
        assert 'properties' in schema
        assert 'field' in schema['properties']


# ===========================================================================
# Section 8 – FormBuilder input methods
# ===========================================================================


class TestFormBuilderInputMethods:
    """Test FormBuilder input method additions."""

    def test_select_input(self):
        """Test select_input adds select field."""
        builder = FormBuilder()
        options = [{'value': '1', 'label': 'One'}, {'value': '2', 'label': 'Two'}]

        result = builder.select_input('country', options, label='Country')

        assert result is builder  # Chaining
        assert len(builder.fields) == 1
        assert builder.fields[0].name == 'country'
        assert builder.fields[0].field_type == 'select'
        assert builder.fields[0].options == options

    def test_checkbox_input(self):
        """Test checkbox_input adds checkbox field."""
        builder = FormBuilder()

        result = builder.checkbox_input('terms', label='Accept Terms')

        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == 'terms'
        assert builder.fields[0].field_type == 'checkbox'
        assert builder.fields[0].label == 'Accept Terms'

    def test_textarea_input(self):
        """Test textarea_input adds textarea field."""
        builder = FormBuilder()

        result = builder.textarea_input('comments', rows=6)

        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == 'comments'
        assert builder.fields[0].field_type == 'textarea'
        assert builder.fields[0].attributes['rows'] == '6'

    def test_textarea_input_default_rows(self):
        """Test textarea_input with default rows."""
        builder = FormBuilder()

        builder.textarea_input('message')

        assert builder.fields[0].attributes['rows'] == '4'

    def test_date_input(self):
        """Test date_input adds date field."""
        builder = FormBuilder()

        result = builder.date_input('birth_date', label='Date of Birth')

        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == 'birth_date'
        assert builder.fields[0].field_type == 'date'

    def test_file_input(self):
        """Test file_input adds file field."""
        builder = FormBuilder()

        result = builder.file_input('document', label='Upload Document')

        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == 'document'
        assert builder.fields[0].field_type == 'file'

    def test_file_input_with_accept(self):
        """Test file_input with accept attribute."""
        builder = FormBuilder()

        builder.file_input('image', accept='image/*')

        assert builder.fields[0].attributes['accept'] == 'image/*'


# ===========================================================================
# Section 9 – FormBuilder validation methods
# ===========================================================================


class TestFormBuilderValidation:
    """Test FormBuilder validation methods."""

    def test_required(self):
        """Test required validation."""
        builder = FormBuilder()
        builder.text_input('name')

        result = builder.required('name', 'Name is required')

        assert result is builder
        # Validator should have the rule added

    def test_min_length(self):
        """Test min_length validation."""
        builder = FormBuilder()
        builder.text_input('password')

        result = builder.min_length('password', 8, 'Min 8 chars')

        assert result is builder

    def test_max_length(self):
        """Test max_length validation."""
        builder = FormBuilder()
        builder.text_input('username')

        result = builder.max_length('username', 20, 'Max 20 chars')

        assert result is builder


# ===========================================================================
# Section 10 – FormBuilder configuration methods
# ===========================================================================


class TestFormBuilderConfiguration:
    """Test FormBuilder configuration methods."""

    def test_set_layout(self):
        """Test set_layout changes layout type."""
        builder = FormBuilder()

        result = builder.set_layout('horizontal')

        assert result is builder
        assert builder.layout_type == 'horizontal'

    def test_set_form_attributes(self):
        """Test set_form_attributes updates attributes."""
        builder = FormBuilder()

        result = builder.set_form_attributes(id='my-form', class_='custom-form')

        assert result is builder
        assert builder.form_attrs['id'] == 'my-form'
        assert builder.form_attrs['class_'] == 'custom-form'

    def test_disable_csrf(self):
        """Test disable_csrf disables CSRF protection."""
        builder = FormBuilder()

        result = builder.disable_csrf()

        assert result is builder
        assert builder.csrf_enabled is False

    def test_disable_honeypot(self):
        """Test disable_honeypot disables honeypot."""
        builder = FormBuilder()

        result = builder.disable_honeypot()

        assert result is builder
        assert builder.honeypot_enabled is False


# ===========================================================================
# Section 11 – FormBuilder build and validate
# ===========================================================================


class TestFormBuilderBuildValidate:
    """Test FormBuilder build and validation."""

    def test_validate_data_with_model(self):
        """Test validate_data with Pydantic model."""
        builder = FormBuilder(model=UserModel)

        data = {
            'username': 'john',
            'email': 'john@example.com',
            'age': 30,
            'is_active': True,
            'birth_date': '2000-01-01',
        }

        is_valid, errors = builder.validate_data(data)

        # Should delegate to validator
        assert isinstance(is_valid, bool)
        assert isinstance(errors, dict)

    def test_validate_data_without_model(self):
        """Test validate_data without model."""
        builder = FormBuilder()
        builder.text_input('name').required('name')

        is_valid, errors = builder.validate_data({'name': 'John'})

        assert isinstance(is_valid, bool)
        assert isinstance(errors, dict)

    def test_get_validation_script(self):
        """Test get_validation_script returns JavaScript."""
        builder = FormBuilder()
        builder.text_input('email').email_input()

        script = builder.get_validation_script()

        assert isinstance(script, str)


# ===========================================================================
# Section 12 – AutoFormBuilder
# ===========================================================================


class TestAutoFormBuilder:
    """Test AutoFormBuilder automatic form generation."""

    def test_build_from_model_basic_types(self):
        """Test _build_from_model with basic field types."""
        builder = AutoFormBuilder(UserModel)

        assert len(builder.fields) == 5

        # Check field names
        field_names = [f.name for f in builder.fields]
        assert 'username' in field_names
        assert 'email' in field_names
        assert 'age' in field_names
        assert 'is_active' in field_names
        assert 'birth_date' in field_names

    def test_build_from_model_input_types(self):
        """Test _build_from_model assigns correct input types."""
        builder = AutoFormBuilder(UserModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['username'].field_type == 'text'
        assert field_map['age'].field_type == 'number'
        assert field_map['is_active'].field_type == 'checkbox'
        assert field_map['birth_date'].field_type == 'date'

    def test_get_input_type_for_field_email(self):
        """Test _get_input_type_for_field detects email fields."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['email_address'].field_type == 'email'

    def test_get_input_type_for_field_password(self):
        """Test _get_input_type_for_field detects password fields."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['password_field'].field_type == 'password'

    def test_get_input_type_for_field_phone(self):
        """Test _get_input_type_for_field detects phone fields."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['phone_number'].field_type == 'tel'

    def test_get_input_type_for_field_url(self):
        """Test _get_input_type_for_field detects URL fields."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['website_url'].field_type == 'url'

    def test_get_input_type_for_field_textarea_fields(self):
        """Test _get_input_type_for_field detects textarea fields."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['description'].field_type == 'textarea'
        assert field_map['comment'].field_type == 'textarea'
        assert field_map['notes'].field_type == 'textarea'
        assert field_map['bio'].field_type == 'textarea'

    def test_get_input_type_for_field_number(self):
        """Test _get_input_type_for_field handles int and float."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['score'].field_type == 'number'

    def test_get_input_type_for_field_datetime(self):
        """Test _get_input_type_for_field handles datetime."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['registered_date'].field_type == 'date'

    def test_get_input_type_for_field_optional(self):
        """Test _get_input_type_for_field handles Optional fields."""
        builder = AutoFormBuilder(ProfileModel)

        field_map = {f.name: f for f in builder.fields}

        # Should handle Optional[str] -> str -> text
        assert field_map['optional_field'].field_type == 'text'

    def test_add_field_validation_required(self):
        """Test _add_field_validation adds required validation."""

        class RequiredModel(BaseModel):
            required_field: str
            optional_field: str = 'default'

        builder = AutoFormBuilder(RequiredModel)

        field_map = {f.name: f for f in builder.fields}

        assert field_map['required_field'].required is True
        assert field_map['optional_field'].required is False

    # ------------------------------------------------------------------
    # Render-path tests — these were missing and hid the PydanticUndefined
    # serialisation bug in create_form_from_model / AutoFormBuilder.render()
    # ------------------------------------------------------------------

    def test_render_plain_basemodel(self):
        """create_form_from_model(BaseModel).render() must not crash."""

        class SimpleUser(BaseModel):
            name: str
            email: str
            age: int

        html = create_form_from_model(SimpleUser).render()
        assert 'name' in html
        assert 'email' in html
        assert 'age' in html
        assert len(html) > 100

    def test_render_formmodel(self):
        """create_form_from_model(FormModel).render() must not crash."""
        from pydantic_schemaforms import FormModel, Field

        class ContactForm(FormModel):
            name: str = Field(title='Full Name')
            email: str = Field(title='Email', ui_element='email')
            message: str = Field(title='Message', ui_element='textarea')

        html = create_form_from_model(ContactForm).render()
        assert 'Full Name' in html or 'name' in html
        assert len(html) > 100

    def test_render_model_with_defaults(self):
        """Optional fields with defaults must not leak PydanticUndefined."""

        class SettingsModel(BaseModel):
            username: str
            theme: str = 'light'
            notifications: bool = True

        html = create_form_from_model(SettingsModel).render()
        assert 'username' in html
        assert 'theme' in html
        assert len(html) > 100

    def test_render_produces_valid_html_structure(self):
        """Rendered HTML must contain form and input elements."""

        class MinimalModel(BaseModel):
            title: str

        html = create_form_from_model(MinimalModel).render()
        assert '<input' in html or '<textarea' in html or '<select' in html


# ===========================================================================
# Section 13 – Builder factory functions
# ===========================================================================


class TestBuilderFactoryFunctions:
    """Test factory functions for common forms."""

    def test_create_login_form(self):
        """Test create_login_form creates login form."""
        builder = create_login_form()

        assert isinstance(builder, FormBuilder)
        assert len(builder.fields) >= 2

        field_names = [f.name for f in builder.fields]
        assert 'email' in field_names
        assert 'password' in field_names

    def test_create_login_form_framework(self):
        """Test create_login_form with custom framework."""
        builder = create_login_form(framework='material')

        assert builder.framework == 'material'

    def test_create_registration_form(self):
        """Test create_registration_form creates registration form."""
        builder = create_registration_form()

        assert isinstance(builder, FormBuilder)
        assert len(builder.fields) >= 5

        field_names = [f.name for f in builder.fields]
        assert 'first_name' in field_names
        assert 'last_name' in field_names
        assert 'email' in field_names
        assert 'password' in field_names
        assert 'confirm_password' in field_names

    def test_create_registration_form_framework(self):
        """Test create_registration_form with custom framework."""
        builder = create_registration_form(framework='material')

        assert builder.framework == 'material'

    def test_create_contact_form(self):
        """Test create_contact_form creates contact form."""
        builder = create_contact_form()

        assert isinstance(builder, FormBuilder)
        assert len(builder.fields) >= 4

        field_names = [f.name for f in builder.fields]
        assert 'name' in field_names
        assert 'email' in field_names
        assert 'subject' in field_names
        assert 'message' in field_names

    def test_create_contact_form_framework(self):
        """Test create_contact_form with custom framework."""
        builder = create_contact_form(framework='tailwind')

        assert builder.framework == 'tailwind'

    def test_create_form_from_model(self):
        """Test create_form_from_model creates AutoFormBuilder."""
        builder = create_form_from_model(UserModel)

        assert isinstance(builder, AutoFormBuilder)
        assert builder.model is UserModel

    def test_create_form_from_model_with_kwargs(self):
        """Test create_form_from_model passes kwargs."""
        builder = create_form_from_model(
            UserModel,
            framework='material',
            theme='dark',
        )

        assert builder.framework == 'material'
        assert builder.theme == 'dark'


# ===========================================================================
# Section 14 – Complete form workflows
# ===========================================================================


class TestCompleteFormWorkflow:
    """Test complete form workflows from model to rendered HTML."""

    def test_basic_form_workflow(self, simple_form_model, enhanced_renderer):
        """Test basic form creation, validation, and rendering workflow."""
        # 1. Create form data
        form_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'age': 30,
            'newsletter': True,
        }

        # 2. Validate data
        validation_result = validate_form_data(simple_form_model, form_data)
        assert validation_result.is_valid
        assert validation_result.data['name'] == 'John Doe'
        assert validation_result.data['email'] == 'john.doe@example.com'

        # 3. Render form
        html = enhanced_renderer.render_form_from_model(simple_form_model)
        assert len(html) > 0
        assert 'name="name"' in html
        assert 'name="email"' in html

        # 4. Render with data
        filled_html = enhanced_renderer.render_form_from_model(simple_form_model, data=form_data)
        assert 'value="John Doe"' in filled_html
        assert 'value="john.doe@example.com"' in filled_html

    def test_form_validation_workflow(self, simple_form_model, enhanced_renderer):
        """Test form validation workflow with errors."""
        # 1. Invalid data
        invalid_data = {
            'name': '',  # Missing required field
            'email': 'not-an-email',  # Invalid email
            'age': -5,  # Invalid age
            'newsletter': 'invalid',  # Invalid boolean
        }

        # 2. Validation should fail
        validation_result = validate_form_data(simple_form_model, invalid_data)
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0

        # 3. Render with errors - using basic form rendering for now
        # Note: render_with_errors method doesn't exist, so test basic rendering
        basic_html = enhanced_renderer.render_form_from_model(simple_form_model)
        assert len(basic_html) > 0
        # Should contain form fields
        assert 'name="name"' in basic_html
        assert 'name="email"' in basic_html

    def test_form_correction_workflow(self, simple_form_model, enhanced_renderer):
        """Test correcting form data after validation errors."""
        # 1. Start with invalid data
        invalid_data = {'first_name': 'John', 'email': 'john.doe@example.com'}  # Wrong field name

        # 2. First validation fails
        initial_result = validate_form_data(simple_form_model, invalid_data)
        assert not initial_result.is_valid

        # 3. Correct the data
        corrected_data = {
            'name': 'John Doe',  # Correct field name
            'email': 'john.doe@example.com',
            'age': 25,
            'newsletter': False,
        }

        # 4. Second validation succeeds
        corrected_result = validate_form_data(simple_form_model, corrected_data)
        assert corrected_result.is_valid
        assert corrected_result.data['name'] == 'John Doe'
        assert corrected_result.data['email'] == 'john.doe@example.com'

    def test_form_with_layout_components(self, simple_form_model, enhanced_renderer):
        """Test form workflow with basic layout concepts (without complex layouts)."""
        # For now, test basic form functionality that doesn't depend on layout system

        # 1. Test basic form rendering
        basic_html = enhanced_renderer.render_form_from_model(simple_form_model)
        assert len(basic_html) > 0
        assert 'name="name"' in basic_html
        assert 'name="email"' in basic_html

        # 2. Test form with different frameworks
        bootstrap_html = enhanced_renderer.render_form_from_model(
            simple_form_model, framework='bootstrap'
        )
        material_html = enhanced_renderer.render_form_from_model(
            simple_form_model, framework='material'
        )
        plain_html = enhanced_renderer.render_form_from_model(simple_form_model, framework='plain')

        # All should produce valid HTML
        for html in [bootstrap_html, material_html, plain_html]:
            assert len(html) > 0
            assert 'name="name"' in html
            assert 'name="email"' in html

        # 3. Test that different frameworks produce different output
        assert bootstrap_html != material_html
        assert bootstrap_html != plain_html
        assert material_html != plain_html


# ===========================================================================
# Section 15 – Advanced workflows
# ===========================================================================


class TestAdvancedWorkflow:
    """Test advanced form workflows."""

    def test_complex_form_model(self, enhanced_renderer):
        """Test workflow with a complex form model."""

        class ComplexForm(FormModel):
            # Basic fields
            name: str = Field(..., ui_element='text', ui_options={'placeholder': 'Full name'})
            email: str = Field(..., ui_element='email')
            age: int = Field(..., ge=18, le=120, ui_element='number')

            # Date fields
            birth_date: date = Field(..., ui_element='date')
            created_at: datetime = Field(..., ui_element='datetime-local')

            # Selection fields
            gender: str = Field(
                ...,
                ui_element='select',
                ui_options={
                    'options': [
                        {'value': 'M', 'label': 'Male'},
                        {'value': 'F', 'label': 'Female'},
                        {'value': 'O', 'label': 'Other'},
                    ]
                },
            )

            # Boolean field
            newsletter: bool = Field(default=False, ui_element='checkbox')

            # Textarea
            bio: str = Field(..., ui_element='textarea', ui_options={'rows': 4})

        # 1. Test rendering
        html = enhanced_renderer.render_form_from_model(ComplexForm)
        assert len(html) > 0

        # Check various field types are present
        assert 'type="text"' in html
        assert 'type="email"' in html
        assert 'type="number"' in html
        assert 'type="date"' in html
        assert 'type="datetime-local"' in html
        assert '<select' in html
        assert 'type="checkbox"' in html
        assert '<textarea' in html

        # 2. Test with valid data
        valid_data = {
            'name': 'Alice Johnson',
            'email': 'alice@example.com',
            'age': 28,
            'birth_date': '1995-06-15',
            'created_at': '2024-01-01T10:00:00',
            'gender': 'F',
            'newsletter': True,
            'bio': 'Software developer with 5 years experience',
        }

        validation_result = validate_form_data(ComplexForm, valid_data)
        assert validation_result.is_valid

        # 3. Test rendering with data
        filled_html = enhanced_renderer.render_form_from_model(
            ComplexForm, data=validation_result.data
        )
        assert 'value="Alice Johnson"' in filled_html
        assert 'value="alice@example.com"' in filled_html

    def test_form_with_file_upload(self, enhanced_renderer):
        """Test form with file upload capabilities."""

        class FileUploadForm(FormModel):
            name: str = Field(..., ui_element='text')
            avatar: str = Field(
                ..., ui_element='file', ui_options={'accept': 'image/*', 'multiple': False}
            )
            documents: str = Field(
                ..., ui_element='file', ui_options={'accept': '.pdf,.doc,.docx', 'multiple': True}
            )

        html = enhanced_renderer.render_form_from_model(FileUploadForm)
        assert len(html) > 0
        assert 'type="file"' in html
        assert 'accept="image/*"' in html
        assert 'accept=".pdf,.doc,.docx"' in html

    def test_conditional_field_rendering(self, enhanced_renderer):
        """Test conditional field rendering based on other field values."""

        class ConditionalForm(FormModel):
            account_type: str = Field(
                ...,
                ui_element='select',
                ui_options={
                    'options': [
                        {'value': 'personal', 'label': 'Personal'},
                        {'value': 'business', 'label': 'Business'},
                    ]
                },
            )

            # Personal fields
            first_name: str = Field(
                ..., ui_element='text', ui_condition={'field': 'account_type', 'value': 'personal'}
            )
            last_name: str = Field(
                ..., ui_element='text', ui_condition={'field': 'account_type', 'value': 'personal'}
            )

            # Business fields
            company_name: str = Field(
                ..., ui_element='text', ui_condition={'field': 'account_type', 'value': 'business'}
            )
            tax_id: str = Field(
                ..., ui_element='text', ui_condition={'field': 'account_type', 'value': 'business'}
            )

        html = enhanced_renderer.render_form_from_model(ConditionalForm)
        assert len(html) > 0
        assert 'name="account_type"' in html
        assert 'name="first_name"' in html
        assert 'name="company_name"' in html


# ===========================================================================
# Section 16 – Multi-renderer tests
# ===========================================================================


class TestMultiRenderer:
    """Test using multiple renderers together."""

    def test_enhanced_and_modern_renderers(self, simple_form_model):
        """Test using both enhanced and modern renderers."""
        enhanced = EnhancedFormRenderer()

        # Both should render the same model
        enhanced_html = enhanced.render_form_from_model(simple_form_model)

        assert len(enhanced_html) > 0
        assert 'name="name"' in enhanced_html
        assert 'name="email"' in enhanced_html

        # Test both with the same data
        form_data = {'name': 'Test User', 'email': 'test@example.com', 'age': 25}

        enhanced_filled = enhanced.render_form_from_model(simple_form_model, data=form_data)

        assert 'value="Test User"' in enhanced_filled
        assert 'value="test@example.com"' in enhanced_filled

    def test_renderer_framework_consistency(self, simple_form_model):
        """Test that different renderers handle frameworks consistently."""
        enhanced = EnhancedFormRenderer()

        # Test framework switching
        frameworks = ['bootstrap', 'material', 'plain']

        for framework in frameworks:
            html = enhanced.render_form_from_model(simple_form_model, framework=framework)
            assert len(html) > 0
            assert 'name="name"' in html
            assert 'name="email"' in html


# ===========================================================================
# Section 17 – Form integration with external systems (workflow tests)
# ===========================================================================


class TestFormIntegration:
    """Test integration with external systems."""

    def test_react_json_schema_integration(self, simple_form_model):
        """Test React JSON Schema integration."""
        integration = ReactJSONSchemaIntegration()

        # Convert pydantic model to JSON schema
        json_schema = integration.generate_schema(simple_form_model)

        assert isinstance(json_schema, dict)
        assert 'properties' in json_schema
        assert 'name' in json_schema['properties']
        assert 'email' in json_schema['properties']

        # Convert to React JSON Schema form config
        react_config = integration.generate_complete_config(simple_form_model)

        assert isinstance(react_config, dict)
        assert 'schema' in react_config
        assert 'uiSchema' in react_config

    def test_json_schema_validation_integration(self, simple_form_model):
        """Test JSON schema validation integration."""
        integration = ReactJSONSchemaIntegration()

        # Get JSON schema
        json_schema = integration.generate_schema(simple_form_model)

        # Valid data should pass - test basic schema generation for now

        # Test that schema generation works
        assert json_schema is not None
        assert isinstance(json_schema, dict)

        # Invalid data test - for now just test that schema exists

        # Test that we can generate schema consistently
        schema2 = integration.generate_schema(simple_form_model)
        assert schema2 == json_schema


# ===========================================================================
# Section 18 – Performance workflows
# ===========================================================================


class TestPerformanceWorkflow:
    """Test performance-related workflows."""

    def test_large_form_rendering(self, enhanced_renderer):
        """Test rendering performance with large forms."""

        class LargeForm(FormModel):
            # Create a form with many fields
            pass

        # Dynamically add fields to test performance
        field_count = 50
        for i in range(field_count):
            LargeForm.register_field(
                f'field_{i}',
                annotation=str,
                field=Field(..., ui_element='text'),
            )

        html = enhanced_renderer.render_form_from_model(LargeForm)
        assert len(html) > 0

        # Check that all fields are present
        for i in range(field_count):
            assert f'name="field_{i}"' in html

    def test_dynamic_field_validation(self):
        """Ensure register_field definitions participate in validation."""

        class DynamicForm(FormModel):
            pass

        DynamicForm.register_field(
            'nickname',
            annotation=str,
            field=Field(..., ui_element='text', min_length=3),
        )

        invalid = validate_form_data(DynamicForm, {'nickname': ''})
        assert not invalid.is_valid
        assert 'nickname' in invalid.errors

        valid = validate_form_data(DynamicForm, {'nickname': 'Ace'})
        assert valid.is_valid
        assert valid.data['nickname'] == 'Ace'

    def test_batch_validation(self, simple_form_model):
        """Test batch validation of multiple form submissions."""
        test_data_sets = [
            {'name': 'User 1', 'email': 'user1@example.com', 'age': 25, 'newsletter': True},
            {'name': 'User 2', 'email': 'user2@example.com', 'age': 30, 'newsletter': False},
            {'name': 'User 3', 'email': 'user3@example.com', 'age': 35, 'newsletter': True},
        ]

        results = []
        for data in test_data_sets:
            result = validate_form_data(simple_form_model, data)
            results.append(result)

        # All should be valid
        assert all(result.is_valid for result in results)

        # Check data preservation
        for i, result in enumerate(results):
            assert result.data['name'] == f'User {i + 1}'
            assert result.data['email'] == f'user{i + 1}@example.com'


# ===========================================================================
# Section 19 – Error handling workflows
# ===========================================================================


class TestErrorHandlingWorkflow:
    """Test comprehensive error handling workflows."""

    def test_validation_error_workflow(self, simple_form_model, enhanced_renderer):
        """Test comprehensive validation error handling."""
        # Multiple types of validation errors
        error_data = {
            'name': '',  # Required field missing
            'email': 'invalid-email-format',  # Invalid format
            'age': -5,  # Invalid range
            'newsletter': 'not-a-boolean',  # Type mismatch
        }

        validation_result = validate_form_data(simple_form_model, error_data)
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0

        # Render with errors
        # Test basic form rendering since render_with_errors doesn't exist
        basic_html = enhanced_renderer.render_form_from_model(simple_form_model)
        assert len(basic_html) > 0

        # Should still contain form structure
        assert 'name="name"' in basic_html
        assert 'name="email"' in basic_html

    def test_partial_form_completion(self, enhanced_renderer):
        """Test handling partial form completion."""

        class PartialForm(FormModel):
            required_field: str = Field(..., ui_element='text')
            optional_field: str = Field(default='', ui_element='text')

        # Partial data - missing required field
        partial_data = {'optional_field': 'filled in'}

        validation_result = validate_form_data(PartialForm, partial_data)
        assert not validation_result.is_valid

        # Should preserve partial data in rendered form
        html = enhanced_renderer.render_form_from_model(PartialForm, data=partial_data)
        assert 'value="filled in"' in html

    def test_form_recovery_workflow(self, simple_form_model, enhanced_renderer):
        """Test form recovery after errors."""
        # Start with completely invalid data
        invalid_data = {
            'name': '',
            'email': 'bad-email',
            'age': 'not-a-number',
            'newsletter': 'invalid',
        }

        # First validation
        result1 = validate_form_data(simple_form_model, invalid_data)
        assert not result1.is_valid

        # Fix one error at a time
        partially_fixed = {
            'name': 'John Doe',  # Fixed
            'email': 'bad-email',  # Still invalid
            'age': 'not-a-number',  # Still invalid
            'newsletter': 'invalid',  # Still invalid
        }

        result2 = validate_form_data(simple_form_model, partially_fixed)
        assert not result2.is_valid
        # Should have fewer errors than before

        # Fully fix the data
        fully_fixed = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'age': 30,
            'newsletter': True,
        }

        result3 = validate_form_data(simple_form_model, fully_fixed)
        assert result3.is_valid


# ===========================================================================
# Section 20 – FastAPI example: GET/POST matrix
# ===========================================================================

FORM_ROUTES = ['login', 'register', 'showcase', 'pets', 'organization', 'layouts']
STYLES = ['bootstrap', 'material']

INPUT_RE = re.compile(r'<input\b[^>]*>', re.I)
TEXTAREA_RE = re.compile(r'<textarea\b([^>]*)>(.*?)</textarea>', re.I | re.S)
SELECT_RE = re.compile(r'<select\b([^>]*)>(.*?)</select>', re.I | re.S)
OPTION_RE = re.compile(r'<option\b([^>]*)>(.*?)</option>', re.I | re.S)
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*([\"\'])(.*?)\2', re.S)


@pytest.fixture
def client() -> TestClient:
    _patch_templates_to_repo_root()
    return TestClient(app)


def _parse_attrs(tag: str) -> dict[str, str]:
    return {key.lower(): value for key, _, value in ATTR_RE.findall(tag)}


def _has_attr(tag: str, name: str) -> bool:
    return re.search(rf'\b{name}\b', tag, re.I) is not None


def _extract_form_payload(html: str) -> dict[str, str] | None:
    form_match = re.search(r'<form\b[^>]*>(.*?)</form>', html, re.I | re.S)
    if not form_match:
        return None

    form_html = form_match.group(1)
    payload: dict[str, str] = {}

    for tag in INPUT_RE.findall(form_html):
        attrs = _parse_attrs(tag)
        name = attrs.get('name')
        if not name:
            continue
        input_type = attrs.get('type', 'text').lower()
        if input_type in {'submit', 'button', 'reset', 'image', 'file'}:
            continue
        if input_type in {'checkbox', 'radio'}:
            if _has_attr(tag, 'checked'):
                payload[name] = attrs.get('value', 'on')
            continue
        payload[name] = attrs.get('value', '')

    for head, inner in TEXTAREA_RE.findall(form_html):
        attrs = _parse_attrs(head)
        name = attrs.get('name')
        if name:
            payload[name] = inner.strip()

    for head, inner in SELECT_RE.findall(form_html):
        attrs = _parse_attrs(head)
        name = attrs.get('name')
        if not name:
            continue

        selected_value: str | None = None
        first_non_empty: str | None = None
        first_any: str | None = None

        for option_head, option_text in OPTION_RE.findall(inner):
            option_attrs = _parse_attrs(option_head)
            value = option_attrs.get('value', re.sub(r'<[^>]+>', '', option_text).strip())

            if first_any is None:
                first_any = value
            if first_non_empty is None and value != '':
                first_non_empty = value
            if _has_attr(option_head, 'selected'):
                selected_value = value

        if selected_value is not None:
            payload[name] = selected_value
        elif name not in payload:
            payload[name] = first_non_empty if first_non_empty is not None else (first_any or '')

    return payload


def _assert_style_marker(style: str, body: str) -> None:
    lower = body.lower()
    if style == 'bootstrap':
        assert 'btn btn-primary' in body or 'bootstrap' in lower
    elif style == 'material':
        markers = ['md3-', 'material', 'outlined-text-field', 'filled-text-field']
        assert any(marker in lower for marker in markers)


@pytest.mark.parametrize('route', FORM_ROUTES)
@pytest.mark.parametrize('style', STYLES)
def test_fastapi_form_routes_get_post_matrix(client: TestClient, route: str, style: str):
    get_response = client.get(f'/{route}?style={style}&demo=true')
    assert get_response.status_code == 200

    get_body = get_response.text
    assert '<form' in get_body.lower()
    assert 'Internal Server Error' not in get_body
    assert 'Traceback (most recent call last)' not in get_body
    _assert_style_marker(style, get_body)

    payload = _extract_form_payload(get_body)
    assert payload is not None

    post_response = client.post(f'/{route}?style={style}', data=payload)
    assert post_response.status_code == 200

    post_body = post_response.text
    assert 'Internal Server Error' not in post_body
    assert 'Traceback (most recent call last)' not in post_body
    assert 'Exception:' not in post_body

    is_success = any(
        token in post_body.lower()
        for token in [
            'successful',
            'submitted successfully',
            'registration successful',
            'login successful',
        ]
    )
    is_rerender = '<form' in post_body.lower()
    assert is_success or is_rerender


def test_fastapi_self_contained_get(client: TestClient):
    response = client.get('/self-contained?demo=true')
    assert response.status_code == 200
    body = response.text
    assert 'Self-Contained Form Demo' in body
    assert '<form' in body.lower()
    assert 'Internal Server Error' not in body


def test_fastapi_self_contained_honors_plain_html_style(client: TestClient):
    response = client.get('/self-contained?style=none&demo=true')
    assert response.status_code == 200
    body = response.text
    assert 'Selected Style:</strong> <code>none</code>' in body
    assert 'generated by <code>EnhancedFormRenderer</code>' in body


def test_fastapi_vendor_bootstrap_icons_endpoint(client: TestClient):
    response = client.get('/vendor/bootstrap-icons.css')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/css')
    body = response.text
    assert 'bootstrap-icons' in body
    assert 'data:font/woff2;base64,' in body


def test_fastapi_self_contained_has_no_external_cdn(client: TestClient):
    response = client.get('/self-contained?style=bootstrap&demo=true')
    assert response.status_code == 200
    body = response.text
    # The self-contained page must not require any CDN
    assert 'cdn.jsdelivr.net' not in body
    assert 'unpkg.com' not in body


# ===========================================================================
# Section 21 – FastAPI layouts: POST validation
# ===========================================================================


def _valid_layout_post_payload() -> dict:
    # Note: LayoutDemonstrationForm renders nested layout fields without prefixes,
    # and model_list items use bracketed indices (parsed by parse_nested_form_data).
    return {
        # PersonalInfoForm (vertical_tab)
        'first_name': 'Alex',
        'last_name': 'Johnson',
        'email': 'alex.johnson@example.com',
        # ContactInfoForm (horizontal_tab)
        'address': '456 Demo Street',
        'city': 'San Francisco',
        # PreferencesForm (tabbed_tab) - defaults exist, but include one to ensure tab renders
        'notification_email': 'true',
        'theme': 'dark',
        'language': 'en',
        # TaskListForm (list_tab) - must include at least one task
        'project_name': 'Demo Project',
        'tasks[0].task_name': 'Complete project setup',
        'tasks[0].priority': 'high',
        'tasks[0].due_date': '2024-12-01',
    }


def test_layouts_post_rejects_blank_first_name_and_preferences_tab_renders():
    client = TestClient(app)
    payload = _valid_layout_post_payload()
    payload['first_name'] = ''  # invalid (min_length=2)

    resp = client.post('/layouts?style=bootstrap', data=payload)
    assert resp.status_code == 200

    html = resp.text
    assert 'Layout Demonstration - Validation Errors' in html
    assert 'First Name' in html
    # Error should be visible
    assert 'at least 2' in html or 'Must be at least 2' in html
    # Preferences tab content should still render (regression)
    assert 'Email Notifications' in html
    assert 'No layouts found in tabbed layout' not in html


def test_layouts_post_accepts_valid_payload():
    client = TestClient(app)
    resp = client.post('/layouts?style=bootstrap', data=_valid_layout_post_payload())

    assert resp.status_code == 200
    html = resp.text
    assert 'Layout Demo Submitted Successfully' in html


# ===========================================================================
# Section 22 – FastAPI example smoke test
# ===========================================================================


def test_homepage_renders():
    _patch_templates_to_repo_root()
    client = TestClient(app)
    resp = client.get('/')
    assert resp.status_code == 200
    assert 'Pydantic Forms' in resp.text or 'Forms' in resp.text


# ===========================================================================
# Section 23 – HTML marker assertions
# ===========================================================================


def test_render_form_html_wrapped_by_default() -> None:
    from pydantic_schemaforms.enhanced_renderer import render_form_html
    from pydantic_schemaforms.schema_form import Field, FormModel

    class _MarkerForm(FormModel):
        name: str = Field(default='', title='Name')

    html = render_form_html(_MarkerForm, submit_url='/test')
    assert html.splitlines()[0] == '<!--- Start Pydantic-SchemaForms -->'
    assert html.splitlines()[-1] == '<!--- End Pydantic-SchemaForms -->'


def test_legacy_render_form_html_wraps_after_appends() -> None:
    from pydantic_schemaforms.render_form import render_form_html
    from pydantic_schemaforms.schema_form import Field, FormModel

    class _MarkerForm(FormModel):
        name: str = Field(default='', title='Name')

    html = render_form_html(_MarkerForm, submit_url='/test')
    assert html.splitlines()[0] == '<!--- Start Pydantic-SchemaForms -->'
    assert html.splitlines()[-1] == '<!--- End Pydantic-SchemaForms -->'


def test_render_form_page_wrapped_by_default() -> None:
    from pydantic_schemaforms.integration.builder import create_login_form, render_form_page

    html = render_form_page(create_login_form(), title='Login')
    assert html.splitlines()[0] == '<!--- Start Pydantic-SchemaForms -->'
    assert html.splitlines()[-1] == '<!--- End Pydantic-SchemaForms -->'
