"""
Tests for integration module - framework integrations and external system connections.
"""


import pytest

from pydantic_schemaforms.integration import (
    FormBuilder,
    FormIntegration,
    JSONSchemaGenerator,
    OpenAPISchemaGenerator,
    ReactJSONSchemaIntegration,
    VueFormulateIntegration,
    handle_async_form,
    handle_form,
    handle_form_async,
    handle_sync_form,
)
from pydantic_schemaforms.schema_form import Field, FormModel


def _build_form_builder(form_model):
    builder = FormBuilder(model=form_model)
    builder.text_input("name", "Name")
    builder.email_input("email", "Email")
    builder.number_input("age", "Age")
    builder.checkbox_input("newsletter", "Newsletter")
    return builder


class TestGenericServerIntegrations:
    """Test the generic sync/async integration helpers used by WSGI/ASGI servers."""

    def test_handle_sync_form_success(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {"name": "John Doe", "email": "john@example.com", "age": 30, "newsletter": True}

        result = handle_sync_form(builder, submitted_data=data)

        assert result["success"] is True
        assert result["data"] == data

    def test_handle_sync_form_errors_include_html(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        invalid_data = {"name": "J", "email": "not-an-email", "age": 10, "newsletter": False}

        result = handle_sync_form(builder, submitted_data=invalid_data)

        assert result["success"] is False
        assert "errors" in result and "email" in result["errors"]
        assert "form_html" in result

    def test_handle_sync_form_initial_render(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)

        result = handle_sync_form(builder)

        assert "form_html" in result
        assert isinstance(result["form_html"], str)

    def test_handle_form_sync_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {"name": "Alias", "email": "alias@example.com", "age": 30, "newsletter": True}

        result = handle_form(builder, submitted_data=data)

        assert result["success"] is True
        assert result["data"] == data

    @pytest.mark.asyncio
    async def test_handle_async_form_success(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {"name": "Jane Doe", "email": "jane@example.com", "age": 28, "newsletter": True}

        result = await handle_async_form(builder, submitted_data=data)

        assert result["success"] is True
        assert result["data"] == data

    @pytest.mark.asyncio
    async def test_handle_async_form_errors_include_html(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        invalid_data = {"name": "J", "email": "bad", "age": 5, "newsletter": False}

        result = await handle_async_form(builder, submitted_data=invalid_data)

        assert result["success"] is False
        assert "errors" in result and "email" in result["errors"]
        assert "form_html" in result

    @pytest.mark.asyncio
    async def test_handle_async_form_initial_render(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)

        result = await handle_async_form(builder)

        assert "form_html" in result
        assert isinstance(result["form_html"], str)

    @pytest.mark.asyncio
    async def test_handle_form_async_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {"name": "Alias", "email": "alias@example.com", "age": 30, "newsletter": True}

        result = await handle_form_async(builder, submitted_data=data)

        assert result["success"] is True
        assert result["data"] == data

    def test_form_integration_sync_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {"name": "Sync", "email": "sync@example.com", "age": 40, "newsletter": True}

        result = FormIntegration.sync_integration(builder, submitted_data=data)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_form_integration_async_alias(self, simple_form_model):
        builder = _build_form_builder(simple_form_model)
        data = {"name": "Async", "email": "async@example.com", "age": 34, "newsletter": True}

        result = await FormIntegration.async_integration(builder, submitted_data=data)

        assert result["success"] is True


class TestReactJSONSchemaIntegration:
    """Test React JSON Schema Forms integration."""

    def test_react_integration_creation(self):
        """Test basic ReactJSONSchemaIntegration creation."""
        integration = ReactJSONSchemaIntegration()
        assert integration is not None
        assert hasattr(integration, "generate_schema")
        assert hasattr(integration, "generate_ui_schema")
        assert hasattr(integration, "generate_form_data")

    def test_react_schema_generation(self, simple_form_model):
        """Test React JSON Schema generation."""
        integration = ReactJSONSchemaIntegration()

        schema = integration.generate_schema(simple_form_model)

        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

        # Check properties
        properties = schema["properties"]
        assert "name" in properties
        assert "email" in properties
        assert "age" in properties
        assert "newsletter" in properties

        # Check property types
        assert properties["name"]["type"] == "string"
        assert properties["email"]["type"] == "string"
        assert properties["age"]["type"] == "integer"
        assert properties["newsletter"]["type"] == "boolean"

    def test_react_ui_schema_generation(self, complex_form_model):
        """Test React UI Schema generation."""
        integration = ReactJSONSchemaIntegration()

        ui_schema = integration.generate_ui_schema(complex_form_model)

        assert isinstance(ui_schema, dict)

        # Should contain UI specifications for different field types
        if "email" in ui_schema:
            assert ui_schema["email"]["ui:widget"] == "email"

        if "bio" in ui_schema:
            assert ui_schema["bio"]["ui:widget"] == "textarea"

        if "birth_date" in ui_schema:
            assert ui_schema["birth_date"]["ui:widget"] == "date"

    def test_react_form_data_generation(self, simple_form_model, sample_form_data):
        """Test React form data generation."""
        integration = ReactJSONSchemaIntegration()

        form_data = integration.generate_form_data(simple_form_model, sample_form_data)

        assert isinstance(form_data, dict)
        assert form_data["name"] == sample_form_data["name"]
        assert form_data["email"] == sample_form_data["email"]

    def test_react_complete_form_config(self, complex_form_model):
        """Test complete React form configuration."""
        integration = ReactJSONSchemaIntegration()

        config = integration.generate_complete_config(complex_form_model)

        assert isinstance(config, dict)
        assert "schema" in config
        assert "uiSchema" in config
        assert "formData" in config

        # Should be valid JSON Schema
        schema = config["schema"]
        assert schema["type"] == "object"
        assert "properties" in schema


class TestVueFormulateIntegration:
    """Test Vue Formulate integration."""

    def test_vue_integration_creation(self):
        """Test basic VueFormulateIntegration creation."""
        integration = VueFormulateIntegration()
        assert integration is not None
        assert hasattr(integration, "generate_form_config")
        assert hasattr(integration, "generate_validation_rules")

    def test_vue_form_config_generation(self, simple_form_model):
        """Test Vue Formulate configuration generation."""
        integration = VueFormulateIntegration()

        config = integration.generate_form_config(simple_form_model)

        assert isinstance(config, list)  # Vue Formulate uses array of fields

        # Check field configurations
        field_names = [field["name"] for field in config if "name" in field]
        assert "name" in field_names
        assert "email" in field_names
        assert "age" in field_names
        assert "newsletter" in field_names

    def test_vue_validation_rules(self, simple_form_model):
        """Test Vue Formulate validation rules."""
        integration = VueFormulateIntegration()

        rules = integration.generate_validation_rules(simple_form_model)

        assert isinstance(rules, dict)

        # Should have validation rules for required fields
        if "name" in rules:
            assert "required" in rules["name"]

        if "email" in rules:
            assert "email" in rules["email"] or "required" in rules["email"]


class TestJSONSchemaGenerator:
    """Test JSON Schema generation utilities."""

    def test_schema_generator_creation(self):
        """Test JSONSchemaGenerator creation."""
        generator = JSONSchemaGenerator()
        assert generator is not None
        assert hasattr(generator, "generate_schema")
        assert hasattr(generator, "generate_field_schema")

    def test_basic_schema_generation(self, simple_form_model):
        """Test basic JSON Schema generation."""
        generator = JSONSchemaGenerator()

        schema = generator.generate_schema(simple_form_model)

        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Check required fields
        required_fields = schema["required"]
        assert "name" in required_fields
        assert "email" in required_fields

    def test_field_schema_generation(self):
        """Test individual field schema generation."""
        generator = JSONSchemaGenerator()

        # Test string field
        string_field = Field(..., description="A string field")
        string_schema = generator.generate_field_schema(str, string_field)

        assert string_schema["type"] == "string"
        assert string_schema["description"] == "A string field"

        # Test integer field with constraints
        int_field = Field(..., ge=1, le=100)
        int_schema = generator.generate_field_schema(int, int_field)

        assert int_schema["type"] == "integer"
        assert int_schema["minimum"] == 1
        assert int_schema["maximum"] == 100

    def test_complex_field_types(self, complex_form_model):
        """Test schema generation for complex field types."""
        generator = JSONSchemaGenerator()

        schema = generator.generate_schema(complex_form_model)

        properties = schema["properties"]

        # Check date field
        if "birth_date" in properties:
            assert properties["birth_date"]["type"] == "string"
            assert properties["birth_date"]["format"] == "date"

        # Check email field
        if "email" in properties:
            assert properties["email"]["type"] == "string"
            assert properties["email"]["format"] == "email"


class TestOpenAPISchemaGenerator:
    """Test OpenAPI schema generation."""

    def test_openapi_generator_creation(self):
        """Test OpenAPISchemaGenerator creation."""
        generator = OpenAPISchemaGenerator()
        assert generator is not None
        assert hasattr(generator, "generate_request_schema")
        assert hasattr(generator, "generate_response_schema")

    def test_request_schema_generation(self, simple_form_model):
        """Test OpenAPI request schema generation."""
        generator = OpenAPISchemaGenerator()

        request_schema = generator.generate_request_schema(simple_form_model)

        assert isinstance(request_schema, dict)
        assert "content" in request_schema
        assert "application/json" in request_schema["content"]

        json_schema = request_schema["content"]["application/json"]["schema"]
        assert json_schema["type"] == "object"
        assert "properties" in json_schema

    def test_response_schema_generation(self, simple_form_model):
        """Test OpenAPI response schema generation."""
        generator = OpenAPISchemaGenerator()

        response_schema = generator.generate_response_schema(simple_form_model)

        assert isinstance(response_schema, dict)
        assert "200" in response_schema  # Success response
        assert "422" in response_schema  # Validation error response

        success_response = response_schema["200"]
        assert "content" in success_response
        assert "description" in success_response

    def test_complete_openapi_spec(self, simple_form_model):
        """Test complete OpenAPI specification generation."""
        generator = OpenAPISchemaGenerator()

        spec = generator.generate_complete_spec(
            simple_form_model, endpoint_path="/submit-form", method="POST"
        )

        assert isinstance(spec, dict)
        assert "paths" in spec
        assert "/submit-form" in spec["paths"]
        assert "post" in spec["paths"]["/submit-form"]

        post_spec = spec["paths"]["/submit-form"]["post"]
        assert "requestBody" in post_spec
        assert "responses" in post_spec


class TestIntegrationUtilities:
    """Test integration utility functions."""

    def test_field_type_mapping(self):
        """Test field type mapping between Pydantic and external systems."""
        from pydantic_schemaforms.integration import map_pydantic_to_json_schema_type

        # Test basic type mappings
        assert map_pydantic_to_json_schema_type(str) == "string"
        assert map_pydantic_to_json_schema_type(int) == "integer"
        assert map_pydantic_to_json_schema_type(float) == "number"
        assert map_pydantic_to_json_schema_type(bool) == "boolean"
        assert map_pydantic_to_json_schema_type(list) == "array"
        assert map_pydantic_to_json_schema_type(dict) == "object"

    def test_ui_element_mapping(self):
        """Test UI element mapping for different frameworks."""
        from pydantic_schemaforms.integration import map_ui_element_to_framework

        # Test email field mapping
        react_email = map_ui_element_to_framework("email", "react")
        assert react_email == "email"

        vue_email = map_ui_element_to_framework("email", "vue")
        assert vue_email in ["email", "text"]

        # Test textarea mapping
        react_textarea = map_ui_element_to_framework("textarea", "react")
        assert react_textarea == "textarea"

    def test_validation_rule_conversion(self):
        """Test conversion of Pydantic validation to framework rules."""
        from pydantic_schemaforms.integration import convert_validation_rules

        field = Field(..., min_length=3, max_length=50, ge=1, le=100)

        # Test React JSON Schema validation
        react_rules = convert_validation_rules(field, "react")
        assert isinstance(react_rules, dict)

        # Test Vue Formulate validation
        vue_rules = convert_validation_rules(field, "vue")
        assert isinstance(vue_rules, (list, dict, str))


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
        flask_available = check_framework_availability("flask")
        assert isinstance(flask_available, bool)

        fastapi_available = check_framework_availability("fastapi")
        assert isinstance(fastapi_available, bool)

    def test_integration_fallbacks(self, simple_form_model):
        """Test integration fallback mechanisms."""
        integration = ReactJSONSchemaIntegration()

        # Test with minimal form model
        class MinimalForm(FormModel):
            field: str = Field(...)

        schema = integration.generate_schema(MinimalForm)
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "field" in schema["properties"]
