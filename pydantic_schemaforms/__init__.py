"""
Pydantic Forms - Modern form generation library using Python 3.14 template strings

A production-ready competitor to WTForms with React JSON Schema Forms capabilities.
Features:
- Python 3.14 native template strings (REQUIRED)
- Comprehensive HTML5 input types
- Multi-framework theming (Bootstrap, Material, Tailwind)
- Advanced validation system
- Async/sync rendering
- Layout system with responsive grids
- CSRF protection and security features

IMPORTANT: This library requires Python 3.14+ and provides NO backward compatibility.
"""

import logging
import os
from importlib import import_module

from .enhanced_renderer import (
    EnhancedFormRenderer,
    SchemaFormValidationError,
    render_form_html_async,
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
# Layout composition system matching design_idea.py vision
from .form_layouts import FormDesign, ListLayout, SectionDesign, TabbedLayout
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
from .render_form import render_form_html
from .rendering.context import RenderContext
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
    create_email_validator,
    create_password_strength_validator,
    create_validator,
)
# Check Python version before any other imports
from .version_check import check_python_version, verify_template_strings

# Legacy compatibility (deprecated) - archived modules
# The following modules have been archived:
# - form_layout.py -> use layouts.py instead
# - form_model.py -> use schema_form.py instead
# - form_renderer.py -> use enhanced_renderer.py or modern_renderer.py instead
# - ui_elements.py -> use inputs/ directory structure instead
# - template_compat.py -> empty/unused

__version__ = "26.1.2.beta"
__author__ = "Pydantic Forms Team"
__description__ = "Modern form generation library for Python 3.14+"

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Set up package-level logger
logger = logging.getLogger(__package__)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.propagate = False

# Main exports for common usage
__all__ = [
    # Primary form building interface
    "FormBuilder",
    "AutoFormBuilder",
    "create_form_from_model",
    # FormModel abstraction
    "FormModel",
    "Field",
    "form_validator",
    "ValidationResult",
    # Enhanced FormField system
    "FormField",
    "TextField",
    "EmailField",
    "NumberField",
    "SelectField",
    "CheckboxField",
    "DateField",
    "TextAreaField",
    # Core renderers
    "EnhancedFormRenderer",
    "SchemaFormValidationError",
    "render_form_html",
    "render_form_html_async",
    # Pre-built form templates
    "create_login_form",
    "create_registration_form",
    "create_contact_form",
    # Layout system
    "VerticalLayout",
    "HorizontalLayout",
    "TabbedLayout",
    "ListLayout",
    "Layout",
    "LayoutComposer",
    # Validation system
    "create_validator",
    "FormValidator",
    "RequiredRule",
    "EmailRule",
    # Input types
    "TEXT_INPUTS",
    "NUMERIC_INPUTS",
    "SELECTION_INPUTS",
    "DATETIME_INPUTS",
    "SPECIALIZED_INPUTS",
    # Framework integration
    "FormIntegration",
    "handle_form",
    "handle_form_async",
] + list(_INPUT_EXPORTS)

# Quick start documentation
__doc__ = """
Pydantic SchemaForms - Modern Python 3.14 Form Generation

Quick Start Examples:

1. Simple form builder:
```python
from pydantic_schemaforms import FormBuilder

form = (FormBuilder()
        .text_input("name", "Full Name")
        .email_input("email")
        .password_input("password")
        .required("name")
        .required("email"))

html = form.render()
```

2. Auto-generate from Pydantic model:
```python
from pydantic import BaseModel
from pydantic_schemaforms import create_form_from_model

class User(BaseModel):
    name: str
    email: str
    age: int

form = create_form_from_model(User)
html = form.render()
```

3. Pre-built forms:
```python
from pydantic_schemaforms import create_login_form, render_form_page

login_form = create_login_form()
page_html = render_form_page(login_form, "Login")
```

4. Advanced layouts:
```python
from pydantic_schemaforms import FormBuilder, Layout

form = FormBuilder()
# ... add fields ...

# Render with different layouts
grid_html = Layout.grid(form.render(), columns="1fr 1fr")
tabs_html = Layout.tabs([
    {"title": "Personal", "content": form.render()},
    {"title": "Settings", "content": "..."}
])
```

5. Framework integration:
```python
# Flask
from pydantic_schemaforms import FormIntegration
result = FormIntegration.flask_integration(form)

# FastAPI
result = await FormIntegration.fastapi_integration(form, data)
```
"""


def __getattr__(name: str):
    """Expose input components lazily at the package root."""

    if name in _INPUT_EXPORTS: # pragma: no cover - improves import time
        inputs_module = import_module("pydantic_schemaforms.inputs")
        attr = getattr(inputs_module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(
        f"module 'pydantic_schemaforms' has no attribute '{name}'"
    )  # pragma: no cover - improves import time


def __dir__():  # pragma: no cover - improves interactive discovery
    return sorted(set(list(globals().keys()) + __all__))
