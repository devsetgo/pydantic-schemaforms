"""Integration convenience imports with lazy framework adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .builder import (
    AutoFormBuilder,
    FormBuilder,
    create_contact_form,
    create_form_from_model,
    create_login_form,
    create_registration_form,
    render_form_page,
)
from .react import ReactJSONSchemaIntegration
from .schema import JSONSchemaGenerator, OpenAPISchemaGenerator
from .utils import (
    check_framework_availability,
    convert_validation_rules,
    map_pydantic_to_json_schema_type,
    map_ui_element_to_framework,
)
from .vue import VueFormulateIntegration

if TYPE_CHECKING:  # pragma: no cover - import-time only for type hints
    from .frameworks import (
        FormIntegration,
        handle_form,
        handle_form_async,
        handle_async_form,
        handle_sync_form,
        normalize_form_data,
    )

__all__ = [
    "FormBuilder",
    "AutoFormBuilder",
    "FormIntegration",
    "ReactJSONSchemaIntegration",
    "VueFormulateIntegration",
    "JSONSchemaGenerator",
    "OpenAPISchemaGenerator",
    "create_login_form",
    "create_registration_form",
    "create_contact_form",
    "create_form_from_model",
    "render_form_page",
    "handle_form",
    "handle_form_async",
    "handle_sync_form",
    "handle_async_form",
    "normalize_form_data",
    "map_pydantic_to_json_schema_type",
    "map_ui_element_to_framework",
    "convert_validation_rules",
    "check_framework_availability",
]

_LAZY_EXPORTS = {
    "FormIntegration": ("pydantic_schemaforms.integration.frameworks", "FormIntegration"),
    "handle_form": ("pydantic_schemaforms.integration.frameworks", "handle_form"),
    "handle_form_async": ("pydantic_schemaforms.integration.frameworks", "handle_form_async"),
    "handle_sync_form": ("pydantic_schemaforms.integration.frameworks", "handle_sync_form"),
    "handle_async_form": ("pydantic_schemaforms.integration.frameworks", "handle_async_form"),
    "normalize_form_data": (
        "pydantic_schemaforms.integration.frameworks",
        "normalize_form_data",
    ),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        module_name, attr = _LAZY_EXPORTS[name]
        module = __import__(module_name, fromlist=[attr])
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:  # pragma: no cover - mirrors __all__ for help()
    return sorted(set(__all__))
