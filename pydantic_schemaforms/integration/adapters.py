"""High-level helpers that expose sync/async integration entry points."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .async_support import handle_async_form
from .builder import FormBuilder
from .sync import handle_sync_form

FormResult = Dict[str, Any]


def handle_form(
    form_builder: FormBuilder,
    submitted_data: Optional[Dict[str, Any]] = None,
    *,
    initial_data: Optional[Dict[str, Any]] = None,
    render_on_error: bool = True,
) -> FormResult:
    """Canonical synchronous entry point.

    - If `submitted_data` is provided, validates and returns `{success, data}` or `{success, errors, form_html}`.
    - If not, returns `{form_html}` for an initial render.
    """

    return handle_sync_form(
        form_builder,
        submitted_data=submitted_data,
        initial_data=initial_data,
        render_on_error=render_on_error,
    )


async def handle_form_async(
    form_builder: FormBuilder,
    submitted_data: Optional[Dict[str, Any]] = None,
    *,
    initial_data: Optional[Dict[str, Any]] = None,
    render_on_error: bool = True,
) -> FormResult:
    """Canonical asynchronous entry point.

    Mirrors `handle_form()` but uses the async render path.
    """

    return await handle_async_form(
        form_builder,
        submitted_data=submitted_data,
        initial_data=initial_data,
        render_on_error=render_on_error,
    )


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
        return handle_form(
            form_builder,
            submitted_data,
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
        return await handle_form_async(
            form_builder,
            submitted_data,
            initial_data=initial_data,
            render_on_error=render_on_error,
        )


__all__ = ["FormIntegration", "handle_form", "handle_form_async", "FormResult"]
