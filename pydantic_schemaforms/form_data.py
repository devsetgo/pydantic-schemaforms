"""Helpers for normalizing/reshaping raw form submissions.

HTML form submissions often arrive as a flat mapping of string keys to values.
SchemaForms uses bracket + dot notation for repeated nested models, e.g.:

- ``pets[0].name``
- ``tasks[3].priority``

Server-side validation expects the corresponding nested Python shape:

- ``{"pets": [{"name": "..."}]}``

These helpers are intentionally framework-agnostic (FastAPI/Flask/etc.).
"""

from __future__ import annotations

import re
from typing import Any
from collections.abc import Iterable, Mapping, MutableMapping


_FORM_PATH_TOKEN_RE = re.compile(r'([^\.\[\]]+)|\[(\d+)\]')


def coerce_form_value(value: Any) -> Any:
    """Coerce common HTML form string values.

    We only do conservative coercions here and let Pydantic handle numeric
    conversion to avoid surprising conversions for string fields.

    - "true"/"false" -> bool
    - "on"/"off"/"yes"/"no"/"1"/"0" -> bool
    """

    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {'true', 'on', 'yes', '1'}:
            return True
        if lowered in {'false', 'off', 'no', '0'}:
            return False
    return value


def _tokenize_form_path(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    for name_token, index_token in _FORM_PATH_TOKEN_RE.findall(path):
        if name_token:
            tokens.append(name_token)
        elif index_token:
            tokens.append(int(index_token))
    return tokens


def _new_container(next_token: str | int | None) -> dict[str, Any] | list[Any]:
    return [] if isinstance(next_token, int) else {}


def _assign_mapping_token(
    current: MutableMapping[str, Any],
    token: str,
    *,
    is_last: bool,
    next_token: str | int | None,
    value: Any,
) -> Any:
    if is_last:
        current[token] = value
        return None

    if token not in current or current[token] is None:
        current[token] = _new_container(next_token)
    return current[token]


def _coerce_to_list(
    current: Any,
    tokens: list[str | int],
    idx: int,
) -> list[Any]:
    if isinstance(current, list):
        return current

    # If the data shape is inconsistent (e.g. a key used as both dict
    # and list), prefer overwriting with a list to match the path.
    current_parent = current
    list_value: list[Any] = []
    if idx > 0 and isinstance(tokens[idx - 1], str):
        current_parent[tokens[idx - 1]] = list_value
    return list_value


def _ensure_list_index(current: list[Any], index: int) -> None:
    while len(current) <= index:
        current.append(None)


def _assign_list_token(
    current: Any,
    token: int,
    *,
    tokens: list[str | int],
    idx: int,
    is_last: bool,
    next_token: str | int | None,
    value: Any,
) -> Any:
    current_list = _coerce_to_list(current, tokens, idx)
    _ensure_list_index(current_list, token)

    if is_last:
        current_list[token] = value
        return None

    if current_list[token] is None:
        current_list[token] = _new_container(next_token)
    return current_list[token]


def _assign_nested(
    container: MutableMapping[str, Any], tokens: list[str | int], value: Any
) -> None:
    current: Any = container

    for idx, token in enumerate(tokens):
        is_last = idx == len(tokens) - 1
        next_token = tokens[idx + 1] if not is_last else None

        if isinstance(token, str):
            next_current = _assign_mapping_token(
                current,
                token,
                is_last=is_last,
                next_token=next_token,
                value=value,
            )
        else:
            next_current = _assign_list_token(
                current,
                token,
                tokens=tokens,
                idx=idx,
                is_last=is_last,
                next_token=next_token,
                value=value,
            )

        if is_last:
            return

        current = next_current


def parse_nested_form_data(
    form_data: Mapping[str, Any] | Iterable[tuple[str, Any]],
    *,
    coerce_values: bool = True,
) -> dict[str, Any]:
    """Convert flat form keys into nested dict/list structures.

    Accepts either a mapping (``dict``/Starlette ``FormData``/etc.) or an
    iterable of ``(key, value)`` pairs.

    A key that repeats -- e.g. a native ``<select multiple>`` or several
    checkboxes sharing one ``name`` -- collects into a list of values
    instead of the last one silently winning. This only works if *form_data*
    actually carries the duplicates: pass ``form_data.multi_items()`` (not
    ``dict(form_data)``, and not a plain ``Mapping``, whose ``.items()``
    can only ever hold one value per key) when the source is a Starlette
    ``FormData``/multidict.

    Example:
        ``{"pets[0].name": "Fido"}`` -> ``{"pets": [{"name": "Fido"}]}``
        ``[("colors", "red"), ("colors", "blue")]`` -> ``{"colors": ["red", "blue"]}``
    """

    items = form_data.items() if isinstance(form_data, Mapping) else form_data

    grouped: dict[str, list[Any]] = {}
    order: list[str] = []
    for key, raw_value in items:
        key = str(key)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(raw_value)

    result: dict[str, Any] = {}

    for key in order:
        raw_values = grouped[key]
        if len(raw_values) == 1:
            value = coerce_form_value(raw_values[0]) if coerce_values else raw_values[0]
        else:
            value = (
                [coerce_form_value(v) for v in raw_values] if coerce_values else list(raw_values)
            )

        tokens = _tokenize_form_path(key)

        if not tokens:
            result[key] = value
            continue

        if len(tokens) == 1 and isinstance(tokens[0], str):
            result[tokens[0]] = value
            continue

        _assign_nested(result, tokens, value)

    return result


def flatten_nested_data(data: Any, *, _prefix: str = '') -> dict[str, Any]:
    """Convert a nested dict/list structure into flat bracket+dot keys.

    Inverse of ``parse_nested_form_data``:
    ``{"pets": [{"name": "Fido"}]}`` -> ``{"pets[0].name": "Fido"}``

    Empty dicts/lists are preserved as literal container values under their
    parent key (e.g. ``{"tags": []}`` -> ``{"tags": []}``) since bracket+dot
    notation has no way to express "empty" via leaf keys alone; the result is
    still ``parse_nested_form_data``-round-trippable, but not every value in
    the returned mapping is guaranteed to be a scalar.
    """
    result: dict[str, Any] = {}

    if isinstance(data, Mapping):
        if not data and _prefix:
            result[_prefix] = {}
            return result
        for key, value in data.items():
            child_prefix = f'{_prefix}.{key}' if _prefix else str(key)
            result.update(flatten_nested_data(value, _prefix=child_prefix))
        return result

    if isinstance(data, list):
        if not data and _prefix:
            result[_prefix] = []
            return result
        for index, item in enumerate(data):
            result.update(flatten_nested_data(item, _prefix=f'{_prefix}[{index}]'))
        return result

    result[_prefix] = data
    return result


__all__ = ['parse_nested_form_data', 'flatten_nested_data', 'coerce_form_value']
