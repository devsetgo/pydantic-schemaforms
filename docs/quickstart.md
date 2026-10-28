# Quick Start

Every form is a `FormModel`: declare it, render it with `render_form_html()`,
and validate submissions with `FormModel.validate()`.

## Define and render a form

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

from pydantic_schemaforms import Field, FormModel, html, render_form_html_async


class User(FormModel):
    name: str = Field(...)
    email: str = Field(..., ui_element="email")


app = FastAPI()


@app.api_route("/user", methods=["GET", "POST"], response_class=HTMLResponse)
async def user_form(request: Request):
    if request.method == "POST":
        result = User.validate(await request.form(), submit_url="/user")
        if result.is_valid:
            # html(t"...") escapes the submitted name; never use an f-string for form data.
            return str(html(t"<p>Hello {result.data['name']}!</p>"))
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

If your host page already loads Bootstrap/Material, keep defaults. If you want a fully self-contained HTML chunk, pass `self_contained=True`. For Bootstrap forms this inlines Bootstrap CSS/JS and Bootstrap Icons (woff2 embedded) — no CDN required.

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

## Sync (Flask / WSGI)

```python
from flask import Flask, request

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)


@app.route("/user", methods=["GET", "POST"])
def user_form():
    if request.method == "POST":
        result = User.validate(request.form, submit_url="/user")
        if result.is_valid:
            return str(html(t"<p>Hello {result.data['name']}!</p>"))
        return result.render_with_errors()
    return render_form_html(User, submit_url="/user")
```

`result.data` is nested like the model (`{"address": {"city": ...}}`) and
`result.errors` is a nested error tree in the same shape; see
`docs/complex_forms.md` and `docs/validation_guide.md`.

## Forms built at runtime

When the fields are only known at runtime (from a database row, an admin
screen, a config file), build the `FormModel` subclass with Pydantic's
`create_model()`. It renders and validates exactly like a declared one:

```python
from pydantic import create_model

from pydantic_schemaforms import Field, FormModel, render_form_html

spec = [("name", "text", True), ("email", "email", True), ("notes", "textarea", False)]

FeedbackForm = create_model(
    "FeedbackForm",
    __base__=FormModel,
    **{
        name: (str, Field(... if required else "", ui_element=ui_element, title=name.title()))
        for name, ui_element, required in spec
    },
)

html_out = render_form_html(FeedbackForm, submit_url="/feedback")
result = FeedbackForm.validate(submitted_form, submit_url="/feedback")
```

## Dual-use: form endpoint + JSON API

Because `FormModel` is a plain Pydantic `BaseModel`, you can use it for JSON
validation directly. Call `as_api_model()` to get a clean `BaseModel` with all
`ui_*` rendering metadata stripped — safe to use as a FastAPI typed body or
`response_model` without cluttering the OpenAPI docs.

```python
ContactSchema = ContactForm.as_api_model()

@app.post("/api/contact", response_model=ContactSchema)
async def api_contact(data: ContactSchema):
    return data          # FastAPI validates JSON; Swagger shows a clean schema
```

`Field(title=...)`, `Field(description=...)`, `Field(examples=[...])`, and all
validation constraints survive the transform unchanged.

See the full pattern in [tutorial_fastapi.md](tutorial_fastapi.md#dual-use-html-form-json-api-from-one-model).

## Notes

- Asset delivery (`asset_mode`) and full-page wrappers are documented in [assets.md](assets.md).
