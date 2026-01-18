# Configuration

This library is driven almost entirely by **render-time options** (which framework/theme to target, whether to inline assets, what layout to use) plus **field-level UI metadata** stored in your model’s JSON Schema.

## Rendering entry points

You can render forms in a few different ways. Pick one that matches your project style:

### 1) Model-first (recommended)

Use `FormModel` + `render_form_html()`.

```python
from pydantic_schemaforms import Field, FormModel
from pydantic_schemaforms.enhanced_renderer import render_form_html


class RegistrationForm(FormModel):
    name: str = Field(..., ui_placeholder="Jane")
    email: str = Field(..., ui_element="email")


form_html = render_form_html(
    RegistrationForm,
    submit_url="/register",
    framework="bootstrap",
    layout="vertical",
)
```

If you prefer a method on the model, use `RegistrationForm.render_form(...)`.

### 2) Builder + handlers (legacy integration)

Docs and examples may still reference the builder pattern:

- Build with `create_form_from_model()`
- Validate + render with `handle_form()` / `handle_form_async()`

This remains supported for backwards compatibility, but the underlying HTML rendering flows through the same enhanced renderer pipeline.

## Framework and assets

There are two separate but related concepts:

- **Framework selection**: `framework="bootstrap" | "material" | "none"`
- **Asset delivery**: whether the form HTML includes the framework CSS/JS

### `include_framework_assets`

- `False` (default): the returned HTML assumes your *page* already loads Bootstrap/Material.
- `True`: the renderer emits framework CSS/JS tags.

### `asset_mode`

Controls *how* the framework assets are provided when `include_framework_assets=True`:

- `"vendored"`: inline the vendored CSS/JS into the output (offline-friendly).
- `"cdn"`: link to a CDN.
- `"none"`: emit no framework tags.

### `self_contained`

For convenience, `self_contained=True` forces a fully-embedded result:

- `include_framework_assets=True`
- `asset_mode="vendored"`

```python
html = render_form_html(
    RegistrationForm,
    submit_url="/register",
    self_contained=True,
)
```

See also: [docs/assets.md](assets.md)

## Layout selection

At the top level, pass `layout=` to the renderer:

- `"vertical"` (default)
- `"tabbed"`
- `"side-by-side"`

```python
html = render_form_html(RegistrationForm, layout="tabbed")
```

For advanced composition (tabs/accordion/grid wrappers and schema-defined layout fields), see [docs/layouts.md](layouts.md).

## Field UI metadata

UI metadata is stored in `json_schema_extra` with keys like `ui_element`, `ui_placeholder`, etc. The library provides a convenience wrapper `pydantic_schemaforms.Field()` that populates these keys.

Common UI keys:

- `ui_element`: widget type (see [docs/inputs.md](inputs.md))
- `ui_placeholder`
- `ui_help_text`
- `ui_options`: widget-specific options (e.g. selection choices)
- `ui_class`, `ui_style`
- `ui_disabled`, `ui_readonly`, `ui_hidden`, `ui_autofocus`
- `ui_order`: field ordering

Example:

```python
class ProfileForm(FormModel):
    bio: str = Field(
        "",
        title="Bio",
        description="A short bio shown publicly",
        ui_element="textarea",
        ui_placeholder="Tell us about yourself…",
        ui_options={"rows": 6},
        ui_order=10,
    )
```

## Escaping and templates (`|safe`)

- If you return the HTML string directly from a framework response (e.g. FastAPI `HTMLResponse`), no extra escaping happens.
- If you embed the HTML into a Jinja template, you must mark it safe:

```jinja2
{{ form_html | safe }}
```

Otherwise Jinja will escape the markup and you’ll see literal `<div>` tags in the browser.
