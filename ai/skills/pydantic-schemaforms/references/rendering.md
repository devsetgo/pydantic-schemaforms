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

<!-- INCLUDE-CODE: docs_src/recipes/jinja_template/templates/signup.html html -->

<!-- INCLUDE-CODE: docs_src/recipes/jinja_template/fastapi_app.py -->

## One model for an HTML form and a JSON API

<!-- INCLUDE-CODE: docs_src/advanced/json_api/models.py -->

<!-- INCLUDE-CODE: docs_src/advanced/json_api/fastapi_app.py -->

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
