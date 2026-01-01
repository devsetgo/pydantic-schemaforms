"""Framework-agnostic synchronous form helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .builder import FormBuilder

FormResult = Dict[str, Any]


def normalize_form_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw request payloads (e.g. checkbox "on" values)."""
    normalized: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            if len(value) == 1:
                value = value[0]
        if isinstance(value, str):
            lowered = value.lower()
            if lowered == "on":
                normalized[key] = True
                continue
            if lowered == "off":
                normalized[key] = False
                continue
        normalized[key] = value
    return normalized


def handle_sync_form(
    form_builder: FormBuilder,
    submitted_data: Optional[Dict[str, Any]] = None,
    *,
    initial_data: Optional[Dict[str, Any]] = None,
    render_on_error: bool = True,
) -> FormResult:
    """Validate and render forms for synchronous frameworks."""
    if submitted_data is not None:
        normalized = normalize_form_data(submitted_data)
        is_valid, errors = form_builder.validate_data(normalized)
        if is_valid:
            return {"success": True, "data": normalized}

        result: FormResult = {"success": False, "errors": errors}
        if render_on_error:
            result["form_html"] = form_builder.render(normalized, errors)
        return result

    form_html = form_builder.render(initial_data or {})
    return {"form_html": form_html}


__all__ = ["handle_sync_form", "normalize_form_data"]
