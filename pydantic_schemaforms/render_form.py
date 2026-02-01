"""
Backwards compatible form rendering functions.
This module maintains compatibility with existing code while using the enhanced renderer.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Type, Union

from .enhanced_renderer import SchemaFormValidationError
from .enhanced_renderer import render_form_html as _core_render_form_html
from .assets.runtime import htmx_script_tag, imask_script_tag
from .schema_form import FormModel

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    *,
    submit_url: str,
    asset_mode: str = "vendored",
    include_imask: bool = False,
    debug: bool = False,
    show_timing: bool = False,
    enable_logging: bool = False,
    include_html_markers: bool = True,
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
        submit_url: Required form submission URL endpoint
        framework: CSS framework to use (bootstrap, material, none)
        enable_logging: Enable library logging (default: False, opt-in for debugging)
        **kwargs: Additional rendering options

    Returns:
        Complete HTML form as string
    """
    # Start timing
    start_time = time.perf_counter()

    # Normalize kwargs
    render_kwargs: Dict[str, Any] = dict(kwargs)

    # Set submit_url and action
    render_kwargs["submit_url"] = submit_url
    render_kwargs.setdefault("action", submit_url)
    render_kwargs.setdefault("method", "POST")

    form_html = _core_render_form_html(
        form_model_cls,
        form_data=form_data,
        errors=errors,
        framework=framework,
        debug=debug,
        show_timing=show_timing,
        include_html_markers=False,
        **render_kwargs,
    )

    # Add HTMX response container and scripts for backward compatibility.
    # Default is offline-by-default: vendored HTMX is inlined unless asset_mode="cdn".
    form_html += '\n<div id="form-response"></div>'
    htmx_tag = htmx_script_tag(asset_mode=asset_mode)
    if htmx_tag:
        form_html += f"\n{htmx_tag}"

    if include_imask:
        imask_tag = imask_script_tag(asset_mode=asset_mode)
        if imask_tag:
            form_html += f"\n{imask_tag}"

    # Calculate and log render time
    render_time = time.perf_counter() - start_time
    if enable_logging:
        logger.debug(f"Form rendered in {render_time:.3f} seconds (model: {form_model_cls.__name__})")

    from .html_markers import wrap_with_schemaforms_markers

    return wrap_with_schemaforms_markers(form_html, enabled=include_html_markers)


async def render_form_html_async(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    *,
    submit_url: str,
    asset_mode: str = "vendored",
    include_imask: bool = False,
    debug: bool = False,
    show_timing: bool = False,
    enable_logging: bool = False,
    include_html_markers: bool = True,
    **kwargs,
) -> str:
    """Async wrapper for render_form_html that avoids blocking the event loop."""

    def render_callable():
        return render_form_html(
            form_model_cls,
            form_data=form_data,
            errors=errors,
            submit_url=submit_url,
            framework=framework,
            asset_mode=asset_mode,
            include_imask=include_imask,
            debug=debug,
            show_timing=show_timing,
            enable_logging=enable_logging,
            include_html_markers=include_html_markers,
            **kwargs,
        )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, render_callable)
