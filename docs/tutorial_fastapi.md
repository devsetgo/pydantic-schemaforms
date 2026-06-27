# Tutorial: A Simple FastAPI Project

This tutorial walks through creating a small FastAPI app that renders a form from a Pydantic model using `pydantic-schemaforms`.

It uses the **async-first** render API so large forms won’t block the event loop.

## Prerequisites

- Python 3.14+

## Note: model-first rendering

This tutorial uses the model-first API (recommended). You only need:

- Define a `FormModel`
- Render it (async) with `render_form_html_async()` or `FormModel.render_form_async()`
- If using Jinja templates, render `{{ form_html | safe }}`

See [configuration.md](configuration.md).

## 1) Create a project

```bash
mkdir schemaforms-fastapi-demo
cd schemaforms-fastapi-demo
python -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

```bash
pip install "pydantic-schemaforms[fastapi]" uvicorn
```

## 3) Create `main.py`

Create a file named `main.py`:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, render_form_html_async


class User(FormModel):
    name: str = Field(...)
    email: str = Field(..., ui_element="email")


app = FastAPI(title="SchemaForms Demo")


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
    <html>
      <body>
        <h1>User</h1>
        {form_html}
      </body>
    </html>
    """
```

`User.validate()` stores the submit URL and framework so `render_with_errors_async()`
needs no arguments on failure — the re-render just works.

## 4) Run the server

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/user

## Sync vs Async (what’s the difference?)

### `render_form_html()` (sync)

Use `render_form_html()` when your web framework is synchronous (WSGI) and you already have submitted data as a plain `dict`.

Typical environments:

- Flask / Django (classic request/response)
- CLI apps or scripts that validate a dict

Example (Flask):

```python
from flask import Flask, request

from pydantic_schemaforms import Field, FormModel, render_form_html


class User(FormModel):
    name: str = Field(...)
    email: str = Field(..., ui_element="email")


app = Flask(__name__)


@app.route("/user", methods=["GET", "POST"])
def user_form():
    if request.method == "POST":
        result = User.validate(request.form.to_dict(), submit_url="/user")
        if result.is_valid:
            return f"Hello {result.data['name']}!"
        return result.render_with_errors()

    return render_form_html(User, submit_url="/user")
```

### `render_form_html_async()` (async)

Use `render_form_html_async()` when you are in an async runtime (ASGI) and you are already `await`-ing things (like `request.form()` in FastAPI/Starlette).

Typical environments:

- FastAPI / Starlette
- Any async stack where you want to keep the request handler non-blocking

### Important FastAPI note

FastAPI’s `Request.form()` is async, so the most natural implementation is an `async def` route and `render_form_html_async()`.

If you *already* have a `dict` of submitted data (for example from a different parsing path), you can still call the sync renderer inside an `async def` route — but for large forms, the async renderer avoids blocking the event loop.

## Dual-use: HTML form + JSON API from one model

`FormModel` is a plain Pydantic `BaseModel` subclass, so it can validate JSON
directly. The only friction is that `Field(ui_element=..., ui_placeholder=...)`
stores rendering metadata in the JSON schema, cluttering the OpenAPI docs when
the class is used as a FastAPI body type.

`as_api_model()` returns a new `BaseModel` with the same fields and validation
rules but no `ui_*` keys — exactly what a hand-written Pydantic model looks
like. `Field(title=...)`, `Field(description=...)`, `Field(examples=[...])`,
and all validation constraints (`min_length`, `ge`, `pattern`, …) are fully
preserved.

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, parse_nested_form_data

app = FastAPI()


class ContactForm(FormModel):
    name: str = Field(
        ...,
        min_length=2,
        title="Full Name",
        examples=["Alice Smith"],
        ui_element="text",
        ui_placeholder="Enter your full name",
    )
    email: str = Field(
        ...,
        title="Email Address",
        examples=["alice@example.com"],
        ui_element="email",
    )
    message: str = Field(
        ...,
        min_length=10,
        title="Message",
        examples=["Hello, I would like to ask about..."],
        ui_element="textarea",
    )


# Derive the clean API model once at module level — safe to use as a
# FastAPI body type or response_model.
ContactSchema = ContactForm.as_api_model()


# ── HTML form ────────────────────────────────────────────────────────────────

@app.get("/contact", response_class=HTMLResponse)
async def contact_get():
    return await ContactForm.render_form_async(submit_url="/contact")


@app.post("/contact", response_class=HTMLResponse)
async def contact_post(request: Request):
    data = parse_nested_form_data(await request.form())
    result = ContactForm.validate(data, submit_url="/contact")
    if result.is_valid:
        return f"<p>Thank you, {result.data['name']}!</p>"
    return HTMLResponse(await result.render_with_errors_async())


# ── JSON API — OpenAPI shows clean schema with examples ─────────────────────

@app.post("/api/contact", response_model=ContactSchema)
async def api_contact(data: ContactSchema):
    # `data` is a fully validated ContactSchema instance.
    # FastAPI's Swagger UI shows the request body and response schema without
    # any ui_* keys, identical to a hand-written Pydantic model.
    return data
```

**What the OpenAPI schema looks like** for the `/api/contact` body:

```json
{
  "properties": {
    "name":    { "minLength": 2, "title": "Full Name",     "examples": ["Alice Smith"],  "type": "string" },
    "email":   {                 "title": "Email Address",  "examples": ["alice@..."],    "type": "string" },
    "message": { "minLength": 10,"title": "Message",        "examples": ["Hello..."],     "type": "string" }
  },
  "required": ["name", "email", "message"]
}
```

No `ui_element`, no `ui_placeholder` — just the information an API consumer
needs.

## Next steps

- Learn about asset delivery (`asset_mode`) in [assets.md](assets.md)
- See the broader integration pattern in [quickstart.md](quickstart.md)
- Configure CSRF for browser + session workflows in [csrf.md](csrf.md)
