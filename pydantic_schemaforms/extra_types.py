"""The input each pydantic-extra-types type renders as, picked from the field's type.

pydantic-extra-types already validates these types; this module only chooses how
they're drawn and shown. A field's own ``ui_element`` always wins. JSON Schema
can't tell a country code from any other string, so the choice is made from the
Python annotation.
"""

from __future__ import annotations

import re
import types
from functools import cache
from typing import Annotated, Any, Union, get_args, get_origin


def _classes(annotation: Any) -> list[type]:
    origin = get_origin(annotation)
    if origin is Annotated:
        return _classes(get_args(annotation)[0])
    if origin in (Union, types.UnionType):
        return [cls for arg in get_args(annotation) for cls in _classes(arg)]
    return [annotation] if isinstance(annotation, type) else []


@cache
def _country_choices(attribute: str) -> tuple[dict[str, str], ...]:
    import pycountry

    countries = sorted(pycountry.countries, key=lambda country: country.name)
    return tuple(
        {'value': str(getattr(country, attribute)), 'label': country.name} for country in countries
    )


@cache
def _language_choices(attribute: str) -> tuple[dict[str, str], ...]:
    import pycountry

    languages = sorted(
        (language for language in pycountry.languages if hasattr(language, 'alpha_2')),
        key=lambda language: language.name,
    )
    return tuple(
        {'value': str(getattr(language, attribute)), 'label': language.name}
        for language in languages
    )


def _text(placeholder: str, **options: Any) -> dict[str, Any]:
    return {'ui_element': 'text', 'ui_options': {'placeholder': placeholder, **options}}


@cache
def _widgets() -> dict[type, Any]:
    from pydantic_extra_types.color import Color
    from pydantic_extra_types.coordinate import Coordinate, Latitude, Longitude
    from pydantic_extra_types.country import (
        CountryAlpha2,
        CountryAlpha3,
        CountryNumericCode,
        CountryShortName,
    )
    from pydantic_extra_types.domain import DomainStr
    from pydantic_extra_types.isbn import ISBN
    from pydantic_extra_types.language_code import LanguageAlpha2, LanguageName
    from pydantic_extra_types.mac_address import MacAddress
    from pydantic_extra_types.payment import PaymentCardNumber
    from pydantic_extra_types.phone_numbers import PhoneNumber
    from pydantic_extra_types.routing_number import ABARoutingNumber
    from pydantic_extra_types.semantic_version import SemanticVersion
    from pydantic_extra_types.ulid import ULID

    def select(choices: Any) -> Any:
        return lambda: {'ui_element': 'select', 'ui_options': {'choices': list(choices())}}

    return {
        Color: lambda: {'ui_element': 'color'},
        PhoneNumber: lambda: {'ui_element': 'phone'},
        PaymentCardNumber: lambda: {'ui_element': 'credit_card'},
        CountryAlpha2: select(lambda: _country_choices('alpha_2')),
        CountryAlpha3: select(lambda: _country_choices('alpha_3')),
        CountryNumericCode: select(lambda: _country_choices('numeric')),
        CountryShortName: select(lambda: _country_choices('name')),
        LanguageAlpha2: select(lambda: _language_choices('alpha_2')),
        LanguageName: select(lambda: _language_choices('name')),
        Latitude: lambda: {
            'ui_element': 'number',
            'ui_options': {'min': -90, 'max': 90, 'step': 'any'},
        },
        Longitude: lambda: {
            'ui_element': 'number',
            'ui_options': {'min': -180, 'max': 180, 'step': 'any'},
        },
        Coordinate: lambda: _text('40.7128, -74.0060'),
        MacAddress: lambda: _text('00:1A:2B:3C:4D:5E', spellcheck='false'),
        ISBN: lambda: _text('9780306406157', inputmode='numeric'),
        ABARoutingNumber: lambda: _text('021000021', inputmode='numeric', maxlength=9),
        ULID: lambda: _text('01ARZ3NDEKTSV4RRFFQ69G5FAV', maxlength=26, spellcheck='false'),
        SemanticVersion: lambda: _text('1.2.3'),
        DomainStr: lambda: _text('example.com', spellcheck='false'),
    }


def widget_for(annotation: Any) -> dict[str, Any] | None:
    """The ``ui_element`` and ``ui_options`` an extra type renders with, or ``None``."""

    try:
        widgets = _widgets()
    except ImportError:
        return None
    for cls in _classes(annotation):
        for extra_type, make in widgets.items():
            if issubclass(cls, extra_type):
                return make()
    return None


def display_value(value: Any) -> Any:
    """An extra type's value as people type it: hex colors, "lat, lon", no ``tel:``."""

    as_hex = getattr(value, 'as_hex', None)
    if callable(as_hex):
        return as_hex(format='long')
    if hasattr(value, 'latitude') and hasattr(value, 'longitude'):
        return f'{value.latitude}, {value.longitude}'
    if isinstance(value, dict) and value.keys() == {'latitude', 'longitude'}:
        return f'{value["latitude"]}, {value["longitude"]}'
    if isinstance(value, str) and value.startswith('tel:'):
        return value[len('tel:') :]
    return value


_DIGITS_ONLY_NAMES = {'PaymentCardNumber', 'ISBN', 'ABARoutingNumber'}


def clean_form_value(annotation: Any, value: str) -> str:
    """Drop the spaces and hyphens people type in card, ISBN and routing numbers."""

    if any(
        cls.__name__ in _DIGITS_ONLY_NAMES and cls.__module__.startswith('pydantic_extra_types')
        for cls in _classes(annotation)
    ):
        return re.sub(r'[\s-]', '', value)
    return value


__all__ = ['clean_form_value', 'display_value', 'widget_for']
