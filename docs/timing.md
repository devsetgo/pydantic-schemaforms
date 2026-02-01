# Render Timing

The pydantic-schemaforms library automatically measures the time it takes to render forms and provides multiple ways to view this performance data.

## Overview

Form rendering timing is **always measured** by the library, giving you insights into form generation performance. You control how and where this timing information is displayed through render-time options.

## Display Methods

### 1. Logging (Default)

Render time is automatically logged at **INFO level** to the library's logger:

```python
import logging
from pydantic_schemaforms import render_form_html

# Configure logging to see timing logs
logging.basicConfig(level=logging.INFO)

html = render_form_html(MyForm)
# Output: INFO pydantic_schemaforms.enhanced_renderer: Form rendered in 0.0045s
```

The logging happens **regardless** of whether you display timing visually. This means:

- ✅ Timing is always tracked for performance monitoring
- ✅ You can collect timing metrics in production (at INFO level)
- ✅ No performance overhead from timing collection

### 2. Inline Display (`show_timing=True`)

Add a small timing display below the submit button:

```python
html = render_form_html(MyForm, show_timing=True)
```

This renders:
```html
<div style="text-align: center; margin-top: 10px; font-size: 0.85rem; color: #666;">
  Rendered in 0.0045s
</div>
```

**Use case**: During development to see quick feedback on render performance.

### 3. Debug Panel (`debug=True`)

Include a comprehensive debug panel showing timing and other metadata:

```python
html = render_form_html(MyForm, debug=True)
```

The debug panel displays in the form header:
```
Debug panel (development only) — 0.0045s render
```

And includes additional information:
- Form name and model
- Number of fields
- Framework and layout info
- Timing breakdown if available

**Use case**: Development mode to understand form structure and performance.

### 4. Combined Display

You can use both `show_timing` and `debug` simultaneously:

```python
html = render_form_html(MyForm, show_timing=True, debug=True)
```

This shows timing in:
1. The inline display below submit button
2. The debug panel header
3. The INFO log

## Practical Examples

### Development: See All Timing

```python
# Enable debug panel with inline timing
html = render_form_html(
    MyForm,
    debug=True,
    show_timing=True,
    framework="bootstrap"
)
```

### Production: Collect Timing Metrics

```python
import logging

# Configure logging to collect timing in production
logging.basicConfig(level=logging.INFO)

# Render normally - timing is logged automatically
html = render_form_html(MyForm, framework="bootstrap")
```

Parse logs to collect performance metrics.

### Hide Timing from Users (but Keep Logging)

```python
# Users won't see timing, but it's still logged
html = render_form_html(MyForm, framework="bootstrap")
```

## Performance Considerations

The timing measurement itself has **minimal overhead** (typically < 0.1ms). The overhead comes from:

1. **Calling `time.time()` twice** (~0.001ms) - negligible
2. **Logging the result** (~0.1-1ms if logging is configured) - depends on log handlers
3. **Rendering the HTML display** (~0.01ms) - only if `show_timing=True`

In practice, form rendering typically takes **5-50ms** depending on form complexity, making timing overhead < 1% of total time.

## Integration with Application Logging

The timing logs respect your application's logging configuration:

```python
import logging
from pydantic_schemaforms import render_form_html

# Production: INFO level logs
logging.basicConfig(level=logging.INFO)
html = render_form_html(MyForm)
# ✅ Timing appears in logs

# Development: DEBUG level
logging.basicConfig(level=logging.DEBUG)
html = render_form_html(MyForm)
# ✅ Timing + detailed library logs appear

# Suppress library logs (but keep timing in code)
logging.getLogger('pydantic_schemaforms').setLevel(logging.WARNING)
html = render_form_html(MyForm)
# ❌ Timing logs suppressed (but timing still measured internally)
```

## FastAPI Example

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic_schemaforms import render_form_html, FormModel, Field
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class LoginForm(FormModel):
    username: str = Field(...)
    password: str = Field(..., ui_element="password")

@app.get("/login", response_class=HTMLResponse)
async def login_page(debug: bool = False):
    # Toggle timing/debug display via query parameter
    html = render_form_html(
        LoginForm,
        show_timing=debug,
        debug=debug,
        framework="bootstrap"
    )
    
    return f"""
    <!doctype html>
    <html>
    <head><title>Login</title></head>
    <body>
        <h1>Login</h1>
        {html}
        <p><small>
            <a href="?debug=true">Show timing & debug</a>
        </small></p>
    </body>
    </html>
    """
```

Visit `/login` for normal form, `/login?debug=true` to see timing and debug panel.

## Reference

### Parameters

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| `show_timing` | `bool` | `False` | Display timing below submit button |
| `debug` | `bool` | `False` | Show debug panel with timing in header |
| `enable_logging` | `bool` | `False` | Enable library DEBUG logging (separate from timing logs) |

**Note**: Timing is **always logged** at INFO level, independent of the `enable_logging` parameter.

### Logger Names

- `pydantic_schemaforms.enhanced_renderer` - Timing logs and general renderer info
- `pydantic_schemaforms` - Root logger for all library components

### Timing Accuracy

Timing uses Python's `time.time()` function:
- Precision: microsecond resolution (0.001ms)
- Accuracy: depends on OS clock (typically within 1-5ms on modern systems)
- Example: `0.0045s` means 4.5 milliseconds

## Troubleshooting

### Timing Not Appearing

**Problem**: You set `show_timing=True` but don't see timing in HTML.

**Solution**: Check that `show_timing=True` is actually being passed. Common mistakes:

```python
# ❌ Wrong - parameter ignored
html = render_form_html(MyForm)

# ✅ Correct
html = render_form_html(MyForm, show_timing=True)
```

### Logs Not Appearing

**Problem**: Timing logs don't appear even with logging configured.

**Solution**: Ensure logging level is at INFO or DEBUG:

```python
import logging

# ❌ WRONG - WARNING level suppresses INFO logs
logging.basicConfig(level=logging.WARNING)

# ✅ CORRECT - INFO level shows timing
logging.basicConfig(level=logging.INFO)
```

### Performance Unexpectedly Slow

**Problem**: Form rendering takes > 100ms.

**Solution**: Check form complexity:

1. Use `debug=True` to see form structure
2. Check if rendering multiple forms in a loop
3. Enable DEBUG logging for detailed timing breakdown:

```python
logging.basicConfig(level=logging.DEBUG)
html = render_form_html(MyForm, debug=True)
```

