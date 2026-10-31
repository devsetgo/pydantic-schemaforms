# Render Timing and Logging

Two development aids: how long a form took to render, and the library's log
messages.

## Render timing

Use render timing options to inspect form performance during development.

### Timing behavior

The renderer measures render duration internally and can expose it in two ways:

1. Inline timing text in form output (`show_timing=True`)
2. Debug panel timing metadata (`debug=True`)

### Inline timing (`show_timing=True`)

```python
from pydantic_schemaforms import render_form_html

html = render_form_html(
    MyForm,
    submit_url="/submit",
    show_timing=True,
)
```

This adds a small timing indicator in the rendered form markup.

### Debug panel (`debug=True`)

```python
html = render_form_html(
    MyForm,
    submit_url="/submit",
    debug=True,
)
```

This appends a richer debug panel that includes timing plus schema/render metadata.

### Combined usage

```python
html = render_form_html(
    MyForm,
    submit_url="/submit",
    show_timing=True,
    debug=True,
)
```

Use this combination for local diagnosis of slow forms.

### Async usage

The same options are available in async mode:

```python
from pydantic_schemaforms import render_form_html_async

html = await render_form_html_async(
    MyForm,
    submit_url="/submit",
    show_timing=True,
)
```

### With logging

If you also want log output, enable it explicitly:

```python
html = render_form_html(
    MyForm,
    submit_url="/submit",
    show_timing=True,
    enable_logging=True,
)
```

`enable_logging=True` controls debug log emission and is independent of timing display in HTML.

### Tips

- Keep `show_timing=False` and `debug=False` for production-facing pages.
- Use representative data when benchmarking complex forms (nested models, model lists, layout-heavy schemas).

## Logging

pydantic-schemaforms uses Python's standard logging module and keeps detailed renderer logs opt-in.

### What is logged by default

Default behavior for rendering calls:

- No per-render debug/timing log lines are emitted.
- Form rendering still works normally with no logging setup.

This keeps production output quiet unless you opt in.

### Enabling renderer logs

Use `enable_logging=True` on render calls:

```python
from pydantic_schemaforms import render_form_html

html = render_form_html(
    MyForm,
    submit_url="/submit",
    enable_logging=True,
)
```

When enabled, the renderer emits debug lines such as render duration and model name.

### Logging level configuration

Renderer logs are emitted at DEBUG level. Configure logging accordingly:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

If your app is set to INFO/WARNING, DEBUG lines will remain hidden.

### Per-request debugging pattern

For web apps, conditionally enable logs during troubleshooting:

```python
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic_schemaforms import SafeHTML, html, render_form_html

app = FastAPI()


@app.get("/demo", response_class=HTMLResponse)
def demo(debug_logs: bool = Query(False)):
    form_html = SafeHTML(render_form_html(
        MyForm,
        submit_url="/demo",
        enable_logging=debug_logs,
    ))
    return html(t"<html><body>{form_html}</body></html>")
```

### Related options

- `show_timing=True`: displays render timing in the returned HTML.
- `debug=True`: appends the renderer debug panel to returned HTML.
- `enable_logging=True`: emits renderer debug log lines.

These options are independent and can be combined.

### Security guidance

- Avoid logging raw secrets (CSRF tokens, passwords, session IDs).
- Prefer logging outcomes and context (`route`, `request_id`, `user_id`) over sensitive payload values.
