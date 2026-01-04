# Pydantic SchemaForms

[![PyPI version](https://badge.fury.io/py/pydantic-schemaforms.svg)](https://pypi.python.org/pypi/pydantic-schemaforms/)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms)](https://pepy.tech/project/pydantic-schemaforms)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms/month)](https://pepy.tech/project/pydantic-schemaforms)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms/week)](https://pepy.tech/project/pydantic-schemaforms)

**Support Python Versions**

![Static Badge](https://img.shields.io/badge/Python-3.14-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Coverage Status](https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/refs/heads/main/coverage-badge.svg)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Tests Status](https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/refs/heads/main/tests-badge.svg)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)

**CI/CD Pipeline:**
[![Testing - Main](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml/badge.svg?branch=main)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)
[![Testing - Dev](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml/badge.svg?branch=dev)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)

**SonarCloud:**

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=coverage)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=alert_status)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)

> **Note**: This project should be considered in beta as it is actively under development and may have breaking changes.

## Overview

**pydantic-schemaforms** is a modern Python library that generates dynamic HTML forms from **Pydantic 2.x+** models.

It is designed for server-rendered apps: you define a model (and optional UI hints) and get back ready-to-embed HTML with validation and framework styling.

**Key Features:**
- 🚀 **Zero-Configuration Forms**: Generate complete HTML forms directly from Pydantic models
- 🎨 **Multi-Framework Support**: Bootstrap, Material Design, Tailwind CSS, and custom frameworks
- ✅ **Built-in Validation**: Client-side HTML5 + server-side Pydantic validation
- 🔧 **React JSON Schema Forms Compatible**: Uses familiar `ui_element`, `ui_autofocus`, `ui_options` syntax
- 📱 **Responsive & Accessible**: Mobile-first design with full ARIA support
- 🌐 **Framework Ready**: First-class Flask and FastAPI helpers, plus plain HTML for other stacks

---

## Documentation

- Docs site: https://devsetgo.github.io/pydantic-schemaforms/
- Live Demo: https://pydantic-schemaforms.devsetgo.com
- Source: https://github.com/devsetgo/pydantic-schemaforms

## Requirements

- Python **3.14+**
- Pydantic **2.7+**

## Quick Start

### Install

```bash
pip install pydantic-schemaforms
```

### FastAPI (async / ASGI)

This is the recommended pattern for FastAPI: build a form once per request and use `handle_form_async()`.

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

from pydantic_schemaforms import create_form_from_model, handle_form_async


class User(BaseModel):
    name: str
    email: EmailStr


app = FastAPI()


@app.api_route("/user", methods=["GET", "POST"], response_class=HTMLResponse)
async def user_form(request: Request):
    builder = create_form_from_model(User, framework="bootstrap")

    if request.method == "POST":
        form = await request.form()
        result = await handle_form_async(builder, submitted_data=dict(form))
        if result.get("success"):
            return f"Saved: {result['data']}"
        return result["form_html"]

    result = await handle_form_async(builder)
    return result["form_html"]
```

Run it:

```bash
pip install "pydantic-schemaforms[fastapi]" uvicorn
uvicorn main:app --reload
```

### Flask (sync / WSGI)

In synchronous apps (Flask), use `handle_form()`.

```python
from flask import Flask, request
from pydantic import BaseModel, EmailStr

from pydantic_schemaforms import create_form_from_model, handle_form


class User(BaseModel):
    name: str
    email: EmailStr


app = Flask(__name__)


@app.route("/user", methods=["GET", "POST"])
def user_form():
    builder = create_form_from_model(User, framework="bootstrap")

    if request.method == "POST":
        result = handle_form(builder, submitted_data=request.form.to_dict())
        if result.get("success"):
            return f"Saved: {result['data']}"
        return result["form_html"]

    return handle_form(builder)["form_html"]
```

---

## React JSON Schema Forms Compatibility

The library supports a React JSON Schema Forms-style vocabulary (UI hints like input types and options),
but you can also stay “pure Pydantic” and let the defaults drive everything.

See the docs site for the current, supported UI hint patterns.

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

## Renderer Architecture

- **EnhancedFormRenderer** is the canonical renderer. It walks the Pydantic `FormModel`, feeds the shared `LayoutEngine`, and delegates chrome/assets to a `RendererTheme`.
- **ModernFormRenderer** now piggybacks on Enhanced by generating a throwaway `FormModel` from legacy `FormDefinition`/`FormField` helpers. It exists so existing builder/integration code keeps working while still benefiting from the shared pipeline. (The old `Py314Renderer` alias has been removed; import `ModernFormRenderer` directly when you need the builder DSL.)

Because everything flows through Enhanced, fixes to layout, validation, or framework themes immediately apply to every renderer (Bootstrap, Material, embedded/self-contained, etc.). Choose the renderer based on the API surface you prefer (Pydantic models for `FormModel` or the builder DSL for `ModernFormRenderer`); the generated HTML is orchestrated by the same core engine either way.

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
from pydantic_schemaforms.schema_form import FormModel, Field

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
from pydantic_schemaforms.schema_form import FormModel, Field

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
git clone https://github.com/devsetgo/pydantic-schemaforms.git
cd pydantic-schemaforms
pip install -e .
```

**Run Tests:**
```bash
python -m pytest tests/
```

---

## Links

- **Documentation**: [pydantic-schemaforms Docs](https://devsetgo.github.io/pydantic-schemaforms/)
- **Repository**: [GitHub](https://github.com/devsetgo/pydantic-schemaforms)
- **PyPI**: [pydantic-schemaforms](https://pypi.org/project/pydantic-schemaforms/)
- **Issues**: [Bug Reports & Feature Requests](https://github.com/devsetgo/pydantic-schemaforms/issues)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details:
https://github.com/devsetgo/pydantic-schemaforms/blob/main/LICENSE
