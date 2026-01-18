# Tutorial: A Simple FastAPI Project

This tutorial walks through creating a small FastAPI app that renders a form from a Pydantic model using `pydantic-schemaforms`.

It also explains when to use the **sync** handler (`handle_form`) vs the **async** handler (`handle_form_async`).

## Prerequisites

- Python 3.14+

## Note: model-first rendering

This tutorial uses the builder + handler flow because it’s easy to drop into a single file demo.

If you prefer a model-first API (and want direct control of assets/layout), use:

- `pydantic_schemaforms.enhanced_renderer.render_form_html()`
- or `FormModel.render_form()`

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
from pydantic import BaseModel, EmailStr

from pydantic_schemaforms import create_form_from_model, handle_form_async


class User(BaseModel):
    name: str
    email: EmailStr


app = FastAPI(title="SchemaForms Demo")


@app.api_route("/user", methods=["GET", "POST"], response_class=HTMLResponse)
async def user_form(request: Request):
    # Build a builder from your model (choose a framework theme).
    builder = create_form_from_model(User, framework="bootstrap")

    if request.method == "POST":
        # FastAPI form parsing is async.
        form = await request.form()

        # Validate + render response.
        result = await handle_form_async(builder, submitted_data=dict(form))

        # On success, result contains parsed/validated data.
        if result.get("success"):
            return f"Saved: {result['data']}"

        # On failure, you typically re-render the form (with errors).
        return result["form_html"]

    # Initial render.
    result = await handle_form_async(builder)
    return result["form_html"]
```

## 4) Run the server

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/user

## Sync vs Async (what’s the difference?)

### `handle_form()` (sync)

Use `handle_form(builder, ...)` when your web framework is synchronous (WSGI) and you already have submitted data as a plain `dict`.

Typical environments:

- Flask / Django (classic request/response)
- CLI apps or scripts that validate a dict

Example (Flask):

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

### `handle_form_async()` (async)

Use `handle_form_async(builder, ...)` when you are in an async runtime (ASGI) and you are already `await`-ing things (like `request.form()` in FastAPI/Starlette).

Typical environments:

- FastAPI / Starlette
- Any async stack where you want to keep the request handler non-blocking

### Important FastAPI note

FastAPI’s `Request.form()` is async, so the most natural implementation is an `async def` route and `handle_form_async()`.

If you *already* have a `dict` of submitted data (for example from a different parsing path), you can still call `handle_form()` inside an `async def` route — but the moment you need to `await` request parsing, you’ll generally prefer the async handler for consistency.

## Next steps

- Learn about asset delivery (`asset_mode`) in `docs/assets.md`
- See the broader integration pattern in `docs/quickstart.md`
