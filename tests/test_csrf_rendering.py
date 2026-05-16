import pytest

from pydantic_schemaforms.enhanced_renderer import CSRFMode, EnhancedFormRenderer
from pydantic_schemaforms.inputs.registry import get_input_component_map
from pydantic_schemaforms.render_form import render_form_html
from pydantic_schemaforms.schema_form import Field, FormModel


class _CsrfDemoForm(FormModel):
    name: str = Field(..., description='Name')


def test_csrf_input_is_registry_addressable():
    mapping = get_input_component_map()

    assert 'csrf' in mapping
    assert mapping['csrf'].__name__ == 'CSRFInput'


def test_include_csrf_backwards_compatibility_renders_field():
    renderer = EnhancedFormRenderer()

    html = renderer.render_form_from_model(_CsrfDemoForm, include_csrf=True)

    assert 'type="hidden"' in html
    assert 'name="csrf_token"' in html


def test_field_only_mode_requires_debug():
    renderer = EnhancedFormRenderer()

    with pytest.raises(ValueError, match='field-only'):
        renderer.render_form_from_model(_CsrfDemoForm, csrf_mode='field-only')


def test_field_only_mode_renders_when_debug_enabled():
    renderer = EnhancedFormRenderer()

    html = renderer.render_form_from_model(
        _CsrfDemoForm,
        csrf_mode='field-only',
        csrf_token_provider=lambda: 'tok123',
        debug=True,
    )

    assert 'name="csrf_token"' in html
    assert 'value="tok123"' in html


def test_required_provider_mode_rejects_missing_token_provider():
    renderer = EnhancedFormRenderer()

    with pytest.raises(ValueError, match='required-provider'):
        renderer.render_form_from_model(_CsrfDemoForm, csrf_mode='required_provider')


def test_required_provider_renders_escaped_token_and_custom_field_name():
    renderer = EnhancedFormRenderer()

    html = renderer.render_form_from_model(
        _CsrfDemoForm,
        csrf_mode='required-provider',
        csrf_token_provider=lambda: 'tok"<unsafe>',
        csrf_field_name='form_csrf',
    )

    assert 'name="form_csrf"' in html
    assert 'value="tok&quot;&lt;unsafe&gt;"' in html


def test_render_form_html_exposes_csrf_options():
    html = render_form_html(
        _CsrfDemoForm,
        submit_url='/submit',
        csrf_mode='required-provider',
        csrf_token_provider=lambda: 'abc123',
    )

    assert 'name="csrf_token"' in html
    assert 'value="abc123"' in html


def test_csrf_mode_enum_is_supported():
    renderer = EnhancedFormRenderer()

    html = renderer.render_form_from_model(
        _CsrfDemoForm,
        csrf_mode=CSRFMode.REQUIRED_PROVIDER,
        csrf_token_provider=lambda: 'enum-token',
    )

    assert 'name="csrf_token"' in html
    assert 'value="enum-token"' in html
