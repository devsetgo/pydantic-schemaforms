"""Framework-specific adapters for sync/async server integrations."""

from __future__ import annotations

from ..adapters import handle_form, handle_form_async
from .adapters import FormIntegration
from .async_support import handle_async_form
from .sync import handle_sync_form, normalize_form_data

__all__ = [
    "FormIntegration",
    "handle_form",
    "handle_form_async",
    "handle_async_form",
    "handle_sync_form",
    "normalize_form_data",
]
