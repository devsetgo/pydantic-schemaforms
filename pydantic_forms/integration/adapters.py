"""High-level helpers that expose sync/async integration entry points."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .async_support import handle_async_form
from .builder import FormBuilder
from .sync import handle_sync_form


class FormIntegration:
    """Facade exposing sync/async helpers for server integrations."""

    @staticmethod
    def sync_integration(
        form_builder: FormBuilder,
        *,
        submitted_data: Optional[Dict[str, Any]] = None,
        initial_data: Optional[Dict[str, Any]] = None,
        render_on_error: bool = True,
    ) -> Dict[str, Any]:
        return handle_sync_form(
            form_builder,
            submitted_data=submitted_data,
            initial_data=initial_data,
            render_on_error=render_on_error,
        )

    @staticmethod
    async def async_integration(
        form_builder: FormBuilder,
        *,
        submitted_data: Optional[Dict[str, Any]] = None,
        initial_data: Optional[Dict[str, Any]] = None,
        render_on_error: bool = True,
    ) -> Dict[str, Any]:
        return await handle_async_form(
            form_builder,
            submitted_data=submitted_data,
            initial_data=initial_data,
            render_on_error=render_on_error,
        )


__all__ = ["FormIntegration"]
