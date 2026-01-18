# Assets & `asset_mode`

`pydantic-schemaforms` is **offline-by-default**: by default, rendered HTML ships all required JS/CSS from this library (vendored assets are embedded/packaged).

This page documents the standard knobs used across entry points to control asset injection.

## Terminology

- **Vendored assets**: Third-party JS/CSS copied into this repo under `pydantic_schemaforms/assets/vendor/**`.
- **Pinned**: Versions are recorded in `pydantic_schemaforms/assets/vendor/vendor_manifest.json` along with `sha256` checksums and source URLs.
- **`asset_mode`**: How a renderer should include assets.

## `asset_mode` values

Most APIs accept `asset_mode` with these values:

- `"vendored"` (default)
  - No external network required.
  - Assets are inlined (e.g., `<script>…</script>` / `<style>…</style>`) from the packaged vendor files.

- `"cdn"` (explicit opt-in)
  - Emits `<script src="…">` / `<link href="…">` tags pointing at a CDN.
  - URLs are **pinned** to the versions in the vendored manifest.

- `"none"`
  - Emits no assets.
  - Useful when your host app provides its own asset pipeline.

## Entry points

### Legacy wrapper: `render_form_html()`

File: `pydantic_schemaforms/render_form.py`

- `asset_mode="vendored" | "cdn" | "none"`
- `include_framework_assets`: whether to include framework CSS/JS (Bootstrap/Materialize) in the returned HTML.
- HTMX is included by default (vendored inline) because this wrapper historically assumed HTMX.
- IMask is available but **not injected unless requested**.

Example:

```python
from pydantic_schemaforms.render_form import render_form_html

html = render_form_html(
    MyForm,
    framework="bootstrap",
    asset_mode="vendored",
    include_framework_assets=True,  # inline Bootstrap CSS/JS for self-contained HTML
    include_imask=True,  # enable when you use masked inputs
)
```

If you already provide Bootstrap/Materialize in your host app (a global layout, bundler, etc.), keep `include_framework_assets=False` and use `asset_mode="none"` or `"vendored"` depending on whether you still want the helper to inject HTMX.

### Enhanced convenience helper: `enhanced_renderer.render_form_html()`

File: `pydantic_schemaforms/enhanced_renderer.py`

- `include_framework_assets`: include framework CSS/JS in the returned HTML (default: `False`).
- `asset_mode`: controls how those assets are emitted.
- `self_contained=True`: convenience flag equivalent to `include_framework_assets=True` and `asset_mode="vendored"`.

Example (simple “just give me a fully styled Bootstrap form”):

```python
from pydantic_schemaforms.enhanced_renderer import render_form_html

html = render_form_html(
  MyForm,
  framework="bootstrap",
  self_contained=True,
)
```

Unlike the legacy wrapper, this helper does **not** append HTMX/IMask tags; it’s a thin convenience wrapper around `EnhancedFormRenderer`.

### Enhanced renderer: `EnhancedFormRenderer`

File: `pydantic_schemaforms/enhanced_renderer.py`

- `include_framework_assets`: whether the renderer should include framework CSS/JS.
- `asset_mode`: controls whether those assets are vendored inline or pinned CDN URLs.

Example:

```python
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

renderer = EnhancedFormRenderer(
    framework="bootstrap",
    include_framework_assets=True,
    asset_mode="vendored",
)
html = renderer.render_form_from_model(MyForm)
```

### Modern/builder path: `FormBuilder` + `render_form_page()`

File: `pydantic_schemaforms/integration/builder.py`

- `FormBuilder(..., include_framework_assets=..., asset_mode=...)` controls how the builder’s form HTML is rendered.
- `render_form_page(..., include_framework_assets=..., asset_mode=...)` controls the full-page wrapper’s CSS/JS emission.

Example:

```python
from pydantic_schemaforms.integration.builder import FormBuilder, render_form_page

builder = FormBuilder(
    framework="bootstrap",
    include_framework_assets=True,
    asset_mode="vendored",
).text_input("ssn", "SSN")

page = render_form_page(
    builder,
    title="Signup",
    include_framework_assets=True,
    asset_mode="vendored",
)
```

## What’s currently vendored

- HTMX
- IMask
- Bootstrap (CSS + bundle JS)
- Materialize (CSS + JS)

See `pydantic_schemaforms/assets/vendor/vendor_manifest.json` for exact versions and file paths.

## Updating vendored assets

Vendored updates are scripted and checksum-verified.

- Verify vendored checksums:
  - `make vendor-verify`

- Update assets:
  - `make vendor-update-htmx HTMX_VERSION=…`
  - `make vendor-update-imask IMASK_VERSION=…` (or omit to use npm latest)
  - `make vendor-update-bootstrap BOOTSTRAP_VERSION=…`
  - `make vendor-update-materialize MATERIALIZE_VERSION=…`

After updating, run `make vendor-verify` and the test suite.

## Security note

`asset_mode="cdn"` is intentionally available, but it re-introduces an external dependency at runtime. For production systems with strict supply-chain or offline requirements, prefer `asset_mode="vendored"`.
