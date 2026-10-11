"""Framework-agnostic synchronous form helpers."""

from __future__ import annotations

from typing import Any

from .builder import FormBuilder

FormResult = dict[str, Any]


def normalize_form_data(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw request payloads (e.g. checkbox "on" values)."""
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, (list, tuple)) and len(value) == 1:
            value = value[0]
        if isinstance(value, str):
            lowered = value.lower()
            if lowered == 'on':
                normalized[key] = True
                continue
            if lowered == 'off':
                normalized[key] = False
                continue
        normalized[key] = value
    return normalized


def validate_submission(
    form_builder: FormBuilder, submitted_data: Any
) -> tuple[bool, dict[Any, Any], dict[str, Any]]:
    """Validate a raw submission: ``(is_valid, errors, data)``.

    Model-backed builders validate through the model, so ``data`` is nested
    JSON and ``errors`` a nested error tree; field-only builders use their
    flat rule-based validator.
    """
    from pydantic_schemaforms.form_data import decode_submission

    decoded = decode_submission(submitted_data)
    if form_builder.model is not None:
        from pydantic_schemaforms.validation import validate_form_data

        result = validate_form_data(form_builder.model, decoded)
        return result.is_valid, result.errors, result.data if result.is_valid else decoded
    normalized = normalize_form_data(decoded)
    is_valid, errors = form_builder.validate_data(normalized)
    return is_valid, errors, normalized


def handle_sync_form(
    form_builder: FormBuilder,
    submitted_data: dict[str, Any] | None = None,
    *,
    initial_data: dict[str, Any] | None = None,
    render_on_error: bool = True,
) -> FormResult:
    """Validate and render forms for synchronous frameworks."""
    if submitted_data is not None:
        is_valid, errors, data = validate_submission(form_builder, submitted_data)
        if is_valid:
            return {'success': True, 'data': data}

        result: FormResult = {'success': False, 'errors': errors}
        if render_on_error:
            result['form_html'] = form_builder.render(data, errors)
        return result

    form_html = form_builder.render(initial_data or {})
    return {'form_html': form_html}


__all__ = ['handle_sync_form', 'normalize_form_data', 'validate_submission']
