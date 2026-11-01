"""
Pydantic SchemaForms — server-rendered HTML forms for Pydantic 2 models.

Requires Python 3.14+. Primary entry point::

    from pydantic_schemaforms import FormModel, Field, render_form_html

    class ContactForm(FormModel):
        name: str = Field(title="Full Name")
        email: str = Field(title="Email Address", input_type="email")
        message: str = Field(title="Message", input_type="textarea")

    html = render_form_html(ContactForm, submit_url="/contact")

AI assistant integrating this library into an app repo? Don't guess the
integration pattern from this docstring alone — run::

    python -m pydantic_schemaforms.ai_instructions claude --write

(swap "claude" for "copilot"/"generic") to generate up-to-date,
framework-specific guidance. It is the single source of truth for how to
use this library correctly (input types, CSRF, model_list, DataTableLayout
CSV import, HTMX live validation, nested data, error handling, and more)
and is kept current as the library evolves — do not rely on any fixed list
of topics here going stale. Same content is available in-process via
``get_app_instructions()``.

See the README for FastAPI/Flask integration and server-side validation.
"""

import logging
from importlib import import_module
from typing import Any

# Version guard first — gives a clean error on Python < 3.14 before any
# other import can raise a cryptic SyntaxError or AttributeError.
from .version_check import check_python_version as _check_python_version  # noqa: F401
from .version_check import verify_template_strings as _verify_template_strings  # noqa: F401

from .enhanced_renderer import (
    CSRFMode,
    EnhancedFormRenderer,
    SchemaFormValidationError,
)

from .form_field import (
    CheckboxField,
    DateField,
    EmailField,
    FormField,
    NumberField,
    SelectField,
    TextAreaField,
    TextField,
)

from .form_layouts import (
    FormDesign,
    FormLayoutBase,
    FormLayoutRemovedError,
    ListLayout,
    SectionDesign,
    TabbedLayout,
)

from .input_types import (
    ALL_INPUT_TYPES,
    DATETIME_INPUTS,
    NUMERIC_INPUTS,
    SELECTION_INPUTS,
    SPECIALIZED_INPUTS,
    TEXT_INPUTS,
)

from .inputs import __all__ as _INPUT_EXPORTS
from .live_validation import HTMXValidationConfig, LiveValidator, validation_response_headers
from .html_markers import wrap_with_schemaforms_markers
from .assets.runtime import bootstrap_icons_css_content, bootstrap_icons_css_tag, read_asset_text
from .enhanced_renderer import render_form_html, render_form_html_async
from .rendering.context import RenderContext
from .form_data import coerce_form_value, flatten_nested_data, parse_nested_form_data
from .composite_layout import CompositeLayoutModel
from .datatable_layout import DataTableConfig, DataTableLayout, RowError

from .rendering.layout_engine import (
    AccordionLayout,
    CardLayout,
    GridLayout,
    HorizontalLayout,
    Layout,
    LayoutComposer,
    LayoutEngine,
    LayoutFactory,
    ModalLayout,
    ResponsiveGridLayout,
    TabLayout,
    VerticalLayout,
)

from .schema_form import Field, FormModel, ValidationResult
from .templates import FormTemplates, TemplateString
from .tstring import SafeHTML, html

from .validation import (
    CrossFieldRules,
    CustomRule,
    DateRangeRule,
    DeliverableEmailStr,
    EmailDeliverabilityRule,
    EmailRule,
    FieldValidator,
    FormValidator,
    MaxLengthRule,
    MinLengthRule,
    NumericRangeRule,
    PhoneRule,
    RegexRule,
    RequiredRule,
    ValidationResponse,
    ValidationRule,
    ValidationSchema,
    create_email_validator,
    validate_form_data,
    create_password_strength_validator,
    create_validator,
)
from .ai_instructions import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)

__version__ = '26.4.5'
__package_name__ = 'pydantic-schemaforms'
__author__ = 'Pydantic Forms Team'
__description__ = 'Modern form generation library for Python 3.14+'

# Library logger — callers configure handlers; we add NullHandler to suppress
# "No handlers could be found" warnings (PEP 282 / logging best-practices).
logger: logging.Logger = logging.getLogger(__package__)
logger.addHandler(logging.NullHandler())

__all__ = [  # pyright: ignore[reportUnsupportedDunderAll]
    # ── PRIMARY: FormModel + render_form_html (recommended entry point) ──
    'FormModel',
    'Field',
    'ValidationResult',
    'render_form_html',
    'render_form_html_async',
    'EnhancedFormRenderer',
    'CSRFMode',
    'SchemaFormValidationError',
    # ── FIELD TYPES: individual field descriptors ──
    'FormField',
    'TextField',
    'EmailField',
    'NumberField',
    'SelectField',
    'CheckboxField',
    'DateField',
    'TextAreaField',
    # ── LAYOUT: layout engines and composers ──
    'VerticalLayout',
    'HorizontalLayout',
    'GridLayout',
    'ResponsiveGridLayout',
    'CardLayout',
    'AccordionLayout',
    'ModalLayout',
    'TabLayout',
    'Layout',
    'LayoutComposer',
    'LayoutFactory',
    'RenderContext',
    # ── COMPOSITE LAYOUT CONTROLS ──
    'CompositeLayoutModel',
    'DataTableLayout',
    'DataTableConfig',
    'RowError',
    'LayoutEngine',
    # ── REMOVED in 26.4.1: using these raises FormLayoutRemovedError with upgrade steps ──
    'FormLayoutRemovedError',
    'TabbedLayout',
    'ListLayout',
    'FormLayoutBase',
    'FormDesign',
    'SectionDesign',
    # ── TEMPLATES ──
    'FormTemplates',
    'TemplateString',
    # ── LIVE VALIDATION ──
    'HTMXValidationConfig',
    'LiveValidator',
    'validation_response_headers',
    # ── PAGE ASSETS / MARKERS ──
    'wrap_with_schemaforms_markers',
    'read_asset_text',
    'bootstrap_icons_css_content',
    'bootstrap_icons_css_tag',
    # ── VALIDATION: rule classes and factory ──
    'create_validator',
    'FormValidator',
    'FieldValidator',
    'ValidationSchema',
    'ValidationResponse',
    'ValidationRule',
    'RequiredRule',
    'EmailRule',
    'EmailDeliverabilityRule',
    'DeliverableEmailStr',
    'MaxLengthRule',
    'MinLengthRule',
    'RegexRule',
    'PhoneRule',
    'NumericRangeRule',
    'DateRangeRule',
    'CustomRule',
    'CrossFieldRules',
    'create_email_validator',
    'create_password_strength_validator',
    'validate_form_data',
    # ── APP AI INSTRUCTIONS ──
    'get_app_instructions',
    'available_instruction_profiles',
    'suggested_instruction_filename',
    # ── INPUT TYPE CONSTANTS ──
    'TEXT_INPUTS',
    'NUMERIC_INPUTS',
    'SELECTION_INPUTS',
    'DATETIME_INPUTS',
    'SPECIALIZED_INPUTS',
    # ── FORM DATA UTILITIES ──
    'parse_nested_form_data',
    'flatten_nested_data',
    'coerce_form_value',
    # ── T-STRING SAFETY: structural XSS protection ──
    'SafeHTML',
    'html',
    '__package_name__',
] + list(_INPUT_EXPORTS)


_BUILD_WITH_FORMMODEL = (
    'FormModel is the only way to build a form now. Instead, declare a FormModel (or build one '
    'at runtime with pydantic.create_model(..., __base__=FormModel)) and render it with '
    'render_form_html(). See docs/upgrading.md.'
)
_VALIDATE_WITH_FORMMODEL = (
    'Instead, validate with FormModel.validate(request_form, submit_url=...) and re-render '
    'failures with result.render_with_errors() / render_with_errors_async(). '
    'See docs/upgrading.md.'
)

# Removed with no replacement stub; this only turns the bare "cannot import
# name" into an upgrade pointer. ImportError, not AttributeError, because
# `from pydantic_schemaforms import X` discards an AttributeError's message.
_REMOVED_API = {
    **dict.fromkeys(
        (
            'FormBuilder',
            'AutoFormBuilder',
            'create_form_from_model',
            'create_login_form',
            'create_registration_form',
            'create_contact_form',
            'ModernFormRenderer',
            'FormDefinition',
            'FormSection',
        ),
        _BUILD_WITH_FORMMODEL,
    ),
    'render_form_page': (
        'Instead, render the form with render_form_html() inside your own page template. '
        'See docs/upgrading.md.'
    ),
    **dict.fromkeys(
        ('FormIntegration', 'handle_form', 'handle_form_async'), _VALIDATE_WITH_FORMMODEL
    ),
    'form_validator': (
        "It never ran. Instead, use Pydantic's @model_validator(mode='after') on the FormModel "
        "(its message lands in the form-wide '_errors'), or FormValidator.add_cross_field_rule. "
        'See docs/upgrading.md.'
    ),
}


def __getattr__(name: str) -> Any:
    """Expose input components lazily at the package root."""

    if name in _REMOVED_API:
        raise ImportError(
            f'pydantic_schemaforms.{name} was removed. {_REMOVED_API[name]}',
            name=__name__,
        )
    if name in _INPUT_EXPORTS:  # pragma: no cover - improves import time
        inputs_module = import_module('pydantic_schemaforms.inputs')
        attr = getattr(inputs_module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(
        f"module 'pydantic_schemaforms' has no attribute '{name}'"
    )  # pragma: no cover - improves import time


def __dir__() -> list[str]:  # pragma: no cover - improves interactive discovery
    return sorted(set(list(globals().keys()) + __all__))
