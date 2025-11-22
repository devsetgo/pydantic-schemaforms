"""
Backwards compatible form rendering functions.
This module maintains compatibility with existing code while using the enhanced renderer.
"""

from typing import Any, Dict, Optional, Type, Union

from .enhanced_renderer import EnhancedFormRenderer, SchemaFormValidationError
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
    # Handle SchemaFormValidationError
    if isinstance(errors, SchemaFormValidationError):
        error_dict = {err.get("name", ""): err.get("message", "") for err in errors.errors}
        errors = error_dict

    # Use Material Design renderer if requested
    if framework == "material":
        from .simple_material_renderer import SimpleMaterialRenderer

        renderer = SimpleMaterialRenderer()
        form_html = renderer.render_form_from_model(
            form_model_cls, data=form_data, errors=errors, submit_url=htmx_post_url, **kwargs
        )
    else:
        renderer = EnhancedFormRenderer(framework=framework)

        # For HTMX compatibility, add HTMX attributes
        form_attrs = {
            "hx-post": htmx_post_url,
            "hx-target": "#form-response",
            "hx-swap": "innerHTML",
        }
        form_attrs.update(kwargs)
        # Ensure action is set after kwargs update
        form_attrs["action"] = htmx_post_url

        form_html = renderer.render_form_from_model(
            form_model_cls, data=form_data, errors=errors, submit_url=htmx_post_url, **form_attrs
        )

    # Add HTMX response container and scripts for backward compatibility
    form_html += '\n<div id="form-response"></div>'
    form_html += '\n<script src="https://unpkg.com/htmx.org@2.0.6"></script>'
    form_html += '\n<script src="https://unpkg.com/imask"></script>'

    return form_html
