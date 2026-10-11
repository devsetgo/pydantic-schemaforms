"""Decoding raw form submissions into nested JSON.

App code never needs this module directly: ``FormModel.validate()`` accepts the
raw request form (Starlette ``FormData``, Werkzeug ``MultiDict``, a list of
``(key, value)`` pairs) and calls ``decode_submission()`` itself.

Wire format (internal): HTML inputs need a string ``name``, so nested fields
are named with dots for sub-models and brackets for list indexes --
``address.city``, ``pets[0].name``. ``decode_submission()`` turns those back
into ``{"address": {"city": ...}, "pets": [{"name": ...}]}``.
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


class _SparseList(dict[int, Any]):
    """A list under construction, keyed by submitted index.

    Indices are compacted into a real list by ``_compact`` once every key has
    been assigned, so memory is bounded by the number of submitted fields, not
    by the index values: ``pets[500000000].name`` costs one entry, not half a
    billion padding slots.
    """


def _new_container(next_token: str | int | None) -> dict[str, Any] | _SparseList:
    return _SparseList() if isinstance(next_token, int) else {}


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

    existing = current.get(token)
    if existing is None:
        current[token] = _new_container(next_token)
    elif isinstance(existing, list):
        # A value assigned directly (e.g. from a repeated key) that a later
        # key now indexes into; convert in place so the index is recorded.
        current[token] = _SparseList(enumerate(existing))
    return current[token]


def _coerce_to_list(
    current: Any,
    tokens: list[str | int],
    idx: int,
) -> _SparseList:
    if isinstance(current, _SparseList):
        return current
    if isinstance(current, list):
        return _SparseList(enumerate(current))

    # If the data shape is inconsistent (e.g. a key used as both dict
    # and list), prefer overwriting with a list to match the path.
    current_parent = current
    list_value = _SparseList()
    if idx > 0 and isinstance(tokens[idx - 1], str):
        current_parent[tokens[idx - 1]] = list_value
    return list_value


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

    if is_last:
        current_list[token] = value
        return None

    existing = current_list.get(token)
    if existing is None:
        current_list[token] = _new_container(next_token)
    elif isinstance(existing, list):
        current_list[token] = _SparseList(enumerate(existing))
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


def _compact(obj: Any) -> Any:
    """Turn every ``_SparseList`` into a list in ascending index order."""

    if isinstance(obj, _SparseList):
        return [_compact(obj[index]) for index in sorted(obj)]
    if isinstance(obj, dict):
        return {key: _compact(value) for key, value in obj.items()}
    return obj


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

    Gaps in list indices are closed: ``pets[0]`` and ``pets[2]`` become a
    two-item list, so an item removed without re-indexing the rest still
    decodes, and no index value can make the decoder allocate padding.

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

    return _compact(result)


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


def _multi_items(raw: Any) -> list[tuple[str, Any]] | None:
    multi_items = getattr(raw, 'multi_items', None)
    if callable(multi_items):
        return list(multi_items())
    if hasattr(raw, 'getlist') and hasattr(raw, 'keys'):
        return [(key, value) for key in raw.keys() for value in raw.getlist(key)]
    return None


def _is_wire_key(key: Any) -> bool:
    return isinstance(key, str) and ('[' in key or '.' in key)


def is_form_submission(raw: Any) -> bool:
    """Whether *raw* is an HTML form's wire-format submission rather than nested JSON."""

    if raw is None or isinstance(raw, (str, bytes)):
        return False
    if _multi_items(raw) is not None:
        return True
    if isinstance(raw, Mapping):
        return any(_is_wire_key(key) for key in raw)
    return isinstance(raw, Iterable)


def decode_submission(raw: Any) -> dict[str, Any]:
    """Return a nested-JSON dict from whatever a route received.

    - Multi-value form objects (Starlette ``FormData``, Werkzeug ``MultiDict``)
      and iterables of ``(key, value)`` pairs are decoded from the wire format,
      collecting repeated keys (multi-selects, checkbox groups) into lists.
    - A plain mapping that uses wire-format keys is decoded the same way.
    - Any other mapping is assumed to already be nested JSON and is returned
      as a shallow copy.

    Values are left as submitted; type-aware coercion happens during
    validation, where the field types are known.
    """

    if raw is None:
        return {}
    pairs = _multi_items(raw)
    if pairs is not None:
        return parse_nested_form_data(pairs, coerce_values=False)
    if isinstance(raw, Mapping):
        if any(_is_wire_key(key) for key in raw):
            return parse_nested_form_data(raw, coerce_values=False)
        return dict(raw)
    if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
        return parse_nested_form_data(list(raw), coerce_values=False)
    raise TypeError(
        f'Cannot decode a form submission of type {type(raw).__name__}; pass the request '
        'form (request.form / await request.form()), a list of (key, value) pairs, or a dict.'
    )


__all__ = [
    'coerce_form_value',
    'decode_submission',
    'flatten_nested_data',
    'parse_nested_form_data',
]
