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

See the README for framework integration (FastAPI, Flask), layout system,
validation, CSRF protection, and HTMX live validation.
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

# Enhanced FormField matching design_idea.py vision
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

# Layout composition system
from .form_layouts import FormDesign, FormLayoutBase, ListLayout, SectionDesign, TabbedLayout

# Input type constants and validation
from .input_types import (
    ALL_INPUT_TYPES,
    DATETIME_INPUTS,
    NUMERIC_INPUTS,
    SELECTION_INPUTS,
    SPECIALIZED_INPUTS,
    TEXT_INPUTS,
)

# Input component export metadata
from .inputs import __all__ as _INPUT_EXPORTS

# Core form building and rendering
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

# Live validation system
from .live_validation import HTMXValidationConfig, LiveValidator

# Modern renderer with Python 3.14 template strings
from .modern_renderer import FormDefinition, FormSection, ModernFormRenderer
from .enhanced_renderer import render_form_html, render_form_html_async
from .rendering.context import RenderContext
from .form_data import coerce_form_value, parse_nested_form_data

# Layout system
from .rendering.layout_engine import (
    AccordionLayout,
    CardLayout,
    GridLayout,
    HorizontalLayout,
    Layout,
    LayoutComposer,
    LayoutFactory,
    ModalLayout,
    ResponsiveGridLayout,
    TabLayout,
    VerticalLayout,
)

# FormModel abstraction for Pydantic models with UI hints
from .schema_form import Field, FormModel, ValidationResult, form_validator
from .templates import FormTemplates, TemplateString
from .tstring import SafeHTML, html

# Validation system
from .validation import (
    CrossFieldRules,
    CustomRule,
    DateRangeRule,
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

# Legacy compatibility (deprecated) - archived modules
# The following modules have been archived:
# - form_layout.py -> use layouts.py instead
# - form_model.py -> use schema_form.py instead
# - form_renderer.py -> use enhanced_renderer.py or modern_renderer.py instead
# - ui_elements.py -> use inputs/ directory structure instead
# - template_compat.py -> empty/unused
# App Name and version

__version__ = '26.2.2'
__package_name__ = 'pydantic-schemaforms'
__author__ = 'Pydantic Forms Team'
__description__ = 'Modern form generation library for Python 3.14+'

# Library logger — callers configure handlers; we add NullHandler to suppress
# "No handlers could be found" warnings (PEP 282 / logging best-practices).
logger: logging.Logger = logging.getLogger(__package__)
logger.addHandler(logging.NullHandler())

# Main exports for common usage
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
