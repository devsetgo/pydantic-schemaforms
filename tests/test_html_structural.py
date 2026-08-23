"""Structural HTML validation for all rendered form output.

These tests parse every rendered form through Python's stdlib HTMLParser to
confirm well-formed, tag-balanced HTML — catching broken attributes or
mismatched tags that substring checks miss.
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Optional

import pytest
from pydantic import EmailStr

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.schema_form import Field, FormModel


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

VOID_ELEMENTS = {
    'area',
    'base',
    'br',
    'col',
    'embed',
    'hr',
    'img',
    'input',
    'link',
    'meta',
    'param',
    'source',
    'track',
    'wbr',
}


class _StructureValidator(HTMLParser):
    """Tracks open/close tags and records structural errors."""

    def __init__(self) -> None:
        super().__init__()
        self._stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag not in VOID_ELEMENTS:
            self._stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_ELEMENTS:
            return
        if not self._stack:
            self.errors.append(f'Unexpected closing </{tag}> — stack empty')
        elif self._stack[-1] == tag:
            self._stack.pop()
        else:
            self.errors.append(f'Mismatched tag: expected </{self._stack[-1]}>, got </{tag}>')

    @property
    def unclosed(self) -> list[str]:
        return list(self._stack)


def assert_valid_html(html: str, label: str = '') -> None:
    """Assert that *html* is structurally valid HTML (balanced tags)."""
    validator = _StructureValidator()
    validator.feed(html)
    prefix = f'[{label}] ' if label else ''
    assert not validator.errors, f'{prefix}Tag errors: {validator.errors}'
    assert not validator.unclosed, f'{prefix}Unclosed tags: {validator.unclosed}'


# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class MinimalForm(FormModel):
    name: str = Field(..., min_length=2, description='Name')


class AllInputTypesForm(FormModel):
    text_field: str = Field(..., description='Text', ui_element='text')
    email_field: EmailStr = Field(..., description='Email', ui_element='email')
    password_field: str = Field(..., description='Password', ui_element='password')
    number_field: int = Field(..., ge=0, le=100, description='Number', ui_element='number')
    range_field: int = Field(5, ge=1, le=10, description='Range', ui_element='range')
    textarea_field: str = Field('', description='Bio', ui_element='textarea')
    checkbox_field: bool = Field(False, description='Subscribe', ui_element='checkbox')
    color_field: str = Field('#ff0000', description='Color', ui_element='color')
    date_field: Optional[str] = Field(None, description='Date', ui_element='date')
    tel_field: Optional[str] = Field(None, description='Phone', ui_element='tel')
    url_field: Optional[str] = Field(None, description='URL', ui_element='url')
    search_field: Optional[str] = Field(None, description='Search', ui_element='search')
    hidden_field: str = Field('secret', description='Hidden', ui_element='hidden')


class OptionalFieldsForm(FormModel):
    required_field: str = Field(..., description='Required')
    optional_field: Optional[str] = Field(None, description='Optional')
    optional_int: Optional[int] = Field(None, ge=0, description='Optional int')


class FileUploadForm(FormModel):
    upload: str = Field('', title='Upload', input_type='file')


# ---------------------------------------------------------------------------
# render_form_html tests
# ---------------------------------------------------------------------------


class TestRenderFormHtmlStructure:
    def test_minimal_form(self) -> None:
        html = render_form_html(MinimalForm, submit_url='/submit')
        assert_valid_html(html, 'minimal')

    def test_all_input_types(self) -> None:
        html = render_form_html(AllInputTypesForm, submit_url='/submit')
        assert_valid_html(html, 'all_input_types')

    def test_optional_fields(self) -> None:
        html = render_form_html(OptionalFieldsForm, submit_url='/submit')
        assert_valid_html(html, 'optional_fields')

    def test_form_contains_required_structure(self) -> None:
        html = render_form_html(MinimalForm, submit_url='/submit')
        assert '<form' in html
        assert '</form>' in html
        assert 'name="name"' in html

    def test_form_action_url(self) -> None:
        html = render_form_html(MinimalForm, submit_url='/my-endpoint')
        assert '/my-endpoint' in html

    def test_method_defaults_to_post(self) -> None:
        html = render_form_html(MinimalForm, submit_url='/submit')
        assert 'method="post"' in html.lower() or "method='post'" in html.lower()

    def test_required_field_has_required_attribute(self) -> None:
        html = render_form_html(MinimalForm, submit_url='/submit')
        assert 'required' in html

    @pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
    def test_all_frameworks_produce_valid_html(self, framework: str) -> None:
        renderer = EnhancedFormRenderer(framework=framework)
        html = renderer.render_form_from_model(MinimalForm)
        assert_valid_html(html, framework)

    @pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
    def test_all_input_types_all_frameworks(self, framework: str) -> None:
        renderer = EnhancedFormRenderer(framework=framework)
        html = renderer.render_form_from_model(AllInputTypesForm)
        assert_valid_html(html, f'{framework}/all_inputs')

    def test_file_field_auto_sets_multipart_enctype(self) -> None:
        """A <form> with a file input still submits as the default
        application/x-www-form-urlencoded unless told otherwise -- which
        silently sends only the filename, never the file's contents. The
        form must auto-opt into multipart/form-data whenever any field is
        input_type='file', with no action required from the caller."""
        html = render_form_html(FileUploadForm, submit_url='/submit')
        assert 'enctype="multipart/form-data"' in html

    def test_explicit_enctype_kwarg_is_not_overridden(self) -> None:
        html = render_form_html(
            FileUploadForm, submit_url='/submit', enctype='application/x-www-form-urlencoded'
        )
        assert 'enctype="application/x-www-form-urlencoded"' in html
        assert 'multipart/form-data' not in html

    def test_form_without_file_field_has_no_enctype(self) -> None:
        html = render_form_html(MinimalForm, submit_url='/submit')
        assert 'enctype' not in html


# ---------------------------------------------------------------------------
# EnhancedFormRenderer tests
# ---------------------------------------------------------------------------


class TestEnhancedRendererStructure:
    def test_bootstrap_renderer_valid_html(self, bootstrap_renderer: EnhancedFormRenderer) -> None:
        html = bootstrap_renderer.render_form_from_model(AllInputTypesForm)
        assert_valid_html(html, 'bootstrap')

    def test_material_renderer_valid_html(self, material_renderer: EnhancedFormRenderer) -> None:
        html = material_renderer.render_form_from_model(AllInputTypesForm)
        assert_valid_html(html, 'material')

    def test_plain_renderer_valid_html(self, plain_renderer: EnhancedFormRenderer) -> None:
        html = plain_renderer.render_form_from_model(AllInputTypesForm)
        assert_valid_html(html, 'plain')

    def test_fields_only_valid_html(self, enhanced_renderer: EnhancedFormRenderer) -> None:
        html = enhanced_renderer.render_form_fields_only(AllInputTypesForm)
        # Fields-only output may not have a <form> wrapper but must still be balanced
        assert_valid_html(html, 'fields_only')

    def test_with_validation_errors_valid_html(
        self, enhanced_renderer: EnhancedFormRenderer
    ) -> None:
        errors = {
            'text_field': 'Required',
            'email_field': 'Invalid email',
        }
        html = enhanced_renderer.render_form_from_model(AllInputTypesForm, errors=errors)
        assert_valid_html(html, 'with_errors')

    def test_with_initial_data_valid_html(self, enhanced_renderer: EnhancedFormRenderer) -> None:
        initial = {
            'text_field': 'Hello',
            'number_field': 42,
            'checkbox_field': True,
        }
        html = enhanced_renderer.render_form_from_model(AllInputTypesForm, data=initial)
        assert_valid_html(html, 'with_initial_data')


# ---------------------------------------------------------------------------
# Input-specific structure checks
# ---------------------------------------------------------------------------


class TestInputElementStructure:
    """Verify specific HTML element structure for each input type."""

    def test_text_input_has_type_text(self) -> None:
        html = render_form_html(MinimalForm, submit_url='/s')
        assert 'type="text"' in html or "type='text'" in html

    def test_number_input_has_type_number(self) -> None:
        class F(FormModel):
            n: int = Field(..., ge=0, description='N', ui_element='number')

        html = render_form_html(F, submit_url='/s')
        assert_valid_html(html)
        assert 'type="number"' in html or "type='number'" in html

    def test_checkbox_input_has_type_checkbox(self) -> None:
        class F(FormModel):
            flag: bool = Field(False, description='Flag', ui_element='checkbox')

        html = render_form_html(F, submit_url='/s')
        assert_valid_html(html)
        assert 'type="checkbox"' in html or "type='checkbox'" in html

    def test_email_input_has_type_email(self) -> None:
        class F(FormModel):
            email: EmailStr = Field(..., description='E', ui_element='email')

        html = render_form_html(F, submit_url='/s')
        assert_valid_html(html)
        assert 'type="email"' in html or "type='email'" in html

    def test_all_inputs_have_name_attributes(self) -> None:
        html = render_form_html(AllInputTypesForm, submit_url='/s')
        assert_valid_html(html)
        for field in ['text_field', 'email_field', 'number_field', 'checkbox_field']:
            assert f'name="{field}"' in html, f'Missing name attribute for {field}'


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string_defaults_valid_html(self) -> None:
        class F(FormModel):
            note: str = Field('', description='Note')

        html = render_form_html(F, submit_url='/s')
        assert_valid_html(html)

    def test_long_field_names_valid_html(self) -> None:
        class F(FormModel):
            a_very_long_field_name_that_tests_attribute_handling: str = Field(
                '', description='Long'
            )

        html = render_form_html(F, submit_url='/s')
        assert_valid_html(html)

    def test_special_chars_in_description_valid_html(self) -> None:
        class F(FormModel):
            field: str = Field('', description='Enter <name> & "value"')

        html = render_form_html(F, submit_url='/s')
        assert_valid_html(html)

    def test_multiple_forms_same_model(self) -> None:
        renderer = EnhancedFormRenderer()
        html1 = renderer.render_form_from_model(MinimalForm)
        html2 = renderer.render_form_from_model(MinimalForm)
        assert_valid_html(html1, 'render1')
        assert_valid_html(html2, 'render2')
