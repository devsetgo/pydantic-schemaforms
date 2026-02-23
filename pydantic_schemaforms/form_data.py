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


def _assign_nested(container: MutableMapping[str, Any], tokens: list[Union[str, int]], value: Any) -> None:
    current: Any = container

    for idx, token in enumerate(tokens):
        is_last = idx == len(tokens) - 1
        next_token = tokens[idx + 1] if not is_last else None

        if isinstance(token, str):
            if is_last:
                current[token] = value
                return

            if token not in current or current[token] is None:
                current[token] = [] if isinstance(next_token, int) else {}
            current = current[token]
            continue

        # token is a list index
        if not isinstance(current, list):
            # If the data shape is inconsistent (e.g. a key used as both dict
            # and list), prefer overwriting with a list to match the path.
            current_parent = current
            current = []
            if isinstance(tokens[idx - 1], str):
                current_parent[tokens[idx - 1]] = current

        while len(current) <= token:
            current.append(None)

        if is_last:
            current[token] = value
            return

        if current[token] is None:
            current[token] = [] if isinstance(next_token, int) else {}
        current = current[token]


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
