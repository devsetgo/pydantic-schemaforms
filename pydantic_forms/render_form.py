"""
Backwards compatible form rendering functions.
This module maintains compatibility with existing code while using the enhanced renderer.
"""

from typing import Any, Dict, Optional, Type, Union

from .enhanced_renderer import (
    SchemaFormValidationError,
    render_form_html as _core_render_form_html,
)
from .schema_form import FormModel


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    htmx_post_url: str = "/submit",
    framework: str = "bootstrap",
    **kwargs,
) -> str:
    """
    Render an HTML form for the given FormModel class with UI element support.

    This function maintains backward compatibility while using the enhanced renderer
    that supports UI elements like React JSON Schema Forms.

    Args:
        form_model_cls: Pydantic FormModel class with UI element specifications
        form_data: Form data to populate fields with
        errors: Validation errors (dict or SchemaFormValidationError)
        htmx_post_url: Form submission URL (for HTMX compatibility)
        framework: CSS framework to use (bootstrap, material, none)
        **kwargs: Additional rendering options

    Returns:
        Complete HTML form as string
    """
    # Normalize kwargs + HTMX defaults
    render_kwargs: Dict[str, Any] = dict(kwargs)

    # Ensure submit_url is propagated to the shared implementation
    render_kwargs.setdefault("submit_url", htmx_post_url)
    submit_url = render_kwargs["submit_url"]

    # Apply HTMX defaults for non-material frameworks (legacy behavior)
    if framework != "material":
        htmx_attrs = {
            "hx-post": htmx_post_url,
            "hx-target": "#form-response",
            "hx-swap": "innerHTML",
        }
        for attr, value in htmx_attrs.items():
            render_kwargs.setdefault(attr, value)

    # Action/method fallbacks mirror the historical implementation
    render_kwargs.setdefault("action", submit_url)
    render_kwargs.setdefault("method", "POST")

    form_html = _core_render_form_html(
        form_model_cls,
        form_data=form_data,
        errors=errors,
        framework=framework,
        **render_kwargs,
    )

    # Add HTMX response container and scripts for backward compatibility
    form_html += '\n<div id="form-response"></div>'
    form_html += '\n<script src="https://unpkg.com/htmx.org@2.0.6"></script>'
    form_html += '\n<script src="https://unpkg.com/imask"></script>'

    return form_html
