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

### `render_form_html()` — the standard entry point

Import from the top-level package:

```python
from pydantic_schemaforms import render_form_html

html = render_form_html(
    MyForm,
    submit_url=”/submit”,
    framework=”bootstrap”,
    asset_mode=”vendored”,
    include_framework_assets=True,  # inline Bootstrap CSS/JS for self-contained HTML
    include_imask=True,  # enable when you use masked inputs
)
```

HTMX and IMask are **not** injected by default — pass `include_htmx_script=True` or `include_imask=True` to opt in.

If you already provide Bootstrap/Materialize in your host app, keep `include_framework_assets=False`.
Use `self_contained=True` as a shorthand for `include_framework_assets=True, asset_mode=”vendored”` — for Bootstrap this also embeds Bootstrap Icons as a data URI (truly zero external dependencies).

### `EnhancedFormRenderer` — direct renderer instance

Use this when you want to render multiple forms with the same configuration, or when you need finer control over the rendering pipeline.

```python
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer

renderer = EnhancedFormRenderer(
    framework=”bootstrap”,
    include_framework_assets=True,
    asset_mode=”vendored”,
)
html = renderer.render_form_from_model(MyForm, submit_url=”/submit”)
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
  submit_url="/submit",
    title="Signup",
    include_framework_assets=True,
    asset_mode="vendored",
)
```

## What’s currently vendored

| Asset | Files |
|---|---|
| HTMX | `htmx.min.js` |
| IMask | `imask.min.js` |
| Bootstrap | `bootstrap.min.css`, `bootstrap.bundle.min.js` |
| Bootstrap Icons | `bootstrap-icons.min.css`, `bootstrap-icons.woff2` |
| Materialize | `materialize.min.css`, `materialize.min.js` |

See `pydantic_schemaforms/assets/vendor/vendor_manifest.json` for exact versions, SHA256 checksums, and source URLs.

## Bootstrap Icons

Bootstrap Icons are included as part of the Bootstrap theme’s asset delivery.  The library
emits `<i class="bi bi-*">` elements for icons (password-toggle, field icons, etc.), so the
icon font must be present for those elements to render correctly.

**When `include_framework_assets=True` (or `self_contained=True`):**

The CSS is inlined as a `<style>` block with the `bootstrap-icons.woff2` font embedded as a
`data:font/woff2;base64,…` URI.  No network request is made — the icon font is fully
self-contained in the HTML.

**When `include_framework_assets=False` (default):**

Bootstrap Icons are not injected by the library.  Your host page is responsible for providing
them.  Options:

- **Use the library’s vendor endpoint** (recommended for apps built on this library):

  ```python
  # In your FastAPI/Flask app
  from pydantic_schemaforms.assets.runtime import bootstrap_icons_css_content

  @app.get("/vendor/bootstrap-icons.css")
  async def bootstrap_icons():
      return Response(content=bootstrap_icons_css_content(), media_type="text/css")
  ```

  Then in your base template:

  ```html
  <link rel="stylesheet" href="/vendor/bootstrap-icons.css" />
  ```

- **CDN** (when `asset_mode="cdn"` and `include_framework_assets=True`): the library emits a
  pinned `<link>` to jsDelivr.

- **Your own asset pipeline**: import `bootstrap-icons` from npm and bundle it yourself.

### Runtime API

```python
from pydantic_schemaforms.assets.runtime import (
    bootstrap_icons_css_tag,     # returns <style>…</style> / <link …/> / ""
    bootstrap_icons_css_content, # returns raw CSS string with woff2 embedded
)

# Inline vendored CSS (default)
tag = bootstrap_icons_css_tag(asset_mode="vendored")

# Pinned CDN link
tag = bootstrap_icons_css_tag(asset_mode="cdn")

# Nothing (you manage the asset yourself)
tag = bootstrap_icons_css_tag(asset_mode="none")

# Raw CSS for serving via your own HTTP endpoint
css = bootstrap_icons_css_content()
```

## Updating vendored assets

Vendored updates are scripted and checksum-verified.

- Verify vendored checksums:
  - `make vendor-verify`

- Update assets:
  - `make vendor-update-htmx HTMX_VERSION=…`
  - `make vendor-update-imask IMASK_VERSION=…` (or omit to use npm latest)
  - `make vendor-update-bootstrap BOOTSTRAP_VERSION=…`
  - `make vendor-update-bootstrap-icons BOOTSTRAP_ICONS_VERSION=…`
  - `make vendor-update-materialize MATERIALIZE_VERSION=…`

After updating, run `make vendor-verify` and the test suite.

## Security note

`asset_mode="cdn"` is intentionally available, but it re-introduces an external dependency at runtime. For production systems with strict supply-chain or offline requirements, prefer `asset_mode="vendored"`.
