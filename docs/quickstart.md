# Quick Start

This page shows the **one recommended way** to integrate pydantic-forms into an app:

- Build a `FormBuilder` (often via `create_form_from_model()`)
- Use exactly one handler per runtime:
  - Sync: `handle_form()`
  - Async: `handle_form_async()`

## 1) Build a form from a Pydantic model

```python
from pydantic import BaseModel, EmailStr

from pydantic_forms import create_form_from_model


class User(BaseModel):
    name: str
    email: EmailStr


builder = create_form_from_model(User, framework="bootstrap")
```

## 2) Sync integration (Flask / WSGI)

```python
from flask import Flask, request

from pydantic_forms import create_form_from_model, handle_form

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

## 3) Async integration (FastAPI / ASGI)

```python
from fastapi import FastAPI, Request

from pydantic_forms import create_form_from_model, handle_form_async

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

## Notes

- `handle_form*()` returns either `{form_html}` (initial render) or `{success: bool, ...}` (submission).
- Asset delivery (`asset_mode`) and full-page wrappers are documented in `docs/assets.md`.
