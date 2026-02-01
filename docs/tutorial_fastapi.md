# Tutorial: A Simple FastAPI Project

This tutorial walks through creating a small FastAPI app that renders a form from a Pydantic model using `pydantic-schemaforms`.

It uses the **async-first** render API so large forms won’t block the event loop.

## Prerequisites

- Python 3.14+

## Note: model-first rendering

This tutorial uses the model-first API (recommended). You only need:

- Define a `FormModel`
- Render it (async) with `render_form_html_async()` or `FormModel.render_form_async()`
- Drop `{{ form_html | safe }}` into your template

See [docs/configuration.md](configuration.md).

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
    <html>
      <body>
        <h1>User</h1>
        {form_html}
      </body>
    </html>
    """
```

You can also use `await User.render_form_async(...)` if you prefer a model method.

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
        form_data = request.form.to_dict()
        errors = {}
        try:
            User(**form_data)
        except Exception as exc:
            errors = {"form": str(exc)}

        return render_form_html(User, form_data=form_data, errors=errors, submit_url="/user")

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

## Next steps

- Learn about asset delivery (`asset_mode`) in `docs/assets.md`
- See the broader integration pattern in `docs/quickstart.md`
