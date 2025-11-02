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

# Check Python version before any other imports
from .version_check import check_python_version, verify_template_strings

import logging
import os

# Core form building and rendering
from .integration import (
    FormBuilder,
    AutoFormBuilder,
    FormIntegration,
    create_login_form,
    create_registration_form,
    create_contact_form,
    create_form_from_model,
    render_form_page,
)

# FormModel abstraction for Pydantic models with UI hints
from .schema_form import FormModel, Field, form_validator, ValidationResult
from .enhanced_renderer import EnhancedFormRenderer, SchemaFormValidationError, render_form_html_async
from .render_form import render_form_html
# from .material_renderer import render_material_form_html_async  # Temporarily disabled due to syntax errors

# Enhanced FormField matching design_idea.py vision
from .form_field import (
    FormField,
    TextField,
    EmailField,
    NumberField,
    SelectField,
    CheckboxField,
    DateField,
    TextAreaField,
)

# Input type constants and validation
from .input_types import (
    TEXT_INPUTS,
    NUMERIC_INPUTS,
    SELECTION_INPUTS,
    DATETIME_INPUTS,
    SPECIALIZED_INPUTS,
    ALL_INPUT_TYPES,
)

# Layout composition system matching design_idea.py vision
from .form_layouts import (
    VerticalLayout,
    HorizontalLayout,
    TabbedLayout,
    ListLayout,
    SectionDesign,
    FormDesign,
)

# Modern renderer with Python 3.14 template strings
from .modern_renderer import ModernFormRenderer, FormDefinition, FormSection
from .py314_renderer import ModernFormRenderer as Py314Renderer, RenderContext
from .templates import TemplateString, FormTemplates

# Live validation system
from .live_validation import (
    LiveValidator, HTMXValidationConfig, ValidationResponse,
    create_email_validator, create_password_strength_validator
)

# Comprehensive input types
from .inputs import *

# Layout system
from .layouts import (
    Layout,
    LayoutFactory,
    HorizontalLayout,
    VerticalLayout,
    GridLayout,
    ResponsiveGridLayout,
    TabLayout,
    AccordionLayout,
    ModalLayout,
    CardLayout,
)

# Validation system
from .validation import (
    ValidationRule,
    RequiredRule,
    MinLengthRule,
    MaxLengthRule,
    RegexRule,
    EmailRule,
    PhoneRule,
    NumericRangeRule,
    DateRangeRule,
    CustomRule,
    FieldValidator,
    FormValidator,
    CrossFieldRules,
    create_validator,
)

# Legacy compatibility (deprecated) - archived modules
# The following modules have been archived:
# - form_layout.py -> use layouts.py instead
# - form_model.py -> use schema_form.py instead
# - form_renderer.py -> use enhanced_renderer.py or modern_renderer.py instead
# - ui_elements.py -> use inputs/ directory structure instead
# - template_compat.py -> empty/unused

__version__ = "25.Q4.1.beta"
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
    # FormModel abstraction and new components
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
    # Renderers
    "EnhancedFormRenderer",
    "SchemaFormValidationError",
    "render_form_html",
    "render_form_html_async",
    "render_material_form_html_async",
    # Pre-built form templates
    "create_login_form",
    "create_registration_form",
    "create_contact_form",
    # Rendering utilities
    "render_form_page",
    "ModernFormRenderer",
    # Enhanced layout composition system
    "VerticalLayout",
    "HorizontalLayout",
    "TabbedLayout",
    "ListLayout",
    "SectionDesign",
    "FormDesign",
    # Original layout components
    "Layout",
    "GridLayout",
    "TabLayout",
    "AccordionLayout",
    "ModalLayout",
    # Validation system
    "create_validator",
    "FormValidator",
    "RequiredRule",
    "EmailRule",
    # Input types (comprehensive list)
    "TEXT_INPUTS",
    "NUMERIC_INPUTS",
    "SELECTION_INPUTS",
    "DATETIME_INPUTS",
    "SPECIALIZED_INPUTS",
    # Framework integration
    "FormIntegration",
]

# Quick start documentation
__doc__ = """
Pydantic Forms - Modern Python 3.14 Form Generation

Quick Start Examples:

1. Simple form builder:
```python
from pydantic_forms import FormBuilder

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
from pydantic_forms import create_form_from_model

class User(BaseModel):
    name: str
    email: str
    age: int

form = create_form_from_model(User)
html = form.render()
```

3. Pre-built forms:
```python
from pydantic_forms import create_login_form, render_form_page

login_form = create_login_form()
page_html = render_form_page(login_form, "Login")
```

4. Advanced layouts:
```python
from pydantic_forms import FormBuilder, Layout

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
from pydantic_forms import FormIntegration
result = FormIntegration.flask_integration(form)

# FastAPI
result = await FormIntegration.fastapi_integration(form, data)
```
"""
