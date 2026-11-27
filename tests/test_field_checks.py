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


def test_strength_meter_is_opt_in_and_uses_the_validators_rules():
    from pydantic_schemaforms.validation import PASSWORD_CHECKS

    class Account(FormModel):
        plain: str = Field(..., ui_element='password')
        metered: str = Field(
            ..., ui_element='password', min_length=10, ui_options={'strength_meter': True}
        )

    page = Account.render_form(submit_url='/a')
    assert page.count('class="sf-strength" data-sf-strength-for=') == 1
    assert 'data-sf-strength-for="metered"' in page
    assert 'minlength="10"' in page
    for _, _, tip in PASSWORD_CHECKS:
        assert tip in page


def test_password_checks_drive_the_server_validator():
    from pydantic_schemaforms import create_password_strength_validator

    response = create_password_strength_validator(min_length=8)('abcdefgh')
    assert response.is_valid
    assert response.suggestions == [
        'Add an uppercase letter (A-Z)',
        'Add a number (0-9)',
        'Add a special character (!@#$%^&*)',
    ]


class Years(FormModel):
    born: int | None = Field(None, ui_element='year', ge=1990, le=2026)
    model_year: int = Field(
        2020,
        ui_element='year',
        ui_options={'min_year': 2015, 'max_year': 2024, 'descending': False},
    )
    any_year: int | None = Field(None, ui_element='year')


def test_year_options_follow_min_max_then_ge_le_then_today():
    import re
    from datetime import date

    page = Years.render_form(submit_url='/y')
    selects = dict(re.findall(r'<select name="(\w+)".*?>(.*?)</select>', page, re.S))
    born = re.findall(r'<option value="(\d*)"', selects['born'])
    assert born[:3] == ['', '2026', '2025'] and born[-1] == '1990'
    model_year = re.findall(r'<option value="(\d+)"', selects['model_year'])
    assert model_year[0] == '2015' and model_year[-1] == '2024'
    assert 'value="2020" selected' in selects['model_year']
    this_year = date.today().year
    any_year = re.findall(r'<option value="(\d+)"', selects['any_year'])
    assert any_year[0] == str(this_year + 10) and any_year[-1] == str(this_year - 100)


def test_year_outside_the_range_stays_selected_and_fails_on_the_server():
    page = Years.render_form({'model_year': 1999}, submit_url='/y')
    assert 'value="1999" selected' in page
    result = Years.validate({'model_year': '1999'}, submit_url='/y')
    assert result.errors == {'model_year': 'Choose a year from 2015 to 2024.'}


def test_year_range_is_checked_only_where_the_field_sets_no_limit():
    assert Years.validate({'model_year': '2020', 'born': '1985'}, submit_url='/y').errors == {
        'born': 'Must be 1990 or greater'
    }
    result = Years.validate({'model_year': '2020', 'born': '', 'any_year': ''}, submit_url='/y')
    assert result.is_valid
    assert result.data == {'born': None, 'model_year': 2020, 'any_year': None}
    assert not Years.validate({'model_year': '2020', 'any_year': '1800'}, submit_url='/y').is_valid


@pytest.mark.parametrize(
    'options',
    [
        {'min_year': '2000'},
        {'min_year': 2030, 'max_year': 2020},
        {'descending': 'no'},
        {'max_year': True},
    ],
)
def test_bad_year_options_fail_at_declaration(options):
    with pytest.raises(ValueError):
        Field(ui_element='year', ui_options=options)


def test_year_needs_an_int_field():
    with pytest.raises(TypeError, match='whole year'):

        class Bad(FormModel):
            year: str = Field(..., ui_element='year')


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_year_renders_as_a_select_in_every_style(framework):
    page = Years.render_form(submit_url='/y', framework=framework)
    assert page.count('<select name=') == 3


class Phones(FormModel):
    us: str = Field(
        ...,
        ui_element='phone',
        ui_options={'e164': True, 'country_code': '+1', 'phone_format': '(###) ###-####'},
    )
    uk: str | None = Field(
        None, ui_element='phone_number', ui_options={'e164': True, 'country_code': '+44'}
    )
    anywhere: str | None = Field(None, ui_element='phone', ui_options={'e164': True})


@pytest.mark.parametrize(
    ('typed', 'stored'),
    [
        ({'us': '(555) 123-4567'}, {'us': '+15551234567'}),
        ({'us': '+1 555.123.4567'}, {'us': '+15551234567'}),
        ({'us': '5551234567', 'uk': '020 7946 0958'}, {'uk': '+442079460958'}),
        ({'us': '5551234567', 'anywhere': '0049 30 1234567'}, {'anywhere': '+49301234567'}),
        ({'us': '5551234567', 'uk': '', 'anywhere': ''}, {'uk': None, 'anywhere': None}),
    ],
)
def test_e164_stores_one_consistent_form(typed, stored):
    result = Phones.validate(typed, submit_url='/p')
    assert result.is_valid, result.errors
    assert stored.items() <= result.data.items()


def test_e164_reports_numbers_it_cannot_complete():
    result = Phones.validate({'us': '555', 'anywhere': '030 1234567'}, submit_url='/p')
    assert result.errors == {
        'us': 'Enter a valid phone number.',
        'anywhere': 'Enter the phone number with its country code, such as +1 555 123 4567.',
    }


def test_e164_value_shows_through_the_mask():
    page = Phones.render_form({'us': '+15551234567'}, submit_url='/p')
    assert 'value="(555) 123-4567"' in page


def test_phone_without_e164_keeps_what_was_typed():
    class Plain(FormModel):
        phone: str = Field(..., ui_element='phone')

    assert Plain.validate({'phone': '(555) 123-4567'}, submit_url='/p').data == {
        'phone': '(555) 123-4567'
    }


@pytest.mark.parametrize(
    ('options', 'message'),
    [
        ({'e164': 'yes'}, 'True or False'),
        ({'e164': True, 'country_code': '44'}, 'such as "\\+44"'),
        ({'e164': True, 'phone_format': '###'}, 'needs a country_code'),
    ],
)
def test_bad_e164_options_fail_at_declaration(options, message):
    with pytest.raises(ValueError, match=message):
        Field(ui_element='phone', ui_options=options)


def test_e164_keeps_the_country_code_out_of_the_typed_value():
    page = Phones.render_form({'uk': '07700 900123'}, submit_url='/p')
    assert 'value="07700 900123"' in page
    assert (
        Phones.validate({'us': '5551234567', 'uk': '07700 900123'}, submit_url='/p').data['uk']
        == '+447700900123'
    )
