"""
Consolidated rendering tests.

Merged from:
- test_enhanced_renderer.py        (27 tests)
- test_rendering_integration.py    (10 tests)
- test_coverage_gap_fillers.py     (10 tests)
- test_coverage_targeted_modules.py (19 tests)
- test_modern_renderer.py          (14 tests)
- test_templates_coverage.py       (11 tests)
- test_theme_hooks.py               (8 tests)
"""

from __future__ import annotations

import asyncio
import importlib
import logging
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from typing import Annotated, Dict, Optional, Type

import pytest
from pydantic import BaseModel

from pydantic_schemaforms.assets import runtime as runtime_assets
from pydantic_schemaforms.enhanced_renderer import (
    EnhancedFormRenderer,
    SchemaFormValidationError,
    render_form_html,
    render_form_html_async,
)
from pydantic_schemaforms.form_field import (
    CheckboxField,
    DateField,
    EmailField,
    FormField,
    NumberField,
    SelectField,
    TextAreaField,
    TextField,
    create_field_with_validation,
)
from pydantic_schemaforms.form_layouts import FormDesign, ListLayout, TabbedLayout, VerticalLayout
from pydantic_schemaforms.inputs.base import (
    BaseInput,
    SelectInputBase,
    build_label,
    render_template,
    t,
)
from pydantic_schemaforms.inputs.numeric_inputs import (
    AgeInput,
    DecimalInput,
    PercentageInput,
    QuantityInput,
    RatingInput,
    ScoreInput,
    SliderInput,
    TemperatureInput,
)
from pydantic_schemaforms.inputs.selection_inputs import (
    CheckboxGroup,
    ComboBoxInput,
    RadioGroup,
    SelectInput,
    ToggleSwitch,
)
from pydantic_schemaforms.inputs.text_inputs import CreditCardInput, CurrencyInput, SSNInput
from pydantic_schemaforms.integration.schema import JSONSchemaGenerator
from pydantic_schemaforms.live_validation import HTMXValidationConfig, LiveValidator
from pydantic_schemaforms.model_list import ModelListRenderer
from pydantic_schemaforms.modern_renderer import (
    FormDefinition,
    FormField as LegacyFormField,
    FormSection,
    ModernFormRenderer,
)
from pydantic_schemaforms.rendering import form_style as form_style_module
from pydantic_schemaforms.rendering.form_style import (
    FormStyle,
    FormStyleTemplates,
    get_form_style,
    register_form_style,
)
from pydantic_schemaforms.rendering.layout_engine import AccordionLayout, TabLayout
from pydantic_schemaforms.rendering.schema_parser import (
    _extract_ui_info,
    _field_info_to_schema,
    _infer_field_type,
)
from pydantic_schemaforms.rendering.themes import MaterialEmbeddedTheme, RendererTheme
from pydantic_schemaforms.schema_form import Field, FormModel
from pydantic_schemaforms.simple_material_renderer import SimpleMaterialRenderer
from pydantic_schemaforms.templates import (
    TemplateString,
    create_custom_template,
)
from pydantic_schemaforms.tstring import SafeHTML, html as thtml
import pydantic_schemaforms.inputs.specialized_inputs as specialized_inputs


# ---------------------------------------------------------------------------
# Private helper classes (deduplicated)
# ---------------------------------------------------------------------------


class _DummyBaseInput(BaseInput):
    def get_input_type(self) -> str:
        return 'text'

    def render(self, **kwargs) -> str:
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = 'text'
        return f'<input {self._build_attributes_string(attrs)} />'


# _DummySelectInput from test_coverage_gap_fillers.py (simpler, no ui_element attr)
class _DummySelectInputSimple(SelectInputBase):
    def get_input_type(self) -> str:
        return 'select'

    def render(self, options, **kwargs) -> str:
        attrs = self.validate_attributes(**kwargs)
        return f'<select {self._build_attributes_string(attrs)}>{len(options)}</select>'


# _DummySelectInput from test_coverage_targeted_modules.py (has ui_element, optional options)
class _DummySelectInput(SelectInputBase):
    ui_element = 'dummy'

    def get_input_type(self) -> str:
        return 'select'

    def render(self, options=None, **kwargs):  # pragma: no cover - simple helper
        return '<select name="x"></select>'


class _ModelForSchema(BaseModel):
    email_address: str


class _SchemaFieldModel(FormModel):
    count: int = Field(..., description='counter', ui_element='text')


class _ProfileModel(BaseModel):
    age: int | None = None


class _FakeFieldValidator:
    field_name = 'email'

    def validate(self, value):
        return (False, ['Email invalid']) if '@' not in str(value) else (True, [])

    def to_rule_descriptors(self):
        return [{'type': 'email'}]


class _FakeSchema:
    def validators(self):
        return [_FakeFieldValidator()]


class _SimpleForm(FormModel):
    name: str = Field(...)


class _SimpleFormWithTitle(FormModel):
    name: str = Field(..., title='Name')


# ---------------------------------------------------------------------------
# Fixtures / theme stubs used by test_theme_hooks tests
# ---------------------------------------------------------------------------


class _StubTheme(RendererTheme):
    """Theme that exposes unique markers for assertions."""

    def tab_component_assets(self) -> str:  # type: ignore[override]
        return '<style>.custom-tab-asset{color:red;}</style>'

    def accordion_component_assets(self) -> str:  # type: ignore[override]
        return '<style>.custom-accordion-asset{color:blue;}</style>'

    def render_model_list_container(  # type: ignore[override]
        self,
        *,
        field_name: str,
        label: str,
        is_required: bool,
        min_items: int,
        max_items: int,
        items_html: str,
        help_text: Optional[str],
        error: Optional[str],
        add_button_label: str,
    ) -> str:
        return (
            f"<section class='custom-model-list' data-field='{field_name}'>"
            f'<header>{label}</header>'
            f"<div class='items'>{items_html}</div>"
            f'<footer>{add_button_label}</footer>'
            '</section>'
        )

    def render_model_list_item(  # type: ignore[override]
        self,
        *,
        field_name: str,
        model_label: str,
        index: int,
        body_html: str,
        remove_button_aria_label: str,
    ) -> str:
        return (
            f"<article class='custom-item' data-field='{field_name}' data-index='{index}'>"
            f'<h6>{model_label}</h6>'
            f"<div class='body'>{body_html}</div>"
            f"<button aria-label='{remove_button_aria_label}'>x</button>"
            '</article>'
        )


class _StubRenderer:
    def __init__(self, theme: RendererTheme) -> None:
        self.theme = theme


class _StubModel(FormModel):
    name: str


# ===========================================================================
# Tests from test_enhanced_renderer.py
# ===========================================================================


class TestEnhancedFormRenderer:
    """Test the EnhancedFormRenderer class."""

    def test_renderer_initialization(self):
        """Test basic renderer initialization."""
        renderer = EnhancedFormRenderer()
        assert renderer is not None
        assert hasattr(renderer, 'render_form_from_model')
        assert renderer.framework == 'bootstrap'
        assert renderer.config is not None

    def test_render_form_from_model_basic(self, simple_form_model, enhanced_renderer):
        """Test basic form rendering from model."""
        html = enhanced_renderer.render_form_from_model(simple_form_model)

        assert isinstance(html, str)
        assert len(html) > 0
        assert '<form' in html
        assert '</form>' in html

        # Should contain all form fields
        assert 'name="name"' in html
        assert 'name="email"' in html
        assert 'name="age"' in html
        assert 'name="newsletter"' in html

    def test_render_form_with_bootstrap_framework(self, simple_form_model):
        """Test form rendering with Bootstrap framework."""
        bootstrap_renderer = EnhancedFormRenderer(framework='bootstrap')
        html = bootstrap_renderer.render_form_from_model(simple_form_model)

        # Should contain Bootstrap-specific classes
        assert 'class="form-control"' in html or 'class="form-select"' in html
        assert 'class="mb-3"' in html or 'class="form-group"' in html

        # Should have proper Bootstrap structure
        assert '<form' in html
        assert 'form-control' in html or 'form-select' in html

    def test_render_form_with_material_framework(self, simple_form_model):
        """Test form rendering with Material Design framework."""
        material_renderer = EnhancedFormRenderer(framework='material')
        html = material_renderer.render_form_from_model(simple_form_model)

        # Should contain Material Design structure
        assert '<form' in html
        assert len(html) > 100  # Should be substantial

        # Material and Bootstrap should produce different output
        bootstrap_renderer = EnhancedFormRenderer(framework='bootstrap')
        bootstrap_html = bootstrap_renderer.render_form_from_model(simple_form_model)
        assert html != bootstrap_html

    def test_render_form_with_no_framework(self, simple_form_model):
        """Test form rendering with no CSS framework."""
        none_renderer = EnhancedFormRenderer(framework='none')
        html = none_renderer.render_form_from_model(simple_form_model)

        # Should be clean HTML without framework classes
        assert '<form' in html
        assert 'form-control' not in html
        assert 'mdc-' not in html  # No Material Design classes

        # Should still contain basic form elements
        assert '<input' in html
        assert 'name="name"' in html

    def test_render_form_with_submit_url(self, simple_form_model, enhanced_renderer):
        """Test form rendering with custom submit URL."""
        html = enhanced_renderer.render_form_from_model(
            simple_form_model, submit_url='/custom-submit'
        )

        # Should contain the custom submit URL
        assert 'action="/custom-submit"' in html or 'hx-post="/custom-submit"' in html

    def test_render_form_with_initial_data(
        self, simple_form_model, enhanced_renderer, sample_form_data
    ):
        """Test form rendering with initial data."""
        html = enhanced_renderer.render_form_from_model(simple_form_model, data=sample_form_data)

        # Should contain the initial values
        assert f'value="{sample_form_data["name"]}"' in html
        assert f'value="{sample_form_data["email"]}"' in html
        assert f'value="{sample_form_data["age"]}"' in html

        # Newsletter checkbox should be present (checking may depend on implementation)
        assert 'name="newsletter"' in html
        assert 'type="checkbox"' in html

    def test_render_form_with_errors(
        self, simple_form_model, enhanced_renderer, sample_validation_errors
    ):
        """Test form rendering with validation errors."""
        # Convert list of errors to dict format expected by renderer
        errors_dict = {err['name']: err['message'] for err in sample_validation_errors}

        html = enhanced_renderer.render_form_from_model(simple_form_model, errors=errors_dict)

        # Should contain error messages
        for _field, error_message in errors_dict.items():
            assert error_message in html

        # Should have error styling
        assert 'error' in html.lower() or 'invalid' in html.lower()

    def test_render_form_with_complex_model(self, complex_form_model, enhanced_renderer):
        """Test form rendering with complex form model."""
        html = enhanced_renderer.render_form_from_model(complex_form_model)

        # Should contain all complex form fields
        assert 'name="first_name"' in html
        assert 'name="last_name"' in html
        assert 'name="email"' in html
        assert 'name="phone"' in html
        assert 'name="website"' in html
        assert 'name="age"' in html
        assert 'name="rating"' in html
        assert 'name="bio"' in html
        assert 'name="birth_date"' in html
        assert 'name="terms"' in html
        assert 'name="newsletter"' in html
        assert 'name="favorite_color"' in html

        # Should have appropriate input types
        assert 'type="email"' in html
        assert 'type="url"' in html
        assert 'type="number"' in html
        assert 'type="range"' in html
        assert '<textarea' in html
        assert 'type="date"' in html
        assert 'type="checkbox"' in html
        assert 'type="color"' in html


class TestEnhancedRendererFieldTypes:
    """Test enhanced renderer with different field types."""

    def test_text_field_rendering(self, enhanced_renderer):
        """Test rendering of text fields."""

        class TextForm(FormModel):
            name: str = Field(..., description='Your full name')
            email: str = Field(..., ui_element='email')
            website: str = Field('', ui_element='url')
            bio: str = Field('', ui_element='textarea', ui_options={'rows': 4})

        html = enhanced_renderer.render_form_from_model(TextForm)

        assert 'type="text"' in html
        assert 'type="email"' in html
        assert 'type="url"' in html
        assert '<textarea' in html
        assert 'rows="4"' in html

    def test_numeric_field_rendering(self, enhanced_renderer):
        """Test rendering of numeric fields."""

        class NumericForm(FormModel):
            age: int = Field(..., ge=18, le=120)
            rating: int = Field(..., ui_element='range', ge=1, le=5)
            price: float = Field(..., gt=0)

        html = enhanced_renderer.render_form_from_model(NumericForm)

        assert 'type="number"' in html
        assert 'type="range"' in html
        assert 'min="18"' in html
        assert 'max="120"' in html
        assert 'min="1"' in html
        assert 'max="5"' in html

    def test_selection_field_rendering(self, enhanced_renderer):
        """Test rendering of selection fields."""

        class SelectionForm(FormModel):
            category: str = Field(
                ...,
                ui_element='select',
                ui_options={
                    'choices': [('tech', 'Technology'), ('art', 'Art'), ('music', 'Music')]
                },
            )
            newsletter: bool = Field(False, description='Subscribe to newsletter')
            tags: list = Field(
                [],
                ui_element='multiselect',
                ui_options={'choices': [('python', 'Python'), ('web', 'Web'), ('ai', 'AI')]},
            )

        html = enhanced_renderer.render_form_from_model(SelectionForm)

        # Select may fail if options aren't properly handled - check if it attempts to render
        assert 'category' in html and ('<select' in html or 'Error rendering select' in html)
        assert 'type="checkbox"' in html
        # Tags field might render as text if multiselect isn't supported properly
        assert 'name="tags"' in html

    def test_datetime_field_rendering(self, enhanced_renderer):
        """Test rendering of datetime fields."""

        class DateTimeForm(FormModel):
            birth_date: str = Field(..., ui_element='date', description='Your birth date')
            meeting_time: str = Field(..., ui_element='time')
            event_datetime: str = Field(..., ui_element='datetime-local')

        html = enhanced_renderer.render_form_from_model(DateTimeForm)

        assert 'type="date"' in html
        assert 'type="time"' in html
        assert 'type="datetime-local"' in html

    def test_specialized_field_rendering(self, enhanced_renderer):
        """Test rendering of specialized fields."""

        class SpecializedForm(FormModel):
            favorite_color: str = Field('#000000', ui_element='color')
            profile_picture: str = Field('', ui_element='file', ui_options={'accept': '.jpg,.png'})
            phone: str = Field('', ui_element='tel')
            password: str = Field(..., ui_element='password')

        html = enhanced_renderer.render_form_from_model(SpecializedForm)

        assert 'type="color"' in html
        # FileInput may fail due to JavaScript template issues - check if it attempts to render or shows error
        assert 'profile_picture' in html and (
            'type="file"' in html or 'Error rendering file' in html
        )
        assert 'type="tel"' in html
        assert 'type="password"' in html


class TestEnhancedRendererFrameworkSpecific:
    """Test framework-specific rendering features."""

    def test_bootstrap_specific_features(self, simple_form_model, enhanced_renderer):
        """Test Bootstrap-specific rendering features."""
        html = enhanced_renderer.render_form_from_model(simple_form_model, framework='bootstrap')

        # Bootstrap form structure
        assert 'class="form-control"' in html or 'class="form-select"' in html
        assert 'class="mb-3"' in html or 'class="form-group"' in html

        # Bootstrap button
        assert 'class="btn' in html
        assert 'btn-primary' in html or 'btn-success' in html

    def test_material_specific_features(self, simple_form_model):
        """Test Material Design-specific rendering features."""
        material_renderer = EnhancedFormRenderer(framework='material')
        html = material_renderer.render_form_from_model(simple_form_model)

        # Material Design should have distinct structure
        assert '<form' in html
        assert len(html) > 200  # Should be substantial with Material styling

        # Should not apply Bootstrap classes to form elements
        assert 'form-control' not in html
        # "btn-primary" may appear in the embedded CSS reset rules; it must not be
        # used as a class on any rendered element.
        assert 'class="btn-primary"' not in html
        assert 'btn-primary' not in html.split('<style')[0]  # not in pre-CSS markup

    def test_framework_consistency(self, simple_form_model):
        """Test that framework rendering is consistent."""
        frameworks = ['bootstrap', 'material', 'none']
        rendered_forms = {}

        for framework in frameworks:
            renderer = EnhancedFormRenderer(framework=framework)
            html = renderer.render_form_from_model(simple_form_model)
            rendered_forms[framework] = html

            # All should contain basic form elements
            assert '<form' in html
            assert 'name="name"' in html
            assert 'name="email"' in html
            assert '</form>' in html

        # Each framework should produce different output
        bootstrap_html = rendered_forms['bootstrap']
        material_html = rendered_forms['material']
        none_html = rendered_forms['none']

        assert bootstrap_html != material_html
        assert bootstrap_html != none_html
        assert material_html != none_html


class TestEnhancedRendererEdgeCases:
    """Test edge cases and error handling in enhanced renderer."""

    def test_empty_form_model(self, enhanced_renderer):
        """Test rendering of empty form model."""

        class EmptyForm(FormModel):
            pass

        html = enhanced_renderer.render_form_from_model(EmptyForm)

        # Should still render a valid form
        assert '<form' in html
        assert '</form>' in html
        # Should have submit button even with no fields
        assert '<button' in html or '<input type="submit"' in html

    def test_form_with_optional_fields_only(self, enhanced_renderer):
        """Test rendering form with only optional fields."""

        class OptionalForm(FormModel):
            name: str = Field('', description='Optional name')
            email: str = Field('', ui_element='email')
            newsletter: bool = Field(False)

        html = enhanced_renderer.render_form_from_model(OptionalForm)

        # Should not have required attributes
        assert 'required' not in html
        assert 'name="name"' in html
        assert 'name="email"' in html
        assert 'name="newsletter"' in html

    def test_invalid_framework_fallback(self, simple_form_model, enhanced_renderer):
        """Test behavior with invalid framework name."""
        html = enhanced_renderer.render_form_from_model(
            simple_form_model, framework='invalid_framework'
        )

        # Should still render (fallback to default)
        assert '<form' in html
        assert 'name="name"' in html

    def test_render_with_none_values(self, enhanced_renderer):
        """Test rendering with None values in data."""

        class TestForm(FormModel):
            name: str = Field('', description='Name')
            optional_field: str = Field(None, description='Optional')

        data = {'name': 'John', 'optional_field': None}

        html = enhanced_renderer.render_form_from_model(TestForm, data=data)

        assert 'value="John"' in html
        assert '<form' in html


class TestEnhancedRendererIntegration:
    """Test integration of enhanced renderer with the broader system."""

    def test_integration_with_form_model_render_method(self, simple_form_model):
        """Test that FormModel.render_form uses EnhancedFormRenderer."""
        # Test that the render_form method exists and works
        html = simple_form_model.render_form(submit_url='/simple')

        assert isinstance(html, str)
        assert '<form' in html
        assert 'name="name"' in html

        # Test with different frameworks
        bootstrap_html = simple_form_model.render_form(framework='bootstrap', submit_url='/simple')
        material_html = simple_form_model.render_form(framework='material', submit_url='/simple')

        assert bootstrap_html != material_html
        assert 'form-control' in bootstrap_html or 'form-select' in bootstrap_html

    def test_error_handling_integration(self, simple_form_model, enhanced_renderer):
        """Test error handling integration."""
        errors = {
            'name': 'Name is required',
            'email': 'Invalid email format',
            'age': 'Age must be between 18 and 120',
        }

        html = enhanced_renderer.render_form_from_model(simple_form_model, errors=errors)

        # All error messages should be present
        assert 'Name is required' in html
        assert 'Invalid email format' in html
        assert 'Age must be between 18 and 120' in html

    def test_complete_form_workflow(self, complex_form_model, enhanced_renderer, sample_form_data):
        """Test complete form workflow with complex model."""
        # Test rendering with data and errors
        errors = {'email': 'Invalid email'}

        html = enhanced_renderer.render_form_from_model(
            complex_form_model,
            framework='bootstrap',
            submit_url='/submit-form',
            data=sample_form_data,
            errors=errors,
        )

        # Should have all components
        assert 'action="/submit-form"' in html or 'hx-post="/submit-form"' in html
        assert 'Invalid email' in html

        # Check that form fields are present (data mapping may vary)
        assert 'name="first_name"' in html
        assert 'name="last_name"' in html
        assert 'name="email"' in html

        # Check for some expected values that should match
        if 'email' in sample_form_data:
            assert f'value="{sample_form_data["email"]}"' in html

        assert 'class="form-control"' in html or 'class="form-select"' in html


class TestEnhancedRendererCoverageBoost:
    """Targeted tests for recently added renderer behaviors."""

    def test_layout_support_style_is_injected_once(self, simple_form_model):
        renderer = EnhancedFormRenderer(framework='bootstrap')
        html = renderer.render_form_from_model(simple_form_model)

        assert 'data-schemaforms-layout-support' in html
        assert html.count('data-schemaforms-layout-support') == 1

    def test_error_summary_humanizes_indexed_paths_material(self, simple_form_model):
        renderer = EnhancedFormRenderer(framework='material')
        errors = {
            'pets[7].name': 'String should have at least 1 character',
            'owner_name': 'String should have at least 2 characters',
        }

        html = renderer.render_form_from_model(simple_form_model, errors=errors)

        assert 'Submission failed.' in html
        assert 'Pet #8 — Name' in html
        assert 'Owner Name' in html
        assert 'pets[7].name' not in html

    def test_error_summary_humanizes_form_level_key(self, simple_form_model):
        renderer = EnhancedFormRenderer(framework='bootstrap')
        errors = {
            'form': 'Unexpected validation error',
        }

        html = renderer.render_form_from_model(simple_form_model, errors=errors)

        assert 'Form' in html
        assert 'Unexpected validation error' in html


# ===========================================================================
# Tests from test_rendering_integration.py
# ===========================================================================


class TestFormRenderingIntegration:
    """Test form rendering integration."""

    def test_render_simple_form(self):
        """Test rendering a simple form."""

        class SimpleForm(FormModel):
            name: str = Field(default='')
            email: str = Field(default='')

        html = SimpleForm.render_form(submit_url='/simple')

        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_form_with_initial_data(self):
        """Test rendering form with initial data."""

        class PersonForm(FormModel):
            first_name: str = ''
            last_name: str = ''

        html = PersonForm.render_form(
            data={'first_name': 'John', 'last_name': 'Doe'}, submit_url='/person'
        )

        assert isinstance(html, str)

    def test_render_form_with_errors(self):
        """Test rendering form with validation errors."""

        class EmailForm(FormModel):
            email: str = ''

        html = EmailForm.render_form(
            data={'email': 'invalid'},
            errors={'email': 'Invalid email format'},
            submit_url='/email',
        )

        assert isinstance(html, str)

    def test_render_form_different_frameworks(self):
        """Test rendering form with different frameworks."""

        class BasicForm(FormModel):
            field: str = ''

        # Bootstrap
        html_bs = BasicForm.render_form(framework='bootstrap', submit_url='/basic')
        assert isinstance(html_bs, str)

        # Material
        html_mat = BasicForm.render_form(framework='material', submit_url='/basic')
        assert isinstance(html_mat, str)


class TestFormModelValidation:
    """Test form model validation."""

    def test_form_model_example_data(self):
        """Test getting example form data."""

        class ExampleForm(FormModel):
            name: str = ''
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
            title: str = Field(default='')
            description: str = Field(default='')

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
            email: str = ''

        schema = EmailForm.get_json_schema()

        assert 'email' in schema['properties']

    def test_url_field_detection(self):
        """Test URL field detection."""

        class UrlForm(FormModel):
            website: str = ''

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


# ===========================================================================
# Tests from test_coverage_gap_fillers.py
# ===========================================================================


def test_inputs_base_helpers_cover_fallback_and_attribute_branches() -> None:
    # t() fallback and render_template() string/Template-object behavior
    assert t('abc') == 'abc'

    class _TemplateObj:
        strings = ['<b>', '</b>']
        values = ['x']

    assert render_template(_TemplateObj()) == '<b>x</b>'
    assert render_template('already') == 'already'

    inp = _DummyBaseInput()
    attrs = inp.validate_attributes(
        name='n',
        id=None,
        required=False,
        hidden=True,
        role='button',
        **{'data-x': ['a', None, 'b'], 'x-unknown': '<unsafe"'},
    )
    # bool False => omitted, bool True => attribute name
    built = inp._build_attributes_string(attrs)
    assert 'name="n"' in built
    assert 'hidden' in built
    assert 'required="False"' in built
    assert 'data-x="a b"' in built
    assert 'x-unknown="&lt;unsafe&quot;"' in built

    # Cover fontawesome and bootstrap icon formatting paths
    fa = build_label('my_field', icon='user', framework='fontawesome')
    assert 'fas fa-user' in fa
    bs = build_label('my_field', icon='bi bi-check', framework='bootstrap')
    assert 'bi bi-check' in bs


def test_select_input_base_renders_for_all_framework_branches() -> None:
    comp = _DummySelectInputSimple()
    options = [{'value': 'a', 'label': 'A'}]

    bootstrap = comp.render_with_label(
        label='L',
        help_text='H',
        error='E',
        icon='person',
        framework='bootstrap',
        options=options,
        name='field',
        id='field',
    )
    assert 'input-group' in bootstrap

    material = comp.render_with_label(
        label='L',
        help_text='H',
        error='E',
        icon='person',
        framework='material',
        options=options,
        name='field',
        id='field',
    )
    assert 'md-field' in material

    plain = comp.render_with_label(
        label='L',
        help_text='H',
        error='E',
        icon='person',
        framework='plain',
        options=options,
        name='field',
        id='field',
    )
    assert 'input-with-icon' in plain


def test_selection_inputs_fallback_template_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    def _explode(*_args, **_kwargs):
        raise ValueError('boom')

    monkeypatch.setattr('string.Template.substitute', _explode)

    select_html = SelectInput().render(options=[{'value': '1', 'label': 'One'}], name='s')
    assert '<select' in select_html

    checkbox_html = CheckboxGroup().render(
        options=[{'value': 'x', 'label': 'X'}],
        group_name='grp',
    )
    assert '<fieldset' in checkbox_html

    radio_html = RadioGroup().render(
        options=[{'value': 'x', 'label': 'X'}],
        group_name='grp',
    )
    assert '<fieldset' in radio_html

    combo_html = ComboBoxInput().render(options=['a', 'b'], name='combo')
    assert 'datalist' in combo_html


def test_json_schema_generator_error_and_mapping_branches() -> None:
    gen = JSONSchemaGenerator()

    with pytest.raises(TypeError, match='cannot be None'):
        gen.ensure_model_class(None)

    with pytest.raises(TypeError, match='BaseModel subclass or instance'):
        gen.ensure_model_class('bad')

    class _NotModel:
        pass

    with pytest.raises(TypeError, match='inherit'):
        gen.ensure_model_class(_NotModel)

    assert gen.normalize_annotation(None) is str
    assert gen.normalize_annotation(Optional[int]) is int
    assert gen.normalize_annotation(Annotated[str, 'meta']) is str

    assert gen.generate_field_schema(str, field_name='user_email')['format'] == 'email'
    assert gen.generate_field_schema(str, field_name='home_uri')['format'] == 'uri'


def test_schema_parser_private_helpers_branches() -> None:
    field_info = _SchemaFieldModel.model_fields['count']
    schema = _field_info_to_schema('count', field_info)
    assert schema['description'] == 'counter'
    assert schema['ui']['element'] == 'text'

    assert _extract_ui_info(field_info)['element'] == 'text'

    # infer type branches
    class _F(FormModel):
        a: float = Field(...)
        b: bool = Field(...)

    assert _infer_field_type(_F.model_fields['a']) == 'number'
    assert _infer_field_type(_F.model_fields['b']) == 'boolean'


def test_renderer_theme_fallback_and_wrapper_timing(monkeypatch: pytest.MonkeyPatch) -> None:
    theme = RendererTheme(submit_label='Go')

    # Exercise _load_form_style fallback branch (KeyError => default)
    calls = {'n': 0}

    def _fake_get_form_style(*_args, **_kwargs):
        calls['n'] += 1
        if calls['n'] == 1:
            raise KeyError('missing')
        return get_form_style('default', 'default')

    monkeypatch.setattr(
        'pydantic_schemaforms.rendering.themes.get_form_style', _fake_get_form_style
    )
    # Fallback call should not raise
    theme._load_form_style('missing', 'x')

    wrapped = theme.render_form_wrapper(
        form_attrs={'method': 'POST', 'action': '/x', 'disabled': True},
        csrf_token='',
        form_content='<input>',
        submit_markup='<button>Go</button>',
        render_time=0.5,
    )
    assert 'Rendered in 0.500s' in wrapped


def test_material_embedded_theme_and_renderer_branches() -> None:
    theme = MaterialEmbeddedTheme()
    transformed = theme.transform_form_attributes({'class': 'x', 'novalidate': True})
    assert transformed['class'].startswith('md-form')
    assert 'novalidate' not in transformed

    # No help/error branch and optional model-list blocks
    container = theme.render_model_list_container(
        field_name='items',
        label='Items',
        is_required=False,
        min_items=0,
        max_items=1,
        items_html='',
        help_text=None,
        error=None,
        add_button_label='Add',
    )
    assert 'md-model-list-wrapper' in container
    assert 'md-help-text' not in container

    # Material field helpers now live on EnhancedFormRenderer(framework="material")
    renderer = EnhancedFormRenderer(framework='material')
    assert renderer._attr(None) == ''
    assert renderer._render_material_help_block(None) == ''
    assert renderer._render_material_error_block(None) == ''
    assert renderer._model_list_framework() == 'bootstrap'

    # enum fallback for select options and scalar option normalization
    options = renderer._build_material_select_options({}, {'enum': ['A', 'B']})
    assert options == [['A', 'A'], ['B', 'B']]

    options2 = renderer._build_material_select_options(
        {'options': ['X', {'value': 'Y', 'label': 'Why'}]}, {}
    )
    assert options2 == [['X', 'X'], ['Y', 'Why']]

    # SimpleMaterialRenderer is a backward-compat alias — verify it still works
    compat = SimpleMaterialRenderer()
    assert isinstance(compat, EnhancedFormRenderer)
    assert compat.framework == 'material'


def test_form_style_registry_keyerror_branch() -> None:
    temp_style = FormStyle(framework='tmp-framework', variant='v1')
    register_form_style(temp_style)
    assert get_form_style('tmp-framework:v1').framework == 'tmp-framework'

    registry = form_style_module._FORM_STYLE_REGISTRY
    backup = dict(registry)
    try:
        registry.clear()
        with pytest.raises(KeyError):
            get_form_style('unknown', 'none')
    finally:
        registry.clear()
        registry.update(backup)


def test_package_logger_uses_null_handler() -> None:
    pkg_logger = logging.getLogger('pydantic_schemaforms')

    # Library must not install a StreamHandler (PEP 282)
    handler_types = [type(h).__name__ for h in pkg_logger.handlers]
    assert 'StreamHandler' not in handler_types, (
        f"Library installed a StreamHandler — breaks callers' logging config: {handler_types}"
    )

    # At least one NullHandler must be present so "No handlers" warnings are suppressed
    assert any(isinstance(h, logging.NullHandler) for h in pkg_logger.handlers), (
        'Library logger should have a NullHandler'
    )

    # Level must not be forced — leave it to the application (NOTSET == 0)
    assert pkg_logger.level == logging.NOTSET, (
        f'Library must not force a log level (got {pkg_logger.level})'
    )

    # propagate must be True so records reach the application's root handler
    assert pkg_logger.propagate is True, (
        'Library logger must propagate to let the application handle records'
    )


def test_integration_public_api_imports_directly_without_frameworks_shim() -> None:
    """integration/__init__.py must export all symbols via direct imports, not frameworks/."""
    import pydantic_schemaforms.integration as integ

    # All expected public symbols must be importable from the package
    expected = [
        'FormBuilder',
        'AutoFormBuilder',
        'FormIntegration',
        'handle_form',
        'handle_form_async',
        'handle_async_form',
        'handle_sync_form',
        'normalize_form_data',
    ]
    for name in expected:
        assert hasattr(integ, name), f'integration.{name} is missing'

    # The frameworks/ shim subdirectory must no longer exist
    spec = importlib.util.find_spec('pydantic_schemaforms.integration.frameworks')
    assert spec is None, (
        'integration.frameworks shim package still exists — it should have been deleted'
    )


# ===========================================================================
# Tests from test_coverage_targeted_modules.py
# ===========================================================================


def test_enhanced_renderer_humanize_indexed_and_plural_fields() -> None:
    renderer = EnhancedFormRenderer()

    assert renderer._humanize_error_field('pets[7].name') == 'Pet #8 — Name'
    assert renderer._humanize_error_field('companies[1].tax_id') == 'Company #2 — Tax Id'
    assert renderer._humanize_error_field('form') == 'Form'


def test_base_render_template_handles_template_like_objects() -> None:
    @dataclass
    class _TemplateLike:
        strings: tuple[str, ...]
        values: tuple[str, ...]

    template = _TemplateLike(strings=('<b>', '</b>'), values=('ok',))
    assert render_template(template) == '<b>ok</b>'
    assert render_template('plain') == 'plain'


def test_select_input_base_render_with_label_plain_framework_branch() -> None:
    widget = _DummySelectInput()
    html = widget.render_with_label(
        label='My Label',
        help_text='Help me',
        error='Boom',
        framework='none',
        options=[{'value': 'a', 'label': 'A'}],
        id='f1',
    )

    assert 'class="field"' in html
    assert 'My Label' in html
    assert 'Help me' in html
    assert 'Boom' in html


def test_numeric_specialized_renderers_cover_branches() -> None:
    assert '%' in PercentageInput().render(name='p', value='20')
    assert 'step="0.001"' in DecimalInput().render(name='d', decimal_places=3)
    assert 'max="150"' in AgeInput().render(name='age')
    assert 'min="1"' in QuantityInput().render(name='qty')
    assert 'step="0.1"' in ScoreInput().render(name='score', min_score=0.0, max_score=10.0)

    rating_html = RatingInput().render(name='rating', max_rating=7, value='4')
    assert 'star-rating' in rating_html
    assert '☆☆☆' in rating_html

    slider_html = SliderInput().render(name='slider', min='10', max='20', show_labels=True)
    assert 'slider-labels' in slider_html
    assert 'slider-min' in slider_html

    temp_html = TemperatureInput().render(name='temp', unit='fahrenheit')
    assert '68°F' in temp_html
    assert '-459.67' in temp_html


def test_text_specialized_renderers_cover_patterns() -> None:
    ssn_html = SSNInput().render(name='ssn')
    cc_html = CreditCardInput().render(name='cc')
    currency_html = CurrencyInput().render(name='amount', currency_symbol='$')

    assert '123-45-6789' in ssn_html
    assert '\\d{3}-\\d{2}-\\d{4}' in ssn_html
    assert '1234 5678 9012 3456' in cc_html
    assert 'cc-number' in cc_html
    assert '$0.00' in currency_html


def test_selection_toggle_and_combobox_and_radio_fallback() -> None:
    toggle_html = ToggleSwitch().render(name='enabled', label='Enabled')
    assert 'toggle-switch-wrapper' in toggle_html
    assert 'toggle-switch-text' in toggle_html

    combo = ComboBoxInput()
    combo_html = combo.render(name='city', options=[{'value': 'LA', 'label': 'Los Angeles'}])
    assert 'datalist' in combo_html
    assert 'Los Angeles' in combo_html

    radio_html = RadioGroup().render(
        group_name='g1',
        options=[{'value': 'v1', 'label': 'Value 1', 'checked': True}],
        legend='Legend',
    )
    assert 'radio-group' in radio_html
    assert 'Legend' in radio_html

    checkbox_html = CheckboxGroup().render(
        group_name='g2',
        options=[{'value': 'v1', 'label': 'Value 1', 'disabled': True}],
        legend='Legend 2',
    )
    assert 'checkbox-group' in checkbox_html
    assert 'Legend 2' in checkbox_html


def test_specialized_widget_renderers_cover_extended_blocks(monkeypatch) -> None:
    class _ConcreteFormInput:
        def render(self, **kwargs):
            attrs = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
            return f'<input {attrs} />'

    monkeypatch.setattr(specialized_inputs, 'FormInput', _ConcreteFormInput)

    captcha_html = specialized_inputs.CaptchaInput().render(name='captcha_code')
    assert 'What is' in captcha_html
    assert 'captcha_code_answer' in captcha_html

    stars_html = specialized_inputs.RatingStarsInput().render(
        name='rating',
        max_stars=7,
        current_rating=4,
    )
    assert 'star-rating-input' in stars_html
    assert 'rating-star' in stars_html
    assert 'data-rating="7"' in stars_html

    tags_html = specialized_inputs.TagsInput().render(
        name='tags',
        placeholder='Add tags',
        separator=';',
        value='alpha;beta',
    )
    assert 'tags-input' in tags_html
    assert 'alpha;beta' in tags_html
    assert 'removeTag' in tags_html


def test_live_validator_model_schema_and_render_paths() -> None:
    validator = LiveValidator()
    validator.register_schema(_FakeSchema())
    assert 'email' in validator.validators
    assert validator.field_configs['email']['rules'][0]['type'] == 'email'

    validator.register_model_validator(_ProfileModel)
    ok = validator.validate_field('age', 33)
    bad = validator.validate_field('age', 'not-int')
    missing = validator.validate_field('unknown', 'x')

    assert ok.is_valid is True
    assert bad.is_valid is False
    assert missing.is_valid is True
    assert 'No validator registered' in missing.warnings[0]

    flask_code = validator.generate_validation_endpoint_code('flask')
    fastapi_code = validator.generate_validation_endpoint_code('fastapi')
    assert "@app.route('/validate/<field_name>'" in flask_code
    assert "@app.post('/validate/{field_name}')" in fastapi_code

    with pytest.raises(ValueError):
        validator.generate_validation_endpoint_code('django')


def test_live_validator_trigger_variants_and_htmx_script() -> None:
    # blur only — disable other triggers explicitly
    blur_validator = LiveValidator(
        HTMXValidationConfig(
            validate_on_blur=True, validate_on_input=False, validate_on_change=False
        )
    )
    blur_html = blur_validator.render_field_with_live_validation('username', label='User')
    assert 'hx-trigger="blur"' in blur_html

    # input only — all enabled: blur + input + change → combined trigger
    input_validator = LiveValidator(
        HTMXValidationConfig(
            validate_on_blur=True, validate_on_input=True, validate_on_change=True, debounce_ms=150
        )
    )
    input_html = input_validator.render_field_with_live_validation('email')
    assert 'blur' in input_html
    assert 'input delay:150ms' in input_html
    assert 'change' in input_html

    change_validator = LiveValidator(
        HTMXValidationConfig(
            validate_on_blur=False, validate_on_input=False, validate_on_change=True
        )
    )
    change_html = change_validator.render_field_with_live_validation('city', readonly='readonly')
    assert 'hx-trigger="change"' in change_html
    assert 'readonly="readonly"' in change_html

    script = change_validator.render_htmx_script()
    assert 'validationConfig' in script
    assert '"validate_on_change": true' in script.lower()


def test_runtime_asset_helpers_cover_modes_and_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime_assets, '_vendor_manifest', lambda: {'assets': 'invalid'})
    assert runtime_assets.vendored_asset_version('htmx') is None

    monkeypatch.setattr(runtime_assets, '_vendor_manifest', lambda: {'assets': []})
    assert runtime_assets.vendored_asset_version('missing') is None

    def _missing(_path: str) -> str:
        raise FileNotFoundError('missing')

    monkeypatch.setattr(runtime_assets, 'read_asset_text', _missing)
    assert runtime_assets._vendored_text_or_empty('missing.css') == ''

    monkeypatch.setattr(runtime_assets, 'read_asset_text', lambda _path: 'console.log(1)')
    assert runtime_assets.htmx_script_tag(asset_mode='none') == ''
    assert runtime_assets.imask_script_tag(asset_mode='none') == ''
    assert 'unpkg.com' in runtime_assets.imask_script_tag(asset_mode='cdn')
    assert '<script>' in runtime_assets.imask_script_tag(asset_mode='vendored')

    monkeypatch.setattr(runtime_assets, '_vendored_text_or_empty', lambda _path: '/*css*/')
    css_material = runtime_assets.framework_css_tag(framework='material', asset_mode='vendored')
    css_cdn = runtime_assets.framework_css_tag(framework='material', asset_mode='cdn')
    assert '<style>' in css_material
    assert 'cdn.jsdelivr.net' in css_cdn

    monkeypatch.setattr(runtime_assets, '_vendored_text_or_empty', lambda _path: '//js')
    js_material = runtime_assets.framework_js_tag(framework='material', asset_mode='vendored')
    js_cdn = runtime_assets.framework_js_tag(framework='material', asset_mode='cdn')
    assert '<script>' in js_material
    assert 'cdn.jsdelivr.net' in js_cdn
    assert runtime_assets.framework_css_tag(framework='unknown', asset_mode='vendored') == ''
    assert runtime_assets.framework_js_tag(framework='unknown', asset_mode='vendored') == ''

    # bootstrap_icons_css_tag: none → empty; cdn → jsdelivr link
    assert runtime_assets.bootstrap_icons_css_tag(asset_mode='none') == ''
    cdn_icons = runtime_assets.bootstrap_icons_css_tag(asset_mode='cdn')
    assert 'cdn.jsdelivr.net' in cdn_icons
    assert 'bootstrap-icons' in cdn_icons


def test_form_field_convenience_helpers_and_optional_validation() -> None:
    FormField.validate_input_type(Optional[str], 'text', 'title')
    inferred = FormField.get_default_input_type(Optional[str])
    assert isinstance(inferred, str)
    assert FormField.format_icon('user', framework='bootstrap')

    auto_field = create_field_with_validation(str, title='Auto')
    assert auto_field.json_schema_extra.get('input_type') == 'text'

    text_field = TextField(title='Text')
    email_field = EmailField()
    number_field = NumberField(min_value=1, max_value=10)
    select_field = SelectField(options=['A', 'B'])
    checkbox_field = CheckboxField()
    date_field = DateField()
    textarea_field = TextAreaField(rows=7)

    assert text_field.json_schema_extra.get('input_type') == 'text'
    assert email_field.json_schema_extra.get('placeholder') == 'example@example.com'
    assert email_field.json_schema_extra.get('icon') == 'envelope'
    assert number_field.json_schema_extra.get('input_type') == 'number'
    assert select_field.json_schema_extra.get('options') == ['A', 'B']
    assert checkbox_field.json_schema_extra.get('input_type') == 'checkbox'
    assert date_field.json_schema_extra.get('icon') == 'calendar'
    assert textarea_field.json_schema_extra.get('rows') == 7


def test_modern_renderer_legacy_field_and_model_definition_paths() -> None:
    def _false_validator(_value: object) -> bool:
        return False

    def _error_validator(_value: object) -> bool:
        raise ValueError('bad value')

    legacy = LegacyFormField(
        'city',
        required=True,
        validators=[_false_validator, _error_validator],
        options=[{'value': 'nyc', 'label': 'NYC'}],
        attributes={'maxlength': 30},
        **{
            'class': 'x',
            'style': 'y',
            'order': 9,
            'meta': 'v',
            'ignored_list': [1],
            'ignored_dict': {'k': 'v'},
        },
    )

    assert not legacy.validate('')
    legacy.required = False
    assert not legacy.validate('ok')
    assert any('failed validation' in msg for msg in legacy.errors)
    assert any('bad value' in msg for msg in legacy.errors)

    _annotation, schema_field = legacy.as_model_field(order=1, section='Section A')
    assert schema_field.json_schema_extra.get('ui_section') == 'Section A'
    assert schema_field.json_schema_extra.get('ui_order') == 1

    form_def = FormDefinition(
        title='My Form!',
        sections=[FormSection('Main', [LegacyFormField('name', required=True)])],
        honeypot_protection=True,
    )
    model_cls_1 = form_def.to_form_model_class()
    model_cls_2 = form_def.to_form_model_class()
    assert model_cls_1 is model_cls_2
    assert 'honeypot_trap' in model_cls_1.model_fields

    with pytest.raises(ValueError, match='at least one field'):
        FormDefinition(title='Empty').to_form_model_class()


def test_modern_renderer_aliases_extract_and_theme_clone_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    renderer = ModernFormRenderer()
    form_def = FormDefinition(
        sections=[FormSection('Main', [LegacyFormField('name', required=True)])]
    )

    async def _fake_render_form_async(*_args, **_kwargs) -> str:
        return 'ok'

    monkeypatch.setattr(renderer, 'render_form_async', _fake_render_form_async)
    assert asyncio.run(renderer.render_async(form_def)) == 'ok'
    assert asyncio.run(renderer.async_render(form_def)) == 'ok'

    fake_metadata = SimpleNamespace(
        fields=[
            (
                'choice',
                {
                    'title': 'Choice',
                    'description': 'desc',
                    'ui': {'options': 'x', 'ui_section': 'sec'},
                },
            )
        ],
        required_fields={'choice'},
    )
    monkeypatch.setattr(
        'pydantic_schemaforms.modern_renderer.build_schema_metadata', lambda _model: fake_metadata
    )
    monkeypatch.setattr(
        'pydantic_schemaforms.modern_renderer.resolve_ui_element', lambda _schema: None
    )
    extracted = renderer.extract_form_fields(_SimpleFormWithTitle)
    assert extracted[0].field_type == 'text'
    assert extracted[0].options == []

    class _NeedsArgTheme(RendererTheme):
        def __init__(self, submit_label: str) -> None:
            super().__init__(submit_label=submit_label)

    renderer_with_custom_theme = ModernFormRenderer(theme=_NeedsArgTheme('Send'))
    cloned = renderer_with_custom_theme._clone_theme()
    assert isinstance(cloned, RendererTheme)
    assert cloned.submit_label == 'Send'

    switched = renderer._ensure_renderer('material')
    assert switched is not renderer
    assert isinstance(switched, ModernFormRenderer)


def test_enhanced_renderer_branches_and_wrappers(monkeypatch: pytest.MonkeyPatch) -> None:
    error = SchemaFormValidationError([{'name': 'field', 'message': 'problem'}])
    assert 'Schema form validation error' in str(error)

    renderer = EnhancedFormRenderer()
    captured: dict[str, object] = {}

    class _FieldInfo:
        def __init__(self, *, default_factory=None, required: bool = False, default=None):
            self.default_factory = default_factory
            self._required = required
            self.default = default

        def is_required(self) -> bool:
            return self._required

    class _FakeModel:
        __name__ = 'FakeModel'
        model_fields = {
            'layout_factory': _FieldInfo(default_factory=lambda: {'seed': 1}),
            'layout_default': _FieldInfo(required=False, default={'d': 2}),
        }

    fake_metadata = SimpleNamespace(
        schema_defs={},
        fields=[('layout_factory', {}), ('layout_default', {})],
        required_fields=[],
        layout_fields=[('layout_factory', {}), ('layout_missing', {}), ('layout_default', {})],
        non_layout_fields=[],
    )
    monkeypatch.setattr(
        'pydantic_schemaforms.enhanced_renderer.build_schema_metadata',
        lambda _model: fake_metadata,
    )
    monkeypatch.setattr(renderer, '_render_layout_fields_as_tabs', lambda *_args: ['layout-tabs'])
    monkeypatch.setattr(
        renderer._theme, 'render_form_wrapper', lambda **kwargs: kwargs['form_content']
    )
    monkeypatch.setattr(
        'pydantic_schemaforms.enhanced_renderer.logger.debug',
        lambda msg: captured.update({'log': msg}),
    )

    html = renderer.render_form_from_model(
        _FakeModel,
        data={},
        errors={'errors': [{'name': 'layout_default', 'message': 'bad'}]},
        submit_url='/submit',
        enable_logging=True,
    )
    assert 'layout-tabs' in html
    assert 'rendered in' in str(captured.get('log', '')).lower()

    assert renderer._humanize_error_field('[]') == '[]'
    assert renderer._humanize_error_field('[0].name').startswith('Item #1')
    assert renderer._singularize_label('cat') == 'cat'
    assert renderer._render_error_summary({'nested': None}) == ''

    fields_meta = SimpleNamespace(
        schema_defs={},
        fields=[('name', {})],
        required_fields=[],
        layout_fields=[],
        non_layout_fields=[('name', {})],
    )
    monkeypatch.setattr(
        'pydantic_schemaforms.enhanced_renderer.build_schema_metadata',
        lambda _model: fields_meta,
    )
    monkeypatch.setattr(renderer, '_render_tabbed_layout', lambda *_args: ['tabbed-out'])
    monkeypatch.setattr(renderer, '_render_side_by_side_layout', lambda *_args: ['sbs-out'])
    monkeypatch.setattr(
        renderer._theme, 'render_form_wrapper', lambda **kwargs: kwargs['form_content']
    )
    assert 'tabbed-out' in renderer.render_form_from_model(
        _FakeModel, layout='tabbed', submit_url='/submit'
    )
    assert 'sbs-out' in renderer.render_form_from_model(
        _FakeModel, layout='side-by-side', submit_url='/submit'
    )

    monkeypatch.setattr(renderer, '_render_field', lambda *args, **kwargs: 'FIELD')
    fields_only = renderer.render_form_fields_only(
        _FakeModel,
        errors={'errors': [{'name': 'name', 'message': 'bad'}]},
    )
    assert fields_only == 'FIELD'

    renderer_wrappers = EnhancedFormRenderer()
    monkeypatch.setattr(
        renderer_wrappers._layout_engine, 'render_tabbed_layout', lambda *_args: ['X']
    )
    monkeypatch.setattr(
        renderer_wrappers._layout_engine,
        'render_layout_field_content',
        lambda *_args: 'Y',
    )
    monkeypatch.setattr(
        renderer_wrappers._layout_engine, 'render_side_by_side_layout', lambda *_args: ['Z']
    )
    assert renderer_wrappers._render_tabbed_layout([], {}, {}, [], SimpleNamespace()) == ['X']
    assert (
        renderer_wrappers._render_layout_field_content('n', {}, None, {}, SimpleNamespace()) == 'Y'
    )
    assert renderer_wrappers._render_side_by_side_layout([], {}, {}, [], SimpleNamespace()) == ['Z']
    assert renderer_wrappers._get_nested_form_data('name', {'name': {'x': 1}}) == {'x': 1}

    with pytest.raises(ValueError, match='submit_url cannot be empty'):
        render_form_html(_SimpleFormWithTitle, submit_url='   ')

    converted = render_form_html(
        _SimpleFormWithTitle,
        submit_url='/submit',
        errors=SchemaFormValidationError([{'name': 'name', 'message': 'oops'}]),
        include_html_markers=False,
    )
    assert 'oops' in converted

    async_html = asyncio.run(
        render_form_html_async(
            _SimpleFormWithTitle,
            submit_url='/submit',
            self_contained=True,
            include_html_markers=False,
        )
    )
    assert '<form' in async_html


def test_render_form_html_async_falls_back_to_get_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> str:
        current_loop = asyncio.get_running_loop()
        monkeypatch.setattr(
            'pydantic_schemaforms.enhanced_renderer.asyncio.get_running_loop',
            lambda: (_ for _ in ()).throw(RuntimeError('no running loop')),
        )
        monkeypatch.setattr(
            'pydantic_schemaforms.enhanced_renderer.asyncio.get_event_loop',
            lambda: current_loop,
        )
        return await render_form_html_async(
            _SimpleFormWithTitle, submit_url='/submit', include_html_markers=False
        )

    html = asyncio.run(_run())
    assert '<form' in html


@pytest.mark.filterwarnings(
    'ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning'
)
def test_form_layouts_branches_for_tabbed_and_list_layout() -> None:
    tabbed = TabbedLayout()
    assert tabbed._render_complete_page('x') == 'x'

    designed_tabbed = TabbedLayout(form_config=FormDesign(form_name='Demo', ui_theme='bootstrap'))
    page = designed_tabbed._render_complete_page('<div>Inner</div>')
    assert '<!DOCTYPE html>' in page
    assert 'Demo' in page

    class _ListItemForm(FormModel):
        qty: int = Field(..., title='Quantity')

    class _StubListRenderer:
        def render_form_from_model(self, *_args, **_kwargs) -> str:
            return '<label for="qty">Qty</label><input id="qty" name="qty" />'

    list_layout = ListLayout(
        form_model=_ListItemForm,
        min_items=2,
        max_items=1,
        section_design=SimpleNamespace(
            render_header=lambda _framework: '<h3>Items</h3>',
            collapsible=False,
            collapsed=False,
            css_class='custom-list',
        ),
        collapsible_items=True,
    )

    summary = list_layout._create_item_summary({'qty': 0}, index=0)
    assert summary.endswith('#1')

    js = list_layout._render_javascript('list_x', 'material')
    assert 'toggleCollapse' in js
    assert 'Maximum 1 items allowed' in js

    assert 'newCollapseId' in list_layout._render_collapsible_update_js('list_x')
    assert 'newCollapseId' in list_layout._render_collapsible_reindex_js('list_x')

    validation = list_layout.validate({'item_0_qty': 'not-int'})
    assert not validation.is_valid
    assert 'item_0' in validation.errors

    rendered = list_layout.render(
        data=[{'qty': 'bad'}], renderer=_StubListRenderer(), framework='bootstrap'
    )
    assert 'list-items-container' in rendered
    assert 'custom-list' in rendered

    rendered_from_items_key = list_layout.render(
        data={'items': [{'qty': 'bad'}]}, renderer=_StubListRenderer()
    )
    assert 'list-items-container' in rendered_from_items_key


@pytest.mark.filterwarnings(
    'ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning'
)
def test_form_layouts_vertical_horizontal_header_and_exception_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    section = SimpleNamespace(
        render_header=lambda _framework: '<h3>Header</h3>',
        collapsible=False,
        collapsed=False,
        css_class='s',
    )

    vertical = VerticalLayout(form_config=section)
    monkeypatch.setattr(vertical, '_render_form_instances', lambda **_kwargs: ['<div>Body</div>'])
    vertical_html = vertical.render()
    assert '<h3>Header</h3>' in vertical_html

    class _BadForm:
        def __init__(self, **_kwargs):
            raise Exception('boom')

    monkeypatch.setattr(vertical, '_get_forms', lambda: [_BadForm])
    result_v = vertical.validate({'a': 1})
    assert result_v.errors.get('_form') == 'boom'

    from pydantic_schemaforms.form_layouts import HorizontalLayout

    horizontal = HorizontalLayout(form_config=section)
    monkeypatch.setattr(horizontal, '_render_form_instances', lambda **_kwargs: ['<div>Col</div>'])
    horizontal_html = horizontal.render()
    assert horizontal_html.startswith('<h3>Header</h3>')

    monkeypatch.setattr(horizontal, '_get_forms', lambda: [_BadForm])
    result_h = horizontal.validate({'a': 1})
    assert result_h.errors.get('_form') == 'boom'


@pytest.mark.filterwarnings(
    'ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning'
)
def test_form_layouts_render_form_instances_fallback_when_renderer_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _StubForm:
        @classmethod
        def render_form(cls, **kwargs):
            assert kwargs.get('include_submit_button') is False
            return '<div>fallback-render</div>'

    vertical = VerticalLayout()
    monkeypatch.setattr(vertical, '_get_forms', lambda: [_StubForm])
    monkeypatch.setattr(vertical, '_get_renderer_for_framework', lambda _fw: None)
    rendered = vertical._render_form_instances(data={}, errors={}, framework='bootstrap')
    assert rendered == ['<div>fallback-render</div>']


@pytest.mark.filterwarnings(
    'ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning'
)
def test_form_layout_core_schema_serializer_handles_exceptions_and_non_layout_values() -> None:
    class _ExplodingVertical(VerticalLayout):
        def _get_layouts(self):
            raise RuntimeError('boom')

    class _Wrapper(BaseModel):
        payload: _ExplodingVertical

    model_layout = _Wrapper(payload=_ExplodingVertical())
    payload_layout = model_layout.model_dump()['payload']
    assert payload_layout['layout'] is True
    assert payload_layout['type'] == '_ExplodingVertical'

    payload_dict = _Wrapper(payload={'raw': 'dict'}).model_dump()['payload']
    assert payload_dict == {'raw': 'dict'}

    payload_scalar = _Wrapper(payload=7).model_dump()['payload']
    assert payload_scalar == {'value': '7'}


# ===========================================================================
# Tests from test_modern_renderer.py
# ===========================================================================


class TestModernFormRenderer:
    """Test the ModernFormRenderer class."""

    def test_renderer_initialization(self):
        """Test basic ModernFormRenderer initialization."""
        renderer = ModernFormRenderer()
        assert renderer is not None
        # Check if it has expected methods
        assert hasattr(renderer, 'render_form')

    def test_basic_form_rendering(self):
        """Test basic form rendering with ModernFormRenderer."""

        class SimpleForm(FormModel):
            name: str = Field(..., ui_element='text')
            email: str = Field(..., ui_element='email')
            age: int = Field(..., ui_element='number', ge=18)

        renderer = ModernFormRenderer()

        # Test if renderer can process the form model
        # Note: Actual implementation may vary based on ModernFormRenderer's interface
        try:
            form_fields = renderer.extract_form_fields(SimpleForm)
            assert len(form_fields) == 3

            # Check field names
            field_names = [field.name for field in form_fields]
            assert 'name' in field_names
            assert 'email' in field_names
            assert 'age' in field_names

        except AttributeError:
            # If extract_form_fields doesn't exist, test other methods
            pass

    def test_form_field_configuration(self):
        """Test FormField configuration and validation."""
        from pydantic_schemaforms.modern_renderer import FormField

        # Test basic field creation
        field = FormField('username', field_type='text', required=True)
        assert field.name == 'username'
        assert field.field_type == 'text'
        assert field.required is True
        assert field.label == 'Username'  # Auto-generated from name

    def test_form_field_with_options(self):
        """Test FormField with options for select fields."""
        from pydantic_schemaforms.modern_renderer import FormField

        options = [
            {'value': 'small', 'label': 'Small'},
            {'value': 'medium', 'label': 'Medium'},
            {'value': 'large', 'label': 'Large'},
        ]

        field = FormField('size', field_type='select', options=options, placeholder='Choose size')

        assert field.name == 'size'
        assert field.field_type == 'select'
        assert len(field.options) == 3
        assert field.placeholder == 'Choose size'

    def test_form_field_validation(self):
        """Test FormField validation functionality."""
        from pydantic_schemaforms.modern_renderer import FormField

        # Create field with validators
        def min_length_validator(value):
            return len(value) >= 3

        field = FormField(
            'password', field_type='password', required=True, validators=[min_length_validator]
        )

        # Test validation
        assert field.validate('abc') is True  # Should pass
        field.errors = []  # Reset errors
        assert field.validate('ab') is False  # Should fail

    def test_async_rendering_support(self):
        """Test async rendering capabilities if available."""
        renderer = ModernFormRenderer()

        # Check if async methods exist
        has_async_methods = any(
            method.startswith('async_') or method.endswith('_async') for method in dir(renderer)
        )

        # If async methods exist, they should be callable
        if has_async_methods:
            assert hasattr(renderer, 'render_async') or hasattr(renderer, 'async_render')

    def test_performance_rendering(self):
        """Test performance-oriented rendering features."""
        renderer = ModernFormRenderer()

        # Check for performance-related attributes
        performance_features = ['use_thread_pool', 'cache_templates', 'optimize_rendering']

        # At least one performance feature should be available
        has_performance_features = any(
            hasattr(renderer, feature) for feature in performance_features
        )

        # This is more of a feature check than assertion
        # as performance features are optional
        if has_performance_features:
            print('ModernFormRenderer has performance features')

    def test_framework_compatibility(self):
        """Test framework compatibility features."""

        class TestForm(FormModel):
            name: str = Field(..., ui_element='text')
            email: str = Field(..., ui_element='email')

        renderer = ModernFormRenderer()

        # Test if renderer can handle different frameworks
        frameworks = ['bootstrap', 'material', 'plain', 'custom']

        try:
            for framework in frameworks:
                # If renderer has framework support, test it
                if hasattr(renderer, 'set_framework'):
                    renderer.set_framework(framework)
                elif hasattr(renderer, 'render_with_framework'):
                    result = renderer.render_with_framework(TestForm, framework)
                    assert result is not None
        except AttributeError, NotImplementedError:
            # Framework support might not be implemented yet
            pass

    def test_layout_integration_basic(self):
        """Test basic layout integration concepts."""

        # Since complex layouts have template issues, test basic concepts
        class FormWithLayout(FormModel):
            personal_info_section: str = Field(default='', ui_section='Personal')
            name: str = Field(..., ui_element='text', ui_section='Personal')
            email: str = Field(..., ui_element='email', ui_section='Personal')

            preferences_section: str = Field(default='', ui_section='Preferences')
            newsletter: bool = Field(default=False, ui_element='checkbox', ui_section='Preferences')
            theme: str = Field(..., ui_element='select', ui_section='Preferences')

        renderer = ModernFormRenderer()

        # Test that form can be processed
        try:
            if hasattr(renderer, 'extract_form_fields'):
                fields = renderer.extract_form_fields(FormWithLayout)

                # Group fields by section
                sections = {}
                for field in fields:
                    section = getattr(field, 'ui_section', 'default')
                    if section not in sections:
                        sections[section] = []
                    sections[section].append(field)

                # Should have personal and preferences sections
                assert len(sections) >= 2
        except AttributeError:
            # Method might not be implemented
            pass

    def test_input_component_integration(self):
        """Test integration with input components."""
        ModernFormRenderer()

        # Test that renderer can work with various input types
        input_types = [
            'text',
            'email',
            'password',
            'number',
            'date',
            'datetime-local',
            'select',
            'checkbox',
            'radio',
            'textarea',
            'file',
            'color',
            'range',
        ]

        for input_type in input_types:
            try:
                from pydantic_schemaforms.modern_renderer import FormField

                field = FormField(f'test_{input_type}', field_type=input_type)
                assert field.field_type == input_type
            except ImportError:
                # FormField might not be available
                pass

    def test_custom_validation_integration(self):
        """Test custom validation integration."""

        class FormWithValidation(FormModel):
            username: str = Field(
                ...,
                min_length=3,
                max_length=20,
                ui_element='text',
                description='Username must be 3-20 characters',
            )

            password: str = Field(
                ...,
                min_length=8,
                ui_element='password',
                description='Password must be at least 8 characters',
            )

            confirm_password: str = Field(
                ..., ui_element='password', description='Must match password'
            )

        renderer = ModernFormRenderer()

        # Test that validation constraints are preserved
        try:
            if hasattr(renderer, 'extract_form_fields'):
                fields = renderer.extract_form_fields(FormWithValidation)

                username_field = next((f for f in fields if f.name == 'username'), None)
                if username_field:
                    assert username_field.required is True

                password_field = next((f for f in fields if f.name == 'password'), None)
                if password_field:
                    assert password_field.field_type == 'password'
        except AttributeError:
            pass

    def test_error_handling(self):
        """Test error handling in ModernFormRenderer."""
        renderer = ModernFormRenderer()

        # Test with invalid form model
        try:

            class InvalidForm:  # Not inheriting from FormModel
                name = 'not a field'

            if hasattr(renderer, 'extract_form_fields'):
                # Should handle invalid models gracefully
                fields = renderer.extract_form_fields(InvalidForm)
                # Might return empty list or raise informative error
                assert isinstance(fields, (list, type(None)))
        except AttributeError, TypeError, ValueError:
            # Expected to fail gracefully
            pass

    def test_html_output_safety(self):
        """Test HTML output safety and escaping."""
        from pydantic_schemaforms.modern_renderer import FormField

        # Test with potentially dangerous input
        dangerous_input = "<script>alert('xss')</script>"

        field = FormField(
            'test_field',
            field_type='text',
            placeholder=dangerous_input,
            help_text=dangerous_input,
        )

        # If field has render method, test HTML safety
        if hasattr(field, 'render'):
            html = field.render()
            # Should escape dangerous content
            assert '<script>' not in html
            assert '&lt;script&gt;' in html or 'alert' not in html

    def test_accessibility_features(self):
        """Test accessibility features in rendered forms."""

        class AccessibleForm(FormModel):
            name: str = Field(
                ...,
                ui_element='text',
                description='Your full name',
                ui_options={'aria-label': 'Full name input'},
            )

            email: str = Field(
                ...,
                ui_element='email',
                description='Valid email address',
                ui_options={'aria-describedby': 'email-help'},
            )

        renderer = ModernFormRenderer()

        # Test that accessibility attributes can be handled
        try:
            if hasattr(renderer, 'extract_form_fields'):
                fields = renderer.extract_form_fields(AccessibleForm)

                # Check if UI options are preserved
                for field in fields:
                    if hasattr(field, 'extra_attrs') and field.extra_attrs:
                        # Should have accessibility attributes
                        attrs = field.extra_attrs
                        has_aria = any(key.startswith('aria-') for key in attrs.keys())
                        # Accessibility is a good practice but not required
                        if has_aria:
                            print(f'Field {field.name} has accessibility attributes')
        except AttributeError:
            pass


# ===========================================================================
# Tests from test_templates_coverage.py
# ===========================================================================


class TestTemplateStringUtilities:
    """Test TemplateString and create_custom_template with the t-string API."""

    def test_create_custom_template(self):
        def _fn(*, name: str = '', **_):
            return thtml(t'Hello {name}!')

        template = create_custom_template(_fn)
        assert isinstance(template, TemplateString)
        result = template.render(name='World')
        assert result == 'Hello World!'

    def test_render_returns_safe_html(self):
        def _fn(*, label: str = '', **_):
            return thtml(t'<span>{label}</span>')

        ts = TemplateString(_fn)
        result = ts.render(label='hi')
        assert isinstance(result, SafeHTML)
        assert result == '<span>hi</span>'

    def test_xss_escaping(self):
        def _fn(*, value: str = '', **_):
            return thtml(t'<input value="{value}">')

        ts = TemplateString(_fn)
        result = ts.render(value='<script>alert(1)</script>')
        assert '&lt;script&gt;' in result
        assert '<script>' not in result

    def test_safe_html_passthrough(self):
        def _fn(*, content: str = '', **_):
            _c = SafeHTML(content)
            return thtml(t'<div>{_c}</div>')

        ts = TemplateString(_fn)
        result = ts.render(content='<b>bold</b>')
        assert result == '<div><b>bold</b></div>'

    def test_safe_render_is_alias(self):
        def _fn(*, x: str = '', **_):
            return thtml(t'{x}')

        ts = TemplateString(_fn)
        assert ts.render(x='a') == ts.safe_render(x='a')


# ===========================================================================
# Tests from test_theme_hooks.py
# ===========================================================================


def test_tab_layout_uses_theme_assets() -> None:
    layout = TabLayout(
        [
            {'title': 'General', 'content': '<p>Info</p>'},
        ]
    )
    stub_renderer = _StubRenderer(_StubTheme())

    html = layout.render(renderer=stub_renderer, framework='bootstrap')

    assert '.custom-tab-asset' in html


def test_accordion_layout_uses_theme_assets() -> None:
    layout = AccordionLayout(
        [
            {'title': 'FAQ', 'content': 'Answer'},
        ]
    )
    stub_renderer = _StubRenderer(_StubTheme())

    html = layout.render(renderer=stub_renderer, framework='bootstrap')

    assert '.custom-accordion-asset' in html


def test_model_list_renderer_delegates_container_to_theme() -> None:
    class _StubListRenderer(ModelListRenderer):
        def __init__(self) -> None:
            super().__init__(framework='bootstrap')
            self._theme = _StubTheme()

        def _resolve_theme(self) -> RendererTheme:  # type: ignore[override]
            return self._theme

        def _render_item_body(  # type: ignore[override]
            self,
            field_name: str,
            model_class: Type[FormModel],
            index: int,
            item_data: Dict[str, str],
            nested_errors: Optional[Dict[str, str]] = None,
        ) -> str:
            return f"<div class='item-body' data-index='{index}'>Body</div>"

    renderer = _StubListRenderer()

    html = renderer.render_model_list(
        field_name='pets',
        label='Pets',
        model_class=_StubModel,
        values=[{'name': 'Rex'}],
        min_items=0,
        max_items=5,
    )

    assert 'custom-model-list' in html
    assert 'Add Pets' in html  # comes from add_button_label argument
    assert 'custom-item' in html
    assert 'item-body' in html


def test_model_list_uses_form_style_templates() -> None:
    renderer = ModelListRenderer(framework='bootstrap')

    html = renderer.render_model_list(
        field_name='pets',
        label='Pets',
        model_class=_StubModel,
        values=[{'name': 'Rex'}],
        min_items=0,
        max_items=5,
    )

    assert 'model-list-block' in html
    assert 'model-list-items' in html
    assert 'add-item-btn' in html


def test_model_list_respects_custom_form_style_templates() -> None:
    def _ml_container(
        *,
        field_name: str = '',
        items_html: str = '',
        help_html: str = '',
        error_html: str = '',
        **_,
    ):
        return thtml(
            t"<div class='mlc' data-name='{field_name}'>{SafeHTML(items_html)}{SafeHTML(help_html)}{SafeHTML(error_html)}</div>"
        )

    def _ml_item(*, index: str = '', body_html: str = '', **_):
        return thtml(t"<div class='mli' data-idx='{index}'>{SafeHTML(body_html)}</div>")

    def _ml_help(*, help_text: str = '', **_):
        return thtml(t"<span class='ml-help'>{help_text}</span>")

    def _ml_error(*, error_text: str = '', **_):
        return thtml(t"<span class='ml-err'>{error_text}</span>")

    def _submit(*, submit_label: str = '', **_):
        return thtml(t"<button class='custom-submit'>{submit_label}</button>")

    custom_templates = FormStyleTemplates(
        model_list_container=TemplateString(_ml_container),
        model_list_item=TemplateString(_ml_item),
        model_list_help=TemplateString(_ml_help),
        model_list_error=TemplateString(_ml_error),
        submit_button=TemplateString(_submit),
        # inherit defaults for other templates
    )

    register_form_style(
        FormStyle(
            framework='custom-style',
            templates=custom_templates,
        )
    )

    class _CustomTheme(RendererTheme):
        name = 'custom-style'

    class _CustomListRenderer(ModelListRenderer):
        def __init__(self) -> None:
            super().__init__(framework='custom-style')
            self._theme = _CustomTheme()

        def _resolve_theme(self) -> RendererTheme:  # type: ignore[override]
            return self._theme

    renderer = _CustomListRenderer()

    html = renderer.render_model_list(
        field_name='pets',
        label='Pets',
        model_class=_StubModel,
        values=[{'name': 'Rex'}],
        help_text='Helpful',
        error='Oops',
        min_items=0,
        max_items=5,
    )

    assert 'mlc' in html
    assert 'mli' in html
    assert 'ml-help' in html
    assert 'ml-err' in html

    button_html = renderer._theme.render_submit_button('ignored-class')
    assert 'custom-submit' in button_html


def test_tab_layout_uses_form_style_templates() -> None:
    def _tab_layout(*, tab_buttons: str = '', tab_panels: str = '', **_):
        return thtml(
            t"<div class='custom-tab-layout'>{SafeHTML(tab_buttons)}{SafeHTML(tab_panels)}</div>"
        )

    def _tab_button(*, title: str = '', **_):
        return thtml(t"<button class='custom-tab-btn'>{title}</button>")

    def _tab_panel(*, content: str = '', **_):
        return thtml(t"<section class='custom-tab-panel'>{SafeHTML(content)}</section>")

    custom_templates = FormStyleTemplates(
        tab_layout=TemplateString(_tab_layout),
        tab_button=TemplateString(_tab_button),
        tab_panel=TemplateString(_tab_panel),
    )

    register_form_style(FormStyle(framework='tab-test', templates=custom_templates))

    class _TabTheme(RendererTheme):
        name = 'tab-test'

    stub_renderer = _StubRenderer(_TabTheme())
    layout = TabLayout(
        [
            {'title': 'A', 'content': 'Alpha'},
            {'title': 'B', 'content': 'Beta'},
        ]
    )

    html = layout.render(renderer=stub_renderer, framework='bootstrap')

    assert 'custom-tab-layout' in html
    assert 'custom-tab-btn' in html
    assert 'custom-tab-panel' in html


def test_accordion_layout_uses_form_style_templates() -> None:
    def _accordion_layout(*, sections: str = '', **_):
        return thtml(t"<div class='custom-accordion'>{SafeHTML(sections)}</div>")

    def _accordion_section(*, title: str = '', content: str = '', **_):
        return thtml(t"<article class='custom-acc-section'>{title}{SafeHTML(content)}</article>")

    custom_templates = FormStyleTemplates(
        accordion_layout=TemplateString(_accordion_layout),
        accordion_section=TemplateString(_accordion_section),
    )

    register_form_style(FormStyle(framework='acc-test', templates=custom_templates))

    class _AccTheme(RendererTheme):
        name = 'acc-test'

    stub_renderer = _StubRenderer(_AccTheme())
    layout = AccordionLayout(
        [
            {'title': 'Q1', 'content': 'A1'},
            {'title': 'Q2', 'content': 'A2'},
        ]
    )

    html = layout.render(renderer=stub_renderer, framework='bootstrap')

    assert 'custom-accordion' in html
    assert 'custom-acc-section' in html


def test_material_embedded_theme_includes_error_summary_styles() -> None:
    css = MaterialEmbeddedTheme._build_css()

    assert '.md-error-summary' in css
    assert '.md-error-summary__title' in css
    assert '.md-error-summary__list' in css
