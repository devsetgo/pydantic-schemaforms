"""Modular integration helpers for pydantic-forms."""

from __future__ import annotations

from .adapters import FormIntegration
from .async_support import handle_async_form
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
from .sync import handle_sync_form, normalize_form_data
from .utils import (
    check_framework_availability,
    convert_validation_rules,
    map_pydantic_to_json_schema_type,
    map_ui_element_to_framework,
)
from .vue import VueFormulateIntegration

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
    "handle_sync_form",
    "handle_async_form",
    "normalize_form_data",
    "map_pydantic_to_json_schema_type",
    "map_ui_element_to_framework",
    "convert_validation_rules",
    "check_framework_availability",
]
