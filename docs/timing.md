# Render Timing

Use render timing options to inspect form performance during development.

## Timing behavior

The renderer measures render duration internally and can expose it in two ways:

1. Inline timing text in form output (`show_timing=True`)
2. Debug panel timing metadata (`debug=True`)

## Inline timing (`show_timing=True`)

```python
from pydantic_schemaforms import render_form_html

html = render_form_html(
    MyForm,
    submit_url="/submit",
    show_timing=True,
)
```

This adds a small timing indicator in the rendered form markup.

## Debug panel (`debug=True`)

```python
html = render_form_html(
    MyForm,
    submit_url="/submit",
    debug=True,
)
```

This appends a richer debug panel that includes timing plus schema/render metadata.

## Combined usage

```python
html = render_form_html(
    MyForm,
    submit_url="/submit",
    show_timing=True,
    debug=True,
)
```

Use this combination for local diagnosis of slow forms.

## Async usage

The same options are available in async mode:

```python
from pydantic_schemaforms import render_form_html_async

html = await render_form_html_async(
    MyForm,
    submit_url="/submit",
    show_timing=True,
)
```

## With logging

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

## Tips

- Keep `show_timing=False` and `debug=False` for production-facing pages.
- Use representative data when benchmarking complex forms (nested models, model lists, layout-heavy schemas).
