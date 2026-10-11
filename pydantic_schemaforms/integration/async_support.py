"""Framework-agnostic asynchronous form helpers."""

from __future__ import annotations

from typing import Any

from .builder import FormBuilder
from .sync import validate_submission

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
        is_valid, errors, data = validate_submission(form_builder, submitted_data)
        if is_valid:
            return {'success': True, 'data': data}

        result: FormResult = {'success': False, 'errors': errors}
        if render_on_error:
            result['form_html'] = await form_builder.render_async(data, errors)
        return result

    form_html = await form_builder.render_async(initial_data or {})
    return {'form_html': form_html}


__all__ = ['handle_async_form']
