"""Runtime registry for input components keyed by their UI element metadata."""

from __future__ import annotations

from functools import lru_cache
from collections.abc import Iterable

from . import (  # noqa: F401
    datetime_inputs,
    numeric_inputs,
    selection_inputs,
    specialized_inputs,
    text_inputs,
)
from .base import BaseInput


_EXTRA_INPUTS: dict[str, type[BaseInput]] = {}


def _iter_input_classes() -> Iterable[type[BaseInput]]:
    """Yield every concrete BaseInput subclass (depth-first, unique)."""

    seen: set[type[BaseInput]] = set()
    stack: list[type[BaseInput]] = list(BaseInput.__subclasses__())

    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        yield cls
        stack.extend(cls.__subclasses__())


def _declared_aliases(cls: type[BaseInput]) -> tuple[str, ...]:
    names: list[str] = []
    primary = getattr(cls, 'ui_element', None)
    if primary:
        names.append(primary)
    aliases = getattr(cls, 'ui_element_aliases', ()) or ()
    names.extend(alias for alias in aliases if alias)
    return tuple(names)


@lru_cache()
def get_input_component_map() -> dict[str, type[BaseInput]]:
    """Return a mapping of ui_element aliases to their component classes."""

    mapping: dict[str, type[BaseInput]] = {}

    for cls in _iter_input_classes():
        for alias in _declared_aliases(cls):
            mapping[alias] = cls

    for alias, cls in _EXTRA_INPUTS.items():
        mapping[alias] = cls

    # Ensure we always have a basic text input fallback
    from .text_inputs import TextInput

    mapping.setdefault('text', TextInput)
    return mapping


def register_input_class(cls: type[BaseInput], *, aliases: Iterable[str] | None = None) -> None:
    """Register a custom input component and clear cached mappings."""

    if not issubclass(cls, BaseInput):  # pragma: no cover - defensive
        raise TypeError('Custom input must subclass BaseInput')

    names = list(aliases or []) or list(_declared_aliases(cls))
    if not names:
        raise ValueError('At least one alias is required to register an input component')

    for name in names:
        if not name:
            continue
        _EXTRA_INPUTS[name] = cls

    get_input_component_map.cache_clear()


def register_inputs(classes: Iterable[type[BaseInput]]) -> None:
    """Register multiple custom input components at once."""

    for cls in classes:
        register_input_class(cls)


def reset_input_registry() -> None:
    """Clear custom inputs and cached component maps (useful in tests)."""

    _EXTRA_INPUTS.clear()
    get_input_component_map.cache_clear()


__all__ = [
    'get_input_component_map',
    'register_input_class',
    'register_inputs',
    'reset_input_registry',
]
