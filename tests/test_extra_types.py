"""pydantic-extra-types fields pick their input from their type."""

from __future__ import annotations

import re

import pytest
from pydantic_extra_types.color import Color
from pydantic_extra_types.coordinate import Coordinate, Latitude, Longitude
from pydantic_extra_types.country import CountryAlpha2, CountryAlpha3
from pydantic_extra_types.isbn import ISBN
from pydantic_extra_types.language_code import LanguageAlpha2
from pydantic_extra_types.mac_address import MacAddress
from pydantic_extra_types.payment import PaymentCardNumber
from pydantic_extra_types.phone_numbers import PhoneNumber
from starlette.datastructures import FormData

from pydantic_schemaforms import Field, FormModel


class Profile(FormModel):
    color: Color = Field(title='Color')
    phone: PhoneNumber = Field(title='Phone')
    country: CountryAlpha2 = Field(title='Country')
    country3: CountryAlpha3 | None = Field(None, title='Country (alpha-3)')
    language: LanguageAlpha2 = Field(title='Language')
    card: PaymentCardNumber = Field(title='Card')
    lat: Latitude = Field(title='Latitude')
    lon: Longitude = Field(title='Longitude')
    place: Coordinate = Field(title='Place')
    isbn: ISBN = Field(title='ISBN')
    mac: MacAddress = Field(title='MAC')
    plain_country: CountryAlpha2 = Field('US', title='Plain', ui_element='text')


GOOD = FormData(
    [
        ('color', '#ff0000'),
        ('phone', '+1 650 253 0000'),
        ('country', 'US'),
        ('country3', ''),
        ('language', 'en'),
        ('card', '4111 1111 1111 1111'),
        ('lat', '40.7128'),
        ('lon', '-74.006'),
        ('place', '51.5074, -0.1278'),
        ('isbn', '978-0-306-40615-7'),
        ('mac', '00:1A:2B:3C:4D:5E'),
        ('plain_country', 'GB'),
    ]
)


def _tag(page: str, name: str) -> str:
    match = re.search(rf'<(input|select)[^>]*name="{name}"[^>]*>', page)
    assert match, name
    return match.group(0)


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        ('color', 'type="color"'),
        ('phone', 'type="tel"'),
        ('country', '<select'),
        ('country3', '<select'),
        ('language', '<select'),
        ('card', 'autocomplete="cc-number"'),
        ('lat', 'max="90"'),
        ('lon', 'min="-180"'),
        ('place', 'placeholder="40.7128, -74.0060"'),
        ('isbn', 'placeholder="9780306406157"'),
        ('mac', 'placeholder="00:1A:2B:3C:4D:5E"'),
        ('plain_country', 'type="text"'),
    ],
)
def test_each_type_gets_its_input(name, expected):
    assert expected in _tag(Profile.render_form(submit_url='/p'), name)


def test_country_and_language_lists_show_names_and_submit_codes():
    page = Profile.render_form(submit_url='/p')
    assert '<option value="US">United States</option>' in page
    assert '<option value="USA">United States</option>' in page
    assert '<option value="en">English</option>' in page
    assert 'pattern=' not in _tag(page, 'country')


def test_a_form_submission_round_trips():
    result = Profile.validate(GOOD, submit_url='/p')
    assert result.is_valid, result.errors
    assert result.data['card'] == '4111111111111111'
    assert result.data['isbn'] == '9780306406157'
    assert result.data['country3'] is None
    page = Profile.render_form(result.data, submit_url='/p')
    assert 'value="#ff0000"' in _tag(page, 'color')
    assert 'value="+1-650-253-0000"' in _tag(page, 'phone')
    assert 'value="51.5074, -0.1278"' in _tag(page, 'place')
    review = Profile.render_display(result.data)
    for text in ('#ff0000', 'United States', 'English', '51.5074, -0.1278'):
        assert text in review


def test_bad_values_are_reported_under_their_fields():
    bad = FormData(
        [
            ('color', 'not-a-color'),
            ('phone', '123'),
            ('country', 'ZZ'),
            ('language', 'zz'),
            ('card', '4111111111111112'),
            ('lat', '95'),
            ('lon', '0'),
            ('place', 'nowhere'),
            ('isbn', '123'),
            ('mac', 'nope'),
        ]
    )
    errors = Profile.validate(bad, submit_url='/p').errors
    assert {'color', 'phone', 'country', 'language', 'card', 'lat', 'place', 'isbn', 'mac'} <= set(
        errors
    )


def test_json_bodies_are_not_reformatted():
    # Only form submissions drop separators; a JSON client sends the clean value.
    result = Profile.validate(
        {**dict(GOOD), 'card': '4111 1111 1111 1111', 'country3': None}, submit_url='/p'
    )
    assert 'card' in result.errors


@pytest.mark.parametrize('framework', ['bootstrap', 'material', 'none'])
def test_renders_in_every_style(framework):
    page = Profile.render_form(submit_url='/p', framework=framework)
    assert page.count('<select name=') == 3
    assert 'type="color"' in page
