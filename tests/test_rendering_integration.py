"""Tests for rendering utilities to improve coverage."""

from datetime import datetime

from pydantic_schemaforms.schema_form import FormModel, Field


class TestFormRenderingIntegration:
    """Test form rendering integration."""

    def test_render_simple_form(self):
        """Test rendering a simple form."""
        class SimpleForm(FormModel):
            name: str = Field(default="")
            email: str = Field(default="")

        html = SimpleForm.render_form(submit_url="/simple")

        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_form_with_initial_data(self):
        """Test rendering form with initial data."""
        class PersonForm(FormModel):
            first_name: str = ""
            last_name: str = ""

        html = PersonForm.render_form(data={'first_name': 'John', 'last_name': 'Doe'}, submit_url="/person")

        assert isinstance(html, str)

    def test_render_form_with_errors(self):
        """Test rendering form with validation errors."""
        class EmailForm(FormModel):
            email: str = ""

        html = EmailForm.render_form(
            data={'email': 'invalid'},
            errors={'email': 'Invalid email format'},
            submit_url="/email",
        )

        assert isinstance(html, str)

    def test_render_form_different_frameworks(self):
        """Test rendering form with different frameworks."""
        class BasicForm(FormModel):
            field: str = ""

        # Bootstrap
        html_bs = BasicForm.render_form(framework='bootstrap', submit_url="/basic")
        assert isinstance(html_bs, str)

        # Material
        html_mat = BasicForm.render_form(framework='material', submit_url="/basic")
        assert isinstance(html_mat, str)


class TestFormModelValidation:
    """Test form model validation."""

    def test_form_model_example_data(self):
        """Test getting example form data."""
        class ExampleForm(FormModel):
            name: str = ""
            age: int = 0
            active: bool = True

        example = ExampleForm.get_example_form_data()

        assert example is not None
        assert 'name' in example
        assert 'age' in example
        assert 'active' in example

    def test_form_model_json_schema(self):
        """Test getting JSON schema from form model."""
        class SchemaForm(FormModel):
            title: str = Field(default="")
            description: str = Field(default="")

        schema = SchemaForm.get_json_schema()

        assert schema['type'] == 'object'
        assert 'properties' in schema
        assert 'title' in schema['properties']
        assert 'description' in schema['properties']


class TestInputTypeDetection:
    """Test input type detection."""

    def test_email_field_detection(self):
        """Test email field is detected."""
        class EmailForm(FormModel):
            email: str = ""

        schema = EmailForm.get_json_schema()

        assert 'email' in schema['properties']

    def test_url_field_detection(self):
        """Test URL field detection."""
        class UrlForm(FormModel):
            website: str = ""

        schema = UrlForm.get_json_schema()

        assert 'website' in schema['properties']

    def test_datetime_field_detection(self):
        """Test datetime field detection."""

        class DateForm(FormModel):
            created_at: datetime

        schema = DateForm.get_json_schema()

        assert 'created_at' in schema['properties']

    def test_boolean_field_detection(self):
        """Test boolean field detection."""
        class CheckboxForm(FormModel):
            agreed: bool = False

        schema = CheckboxForm.get_json_schema()

        props = schema['properties']
        assert 'agreed' in props
        assert props['agreed']['type'] == 'boolean'
