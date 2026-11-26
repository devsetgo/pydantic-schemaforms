"""Server-side checks a widget's options imply, attached by Field() and FormField()."""

from __future__ import annotations

import pytest

from pydantic_schemaforms import Field, FormField, FormModel


class CodeForm(FormModel):
    code: str = Field(..., title='Code', ui_element='otp')
    backup: str | None = Field(
        None, ui_element='one_time_code', ui_options={'length': 8, 'numeric': False}
    )


class Item(FormModel):
    code: str = Field(..., ui_element='otp', ui_options={'length': 4})


class Order(FormModel):
    items: list[Item] = Field(default_factory=list)


def test_otp_strips_spaces_and_dashes():
    result = CodeForm.validate({'code': '123 456', 'backup': 'ab-cd 12-34'}, submit_url='/c')
    assert result.is_valid
    assert result.data == {'code': '123456', 'backup': 'abcd1234'}


def test_otp_keeps_leading_zeros():
    result = CodeForm.validate({'code': '004217'}, submit_url='/c')
    assert result.data['code'] == '004217'


def test_blank_optional_otp_is_none():
    result = CodeForm.validate({'code': '123456', 'backup': ''}, submit_url='/c')
    assert result.is_valid
    assert result.data['backup'] is None


@pytest.mark.parametrize('code', ['12345', '1234567', '12a456', ''])
def test_wrong_otp_is_reported_under_the_field(code):
    result = CodeForm.validate({'code': code}, submit_url='/c')
    assert not result.is_valid
    assert result.errors == {'code': 'Enter the 6-digit code.'}


def test_letters_otp_names_characters():
    result = CodeForm.validate({'code': '123456', 'backup': 'abc!1234'}, submit_url='/c')
    assert result.errors == {'backup': 'Enter the 8-character code.'}


def test_otp_check_runs_in_list_items_and_json():
    result = Order.validate({'items': [{'code': '1234'}, {'code': '12'}]}, submit_url='/o')
    assert result.errors == {'items': {1: {'code': 'Enter the 4-digit code.'}}}
    with pytest.raises(ValueError, match='4-digit'):
        Item.model_validate({'code': '12'})


def test_otp_on_a_form_field_is_checked_too():
    class Legacy(FormModel):
        code: str = FormField(..., input_type='otp')

    assert Legacy.validate({'code': '12'}, submit_url='/l').errors == {
        'code': 'Enter the 6-digit code.'
    }


@pytest.mark.parametrize('length', [3, 13, '6', True])
def test_bad_otp_length_fails_at_declaration(length):
    with pytest.raises(ValueError, match='4 to 12'):
        Field(ui_element='otp', ui_options={'length': length})


def test_bad_otp_numeric_fails_at_declaration():
    with pytest.raises(ValueError, match='True or False'):
        Field(ui_element='otp', ui_options={'numeric': 'yes'})


def test_otp_needs_a_str_field():
    with pytest.raises(TypeError, match='leading zeros'):

        class Bad(FormModel):
            code: int = Field(..., ui_element='otp')


def test_otp_renders_one_named_input_with_autofill():
    page = CodeForm.render_form(submit_url='/c')
    assert 'autocomplete="one-time-code"' in page
    assert 'data-sf-otp="6"' in page
    assert 'data-sf-otp="8"' in page
    assert 'data-sf-otp-letters' in page
    assert 'inputmode="numeric"' in page
    assert page.count('name="code"') == 1


def test_otp_is_left_out_of_autosave():
    page = CodeForm.render_form(submit_url='/c', autosave=True)
    tag = page[page.index('name="code"') :].split('>', 1)[0]
    assert 'data-sf-no-autosave' in tag


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_otp_renders_in_every_style(framework):
    page = CodeForm.render_form(submit_url='/c', framework=framework)
    assert 'data-sf-otp="6"' in page
    assert 'schemaformsOtp' in page
