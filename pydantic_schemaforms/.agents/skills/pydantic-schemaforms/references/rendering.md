<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/pydantic-schemaforms/references/rendering.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
# Rendering reference

## `render_form_html()` options

`render_form_html(Model, form_data=None, errors=None, framework="bootstrap", *, submit_url, ...)`
returns the `<form>` with its fields, error summary, submit button and the small scripts its
inputs need. It's a fragment for a page, not a whole page. `render_form_html_async()` takes the
same arguments and renders in a worker thread; use it in `async def` routes.
`Model.render_form(...)` is the same as `render_form_html(Model, ...)`.

| Option | Default | Effect |
|---|---|---|
| `submit_url` | required | The form's `action`; never guessed |
| `form_data` | `None` | Values to show; `None` starts from field defaults |
| `errors` | `None` | Messages shaped like the data; `"_errors"` for the whole form |
| `framework` | `"bootstrap"` | `"bootstrap"`, `"material"` or `"none"` |
| `layout` | `"vertical"` | See the complex forms reference |
| `wizard_options` | `None` | With `layout="wizard"` |
| `method` | `"POST"` | The form's method |
| `include_submit_button` | `True` | `False` when the form is submitted another way |
| `csrf_mode`, `csrf_token_provider`, `csrf_field_name` | `"off"` | See the security reference |
| `include_framework_assets` | `False` | Add the framework's CSS and JavaScript |
| `asset_mode` | `"vendored"` | With assets: `"vendored"` inlines packaged copies, `"cdn"` links pinned CDN URLs |
| `self_contained` | `False` | Assets inlined, Bootstrap Icons included: no external requests at all |
| `show_timing` / `debug` / `enable_logging` | `False` | Render time under the form / a debug panel / DEBUG log lines |
| `include_html_markers` | `True` | `<!--- Start/End Pydantic-SchemaForms -->` comments around the output |

Any other keyword becomes an attribute of the `<form>` tag (`id="signup"`,
`**{"hx-post": "/signup"}`). A form with a file input gets `enctype="multipart/form-data"`.

## Styling and assets

- **`framework="bootstrap"`** (default) uses Bootstrap 5 classes. **`"material"`** is a
  self-contained Material Design 3 style with its own CSS; it needs no external framework.
  `material_variant="filled"` gives filled text fields, `data-md-theme="dark"` on an ancestor
  gives the dark scheme, and overriding `--md-sys-color-*` on `.md-form` re-colors it.
  **`"none"`** is plain semantic HTML with no framework classes.
- By default **no framework CSS is included**: the app's page template is expected to load it.
  `include_framework_assets=True` adds it (inlined by default, or `asset_mode="cdn"`).
- Use the same `framework=` in `validate()`, so the failed form comes back in the same style.
- HTMX (live validation) and IMask are not included by `render_form_html()`. Load them in the
  page, or serve the packaged copies:
  `read_asset_text("assets/vendor/htmx/htmx.min.js")`.

## Putting the form in a page template

`render_form_html()` returns trusted HTML, so mark it safe in the template and nothing else:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sign up</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body>
  <main class="container py-4" style="max-width: 40rem">
    <h1>Sign up</h1>
    {% if name %}
      <div class="alert alert-success">Welcome aboard, {{ name }}!</div>
    {% endif %}
    {{ form_html | safe }}
  </main>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models import SignupForm

from pydantic_schemaforms import render_form_html_async

app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


@app.get('/signup', response_class=HTMLResponse)
async def show_signup(request: Request):
    form_html = await render_form_html_async(SignupForm, submit_url='/signup')
    return templates.TemplateResponse(request, 'signup.html', {'form_html': form_html})


@app.post('/signup', response_class=HTMLResponse)
async def signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup')
    if not result.is_valid:
        form_html = await result.render_with_errors_async()
        return templates.TemplateResponse(
            request, 'signup.html', {'form_html': form_html}, status_code=422
        )
    form_html = await render_form_html_async(SignupForm, submit_url='/signup')
    context = {'form_html': form_html, 'name': result.data['name']}
    return templates.TemplateResponse(request, 'signup.html', context)
```

## One model for an HTML form and a JSON API

```python
from pydantic_schemaforms import Field, FormModel


class ContactForm(FormModel):
    name: str = Field(title='Full name', min_length=2, examples=['Ada Lovelace'], ui_autofocus=True)
    email: str = Field(title='Email', examples=['ada@example.com'], ui_element='email')
    message: str = Field(title='Message', min_length=10, ui_element='textarea')
```

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ContactForm

from pydantic_schemaforms import html, render_form_html_async

ContactSchema = ContactForm.as_api_model()  # same fields and rules, no ui_* settings
app = FastAPI()


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return await render_form_html_async(ContactForm, submit_url='/contact')


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), submit_url='/contact')
    if not result.is_valid:
        return await result.render_with_errors_async()
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')


@app.post('/api/contact', response_model=ContactSchema)
async def api_contact(contact: ContactSchema):
    return contact
```

- `as_api_model()` returns a plain Pydantic model with the same fields and validation but none of
  the form settings, for request bodies and `response_model`. Create it once at import time.
- `validate()` also accepts a parsed JSON body and returns the same nested errors, so a non-FastAPI
  API route can answer with `result.errors` and status 422.
- `get_pydantic_json_schema()` returns standard JSON Schema with sub-forms as `$defs`; Pydantic's
  `model_json_schema()` options pass through (for example
  `ref_template="#/components/schemas/{model}"`). `get_json_schema()` is the renderer's internal
  shape, form settings included.

## Other tools

- `EnhancedFormRenderer(framework=..., include_framework_assets=..., asset_mode=...)` with
  `.render_form_from_model(Model, data, errors, submit_url=..., layout=...)` renders many forms
  with one set of options.
- `GridLayout`, `ResponsiveGridLayout`, `HorizontalLayout`, `VerticalLayout`, `CardLayout`,
  `TabLayout`, `AccordionLayout` and `ModalLayout` arrange **already-rendered HTML** on a page
  (for example two forms side by side). They are not how a form's own fields are grouped; that's
  nested models and `layout=`.
