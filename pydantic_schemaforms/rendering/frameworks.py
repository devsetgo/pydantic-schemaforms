"""Framework configuration and component mappings for renderers."""

from __future__ import annotations

from typing import Dict, Type

from ..inputs import TextInput
from ..inputs.base import BaseInput
from ..inputs.registry import get_input_component_map

# Framework configurations extracted from the enhanced renderer to keep the class slim.
FRAMEWORKS: Dict[str, Dict[str, str]] = {
    "bootstrap": {
        "css_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
        "js_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
        "form_class": "needs-validation",
        "input_class": "form-control",
        "select_class": "form-select",
        "checkbox_class": "form-check-input",
        "radio_class": "form-check-input",
        "button_class": "btn btn-primary",
        "error_class": "invalid-feedback",
        "label_class": "form-label",
        "help_class": "form-text text-muted",
        "field_wrapper_class": "mb-3",
    },
    "material": {
        "css_url": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css",
        "js_url": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js",
        "form_class": "col s12",
        "input_class": "validate",
        "select_class": "browser-default",
        "checkbox_class": "filled-in",
        "radio_class": "",
        "button_class": "btn waves-effect waves-light",
        "error_class": "helper-text red-text",
        "label_class": "",
        "help_class": "helper-text",
        "field_wrapper_class": "input-field col s12",
    },
    "none": {
        "css_url": "",
        "js_url": "",
        "form_class": "",
        "input_class": "",
        "select_class": "",
        "checkbox_class": "",
        "radio_class": "",
        "button_class": "",
        "error_class": "error",
        "label_class": "",
        "help_class": "help-text",
        "field_wrapper_class": "field",
    },
}

UI_ELEMENT_MAPPING: Dict[str, Type[BaseInput]] = get_input_component_map()


def get_framework_config(framework: str) -> Dict[str, str]:
    """Return the framework configuration, defaulting to Bootstrap."""
    return FRAMEWORKS.get(framework, FRAMEWORKS["bootstrap"])


def get_input_component(element: str):
    """Return the input component class for the given UI element key."""
    return UI_ELEMENT_MAPPING.get(element, TextInput)
