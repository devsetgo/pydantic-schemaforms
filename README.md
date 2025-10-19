# Pydantic Forms

[![PyPI version](https://badge.fury.io/py/pydantic-forms.svg)](https://pypi.python.org/pypi/pydantic-forms/)
[![Downloads](https://static.pepy.tech/badge/pydantic-forms)](https://pepy.tech/project/pydantic-forms)
[![Downloads](https://static.pepy.tech/badge/pydantic-forms/month)](https://pepy.tech/project/pydantic-forms)
[![Downloads](https://static.pepy.tech/badge/pydantic-forms/week)](https://pepy.tech/project/pydantic-forms)

**Support Python Versions**

![Static Badge](https://img.shields.io/badge/Python-3.14-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Coverage Status](https://raw.githubusercontent.com/devsetgo/pydantic-forms/refs/heads/main/coverage-badge.svg)](./reports/coverage/index.html)
[![Tests Status](https://raw.githubusercontent.com/devsetgo/pydantic-forms/refs/heads/main/tests-badge.svg)](./reports/coverage/index.html)

**CI/CD Pipeline:**

[![Testing - Main](https://github.com/devsetgo/pydantic-forms/actions/workflows/testing.yml/badge.svg?branch=main)](https://github.com/devsetgo/pydantic-forms/actions/workflows/testing.yml)
[![Testing - Dev](https://github.com/devsetgo/pydantic-forms/actions/workflows/testing.yml/badge.svg?branch=dev)](https://github.com/devsetgo/pydantic-forms/actions/workflows/testing.yml)

**SonarCloud:**

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-forms&metric=coverage)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-forms)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-forms&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-forms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-forms&metric=alert_status)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-forms)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-forms&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-forms)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-forms&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-forms)

> **Note**: This project should be considered in beta as it is actively under development and may have breaking changes.

## Overview

**pydantic-forms** is a modern Python library that generates dynamic HTML forms using Pydantic 2.x+ models with React JSON Schema Forms compatibility. Create beautiful, validated forms with minimal code - just define your Pydantic model and get a complete HTML form with CSS framework integration.

**Key Features:**
- 🚀 **Zero-Configuration Forms**: Generate complete HTML forms directly from Pydantic models
- 🎨 **Multi-Framework Support**: Bootstrap, Material Design, Tailwind CSS, and custom frameworks
- ✅ **Built-in Validation**: Client-side HTML5 + server-side Pydantic validation
- 🔧 **React JSON Schema Forms Compatible**: Uses familiar `ui_element`, `ui_autofocus`, `ui_options` syntax
- 📱 **Responsive & Accessible**: Mobile-first design with full ARIA support
- 🌐 **Framework Agnostic**: Works with Flask, FastAPI, Django, or any Python web framework

---

## Quick Start

### Installation

```bash
pip install pydantic-forms
```

### Basic Example

```python
from pydantic_forms.schema_form import FormModel, Field
from flask import Flask

app = Flask(__name__)

# Define your form using Pydantic model + UI elements
class UserForm(FormModel):
    username: str = Field(
        ...,
        min_length=3,
        description="Choose a username",
        ui_autofocus=True
    )
    email: str = Field(
        ...,
        description="Your email address",
        ui_element="email"
    )
    age: int = Field(
        ...,
        ge=18,
        le=120,
        description="Your age",
        ui_element="number"
    )
    newsletter: bool = Field(
        False,
        description="Subscribe to newsletter",
        ui_element="checkbox"
    )

@app.route("/")
def user_form():
    # Generate complete HTML form with Bootstrap styling
    form_html = UserForm.render_form(framework="bootstrap", submit_url="/submit")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>User Form</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container my-5">
            {form_html}
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
```

That's it! You now have a fully functional, validated, accessible form with Bootstrap styling.

---

## React JSON Schema Forms Compatibility

Pydantic Forms uses the same UI element specifications as React JSON Schema Forms for familiarity:

```python
from pydantic_forms.schema_form import FormModel, Field

class ContactForm(FormModel):
    name: str = Field(
        ...,
        description="Your name",
        ui_autofocus=True  # Auto-focus this field
    )

    email: str = Field(
        ...,
        description="Email address",
        ui_element="email"  # Use email input type
    )

    phone: str = Field(
        None,
        description="Phone number",
        ui_element="tel"  # Use tel input type
    )

    website: str = Field(
        None,
        description="Your website",
        ui_element="url"  # Use URL input type
    )

    birth_date: str = Field(
        None,
        description="Birth date",
        ui_element="date"  # Use date picker
    )

    message: str = Field(
        ...,
        min_length=10,
        description="Your message",
        ui_element="textarea",
        ui_options={"rows": 4}  # Textarea with 4 rows
    )

    color_preference: str = Field(
        "#3498db",
        description="Preferred color",
        ui_element="color"  # Color picker
    )

# Generate form with Material Design
form_html = ContactForm.render_form(framework="material", submit_url="/contact")
```

**Supported UI Elements:**
- `text` (default), `email`, `password`, `tel`, `url`
- `number`, `date`, `time`, `datetime-local`, `color`
- `textarea`, `checkbox`, `radio`, `select`
- `file`, `hidden`, `range`

**UI Options:**
- `ui_autofocus`: Auto-focus the field
- `ui_options`: Additional options (e.g., `{"rows": 4}` for textarea)
- Standard Pydantic Field options: `description`, `min_length`, `max_length`, `ge`, `le`, etc.

---

## Framework Support

### Bootstrap 5 (Recommended)
```python
UserForm.render_form(framework="bootstrap", submit_url="/submit")
```
- Complete Bootstrap integration
- Form validation states and styling
- Responsive grid system
- Custom form controls

### Material Design
```python
UserForm.render_form(framework="material", submit_url="/submit")
```
- Materialize CSS framework
- Floating labels and animations
- Material icons integration

### Plain HTML
```python
UserForm.render_form(framework="none", submit_url="/submit")
```
- Clean HTML5 forms
- No framework dependencies
- Easy to style with custom CSS

---

## Advanced Examples

### File Upload Form
```python
class FileUploadForm(FormModel):
    title: str = Field(..., description="Upload title")
    files: str = Field(
        ...,
        description="Select files",
        ui_element="file",
        ui_options={"accept": ".pdf,.docx", "multiple": True}
    )
    description: str = Field(
        ...,
        description="File description",
        ui_element="textarea",
        ui_options={"rows": 3}
    )
```

### Event Creation Form
```python
class EventForm(FormModel):
    event_name: str = Field(..., description="Event name", ui_autofocus=True)
    event_datetime: str = Field(
        ...,
        description="Event date and time",
        ui_element="datetime-local"
    )
    max_attendees: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Maximum attendees",
        ui_element="number"
    )
    is_public: bool = Field(
        True,
        description="Make event public",
        ui_element="checkbox"
    )
    theme_color: str = Field(
        "#3498db",
        description="Event color",
        ui_element="color"
    )
```

### Form Validation
```python
from pydantic import ValidationError

@app.route("/submit", methods=["POST"])
def handle_submit():
    try:
        # Validate form data using your Pydantic model
        user_data = UserForm(**request.form)

        # Process valid data
        return f"Welcome {user_data.username}!"

    except ValidationError as e:
        # Handle validation errors
        errors = e.errors()
        return f"Validation failed: {errors}", 400
```

---

## Flask Integration

Complete Flask application example:

```python
from flask import Flask, request, render_template_string
from pydantic import ValidationError
from pydantic_forms.schema_form import FormModel, Field

app = Flask(__name__)

class UserRegistrationForm(FormModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Choose a unique username",
        ui_autofocus=True
    )
    email: str = Field(
        ...,
        description="Your email address",
        ui_element="email"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Choose a secure password",
        ui_element="password"
    )
    age: int = Field(
        ...,
        ge=13,
        le=120,
        description="Your age",
        ui_element="number"
    )
    newsletter: bool = Field(
        False,
        description="Subscribe to our newsletter",
        ui_element="checkbox"
    )

@app.route("/", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        try:
            # Validate form data
            user = UserRegistrationForm(**request.form)
            return f"Registration successful for {user.username}!"
        except ValidationError as e:
            errors = e.errors()
            # Re-render form with errors
            form_html = UserRegistrationForm.render_form(
                framework="bootstrap",
                submit_url="/",
                errors=errors
            )
            return render_template_string(BASE_TEMPLATE, form_html=form_html)

    # Render empty form
    form_html = UserRegistrationForm.render_form(framework="bootstrap", submit_url="/")
    return render_template_string(BASE_TEMPLATE, form_html=form_html)

BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>User Registration</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container my-5">
        <h1>User Registration</h1>
        {{ form_html | safe }}
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
```

---

## Examples in This Repository

The repository includes several complete examples:

1. **`example_usage.py`** - React JSON Schema Forms compatible examples
2. **`pydantic_example.py`** - Flask integration with multiple form types
3. **`simple_example.py`** - Basic usage without frameworks
4. **`example.py`** - Low-level UI components demonstration

Run any example:
```bash
python example_usage.py     # http://localhost:5000
python pydantic_example.py  # http://localhost:5001
python example.py           # http://localhost:5002
```

---

## Supported Input Types

**Text Inputs:**
- `text` (default), `email`, `password`, `search`
- `tel`, `url`
- `textarea`

**Numeric Inputs:**
- `number`, `range`

**Date/Time Inputs:**
- `date`, `time`, `datetime-local`
- `week`, `month`

**Selection Inputs:**
- `checkbox`, `radio`, `select`

**Specialized Inputs:**
- `file`, `color`, `hidden`

**Input Options:**
All HTML5 input attributes are supported through `ui_options` or Field parameters.

---

## API Reference

### FormModel

Extend your Pydantic models with `FormModel` to add form rendering capabilities:

```python
from pydantic_forms.schema_form import FormModel, Field

class MyForm(FormModel):
    field_name: str = Field(..., ui_element="email")

    @classmethod
    def render_form(cls, framework="bootstrap", submit_url="/submit", **kwargs):
        """Render complete HTML form"""
```

### Field Function

Enhanced Field function with UI element support:

```python
Field(
    default=...,           # Pydantic default value
    description="Label",   # Field label
    ui_element="email",    # Input type
    ui_autofocus=True,     # Auto-focus field
    ui_options={...},      # Additional options
    # All standard Pydantic Field options...
)
```

### Framework Options

- `"bootstrap"` - Bootstrap 5 styling (recommended)
- `"material"` - Material Design (Materialize CSS)
- `"none"` - Plain HTML5 forms

---

## Contributing

Contributions are welcome! Please check out the [Contributing Guide](contribute.md) for details.

**Development Setup:**
```bash
git clone https://github.com/devsetgo/pydantic-forms.git
cd pydantic-forms
pip install -e .
```

**Run Tests:**
```bash
python -m pytest tests/
```

---

## Links

- **Documentation**: [pydantic-forms Docs](https://devsetgo.github.io/pydantic-forms/)
- **Repository**: [GitHub](https://github.com/devsetgo/pydantic-forms)
- **PyPI**: [pydantic-forms](https://pypi.org/project/pydantic-forms/)
- **Issues**: [Bug Reports & Feature Requests](https://github.com/devsetgo/pydantic-forms/issues)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
