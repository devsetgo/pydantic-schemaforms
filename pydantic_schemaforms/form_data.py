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
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Union


_FORM_PATH_TOKEN_RE = re.compile(r"([^\.\[\]]+)|\[(\d+)\]")


def coerce_form_value(value: Any) -> Any:
    """Coerce common HTML form string values.

    We only do conservative coercions here and let Pydantic handle numeric
    conversion to avoid surprising conversions for string fields.

    - "true"/"false" -> bool
    - "on"/"off"/"yes"/"no"/"1"/"0" -> bool
    """

    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "on", "yes", "1"}:
            return True
        if lowered in {"false", "off", "no", "0"}:
            return False
    return value


def _tokenize_form_path(path: str) -> list[Union[str, int]]:
    tokens: list[Union[str, int]] = []
    for name_token, index_token in _FORM_PATH_TOKEN_RE.findall(path):
        if name_token:
            tokens.append(name_token)
        elif index_token:
            tokens.append(int(index_token))
    return tokens


def _new_container(next_token: Union[str, int, None]) -> Union[dict[str, Any], list[Any]]:
    return [] if isinstance(next_token, int) else {}


def _assign_mapping_token(
    current: MutableMapping[str, Any],
    token: str,
    *,
    is_last: bool,
    next_token: Union[str, int, None],
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
    tokens: list[Union[str, int]],
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
    tokens: list[Union[str, int]],
    idx: int,
    is_last: bool,
    next_token: Union[str, int, None],
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


def _assign_nested(container: MutableMapping[str, Any], tokens: list[Union[str, int]], value: Any) -> None:
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
    form_data: Union[Mapping[str, Any], Iterable[tuple[str, Any]]],
    *,
    coerce_values: bool = True,
) -> Dict[str, Any]:
    """Convert flat form keys into nested dict/list structures.

    Accepts either a mapping (``dict``/Starlette ``FormData``/etc.) or an
    iterable of ``(key, value)`` pairs.

    Example:
        ``{"pets[0].name": "Fido"}`` -> ``{"pets": [{"name": "Fido"}]}``
    """

    items = form_data.items() if isinstance(form_data, Mapping) else form_data

    result: Dict[str, Any] = {}

    for key, raw_value in items:
        value = coerce_form_value(raw_value) if coerce_values else raw_value
        tokens = _tokenize_form_path(str(key))

        if not tokens:
            result[str(key)] = value
            continue

        if len(tokens) == 1 and isinstance(tokens[0], str):
            result[tokens[0]] = value
            continue

        _assign_nested(result, tokens, value)

    return result


__all__ = ["parse_nested_form_data", "coerce_form_value"]
