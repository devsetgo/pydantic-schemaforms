"""
Pydantic SchemaForms — server-rendered HTML forms for Pydantic 2 models.

Requires Python 3.14+. Primary entry point::

    from pydantic_schemaforms import FormModel, Field, render_form_html

    class ContactForm(FormModel):
        name: str = Field(title="Full Name")
        email: str = Field(title="Email Address", input_type="email")
        message: str = Field(title="Message", input_type="textarea")

    html = render_form_html(ContactForm, submit_url="/contact")

Alternatively, use the builder DSL for programmatic form construction::

    from pydantic_schemaforms import FormBuilder

    form = FormBuilder().text_input("name").email_input("email")
    html = form.set_form_attributes(submit_url="/contact").render()

AI assistant integrating this library into an app repo? Don't guess the
integration pattern from this docstring alone — run::

    python -m pydantic_schemaforms.ai_instructions claude --write

(swap "claude" for "copilot"/"generic") to generate up-to-date,
framework-specific guidance covering CSRF, model_list (repeating
sub-forms), as_api_model (dual-use JSON+HTML models), and the
Field-constraint-vs-ui_options distinction. Same content is available
in-process via ``get_app_instructions()``.

See the README for FastAPI/Flask integration and server-side validation.
Layout system and CSRF protection are covered by the guidance generated
via `ai_instructions`/`get_app_instructions()` above. HTMX live validation
is not yet part of that guidance — see the hosted docs site linked from
the README.
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
    HorizontalLayout,
    ListLayout,
    SectionDesign,
    TabbedLayout,
    VerticalLayout,
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
from .integration import (
    AutoFormBuilder,
    FormBuilder,
    FormIntegration,
    create_contact_form,
    create_form_from_model,
    create_login_form,
    create_registration_form,
    handle_form,
    handle_form_async,
    render_form_page,
)

from .live_validation import HTMXValidationConfig, LiveValidator
from .modern_renderer import FormDefinition, FormSection, ModernFormRenderer
from .enhanced_renderer import render_form_html, render_form_html_async
from .rendering.context import RenderContext
from .form_data import coerce_form_value, flatten_nested_data, parse_nested_form_data

from .rendering.layout_engine import (
    AccordionLayout,
    CardLayout,
    GridLayout,
    Layout,
    LayoutComposer,
    LayoutFactory,
    ModalLayout,
    ResponsiveGridLayout,
    TabLayout,
)

from .schema_form import Field, FormModel, ValidationResult, form_validator
from .templates import FormTemplates, TemplateString
from .tstring import SafeHTML, html

from .validation import (
    CrossFieldRules,
    CustomRule,
    DateRangeRule,
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
    create_password_strength_validator,
    create_validator,
)
from .ai_instructions import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)

__version__ = '26.3.2'
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
    'form_validator',
    'ValidationResult',
    'render_form_html',
    'render_form_html_async',
    'EnhancedFormRenderer',
    'CSRFMode',
    'SchemaFormValidationError',
    # ── BUILDER DSL: FormBuilder / AutoFormBuilder ──
    'FormBuilder',
    'AutoFormBuilder',
    'create_form_from_model',
    'create_login_form',
    'create_registration_form',
    'create_contact_form',
    'render_form_page',
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
    'TabbedLayout',
    'ListLayout',
    'FormLayoutBase',
    'FormDesign',
    'SectionDesign',
    'Layout',
    'LayoutComposer',
    'LayoutFactory',
    'RenderContext',
    # ── MODERN RENDERER ──
    'ModernFormRenderer',
    'FormDefinition',
    'FormSection',
    # ── TEMPLATES ──
    'FormTemplates',
    'TemplateString',
    # ── LIVE VALIDATION ──
    'HTMXValidationConfig',
    'LiveValidator',
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
    # ── FRAMEWORK INTEGRATION: helpers for Flask / FastAPI ──
    'FormIntegration',
    'handle_form',
    'handle_form_async',
    # ── FORM DATA UTILITIES ──
    'parse_nested_form_data',
    'flatten_nested_data',
    'coerce_form_value',
    # ── T-STRING SAFETY: structural XSS protection ──
    'SafeHTML',
    'html',
    '__package_name__',
] + list(_INPUT_EXPORTS)


def __getattr__(name: str) -> Any:
    """Expose input components lazily at the package root."""

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
