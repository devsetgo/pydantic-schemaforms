"""
Tests for integration module - framework integrations and external system connections.
"""

from unittest.mock import Mock, patch

import pytest

from pydantic_forms.integration import (
    DjangoIntegration,
    FastAPIIntegration,
    FlaskIntegration,
    JSONSchemaGenerator,
    OpenAPISchemaGenerator,
    ReactJSONSchemaIntegration,
    VueFormulateIntegration,
)
from pydantic_forms.schema_form import Field, FormModel


class TestFlaskIntegration:
    """Test Flask framework integration."""

    def test_flask_integration_creation(self):
        """Test basic FlaskIntegration creation."""
        integration = FlaskIntegration()
        assert integration is not None
        assert hasattr(integration, "create_route")
        assert hasattr(integration, "handle_form_submission")
        assert hasattr(integration, "render_form_template")

    @patch("flask.request")
    def test_flask_form_handling(self, mock_request, simple_form_model):
        """Test Flask form handling."""
        # Mock Flask request data
        mock_request.method = "POST"
        mock_request.form = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": "25",
            "newsletter": "on",
        }

        integration = FlaskIntegration()

        # Test form handling
        result = integration.handle_form_submission(simple_form_model, mock_request)

        assert result is not None
        assert hasattr(result, "is_valid")
        if result.is_valid:
            assert result.data["name"] == "John Doe"
            assert result.data["email"] == "john@example.com"

    def test_flask_route_creation(self, simple_form_model):
        """Test Flask route creation."""
        integration = FlaskIntegration()

        # Create a mock Flask app
        mock_app = Mock()
        mock_app.route = Mock(return_value=lambda f: f)

        # Test route creation
        route_func = integration.create_route(
            mock_app, "/contact", simple_form_model, methods=["GET", "POST"]
        )

        assert callable(route_func)
        mock_app.route.assert_called_once()

    def test_flask_template_rendering(self, simple_form_model):
        """Test Flask template rendering."""
        integration = FlaskIntegration()

        # Mock render_template
        with patch("flask.render_template") as mock_render:
            mock_render.return_value = "<html>Form</html>"

            html = integration.render_form_template(
                "form.html", form_model=simple_form_model, framework="bootstrap"
            )

            assert html == "<html>Form</html>"
            mock_render.assert_called_once()


class TestFastAPIIntegration:
    """Test FastAPI framework integration."""

    def test_fastapi_integration_creation(self):
        """Test basic FastAPIIntegration creation."""
        integration = FastAPIIntegration()
        assert integration is not None
        assert hasattr(integration, "create_endpoint")
        assert hasattr(integration, "create_form_dependency")
        assert hasattr(integration, "generate_openapi_schema")

    def test_fastapi_endpoint_creation(self, simple_form_model):
        """Test FastAPI endpoint creation."""
        integration = FastAPIIntegration()

        # Mock FastAPI app
        mock_app = Mock()
        mock_app.post = Mock(return_value=lambda f: f)
        mock_app.get = Mock(return_value=lambda f: f)

        # Test endpoint creation
        endpoint_func = integration.create_endpoint(mock_app, "/submit-form", simple_form_model)

        assert callable(endpoint_func)
        mock_app.post.assert_called()

    def test_fastapi_form_dependency(self, simple_form_model):
        """Test FastAPI form dependency creation."""
        integration = FastAPIIntegration()

        # Create form dependency
        form_dependency = integration.create_form_dependency(simple_form_model)

        assert callable(form_dependency)

        # Test with mock request data
        mock_data = {"name": "Jane Doe", "email": "jane@example.com", "age": 30, "newsletter": True}

        # The dependency should validate the data
        result = form_dependency(mock_data)
        assert hasattr(result, "name")
        assert result.name == "Jane Doe"

    def test_fastapi_openapi_schema(self, simple_form_model):
        """Test FastAPI OpenAPI schema generation."""
        integration = FastAPIIntegration()

        schema = integration.generate_openapi_schema(simple_form_model)

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "email" in schema["properties"]
        assert "required" in schema


class TestDjangoIntegration:
    """Test Django framework integration."""

    def test_django_integration_creation(self):
        """Test basic DjangoIntegration creation."""
        integration = DjangoIntegration()
        assert integration is not None
        assert hasattr(integration, "create_django_form")
        assert hasattr(integration, "create_model_form")
        assert hasattr(integration, "handle_view")

    def test_django_form_creation(self, simple_form_model):
        """Test Django form creation from Pydantic model."""
        integration = DjangoIntegration()

        # Mock Django forms
        with patch("django.forms.Form"):
            django_form = integration.create_django_form(simple_form_model)

            # Should create a Django form class
            assert django_form is not None

    def test_django_model_form_creation(self, simple_form_model):
        """Test Django ModelForm creation."""
        integration = DjangoIntegration()

        # Mock Django model
        mock_model = Mock()
        mock_model._meta.fields = []

        with patch("django.forms.ModelForm"):
            model_form = integration.create_model_form(simple_form_model, mock_model)

            assert model_form is not None

    def test_django_view_handling(self, simple_form_model):
        """Test Django view handling."""
        integration = DjangoIntegration()

        # Mock Django request
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.POST = {
            "name": "Test User",
            "email": "test@example.com",
            "age": "25",
            "newsletter": "on",
        }

        # Mock Django HttpResponse
        with patch("django.http.HttpResponse"):
            response = integration.handle_view(
                mock_request, simple_form_model, template_name="form.html"
            )

            # Should handle the request
            assert response is not None


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
        from pydantic_forms.integration import map_pydantic_to_json_schema_type

        # Test basic type mappings
        assert map_pydantic_to_json_schema_type(str) == "string"
        assert map_pydantic_to_json_schema_type(int) == "integer"
        assert map_pydantic_to_json_schema_type(float) == "number"
        assert map_pydantic_to_json_schema_type(bool) == "boolean"
        assert map_pydantic_to_json_schema_type(list) == "array"
        assert map_pydantic_to_json_schema_type(dict) == "object"

    def test_ui_element_mapping(self):
        """Test UI element mapping for different frameworks."""
        from pydantic_forms.integration import map_ui_element_to_framework

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
        from pydantic_forms.integration import convert_validation_rules

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
        from pydantic_forms.integration import check_framework_availability

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


# Helper functions for integration tests
def create_mock_flask_app():
    """Create a mock Flask app for testing."""
    mock_app = Mock()
    mock_app.route = Mock(return_value=lambda f: f)
    return mock_app


def create_mock_fastapi_app():
    """Create a mock FastAPI app for testing."""
    mock_app = Mock()
    mock_app.post = Mock(return_value=lambda f: f)
    mock_app.get = Mock(return_value=lambda f: f)
    return mock_app


def create_mock_django_request(data=None):
    """Create a mock Django request for testing."""
    mock_request = Mock()
    mock_request.method = "POST" if data else "GET"
    mock_request.POST = data or {}
    mock_request.GET = {}
    return mock_request
