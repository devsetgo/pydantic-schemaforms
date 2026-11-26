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


def check_widget_options(extra: dict[str, Any]) -> None:
    """Fail at declaration, not at the first render, for a widget option that can't work."""

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
    return field_info
