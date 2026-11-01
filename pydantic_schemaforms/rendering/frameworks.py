"""Input component lookup for renderers."""

from __future__ import annotations


from pydantic_schemaforms.inputs import TextInput as _TextInput
from pydantic_schemaforms.inputs.base import BaseInput
from pydantic_schemaforms.inputs.registry import get_input_component_map

# TextInput is imported through the inputs package's lazy-loading __getattr__
# facade, which (necessarily) returns Any -- annotate the fallback explicitly
# so get_input_component's return type stays type[BaseInput], not
# type[BaseInput] | None.
_DEFAULT_INPUT: type[BaseInput] = _TextInput


def get_input_component(element: str) -> type[BaseInput]:
    """Return the input component class for the given UI element key.

    Calls get_input_component_map() fresh (it's @lru_cache()'d in registry.py,
    so this stays cheap) rather than reading a module-level snapshot -- a
    snapshot taken at import time would never see components registered via
    register_input_class()/register_inputs() after pydantic_schemaforms
    itself has been imported, which is every real call site (the package's
    own __init__.py eagerly imports this module transitively).
    """
    return get_input_component_map().get(element, _DEFAULT_INPUT)
