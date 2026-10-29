"""Nested validation-error trees.

``ValidationResult.errors`` mirrors the shape of the submitted data instead of
using string paths, so the developer reads errors the same way they read data::

    result.data   == {"address": {"city": "X"}, "pets": [{"name": "Rex"}, {"name": ""}]}
    result.errors == {"address": {"city": "String should have at least 2 characters"},
                      "pets": {1: {"name": "Field required"}}}

Rules:

- A node is either a message string or a dict of child nodes. (A list of
  strings is also accepted as a message, joined with "; " -- the shape the
  rule-based ``FormValidator`` produces.)
- A list's errors are a dict keyed by the integer item index (only failing
  items appear; JSON serialises the keys as strings).
- A message about a container itself (a whole list or sub-model, e.g. a
  ``min_length`` on a list, or a ``@model_validator``) is stored as a plain
  string when the container has no child errors, and under the reserved key
  ``"_errors"`` when it does. Form-wide messages live in the top-level
  ``"_errors"``.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import Any

ErrorTree = dict[str | int, Any]

CONTAINER_ERROR_KEY = '_errors'


def _friendly_message(error: Mapping[str, Any]) -> str:
    message = str(error.get('msg', ''))
    error_type = str(error.get('type', ''))
    ctx = error.get('ctx') or {}

    if 'greater_than_equal' in error_type and ctx.get('ge') is not None:
        return f'Must be {ctx["ge"]} or greater'
    if 'less_than_equal' in error_type and ctx.get('le') is not None:
        return f'Must be {ctx["le"]} or less'
    # Pydantic prefixes a ValueError raised in a validator; the form shows
    # the validator's own message.
    if error_type == 'value_error':
        return message.removeprefix('Value error, ')
    return message


def _set_container_message(parent: dict[Any, Any], key: Any, message: str) -> None:
    existing = parent.get(key)
    if existing is None:
        parent[key] = message
    elif isinstance(existing, dict):
        existing.setdefault(CONTAINER_ERROR_KEY, message)


def _descend(parent: dict[Any, Any], key: Any) -> dict[Any, Any]:
    existing = parent.get(key)
    if isinstance(existing, dict):
        return existing
    child: dict[Any, Any] = {}
    if isinstance(existing, str):
        # A message was already recorded on this container; keep it while
        # making room for child errors.
        child[CONTAINER_ERROR_KEY] = existing
    parent[key] = child
    return child


def build_error_tree(errors: Sequence[Mapping[str, Any]]) -> ErrorTree:
    """Turn Pydantic's ``ValidationError.errors()`` list into a nested error tree."""

    tree: ErrorTree = {}
    for error in errors:
        loc: tuple[Any, ...] = tuple(error.get('loc') or ())
        message = _friendly_message(error)
        if not loc:
            tree.setdefault(CONTAINER_ERROR_KEY, message)
            continue
        node: dict[Any, Any] = tree
        for segment in loc[:-1]:
            node = _descend(node, segment)
        _set_container_message(node, loc[-1], message)
    return tree


def _is_path_key(key: Any) -> bool:
    return isinstance(key, str) and ('[' in key or '.' in key)


def normalize_error_tree(errors: Any) -> ErrorTree:
    """Accept errors in any shape a caller may hold and return a tree.

    - ``None`` -> ``{}``
    - an error tree -> returned unchanged
    - the SchemaForm contract ``{"errors": [{"name": ..., "message": ...}]}``
    - a mapping whose keys are wire paths (``"address.city"``, ``"pets[0].name"``)
    """
    from .form_data import _tokenize_form_path

    if not errors:
        return {}
    if not isinstance(errors, Mapping):
        return {CONTAINER_ERROR_KEY: str(errors)}
    if isinstance(errors.get('errors'), list):
        pairs = [
            (str(item.get('name', '')), item.get('message', ''))
            for item in errors['errors']
            if isinstance(item, Mapping)
        ]
    elif any(_is_path_key(key) for key in errors):
        pairs = list(errors.items())
    else:
        return dict(errors)

    flat: list[dict[str, Any]] = []
    for path, message in pairs:
        loc = tuple(_tokenize_form_path(path)) if path else ()
        flat.append({'loc': loc, 'msg': str(message), 'type': ''})
    return build_error_tree(flat)


def _message_text(node: Any) -> str | None:
    if isinstance(node, str):
        return node or None
    if isinstance(node, (list, tuple)) and all(isinstance(item, str) for item in node):
        return '; '.join(item for item in node if item) or None
    return None


def field_message(node: Any) -> str | None:
    """The message attached to one node itself (not its children)."""

    text = _message_text(node)
    if text is not None:
        return text
    if isinstance(node, Mapping):
        message = node.get(CONTAINER_ERROR_KEY)
        return str(message) if message else None
    return None


def child_errors(node: Any) -> dict[Any, Any]:
    """The child-error mapping of a node, or ``{}`` for a message/None node."""

    return dict(node) if isinstance(node, Mapping) else {}


def iter_errors(tree: Any, loc: tuple[str | int, ...] = ()) -> Iterator[tuple[tuple, str]]:
    """Yield ``(loc, message)`` depth-first, container messages before children."""

    text = _message_text(tree)
    if text is not None:
        yield loc, text
        return
    if not isinstance(tree, Mapping):
        return
    own = tree.get(CONTAINER_ERROR_KEY)
    if own:
        yield loc, str(own)
    for key, child in tree.items():
        if key == CONTAINER_ERROR_KEY:
            continue
        yield from iter_errors(child, (*loc, key))


def error_list(tree: Any) -> list[dict[str, Any]]:
    """Flat Pydantic-style ``[{"loc": [...], "msg": ...}]`` view of a tree."""

    return [{'loc': list(loc), 'msg': message} for loc, message in iter_errors(tree)]


def has_errors(tree: Any) -> bool:
    return next(iter_errors(tree), None) is not None


__all__ = [
    'CONTAINER_ERROR_KEY',
    'ErrorTree',
    'build_error_tree',
    'child_errors',
    'error_list',
    'field_message',
    'has_errors',
    'iter_errors',
    'normalize_error_tree',
]
