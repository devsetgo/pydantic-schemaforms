# Rendering API

The functions and methods that turn a model into HTML and a submission into
data. Everything is imported from the top-level package.

## `render_form_html()`

```python
render_form_html(Model, form_data=None, errors=None, framework="bootstrap", *, submit_url, ...) -> str
```

Returns the form as an HTML string: the `<form>` element with its fields,
error summary and submit button, plus the small scripts and styles the form's
inputs need. It is a fragment for your page, not a whole page.

| Argument | Default | Effect |
|---|---|---|
| `submit_url` | required | The form's `action`. Never guessed. |
| `form_data` | `None` | Values to show. `None` starts from the field defaults; a dict is used as is (see [Fields and Inputs](../tutorial/fields.md#defaults-and-pre-filled-forms)). Nested dicts, Enum members and dates are fine. |
| `errors` | `None` | Messages to show, shaped like the data: `{"email": "..."}`, `{"address": {"city": "..."}}`, `"_errors"` for the whole form |
| `framework` | `"bootstrap"` | `"bootstrap"`, `"material"` or `"none"`; see [Styling](../tutorial/styling.md) |
| `layout` | `"vertical"` | See [Layouts](layouts.md) |
| `wizard_options` | `None` | See [Layouts](layouts.md#wizard_options) |
| `method` | `"POST"` | The form's `method` |
| `include_submit_button` | `True` | `False` leaves the button out, for a form you submit some other way |
| `csrf_mode` | `"off"` | `"required-provider"` adds a hidden CSRF field; see [CSRF Protection](../tutorial/csrf.md) |
| `csrf_token_provider` | `None` | The token, or a function returning it |
| `csrf_field_name` | `"csrf_token"` | Name of the hidden CSRF field |
| `include_framework_assets` | `False` | Add the framework's CSS and JavaScript to the output |
| `asset_mode` | `"vendored"` | With assets included: `"vendored"` inlines the packaged files, `"cdn"` links pinned CDN copies |
| `self_contained` | `False` | Shortcut for `include_framework_assets=True` with inlined files, Bootstrap Icons included; see [Assets](../advanced/assets.md) |
| `show_timing` | `False` | Show how long rendering took under the form |
| `debug` | `False` | Add a debug panel with the schema, data and errors |
| `enable_logging` | `False` | Log rendering at DEBUG level; see [Render Timing and Logging](../advanced/timing-logging.md) |
| `include_html_markers` | `True` | Wrap the output in `<!--- Start/End Pydantic-SchemaForms -->` comments |
| `inject_layout_styles` | `True` | Add the small stylesheet that makes the form fill its container |

Any other keyword becomes an attribute of the `<form>` tag, for example
`id="signup"` or `**{"hx-post": "/signup"}`. A form with a file input gets
`enctype="multipart/form-data"` unless you pass your own `enctype`.

## `render_form_html_async()`

The same arguments and result as `render_form_html()`. It renders in a worker
thread so an async route doesn't block the event loop. Use it in FastAPI and
other async frameworks.

## `FormModel`

`FormModel` is a Pydantic `BaseModel` with these class methods added:

| Method | Returns |
|---|---|
| `validate(data, *, submit_url=None, framework="bootstrap", **render_options)` | A `ValidationResult`. `data` is the raw request form (`await request.form()`, `request.form`) or a nested dict such as a JSON body. Render options (`layout=`, `csrf_mode=`, ...) are kept for `render_with_errors()`. |
| `render_form(data=None, errors=None, framework="bootstrap", *, submit_url, **options)` | The same as `render_form_html(Model, ...)` |
| `as_api_model()` | A plain Pydantic model with the same fields and validation but without the form settings, for request bodies and `response_model`; see [JSON API and JSON Schema](../advanced/json-api.md) |
| `get_pydantic_json_schema(**options)` | The standard JSON Schema, with sub-forms as `$defs`; Pydantic's `model_json_schema()` options pass through |
| `get_json_schema()` | The schema the renderer uses internally, form settings included |

The model's own `model_config = {"title": "..."}` titles the form's first
group in the grouped layouts.

## `ValidationResult`

| Member | Holds |
|---|---|
| `is_valid` | `True` when everything passed |
| `data` | The validated values, nested like the model (`{}` when invalid) |
| `instance` | The validated model object (`None` when invalid) |
| `errors` | The messages, nested like the data; `"_errors"` holds form-wide ones |
| `error_list()` | The same errors as a flat list: `[{"loc": ["pets", 1, "age"], "msg": "..."}]` |
| `original_data` | The submission decoded into nested form, before validation |
| `render_with_errors(**options)` | The form again with the submitted values and the errors, using the options given to `validate()`. Pass `errors=` to show a different set, such as these merged with a `FormValidator`'s. |
| `render_with_errors_async(**options)` | The same, off the event loop |

## `html()` and `SafeHTML`

`html(t"...")` builds HTML from a Python 3.14 t-string and escapes every
interpolated value. Use it for anything you build around submitted data:

```python
from pydantic_schemaforms import html

name = result.data["name"]
page = html(t"<p>Thanks, {name}!</p>")
```

It returns a `SafeHTML`, a `str` that `html()` won't escape again, so pieces
nest. Wrap a string in `SafeHTML(...)` only when it's HTML you trust, such as
another form you rendered.

## Lower-level pieces

- `EnhancedFormRenderer(framework=..., include_framework_assets=..., asset_mode=...)`
  is the renderer behind `render_form_html()`;
  `.render_form_from_model(Model, data=None, errors=None, *, submit_url=..., ...)`
  takes the same options. Reuse one instance to render many forms with the
  same settings.
- `CSRFMode` is the enum behind `csrf_mode` (`CSRFMode.REQUIRED_PROVIDER`, ...).
- `read_asset_text(path)` returns a packaged asset, such as the vendored HTMX,
  for serving yourself; see [Assets](../advanced/assets.md).
- `parse_nested_form_data()` and `flatten_nested_data()` convert between the
  input names (`pets[0].name`) and nested data, for tests that post raw form
  data.
