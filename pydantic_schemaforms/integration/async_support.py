"""Framework-agnostic asynchronous form helpers."""

from __future__ import annotations

from typing import Any

from .builder import FormBuilder
from .sync import normalize_form_data

FormResult = dict[str, Any]


async def handle_async_form(
    form_builder: FormBuilder,
    submitted_data: dict[str, Any] | None = None,
    *,
    initial_data: dict[str, Any] | None = None,
    render_on_error: bool = True,
) -> FormResult:
    """Validate and render forms for async frameworks (FastAPI, Litestar, etc.)."""
    if submitted_data is not None:
        normalized = normalize_form_data(submitted_data)
        is_valid, errors = form_builder.validate_data(normalized)
        if is_valid:
            return {'success': True, 'data': normalized}

        result: FormResult = {'success': False, 'errors': errors}
        if render_on_error:
            result['form_html'] = await form_builder.render_async(normalized, errors)
        return result

    form_html = await form_builder.render_async(initial_data or {})
    return {'form_html': form_html}


__all__ = ['handle_async_form']
