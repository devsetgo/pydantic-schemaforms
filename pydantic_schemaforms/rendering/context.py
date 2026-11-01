"""Render context helpers shared across renderer implementations."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RenderContext:
    """Immutable payload passed through render helpers to avoid shared state.

    error/required_fields/child_errors default empty and are only populated
    per-field, right before dispatching to a registered ui_element renderer
    (see LayoutEngine.get_renderer_for_element) -- a composite renderer reads
    its own field's message (`error`), required-ness, and the error sub-tree
    for its children (`child_errors`, same shape as the field's value; see
    `pydantic_schemaforms.error_tree`) from here instead of the
    LayoutRenderer signature growing new positional params.
    """

    form_data: dict[str, Any]
    schema_defs: dict[str, Any]
    error: str | None = None
    required_fields: tuple[str, ...] = ()
    child_errors: dict[Any, Any] = field(default_factory=dict)
    # form_data without the fields hidden by a ui_show_when rule, when any exist:
    # a field may depend on one that is itself hidden.
    visible_data: dict[str, Any] | None = None
