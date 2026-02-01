# Logging

The pydantic-schemaforms library uses Python's standard logging module to provide visibility into form rendering operations. By default, the library logs at DEBUG level, so logs won't appear in typical production setups.

## Overview

Logging in pydantic-schemaforms is designed to:

- ✅ Not interfere with your application's logging
- ✅ Provide detailed debug information when needed
- ✅ Use standard Python logging practices
- ✅ Always log timing information (at INFO level, not DEBUG)

## Logging Levels

### Library Logs (DEBUG level)

The library uses DEBUG level for detailed information:

```python
import logging

# Configure to see library DEBUG logs
logging.basicConfig(level=logging.DEBUG)

from pydantic_schemaforms import render_form_html

html = render_form_html(MyForm)
# Now you'll see DEBUG logs from the library
```

Examples of DEBUG logs:
- Schema parsing steps
- Field rendering decisions
- Asset inclusion checks
- Layout calculations

### Timing Logs (INFO level)

Render timing is logged at **INFO level**, so it appears even in production:

```python
import logging

logging.basicConfig(level=logging.INFO)

html = render_form_html(MyForm)
# Output: INFO pydantic_schemaforms.enhanced_renderer: Form rendered in 0.0045s
```

This is intentional - timing metrics are valuable for production monitoring while keeping other debug logs suppressed.

## Configuration Approaches

### Approach 1: Application-Level Control (Recommended)

Configure your application's logging level. The library respects it:

```python
import logging

# Production: INFO level
logging.basicConfig(level=logging.INFO)
# ✅ Timing logs appear
# ❌ Library DEBUG logs suppressed

# Development: DEBUG level
logging.basicConfig(level=logging.DEBUG)
# ✅ Timing logs appear
# ✅ Library DEBUG logs appear

# Silent: WARNING level
logging.basicConfig(level=logging.WARNING)
# ❌ Timing logs suppressed
# ❌ Library DEBUG logs suppressed
```

**Pros**:
- Standard Python logging approach
- Simple and predictable
- Works with all logging handlers

**Cons**:
- Can't selectively enable library logs without enabling all DEBUG logs

### Approach 2: Library-Specific Control

Enable/disable logging **per render call**:

```python
from pydantic_schemaforms import render_form_html

# Enable library DEBUG logs for this render
html = render_form_html(MyForm, enable_logging=True)

# Disable library DEBUG logs even if DEBUG level is set
html = render_form_html(MyForm, enable_logging=False)
```

**Pros**:
- Fine-grained control per call
- Can debug specific forms

**Cons**:
- `enable_logging` only controls DEBUG level
- `enable_logging` doesn't affect timing logs (INFO level)

**Note**: `enable_logging` is for DEBUG logs. Timing (INFO level) is always logged unless you configure logging levels.

### Approach 3: Selective Logger Configuration

Enable DEBUG logging only for the library:

```python
import logging

# Application logs at INFO level
logging.basicConfig(level=logging.INFO)

# Library logs at DEBUG level
library_logger = logging.getLogger('pydantic_schemaforms')
library_logger.setLevel(logging.DEBUG)

from pydantic_schemaforms import render_form_html

html = render_form_html(MyForm)
# ✅ Timing logs appear (INFO)
# ✅ Library DEBUG logs appear
# ✅ Other DEBUG logs from your app are suppressed
```

**Pros**:
- Selective logging without affecting app
- Can debug library without app noise

**Cons**:
- More complex setup
- Requires understanding logger hierarchy

## Practical Scenarios

### Production Server

```python
# At app startup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Forms render normally
html = render_form_html(MyForm)
# ✅ Timing appears in logs for monitoring
# ❌ Debug logs suppressed
```

### Local Development

```python
# At app startup
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# See all details
html = render_form_html(MyForm)
# ✅ Timing logs appear
# ✅ Detailed library DEBUG logs appear
```

### Development (Want App Logs Only)

```python
import logging

# App at DEBUG level, library at WARNING level
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pydantic_schemaforms').setLevel(logging.WARNING)

html = render_form_html(MyForm)
# ✅ Your app's DEBUG logs appear
# ❌ Library logs suppressed
```

### Debugging a Specific Form

```python
import logging

# Global INFO level
logging.basicConfig(level=logging.INFO)

# Debug this specific form
html = render_form_html(MyForm, enable_logging=True)

# Render other forms normally (no debug logs)
html2 = render_form_html(OtherForm)
```

## FastAPI Integration

### Example 1: Production Setup

```python
from fastapi import FastAPI
import logging

app = FastAPI()

# Configure logging once at startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

from pydantic_schemaforms import render_form_html, FormModel, Field

class LoginForm(FormModel):
    username: str = Field(...)
    password: str = Field(..., ui_element="password")

@app.get("/login")
def login_page():
    html = render_form_html(LoginForm, framework="bootstrap")
    # ✅ Timing automatically logged
    # ❌ No debug spam
    return f"<html><body>{html}</body></html>"
```

### Example 2: Development with Debug Toggle

```python
from fastapi import FastAPI, Query
import logging

app = FastAPI()

# Configure at DEBUG for development
logging.basicConfig(level=logging.DEBUG)

from pydantic_schemaforms import render_form_html

@app.get("/login")
def login_page(debug: bool = False):
    # Control logging per request
    html = render_form_html(
        LoginForm,
        enable_logging=debug,
        debug=debug,  # Also show debug panel
        framework="bootstrap"
    )
    return f"<html><body>{html}</body></html>"

# Visit /login for normal form
# Visit /login?debug=true for debug logs + panel
```

### Example 3: Custom Log Handler

```python
import logging
from pythonjsonlogger import jsonlogger

# Use JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

from fastapi import FastAPI
from pydantic_schemaforms import render_form_html

app = FastAPI()

@app.get("/login")
def login_page():
    html = render_form_html(LoginForm, framework="bootstrap")
    # ✅ Timing logged as JSON for structured logging
    return f"<html><body>{html}</body></html>"
```

## Flask Integration

### Basic Setup

```python
from flask import Flask
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

from pydantic_schemaforms import render_form_html

@app.route("/login")
def login():
    html = render_form_html(LoginForm, framework="bootstrap")
    # ✅ Timing automatically logged
    return f"<html><body>{html}</body></html>"
```

### Conditional Logging

```python
import logging
from flask import Flask

app = Flask(__name__)

# Configure based on environment
log_level = logging.DEBUG if app.debug else logging.INFO
logging.basicConfig(level=log_level)

# Can also use Flask's logger
app.logger.setLevel(log_level)

from pydantic_schemaforms import render_form_html

@app.route("/login")
def login():
    html = render_form_html(LoginForm, framework="bootstrap")
    # ✅ Respects Flask's log level
    return f"<html><body>{html}</body></html>"
```

## Logger Names

The library uses these logger names for organization:

```python
import logging

# Main renderer logger - timing and general info
renderer_logger = logging.getLogger('pydantic_schemaforms.enhanced_renderer')

# Root library logger - all components
root_logger = logging.getLogger('pydantic_schemaforms')

# Configure root to affect all components
root_logger.setLevel(logging.DEBUG)
```

## Reference

### Logging Control Parameters

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| `enable_logging` | `bool` | `False` | Enable DEBUG-level library logs for this render |

**Important**: `enable_logging` only affects DEBUG level logs. Timing (INFO level) is **always logged** and controlled by your application's logging configuration.

### Log Levels in Use

| Level | Who Controls | Use Case |
|-------|--------------|----------|
| INFO | Application logging config | Timing metrics, important events |
| DEBUG | `enable_logging` param + app config | Detailed rendering steps, diagnostics |
| WARNING | Application logging config | Important warnings, issues |

## Best Practices

### ✅ DO

- Use application-level logging configuration (Approach 1)
- Configure INFO level for production (to see timing)
- Enable DEBUG level during development (to see all details)
- Use standard Python logging handlers and formatters
- Log to structured formats (JSON) in production

### ❌ DON'T

- Rely on `enable_logging` for production debugging
- Configure library logging differently from your app
- Expect DEBUG logs without DEBUG level configured
- Forget that timing is INFO level (appears in production)

## Troubleshooting

### Logs Not Appearing

**Problem**: Library logs don't appear even with `enable_logging=True`.

**Solution**: Check logging level:

```python
import logging

# ❌ WRONG - WARNING suppresses DEBUG
logging.basicConfig(level=logging.WARNING)
html = render_form_html(MyForm, enable_logging=True)

# ✅ CORRECT - INFO or DEBUG allows logs
logging.basicConfig(level=logging.DEBUG)
html = render_form_html(MyForm, enable_logging=True)
```

### Too Many Logs

**Problem**: Library logs are overwhelming your app logs.

**Solution**: Configure library logger separately:

```python
import logging

# App at DEBUG
logging.basicConfig(level=logging.DEBUG)

# Library at WARNING (suppress DEBUG logs)
logging.getLogger('pydantic_schemaforms').setLevel(logging.WARNING)
```

### Can't Find Timing in Logs

**Problem**: Timing logs aren't appearing.

**Solution**: Timing logs at INFO level:

```python
import logging

# ❌ WRONG - WARNING suppresses INFO
logging.basicConfig(level=logging.WARNING)

# ✅ CORRECT - INFO or DEBUG shows timing
logging.basicConfig(level=logging.INFO)
```

### JSON Logging Not Working

**Problem**: Logs don't serialize to JSON properly.

**Solution**: Ensure JSON formatter handles all log attributes:

```python
from pythonjsonlogger import jsonlogger
import logging

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

