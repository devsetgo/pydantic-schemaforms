# Pydantic SchemaForms

<img align="right" src="https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/main/docs/pydantic-schemaform-logo.png" alt="Pydantic SchemaForms logo" width="336" />

[![PyPI version](https://badge.fury.io/py/pydantic-schemaforms.svg)](https://pypi.python.org/pypi/pydantic-schemaforms/)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms)](https://pepy.tech/project/pydantic-schemaforms)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms/month)](https://pepy.tech/project/pydantic-schemaforms)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms/week)](https://pepy.tech/project/pydantic-schemaforms)

**Support Python Versions**

![Static Badge](https://img.shields.io/badge/Python-3.14-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Coverage Status](https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/refs/heads/main/coverage-badge.svg)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Tests Status](https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/refs/heads/main/tests-badge.svg)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)
[![Versioning: Year-Quarter-Build](https://img.shields.io/badge/Versioning-Year--Quarter--Build-informational)](#ui-vocabulary-compatibility)

**CI/CD Pipeline:**
[![Testing - Main](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml/badge.svg?branch=main)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)
[![Testing - Dev](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml/badge.svg?branch=dev)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)

**SonarCloud:**

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=coverage)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=alert_status)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)

<br clear="right" />

> **Requires Python 3.14+** — this library uses Python 3.14 language features and will not import on older versions.

## Overview

**pydantic-schemaforms** is a modern Python library that generates dynamic HTML forms from **Pydantic 2.x+** models.

It is designed for server-rendered apps: you define a model (and optional UI hints) and get back ready-to-embed HTML with validation and framework styling.

**Key Features:**
- 🚀 **Zero-Configuration Forms**: Generate complete HTML forms directly from Pydantic models
- 🎨 **Multi-Framework Support**: Bootstrap, Material Design, and plain HTML (`framework="none"`)
- ✅ **Built-in Validation**: Client-side HTML5 + server-side Pydantic validation
- 🔧 **JSON-Schema-form style UI hints**: Uses a familiar `ui_element`, `ui_autofocus`, `ui_options` vocabulary
- 📱 **Responsive & Accessible**: Mobile-first design with full ARIA support
- 🌐 **Framework Ready**: First-class Flask and FastAPI helpers, plus plain HTML for other stacks
- 🔀 **Dual-use form + JSON API**: `as_api_model()` returns a clean Pydantic `BaseModel` — one model class drives both the HTML form and a typed JSON API, with UI metadata stripped from OpenAPI docs
- 🧬 **Standard JSON Schema output**: `get_pydantic_json_schema()` returns spec-compliant JSON Schema (`$defs`/`$ref`) for the underlying Pydantic model, including nested `BaseModel`/`List[BaseModel]` fields
- 🪆 **Nested by default, flat by choice**: `validate()` output/input mirrors the Pydantic model's nested shape by default; pass `flatten=True` for bracket+dot flat keys instead
- 🕐 **Custom date/time display formats**: `date`/`time`/`datetime` fields default to the browser's own locale-controlled display; set `date_format`/`time_format`/`datetime_format` in `ui_options` (e.g. 24-hour "military" time) to opt into any `strftime`-defined shape instead
- 📊 **Composite layout controls**: `DataTableLayout` turns a `FormModel` subclass into a CSV-import-to-table control — built-in file upload, per-cell editable widgets, row-level validation, and DataTables.js search/sort/paging — with no hand-built button HTML or load/submit branching; `model_list` renders repeating sub-forms the same way. Both plug into the same extensible layout-renderer registry documented in `docs/plugin_hooks.md`, so you can register your own composite controls the same way

> **Important**: `submit_url` is required when rendering forms. The library does not choose a default submit target.

---

## Documentation

- Docs site: [GitHub Documentation Site](https://devsetgo.github.io/pydantic-schemaforms/)
- Live Demo: [Running Demo of Current Version](https://pydantic-schemaforms.devsetgo.com)
- Source: [GitHub Source Code](https://github.com/devsetgo/pydantic-schemaforms)

## Requirements

> **Python 3.14+ is required.** The library will raise `RuntimeError` on import if your Python version is older.

- Python **3.14+** (hard requirement — no fallback or compatibility shim)
- Pydantic **2.13+** (included as a dependency)

## Quick Start

### Install

```bash
pip install pydantic-schemaforms
```

If any of your forms use an email field typed as `EmailStr` or `DeliverableEmailStr`
(the recommended pattern throughout this README and the docs), also install the `email`
extra — Pydantic's `EmailStr` requires the `email-validator` package just to *define* a
model field with that type, not only to validate a value:

```bash
pip install pydantic-schemaforms[email]
```

`DeliverableEmailStr` additionally performs a real DNS/MX lookup for the domain — see
`docs/validation_guide.md` for details.

### AI Assistant Bootstrap (for app repositories)

If you are using Copilot or Claude in your application project, you can pull
packaged instructions directly from the installed library into your app
repo's instruction file — one command, no manual copy-paste:

```bash
python -m pydantic_schemaforms.ai_instructions claude --write     # writes ./CLAUDE.md
python -m pydantic_schemaforms.ai_instructions copilot --write    # writes ./.github/copilot-instructions.md
python -m pydantic_schemaforms.ai_instructions generic > AI_INSTRUCTIONS.md
```

Or from Python:

```python
from pydantic_schemaforms import get_app_instructions, suggested_instruction_filename

assistant = 'copilot'  # or 'claude' / 'generic'
print(f'Suggested destination: {suggested_instruction_filename(assistant)}')
print(get_app_instructions(assistant))
```

This avoids having assistants reverse-engineer internals and keeps generated
app code aligned with the supported FormModel + render_form_html flow.

### FastAPI (async / ASGI)

This is the recommended “drop-in HTML” pattern for FastAPI: define a `FormModel` and call `render_form_html()`.

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.schema_form import Field, FormModel


class MinimalLoginForm(FormModel):
    username: str = Field(
        title="Username",
        ui_autofocus=True,
        ui_placeholder="demo_user",
    )
    password: str = Field(
        title="Password",
        ui_element="password",
    )
    remember_me: bool = Field(
        default=False,
        title="Remember me",
        ui_element="checkbox",
    )


app = FastAPI()


@app.api_route("/login", methods=["GET", "POST"], response_class=HTMLResponse)
async def login(request: Request, style: str = "bootstrap"):
    form_data = {}
    errors = {}

    if request.method == "POST":
        submitted = dict(await request.form())
        form_data = submitted
        try:
            MinimalLoginForm(**submitted)
        except ValidationError as e:
            errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}
    else:
        # optional demo data
        form_data = {"username": "demo_user", "remember_me": True}

    form_html = render_form_html(
        MinimalLoginForm,
        framework=style,
        form_data=form_data,
        errors=errors,
        submit_url="/login",
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Login</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"container my-5\">
  <h1 class=\"mb-4\">Login</h1>
  {form_html}
</body>
</html>"""
```

Run it:

```bash
pip install "pydantic-schemaforms[fastapi]" uvicorn
uvicorn main:app --reload
```

#### FastAPI: simple registration page

This mirrors the in-repo example apps: your host page loads Bootstrap, and `render_form_html()` returns form markup (plus any inline helper scripts), ready to embed.

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.schema_form import FormModel, Field


class UserRegistrationForm(FormModel):
    username: str = Field(title="Username", min_length=3)
    email: str = Field(title="Email", ui_element="email")
    password: str = Field(title="Password", ui_element="password", min_length=8)


app = FastAPI()


@app.api_route("/register", methods=["GET", "POST"], response_class=HTMLResponse)
async def register(request: Request):
    form_data = {}
    errors = {}

    if request.method == "POST":
        submitted = dict(await request.form())
        form_data = submitted
        try:
            UserRegistrationForm(**submitted)
        except ValidationError as e:
            errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}

    form_html = render_form_html(
        UserRegistrationForm,
        framework="bootstrap",
        form_data=form_data,
        errors=errors,
        submit_url="/register",
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Register</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"container my-5\">
  <h1 class=\"mb-4\">Register</h1>
  {form_html}
</body>
</html>"""
```

### Flask (sync / WSGI)

In synchronous apps (Flask), the simplest pattern is the same: define a `FormModel` and call `render_form_html()`.

```python
from flask import Flask, request
from pydantic import ValidationError

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.schema_form import Field, FormModel


class MinimalLoginForm(FormModel):
    username: str = Field(title="Username", ui_autofocus=True)
    password: str = Field(title="Password", ui_element="password")
    remember_me: bool = Field(default=False, title="Remember me", ui_element="checkbox")


app = Flask(__name__)


@app.route("/login", methods=["GET", "POST"])
def login():
    form_data = {}
    errors = {}

    if request.method == "POST":
        submitted = request.form.to_dict()
        form_data = submitted
        try:
            MinimalLoginForm(**submitted)
        except ValidationError as e:
            errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}

    form_html = render_form_html(
        MinimalLoginForm,
        framework="bootstrap",
        form_data=form_data,
        errors=errors,
        submit_url="/login",
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Login</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"container my-5\">
  <h1 class=\"mb-4\">Login</h1>
    {form_html}
</body>
</html>"""
```

#### Flask: simple registration page

```python
from flask import Flask, request
from pydantic import ValidationError

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.schema_form import FormModel, Field


class UserRegistrationForm(FormModel):
    username: str = Field(title="Username", min_length=3)
    email: str = Field(title="Email", ui_element="email")
    password: str = Field(title="Password", ui_element="password", min_length=8)


app = Flask(__name__)


@app.route("/register", methods=["GET", "POST"])
def register():
    form_data = {}
    errors = {}

    if request.method == "POST":
        submitted = request.form.to_dict()
        form_data = submitted
        try:
            UserRegistrationForm(**submitted)
        except ValidationError as e:
            errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}

    form_html = render_form_html(
        UserRegistrationForm,
        framework="bootstrap",
        form_data=form_data,
        errors=errors,
        submit_url="/register",
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Register</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"container my-5\">
  <h1 class=\"mb-4\">Register</h1>
    {form_html}
</body>
</html>"""
```

Template note:

- In Python f-string responses, use `{form_html}`.
- In Jinja templates, use `{{ form_html | safe }}`.

---

## UI vocabulary compatibility

The library supports a JSON-Schema-form style vocabulary (UI hints like input types and options),
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

Note: Bootstrap **markup/classes** are always generated, but Bootstrap **CSS/JS** are only included if your host template provides them or you opt into `self_contained=True` / `include_framework_assets=True`.

#### Self-contained Bootstrap (no host template assets)

If you want a single HTML string that includes Bootstrap CSS/JS inline (no CDN, no global layout requirements), use the `self_contained=True` convenience flag:

```python
from pydantic_schemaforms import render_form_html

form_html = render_form_html(
    UserRegistrationForm,
    framework=style,
    form_data=form_data,
    debug=debug,
    self_contained=True,
    submit_url="/register",
)
```

You can also call the `FormModel` convenience if you prefer:

```python
form_html = UserRegistrationForm.render_form(
    data=form_data,
    framework=style,
    debug=debug,
    self_contained=True,
    submit_url="/register",
)
```

### Material Design
```python
UserForm.render_form(framework="material", submit_url="/submit")
```
- Self-contained Material Design 3 theme (no Materialize CSS dependency)
- Floating labels and animations via `MaterialEmbeddedTheme`
- Material icons integration

### Plain HTML
```python
UserForm.render_form(framework="none", submit_url="/submit")
```
- Clean HTML5 forms
- No framework dependencies
- Easy to style with custom CSS
- FastAPI example support: append `?style=none` (for example: `/login?style=none&demo=true`)

## Renderer Architecture

- **EnhancedFormRenderer** is the canonical renderer. It walks the Pydantic `FormModel`, feeds the shared `LayoutEngine`, and delegates chrome/assets to a `RendererTheme`.
- **ModernFormRenderer** now piggybacks on Enhanced by generating a throwaway `FormModel` from legacy `FormDefinition`/`FormField` helpers. It exists so existing builder/integration code keeps working while still benefiting from the shared pipeline. (The old `Py314Renderer` alias has been removed; import `ModernFormRenderer` directly when you need the builder DSL.)

Because everything flows through Enhanced, fixes to layout, validation, or framework themes immediately apply to every renderer (Bootstrap, Material, embedded/self-contained, etc.). Choose the renderer based on the API surface you prefer (Pydantic models for `FormModel` or the builder DSL for `ModernFormRenderer`); the generated HTML is orchestrated by the same core engine either way.

---

## Advanced Examples

### Configuration Form (code/data field)
```python
class ServiceConfigForm(FormModel):
    name: str = Field(..., description="Service name")
    config: str = Field(
        "{}",
        description="Service configuration (JSON)",
        ui_element="textarea",
        ui_options={"language": "json", "rows": 10}
    )
```
Renders a plain `<textarea>` with a Format button, Tab-key indentation, and syntax
highlighting layered on top — `language` also accepts `yaml`, `toml`, `bash`, and `python`.
See `docs/recipes.md` for the full option list and per-language formatting behavior.

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
        # Convert Pydantic errors to field→message mapping
        errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}
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
            # Convert Pydantic errors to field→message mapping expected by render_form
            errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}
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

## Render Timing

The library automatically measures form rendering time with multiple display options:

### Display Timing Below Submit Button

Add a small timing display to your form:

```python
html = render_form_html(MyForm, show_timing=True, submit_url="/submit")
```

This shows: **Rendered in 0.0045s**

### Display in Debug Panel

Include comprehensive debugging information:

```python
html = render_form_html(MyForm, debug=True, submit_url="/submit")
```

Shows timing in the debug panel header: **Debug panel (development only) — 0.0045s render**

### Automatic INFO-Level Logging

Timing is **always logged** at INFO level:

```python
import logging
logging.basicConfig(level=logging.INFO)

html = render_form_html(MyForm, submit_url="/submit")
# Logs: INFO pydantic_schemaforms: Form rendered in 0.0045s
```

**Use Cases:**
- Development: Use `show_timing=True` to see performance quickly
- Debugging: Use `debug=True` to see form structure and timing
- Production: Timing is logged automatically at INFO level for monitoring

See [Render Timing Docs](https://devsetgo.github.io/pydantic-schemaforms/timing/) for complete details.

---

## Application Logging

The library provides optional DEBUG-level logging that respects your application's logging configuration:

### Automatic Timing Logs

Timing is always logged at INFO level (for production monitoring):

```python
import logging
from pydantic_schemaforms import render_form_html

logging.basicConfig(level=logging.INFO)
html = render_form_html(MyForm, submit_url="/submit")
# Timing is logged automatically
```

### Optional Debug Logs

Enable DEBUG logging to see detailed rendering steps:

```python
import logging
from pydantic_schemaforms import render_form_html

# Option 1: Application-level DEBUG
logging.basicConfig(level=logging.DEBUG)
html = render_form_html(MyForm, submit_url="/submit")
# ✅ Timing + debug logs appear

# Option 2: Per-render control
html = render_form_html(MyForm, enable_logging=True, submit_url="/submit")
# ✅ Debug logs appear for this render only
```

### Selective Logger Configuration

Enable library debugging without affecting your app's logging:

```python
import logging

# Application at INFO level
logging.basicConfig(level=logging.INFO)

# Library DEBUG logs
library_logger = logging.getLogger('pydantic_schemaforms')
library_logger.setLevel(logging.DEBUG)

html = render_form_html(MyForm, submit_url="/submit")
# ✅ Library debug logs visible
# ✅ App remains at INFO level
```

**Best Practice**: Use Approach 1 (application-level configuration) in most cases. The library respects your app's logging setup.

See [Application Logging Docs](https://devsetgo.github.io/pydantic-schemaforms/logging/) for complete details and integration examples.

---

## Examples in This Repository

The main runnable demo in this repo is the FastAPI example:

- Run: `make ex-run`
- Visit: http://localhost:8000
- Self-contained demo: http://localhost:8000/self-contained

See `examples/main.py` (composition root), `examples/fastapi_routes.py` (routes), and
`examples/shared_models.py` for the complete implementation.

For render timing and logging configuration patterns, see the
[Render Timing](https://devsetgo.github.io/pydantic-schemaforms/timing/) and
[Application Logging](https://devsetgo.github.io/pydantic-schemaforms/logging/) docs — the
standalone timing/logging demo scripts previously linked here have been removed from `examples/`.

---

## Supported Input Types

**Text Inputs:**
- `text` (default), `email`, `password`, `search`
- `tel`, `url`
- `textarea` — with an opt-in code/data mode (`ui_options={"language": "json"}`, also
  `yaml`/`toml`/`bash`/`python`) adding a client-side Format button, Tab-key indentation, and
  light syntax highlighting; see `docs/recipes.md`

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

# Render Bootstrap markup (expects host page to load Bootstrap)
html = MyForm.render_form(framework="bootstrap", submit_url="/submit")

# Render fully self-contained Bootstrap HTML (inlines vendored Bootstrap CSS/JS)
html = MyForm.render_form(framework="bootstrap", submit_url="/submit", self_contained=True)
```

#### `as_api_model()` — dual-use form + JSON API

`FormModel` is a plain Pydantic `BaseModel`, so it validates JSON directly. However, `ui_*` metadata stored in `json_schema_extra` clutters the FastAPI/OpenAPI docs when used as a body type. `as_api_model()` strips that metadata and returns a clean `BaseModel` that is safe to use as a FastAPI request/response model:

```python
from pydantic_schemaforms import Field, FormModel

class ContactForm(FormModel):
    name: str = Field(..., min_length=2, title="Full Name",
                      examples=["Alice Smith"],
                      ui_element="text", ui_placeholder="Your name")
    email: str = Field(..., title="Email", examples=["alice@example.com"],
                       ui_element="email")

# Derive once at module level — cached per subclass
ContactSchema = ContactForm.as_api_model()

@app.post("/api/contact", response_model=ContactSchema)
async def api_contact(data: ContactSchema):
    return data   # Swagger shows clean schema; no ui_* keys
```

`Field(title=...)`, `Field(examples=[...])`, descriptions, and all validation constraints (`min_length`, `ge`, `pattern`, …) are fully preserved in the API model. Only `ui_*` keys are removed.

#### `get_pydantic_json_schema()` — standard JSON Schema output

Returns the standard JSON Schema (`$defs`/`$ref` and all) of the form's underlying Pydantic model, built on `as_api_model()`. Use this — not `get_json_schema()`, which returns a flattened, UI-oriented shape for the renderer and does not represent nested fields — whenever you need a spec-compliant schema for OpenAPI tooling, a JSON Schema validator, or a code generator:

```python
schema = ContactForm.get_pydantic_json_schema()
# schema["properties"], and schema["$defs"] for any nested BaseModel/List[BaseModel] fields

schema = ContactForm.get_pydantic_json_schema(ref_template="#/components/schemas/{model}")
```

#### Nested vs. flat form data — `validate(..., flatten=True)`

`FormModel.validate()` returns `result.data` shaped exactly like the underlying Pydantic model by default — nested `BaseModel`/`List[BaseModel]` fields come back nested, matching `model_dump()`. Pass `flatten=True` to accept and return bracket+dot flat keys instead (`"pets[0].name"`, the same notation used for `model_list` field names):

```python
result = PersonForm.validate(data, submit_url="/people", flatten=True)
# result.data uses flat "field[0].sub" keys instead of nested dicts/lists
```

See "Nested vs. flat form data" in the recipes guide (`docs/recipes.md`) for a full example.

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
- `"material"` - Material Design 3 (self-contained, no external CSS framework)
- `"none"` - Plain HTML5 forms

---

## Contributing

Contributions are welcome! Please check out the [Contributing Guide](https://github.com/devsetgo/pydantic-schemaforms/blob/main/CONTRIBUTING.md) for details.

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
