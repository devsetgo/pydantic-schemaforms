"""Framework configuration and component mappings for renderers."""

from __future__ import annotations


from pydantic_schemaforms.inputs import TextInput as _TextInput
from pydantic_schemaforms.inputs.base import BaseInput
from pydantic_schemaforms.inputs.registry import get_input_component_map

# TextInput is imported through the inputs package's lazy-loading __getattr__
# facade, which (necessarily) returns Any -- annotate the fallback explicitly
# so get_input_component's return type stays type[BaseInput], not
# type[BaseInput] | None.
_DEFAULT_INPUT: type[BaseInput] = _TextInput

# Framework configurations extracted from the enhanced renderer to keep the class slim.
FRAMEWORKS: dict[str, dict[str, str]] = {
    'bootstrap': {
        'css_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
        'js_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
        'form_class': 'needs-validation',
        'input_class': 'form-control',
        'select_class': 'form-select',
        'checkbox_class': 'form-check-input',
        'radio_class': 'form-check-input',
        'button_class': 'btn btn-primary',
        'error_class': 'invalid-feedback',
        'label_class': 'form-label',
        'help_class': 'form-text text-muted',
        'field_wrapper_class': 'mb-3',
    },
    'material': {
        'css_url': 'https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css',
        'js_url': 'https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js',
        'form_class': 'col s12',
        'input_class': 'validate',
        'select_class': 'browser-default',
        'checkbox_class': 'filled-in',
        'radio_class': '',
        'button_class': 'btn waves-effect waves-light',
        'error_class': 'helper-text red-text',
        'label_class': '',
        'help_class': 'helper-text',
        'field_wrapper_class': 'input-field col s12',
    },
    'none': {
        'css_url': '',
        'js_url': '',
        'form_class': '',
        'input_class': '',
        'select_class': '',
        'checkbox_class': '',
        'radio_class': '',
        'button_class': '',
        'error_class': 'error',
        'label_class': '',
        'help_class': 'help-text',
        'field_wrapper_class': 'field',
    },
}


def get_framework_config(framework: str) -> dict[str, str]:
    """Return the framework configuration, defaulting to Bootstrap."""
    return FRAMEWORKS.get(framework, FRAMEWORKS['bootstrap'])


def get_input_component(element: str) -> type[BaseInput]:
    """Return the input component class for the given UI element key.

    Calls get_input_component_map() fresh (it's @lru_cache()'d in registry.py,
    so this stays cheap) rather than reading a module-level snapshot -- a
    snapshot taken at import time would never see components registered via
    register_input_class()/register_inputs() after pydantic_schemaforms
    itself has been imported, which is every real call site (the package's
    own __init__.py eagerly imports this module transitively).
    """
    return get_input_component_map().get(element, _DEFAULT_INPUT)
