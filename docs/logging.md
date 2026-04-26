# Logging

pydantic-schemaforms uses Python's standard logging module and keeps detailed renderer logs opt-in.

## What is logged by default

Default behavior for rendering calls:

- No per-render debug/timing log lines are emitted.
- Form rendering still works normally with no logging setup.

This keeps production output quiet unless you opt in.

## Enabling renderer logs

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

## Logging level configuration

Renderer logs are emitted at DEBUG level. Configure logging accordingly:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

If your app is set to INFO/WARNING, DEBUG lines will remain hidden.

## Per-request debugging pattern

For web apps, conditionally enable logs during troubleshooting:

```python
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic_schemaforms import render_form_html

app = FastAPI()


@app.get("/demo", response_class=HTMLResponse)
def demo(debug_logs: bool = Query(False)):
    form_html = render_form_html(
        MyForm,
        submit_url="/demo",
        enable_logging=debug_logs,
    )
    return f"<html><body>{form_html}</body></html>"
```

## Related options

- `show_timing=True`: displays render timing in the returned HTML.
- `debug=True`: appends the renderer debug panel to returned HTML.
- `enable_logging=True`: emits renderer debug log lines.

These options are independent and can be combined.

## Security guidance

- Avoid logging raw secrets (CSRF tokens, passwords, session IDs).
- Prefer logging outcomes and context (`route`, `request_id`, `user_id`) over sensitive payload values.
