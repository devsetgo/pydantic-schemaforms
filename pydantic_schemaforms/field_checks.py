"""Server-side checks a widget's options imply, attached when the field is declared.

They are Pydantic field metadata, like the upload limits in ``uploads.py``, so
they run wherever the model validates: ``validate()``, sub-forms, list items
and JSON bodies alike, with the error under the field.
"""

from __future__ import annotations

import re
import types
from dataclasses import dataclass
from typing import Any, Union, get_args, get_origin

from pydantic import GetCoreSchemaHandler
from pydantic.fields import FieldInfo
from pydantic_core import PydanticCustomError, core_schema

_OTP_ELEMENTS = {'otp', 'one_time_code'}
_YEAR_ELEMENTS = {'year'}
_PHONE_ELEMENTS = {'phone', 'phone_number'}
_E164 = re.compile(r'\+[1-9]\d{6,14}')
_COUNTRY_CODE = re.compile(r'\+[1-9]\d{0,2}')
_PHONE_FORMATTING = re.compile(r'[\s().\-/]')
_OTP_SEPARATORS = re.compile(r'[\s-]')


def _declared_element(extra: dict[str, Any]) -> str | None:
    return extra.get('ui_element') or extra.get('input_type')


def _options(extra: dict[str, Any]) -> dict[str, Any]:
    options = extra.get('ui_options')
    return options if isinstance(options, dict) else {}


def _union_args(source: Any) -> tuple[Any, ...]:
    if get_origin(source) in (Union, types.UnionType):
        return get_args(source)
    return (source,)


@dataclass(frozen=True)
class _OneTimeCode:
    length: int
    numeric: bool

    def __get_pydantic_core_schema__(
        self, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        args = _union_args(source)
        if str not in args:
            raise TypeError(
                'An otp field keeps the code as typed, leading zeros included, so type it '
                f'str or str | None, not {source!r}'
            )
        allows_none = type(None) in args
        checked = core_schema.no_info_after_validator_function(self._check, handler(source))

        def clean(value: Any) -> Any:
            if not isinstance(value, str):
                return value
            value = _OTP_SEPARATORS.sub('', value)
            return None if value == '' and allows_none else value

        return core_schema.no_info_before_validator_function(clean, checked)

    def _check(self, value: Any) -> Any:
        if value is None:
            return value
        chars = r'\d' if self.numeric else '[0-9A-Za-z]'
        if not re.fullmatch(f'{chars}{{{self.length}}}', value):
            noun = 'digit' if self.numeric else 'character'
            raise PydanticCustomError(
                'otp_invalid',
                'Enter the {length}-' + noun + ' code.',
                {'length': self.length},
            )
        return value


@dataclass(frozen=True)
class _YearRange:
    """The years a year picker offers, checked on the server.

    A side the field already limits with ge/le is left to Pydantic; an open side
    uses the picker's default, worked out when the form is checked.
    """

    min_year: int | None
    max_year: int | None
    field_limits_low: bool
    field_limits_high: bool

    def __get_pydantic_core_schema__(
        self, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        args = _union_args(source)
        if int not in args:
            raise TypeError(
                f'A year field holds a whole year, so type it int or int | None, not {source!r}'
            )
        return core_schema.no_info_after_validator_function(self._check, handler(source))

    def _check(self, value: Any) -> Any:
        if value is None:
            return value
        from .inputs.datetime_inputs import year_bounds

        low, high = year_bounds(self.min_year, self.max_year)
        too_low = not self.field_limits_low and value < low
        too_high = not self.field_limits_high and value > high
        if too_low or too_high:
            raise PydanticCustomError(
                'year_out_of_range',
                'Choose a year from {low} to {high}.',
                {'low': low, 'high': high},
            )
        return value


@dataclass(frozen=True)
class _E164Phone:
    """Store a phone number as E.164 (+15551234567), whatever formatting it was typed with."""

    country_code: str | None

    def __get_pydantic_core_schema__(
        self, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        args = _union_args(source)
        if str not in args:
            raise TypeError(
                f'An e164 phone field holds text such as +15551234567, so type it str, not {source!r}'
            )
        allows_none = type(None) in args
        checked = core_schema.no_info_after_validator_function(self._check, handler(source))

        def normalize(value: Any) -> Any:
            if not isinstance(value, str):
                return value
            number = _PHONE_FORMATTING.sub('', value)
            if number == '':
                return None if allows_none else number
            if number.startswith('00'):
                number = '+' + number[2:]
            if not number.startswith('+') and self.country_code:
                # Most countries dial a leading 0 at home that the international form drops.
                number = self.country_code + (number[1:] if number.startswith('0') else number)
            return number

        return core_schema.no_info_before_validator_function(normalize, checked)

    def _check(self, value: Any) -> Any:
        if value is None or _E164.fullmatch(value):
            return value
        if self.country_code:
            raise PydanticCustomError('phone_e164', 'Enter a valid phone number.')
        raise PydanticCustomError(
            'phone_e164', 'Enter the phone number with its country code, such as +1 555 123 4567.'
        )


def _check_phone_options(options: dict[str, Any]) -> None:
    e164 = options.get('e164', False)
    if not isinstance(e164, bool):
        raise ValueError(
            f"ui_options={{'e164': ...}} for a phone field is True or False, not {e164!r}"
        )
    if not e164:
        return
    country_code = options.get('country_code')
    if country_code is not None and not (
        isinstance(country_code, str) and _COUNTRY_CODE.fullmatch(country_code)
    ):
        raise ValueError(
            f'country_code is a + and 1 to 3 digits, such as "+44", not {country_code!r}'
        )
    if options.get('phone_format') and not country_code:
        raise ValueError(
            'An e164 phone field with a phone_format mask needs a country_code: '
            'the mask keeps only digits, so the user cannot type the +'
        )


def _check_year_options(options: dict[str, Any]) -> None:
    for key in ('min_year', 'max_year'):
        value = options.get(key)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            raise ValueError(
                f"ui_options={{'{key}': ...}} for a year field is a whole year, not {value!r}"
            )
    low, high = options.get('min_year'), options.get('max_year')
    if low is not None and high is not None and low > high:
        raise ValueError(f"A year field's min_year ({low}) is after its max_year ({high})")
    if not isinstance(options.get('descending', True), bool):
        raise ValueError("ui_options={'descending': ...} for a year field is True or False")


def check_widget_options(extra: dict[str, Any]) -> None:
    """Fail at declaration, not at the first render, for a widget option that can't work."""

    if _declared_element(extra) in _YEAR_ELEMENTS:
        _check_year_options(_options(extra))
    if _declared_element(extra) in _PHONE_ELEMENTS:
        _check_phone_options(_options(extra))
    if _declared_element(extra) in _OTP_ELEMENTS:
        options = _options(extra)
        length = options.get('length', 6)
        if not isinstance(length, int) or isinstance(length, bool) or not 4 <= length <= 12:
            raise ValueError(
                f"ui_options={{'length': ...}} for an otp field is 4 to 12, not {length!r}"
            )
        numeric = options.get('numeric', True)
        if not isinstance(numeric, bool):
            raise ValueError(
                f"ui_options={{'numeric': ...}} for an otp field is True or False, not {numeric!r}"
            )


def attach_widget_checks(field_info: FieldInfo, extra: dict[str, Any]) -> FieldInfo:
    """Add the server-side check a field's widget implies, if it has one."""

    check_widget_options(extra)
    if _declared_element(extra) in _OTP_ELEMENTS:
        options = _options(extra)
        field_info.metadata.append(
            _OneTimeCode(options.get('length', 6), options.get('numeric', True))
        )
    if _declared_element(extra) in _PHONE_ELEMENTS and _options(extra).get('e164'):
        field_info.metadata.append(_E164Phone(_options(extra).get('country_code')))
    if _declared_element(extra) in _YEAR_ELEMENTS:
        options = _options(extra)
        limits = {type(item).__name__ for item in field_info.metadata}
        field_info.metadata.append(
            _YearRange(
                options.get('min_year'),
                options.get('max_year'),
                field_limits_low=bool(limits & {'Ge', 'Gt'}),
                field_limits_high=bool(limits & {'Le', 'Lt'}),
            )
        )
    return field_info
