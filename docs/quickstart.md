# Quick Start

This page shows two common ways to integrate pydantic-schemaforms into an app:

- Model-first rendering (`FormModel` + `render_form_html()`)
- Builder + handlers (legacy):
    - Build a `FormBuilder` (often via `create_form_from_model()`)
    - Use exactly one handler per runtime:
        - Sync: `handle_form()`
        - Async: `handle_form_async()`

## Option A: Model-first rendering (recommended)

```python
from pydantic_schemaforms import Field, FormModel, render_form_html


class User(FormModel):
    name: str = Field(...)
    email: str = Field(..., ui_element="email")


html = render_form_html(User, submit_url="/user")
```

### Async (FastAPI / ASGI)

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, render_form_html_async


class User(FormModel):
    name: str = Field(...)
    email: str = Field(..., ui_element="email")


app = FastAPI()


@app.api_route("/user", methods=["GET", "POST"], response_class=HTMLResponse)
async def user_form(request: Request):
    if request.method == "POST":
        submitted = dict(await request.form())
        result = User.validate(submitted, submit_url="/user")
        if result.is_valid:
            return f"<p>Hello {result.data['name']}!</p>"
        form_html = await result.render_with_errors_async()
    else:
        form_html = await render_form_html_async(User, submit_url="/user")

    return f"""
    <!doctype html>
    <html>
    <body>
      <h1>User</h1>
      {form_html}
    </body>
    </html>
    """
```

`User.validate()` stores the submit URL so `render_with_errors_async()` needs no arguments.
Use `render_with_errors_async()` in async routes to avoid blocking the event loop.

If your host page already loads Bootstrap/Material, keep defaults. If you want a fully self-contained HTML chunk, pass `self_contained=True`.

See: [configuration.md](configuration.md) and [assets.md](assets.md).

Template note:

- In Python f-string responses, embed `{form_html}` directly.
- In Jinja templates, render with `{{ form_html | safe }}`.

## CSRF setup

For browser forms with cookie/session auth, enable CSRF and verify token on submission.

Recommended rendering configuration:

```python
from pydantic_schemaforms import CSRFMode

form_html = await render_form_html_async(
    User,
    form_data=form_data,
    errors=errors,
    submit_url="/user",
    csrf_mode=CSRFMode.REQUIRED_PROVIDER,
    csrf_token_provider=csrf_token,
    csrf_field_name="csrf_token",
)
```

Notes:

- `csrf_mode` accepts either strings (`"off"`, `"field-only"`, `"required-provider"`) or `CSRFMode` enum values.
- Explicit `field-only` mode is debug-only and requires `debug=True`.
- Legacy `include_csrf=True` still works for backwards compatibility.

Then, in your POST handler, read and validate the submitted token before model validation.

See the full guide: [csrf.md](csrf.md).

## 1) Build a form from a Pydantic model

```python
from pydantic import BaseModel, EmailStr

from pydantic_schemaforms import create_form_from_model


class User(BaseModel):
    name: str
    email: EmailStr


builder = create_form_from_model(User, framework="bootstrap")
```

## 2) Async integration (FastAPI / ASGI)

```python
from fastapi import FastAPI, Request

from pydantic_schemaforms import create_form_from_model, handle_form_async

app = FastAPI()


@app.api_route("/user", methods=["GET", "POST"])
async def user_form(request: Request):
    builder = create_form_from_model(User, framework="bootstrap")

    if request.method == "POST":
        form = await request.form()
        result = await handle_form_async(builder, submitted_data=dict(form))
        if result.get("success"):
            return {"ok": True, "data": result["data"]}
        return result["form_html"]

    result = await handle_form_async(builder)
    return result["form_html"]
```

## 3) Sync integration (Flask / WSGI)

```python
from flask import Flask, request

from pydantic_schemaforms import create_form_from_model, handle_form

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

## Notes

- `handle_form*()` returns either `{form_html}` (initial render) or `{success: bool, ...}` (submission).
- Asset delivery (`asset_mode`) and full-page wrappers are documented in [assets.md](assets.md).
