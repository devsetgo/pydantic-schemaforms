"""Render context helpers shared across renderer implementations."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RenderContext:
    """Immutable payload passed through render helpers to avoid shared state."""

    form_data: Dict[str, Any]
    schema_defs: Dict[str, Any]
