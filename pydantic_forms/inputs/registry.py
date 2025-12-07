"""Runtime registry for input components keyed by their UI element metadata."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Set, Tuple, Type

from . import (  # noqa: F401
    datetime_inputs,
    numeric_inputs,
    selection_inputs,
    specialized_inputs,
    text_inputs,
)
from .base import BaseInput


def _iter_input_classes() -> Iterable[Type[BaseInput]]:
    """Yield every concrete BaseInput subclass (depth-first, unique)."""

    seen: Set[Type[BaseInput]] = set()
    stack: List[Type[BaseInput]] = list(BaseInput.__subclasses__())

    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        yield cls
        stack.extend(cls.__subclasses__())


def _declared_aliases(cls: Type[BaseInput]) -> Tuple[str, ...]:
    names: List[str] = []
    primary = getattr(cls, "ui_element", None)
    if primary:
        names.append(primary)
    aliases = getattr(cls, "ui_element_aliases", ()) or ()
    names.extend(alias for alias in aliases if alias)
    return tuple(names)


@lru_cache()
def get_input_component_map() -> Dict[str, Type[BaseInput]]:
    """Return a mapping of ui_element aliases to their component classes."""

    mapping: Dict[str, Type[BaseInput]] = {}

    for cls in _iter_input_classes():
        for alias in _declared_aliases(cls):
            mapping[alias] = cls

    # Ensure we always have a basic text input fallback
    from .text_inputs import TextInput

    mapping.setdefault("text", TextInput)
    return mapping


__all__ = ["get_input_component_map"]
