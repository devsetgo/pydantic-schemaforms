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
    form_data = {}
    errors = {}

    if request.method == "POST":
        submitted = dict(await request.form())
        form_data = submitted
        try:
            User(**submitted)
        except Exception as exc:
            errors = {"form": str(exc)}

    form_html = await render_form_html_async(
        User,
        form_data=form_data,
        errors=errors,
        submit_url="/user",
    )

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

You can also call `await User.render_form_async(...)` directly if you prefer a model method.
```python

If your host page already loads Bootstrap/Material, keep defaults. If you want a fully self-contained HTML chunk, pass `self_contained=True`.

See: `docs/configuration.md` and `docs/assets.md`.

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
- Asset delivery (`asset_mode`) and full-page wrappers are documented in `docs/assets.md`.
