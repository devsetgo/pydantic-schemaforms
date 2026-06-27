"""
Tests for schema_form module - FormModel and Field functionality.
"""

import pytest
from pydantic import ValidationError

from pydantic_schemaforms.schema_form import Field, FormModel


class TestField:
    """Test the enhanced Field function with UI parameters."""

    def test_field_basic_functionality(self):
        """Test basic Field functionality."""
        field = Field(default='test', description='Test field')
        assert field.default == 'test'
        assert field.description == 'Test field'

    def test_field_ui_element_parameter(self):
        """Test ui_element parameter."""
        field = Field(default='', ui_element='email')
        # Check that ui_element is stored in json_schema_extra
        assert field.json_schema_extra is not None
        assert field.json_schema_extra.get('ui_element') == 'email'

    def test_field_ui_autofocus_parameter(self):
        """Test ui_autofocus parameter."""
        field = Field(default='', ui_autofocus=True)
        assert field.json_schema_extra.get('ui_autofocus') is True

    def test_field_ui_options_parameter(self):
        """Test ui_options parameter."""
        options = {'rows': 4, 'cols': 50}
        field = Field(default='', ui_options=options)
        assert field.json_schema_extra.get('ui_options') == options

    def test_field_multiple_ui_parameters(self):
        """Test multiple UI parameters together."""
        field = Field(
            default='',
            description='Test field',
            ui_element='textarea',
            ui_autofocus=True,
            ui_options={'rows': 3},
            ui_placeholder='Enter text here',
            ui_help_text='Help text',
            ui_class='custom-class',
        )

        schema_extra = field.json_schema_extra
        assert schema_extra.get('ui_element') == 'textarea'
        assert schema_extra.get('ui_autofocus') is True
        assert schema_extra.get('ui_options') == {'rows': 3}
        assert schema_extra.get('ui_placeholder') == 'Enter text here'
        assert schema_extra.get('ui_help_text') == 'Help text'
        assert schema_extra.get('ui_class') == 'custom-class'

    def test_field_merges_with_existing_json_schema_extra(self):
        """Test that UI parameters merge with existing json_schema_extra."""
        existing_extra = {'custom_key': 'custom_value'}
        field = Field(default='', json_schema_extra=existing_extra, ui_element='email')

        schema_extra = field.json_schema_extra
        assert schema_extra.get('custom_key') == 'custom_value'
        assert schema_extra.get('ui_element') == 'email'

    def test_field_none_values_not_included(self):
        """Test that None UI parameter values are not included."""
        field = Field(
            default='',
            ui_element='text',
            ui_autofocus=None,  # Should not be included
            ui_options=None,  # Should not be included
        )

        schema_extra = field.json_schema_extra
        assert schema_extra.get('ui_element') == 'text'
        assert 'ui_autofocus' not in schema_extra
        assert 'ui_options' not in schema_extra


class TestFormModel:
    """Test the FormModel base class functionality."""

    def test_form_model_basic_creation(self, simple_form_model):
        """Test basic FormModel creation."""
        data = {'name': 'John Doe', 'email': 'john@example.com', 'age': 25, 'newsletter': True}

        form = simple_form_model(**data)
        assert form.name == 'John Doe'
        assert form.email == 'john@example.com'
        assert form.age == 25
        assert form.newsletter is True

    def test_form_model_validation_success(self, simple_form_model, sample_form_data):
        """Test successful form validation."""
        form = assert_form_validates(simple_form_model, sample_form_data)
        assert form.name == sample_form_data['name']
        assert form.email == sample_form_data['email']

    def test_form_model_validation_failures(self, simple_form_model):
        """Test form validation failures."""
        # Test required field missing
        assert_form_validation_fails(
            simple_form_model, {'email': 'test@example.com', 'age': 25}, ['name']
        )

        # Test invalid email
        assert_form_validation_fails(
            simple_form_model, {'name': 'John', 'email': 'invalid-email', 'age': 25}, ['email']
        )

        # Test age out of range
        assert_form_validation_fails(
            simple_form_model, {'name': 'John', 'email': 'john@example.com', 'age': 17}, ['age']
        )

    def test_form_model_render_form_method(self, simple_form_model):
        """Test that FormModel has render_form method."""
        assert hasattr(simple_form_model, 'render_form')

        # Test basic rendering
        html = simple_form_model.render_form(submit_url='/simple')
        assert isinstance(html, str)
        assert len(html) > 0
        assert '<form' in html

    def test_form_model_render_form_with_framework(self, simple_form_model):
        """Test FormModel rendering with different frameworks."""
        frameworks = ['bootstrap', 'material', 'none']

        for framework in frameworks:
            html = simple_form_model.render_form(framework=framework, submit_url='/simple')
            assert isinstance(html, str)
            assert '<form' in html
            # Each framework should produce different output
            assert len(html) > 50  # Should be substantial HTML

    def test_form_model_render_form_with_submit_url(self, simple_form_model):
        """Test FormModel rendering with custom submit URL."""
        html = simple_form_model.render_form(submit_url='/custom-submit')
        assert 'action="/custom-submit"' in html or 'hx-post="/custom-submit"' in html

    def test_form_model_with_complex_fields(self, complex_form_model):
        """Test FormModel with complex field types."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'age': 25,
            'rating': 4,
            'terms': True,
            'newsletter': False,
            'favorite_color': '#ff0000',
        }

        form = assert_form_validates(complex_form_model, data)
        assert form.first_name == 'John'
        assert form.last_name == 'Doe'
        assert form.rating == 4
        assert form.terms is True

    def test_form_model_optional_fields(self, complex_form_model):
        """Test FormModel with optional fields."""
        # Minimal required data
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'age': 30,
            'rating': 3,
            'terms': True,
        }

        form = assert_form_validates(complex_form_model, data)
        assert form.phone is None
        assert form.website is None
        assert form.bio is None
        assert form.birth_date is None

    def test_form_model_field_extraction(self, simple_form_model):
        """Test that FormModel can extract field information."""
        from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

        renderer = EnhancedFormRenderer()
        html = renderer.render_form_from_model(simple_form_model)

        # Should contain all form fields
        assert 'name="name"' in html
        assert 'name="email"' in html
        assert 'name="age"' in html
        assert 'name="newsletter"' in html

    def test_form_model_ui_element_extraction(self):
        """Test extraction of UI element specifications."""

        class TestForm(FormModel):
            email: str = Field(..., ui_element='email')
            password: str = Field(..., ui_element='password')
            bio: str = Field(..., ui_element='textarea', ui_options={'rows': 4})
            color: str = Field('#000000', ui_element='color')

        from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

        renderer = EnhancedFormRenderer()
        html = renderer.render_form_from_model(TestForm)

        # Should generate appropriate input types
        assert 'type="email"' in html
        assert 'type="password"' in html
        assert '<textarea' in html
        assert 'type="color"' in html


class TestFormModelValidate:
    """Test FormModel.validate() classmethod."""

    def test_validate_valid_data(self, simple_form_model, sample_form_data):
        """validate() succeeds and returns clean data."""
        result = simple_form_model.validate(sample_form_data, submit_url='/submit')

        assert result.is_valid
        assert result.data['name'] == sample_form_data['name']
        assert result.errors == {}

    def test_validate_invalid_data(self, simple_form_model):
        """validate() returns errors on bad input."""
        result = simple_form_model.validate({'name': 'Alice'}, submit_url='/submit')

        assert not result.is_valid
        assert result.errors

    def test_validate_render_with_errors_no_args(self, simple_form_model):
        """render_with_errors() works with no arguments after validate()."""
        result = simple_form_model.validate({}, submit_url='/simple')

        assert not result.is_valid
        html = result.render_with_errors()
        assert isinstance(html, str)
        assert '<form' in html

    def test_validate_without_submit_url_raises_on_render(self, simple_form_model):
        """render_with_errors() raises when submit_url was never given."""
        result = simple_form_model.validate({})

        assert not result.is_valid
        with pytest.raises(ValueError, match='submit_url is required'):
            result.render_with_errors()


class TestFormModelIntegration:
    """Test FormModel integration with the rendering system."""

    def test_form_model_with_bootstrap_framework(self, simple_form_model):
        """Test FormModel rendering with Bootstrap framework."""
        html = simple_form_model.render_form(framework='bootstrap', submit_url='/simple')

        # Should contain Bootstrap classes
        assert 'class="form-control"' in html or 'class="form-select"' in html
        assert 'class="mb-3"' in html or 'form-group' in html

    def test_form_model_with_material_framework(self, simple_form_model):
        """Test FormModel rendering with Material Design framework."""
        html = simple_form_model.render_form(framework='material', submit_url='/simple')

        # Should contain Material Design structure
        assert '<form' in html
        # Material framework should produce different output than Bootstrap
        assert len(html) > 100

    def test_form_model_with_error_handling(self, simple_form_model):
        """Test FormModel rendering with validation errors."""
        errors = {'name': 'This field is required', 'email': 'Invalid email format'}

        html = simple_form_model.render_form(errors=errors, submit_url='/simple')

        # Should contain error messages
        assert 'This field is required' in html
        assert 'Invalid email format' in html

    def test_form_model_with_initial_data(self, simple_form_model):
        """Test FormModel rendering with initial data."""
        data = {'name': 'John Doe', 'email': 'john@example.com', 'age': 25, 'newsletter': True}

        html = simple_form_model.render_form(data=data, submit_url='/simple')

        # Should contain the initial values
        assert 'value="John Doe"' in html
        assert 'value="john@example.com"' in html
        assert 'value="25"' in html
        # Note: Checkbox state representation varies by renderer implementation


# Helper function for tests
def assert_form_validates(form_model, data):
    """Helper to assert form validation succeeds."""
    try:
        return form_model(**data)
    except ValidationError as e:
        pytest.fail(f'Form validation failed: {e.errors()}')


def assert_form_validation_fails(form_model, data, expected_fields=None):
    """Helper to assert form validation fails."""
    with pytest.raises(ValidationError) as exc_info:
        form_model(**data)

    if expected_fields:
        error_fields = [err['loc'][0] for err in exc_info.value.errors()]
        for field in expected_fields:
            assert field in error_fields, (
                f"Expected validation error for field '{field}', got errors for: {error_fields}"
            )


class TestAsApiModel:
    """Tests for FormModel.as_api_model()."""

    def _make_form(self):
        class ContactForm(FormModel):
            name: str = Field(
                ...,
                min_length=2,
                title='Full Name',
                description='Your full name',
                examples=['Alice Smith'],
                ui_element='text',
                ui_placeholder='Enter name',
            )
            email: str = Field(
                ...,
                title='Email Address',
                examples=['alice@example.com'],
                ui_element='email',
            )
            age: int = Field(..., ge=0, le=120)

        return ContactForm

    def test_returns_basemodel_not_formmodel(self):
        ContactForm = self._make_form()
        ApiModel = ContactForm.as_api_model()
        from pydantic import BaseModel
        assert issubclass(ApiModel, BaseModel)
        assert not issubclass(ApiModel, FormModel)

    def test_same_field_names(self):
        ContactForm = self._make_form()
        ApiModel = ContactForm.as_api_model()
        assert set(ApiModel.model_fields) == set(ContactForm.model_fields)

    def test_ui_keys_stripped_from_schema(self):
        ContactForm = self._make_form()
        schema = ContactForm.as_api_model().model_json_schema()
        for prop in schema.get('properties', {}).values():
            for key in prop:
                assert not key.startswith('ui_'), f'UI key {key!r} found in API schema'

    def test_examples_survive(self):
        ContactForm = self._make_form()
        schema = ContactForm.as_api_model().model_json_schema()
        assert schema['properties']['name']['examples'] == ['Alice Smith']
        assert schema['properties']['email']['examples'] == ['alice@example.com']

    def test_titles_and_descriptions_survive(self):
        ContactForm = self._make_form()
        schema = ContactForm.as_api_model().model_json_schema()
        assert schema['properties']['name']['title'] == 'Full Name'
        assert schema['properties']['name']['description'] == 'Your full name'

    def test_validation_constraints_enforced(self):
        ContactForm = self._make_form()
        ApiModel = ContactForm.as_api_model()
        with pytest.raises(Exception):
            ApiModel.model_validate({'name': 'A', 'email': 'x@x.com', 'age': 30})
        with pytest.raises(Exception):
            ApiModel.model_validate({'name': 'Alice', 'email': 'x@x.com', 'age': -1})

    def test_valid_data_accepted(self):
        ContactForm = self._make_form()
        ApiModel = ContactForm.as_api_model()
        instance = ApiModel.model_validate({'name': 'Alice', 'email': 'alice@example.com', 'age': 30})
        assert instance.name == 'Alice'
        assert instance.age == 30

    def test_result_is_cached(self):
        ContactForm = self._make_form()
        assert ContactForm.as_api_model() is ContactForm.as_api_model()

    def test_subclass_cache_is_isolated(self):
        class FormA(FormModel):
            x: str = Field(..., ui_element='text')

        class FormB(FormModel):
            y: int = Field(..., ge=0)

        assert FormA.as_api_model() is not FormB.as_api_model()
        assert 'x' in FormA.as_api_model().model_fields
        assert 'y' in FormB.as_api_model().model_fields

    def test_original_schema_still_has_ui_keys(self):
        ContactForm = self._make_form()
        _ = ContactForm.as_api_model()  # populate cache
        original_schema = ContactForm.model_json_schema()
        props = original_schema.get('properties', {})
        assert 'ui_element' in props['name']
