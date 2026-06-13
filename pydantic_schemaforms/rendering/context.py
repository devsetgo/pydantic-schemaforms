"""Render context helpers shared across renderer implementations."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RenderContext:
    """Immutable payload passed through render helpers to avoid shared state."""

    form_data: dict[str, Any]
    schema_defs: dict[str, Any]
