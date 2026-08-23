"""Render context helpers shared across renderer implementations."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RenderContext:
    """Immutable payload passed through render helpers to avoid shared state.

    error/required_fields/all_errors default empty and are only populated
    per-field, right before dispatching to a registered ui_element renderer
    (see LayoutEngine.get_renderer_for_element) -- a composite renderer that
    needs its own field's error/required-ness/nested errors (e.g. model_list)
    reads them from here instead of the LayoutRenderer signature growing new
    positional params every registrant would have to accept.
    """

    form_data: dict[str, Any]
    schema_defs: dict[str, Any]
    error: str | None = None
    required_fields: tuple[str, ...] = ()
    all_errors: dict[str, Any] | None = None
