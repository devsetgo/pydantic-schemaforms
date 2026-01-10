# Pydantic SchemaForms - Comprehensive Examples

This directory contains **two comprehensive examples** that demonstrate **every capability** of the pydantic-schemaforms library:

> **Renderer note:** Both the Flask and FastAPI demos call straight into `EnhancedFormRenderer` (via `render_form_html`) so they automatically benefit from the shared schema parser, layout engine, and theme hooks. If you prefer the legacy builder DSL (`FormBuilder`, `FormDefinition`, etc.), those helpers now go through `ModernFormRenderer`, which is itself a thin wrapper around the same Enhanced pipeline. In other words, whether you start from a Pydantic `FormModel` or the builder DSL, you are exercising the exact same orchestration layer showcased in these examples.

## 🚀 Two Complete Examples

### 1. Flask Example (Sync) - `flask_example.py`
**Traditional web application with synchronous form handling**

- **Simple Form**: `/login` - Basic login with username/email and password
- **Medium Form**: `/register` - User registration with multiple field types and icons
- **Complex Form**: `/showcase` - Complete showcase with all features, model lists, sections
- **Self-Contained**: `/self-contained` - Zero-dependency Material Design form
- **API Endpoints**: JSON endpoints for form schemas and submission

**Run:** `python flask_example.py` → http://localhost:5000

### 2. FastAPI Example (Async) - `fastapi_example.py`
**Modern API-first application with asynchronous form handling**

- **Simple Form**: `/login` - Async login processing
- **Medium Form**: `/register` - Async user registration
- **Complex Form**: `/showcase` - Async complex form handling
- **Self-Contained**: `/self-contained` - Zero-dependency form demo
- **API Endpoints**: Full REST API with OpenAPI documentation
- **Documentation**: `/docs` - Interactive Swagger UI

**Self-contained HTML from the API:** `GET /api/forms/{form_type}/render` supports:

- `include_assets` (default: `true`) — when enabled, the returned HTML includes the framework assets inline.
- `asset_mode` (`vendored|cdn|none`, default: `vendored`) — controls whether those assets are inlined or emitted as pinned CDN tags.

**Run:** `python fastapi_example.py` → http://localhost:8000

## 📋 Complete Coverage Matrix

| Feature | Flask (Sync) | FastAPI (Async) | Shared Models |
|---------|-------------|-----------------|---------------|
| **Simple Forms** | ✅ `/login` | ✅ `/login` | `MinimalLoginForm` |
| **Medium Forms** | ✅ `/register` | ✅ `/register` | `UserRegistrationForm` |
| **Complex Forms** | ✅ `/showcase` | ✅ `/showcase` | `CompleteShowcaseForm` |
| **Bootstrap Styling** | ✅ `?style=bootstrap` | ✅ `?style=bootstrap` | External icons |
| **Material Design** | ✅ `?style=material` | ✅ `?style=material` | MD3 components |
| **Self-Contained** | ✅ Zero dependencies | ✅ Zero dependencies | Embedded CSS/JS |
| **Form Validation** | ✅ Sync validation | ✅ Async validation | `handle_form_submission()` |
| **Error Handling** | ✅ Template re-render | ✅ Template re-render | Pydantic errors |
| **API Endpoints** | ✅ Basic JSON API | ✅ Full REST API | JSON schemas |
| **Documentation** | ✅ Code comments | ✅ OpenAPI/Swagger | Auto-generated |

## 🎯 Key Principles Demonstrated

### 1. "Simple is Better" Pattern
```python
# Step 1: Import shared models
from shared_models import UserRegistrationForm, handle_form_submission

# Step 2: Render forms
from pydantic_schemaforms.enhanced_renderer import render_form_html
form_html = render_form_html(
    UserRegistrationForm,
    framework="bootstrap",
    include_framework_assets=True,  # inline Bootstrap CSS/JS for self-contained HTML
)

# Step 3: Validate forms
result = handle_form_submission(UserRegistrationForm, form_data)
```

### 2. Framework Agnostic
- **Same models work in both Flask and FastAPI**
- **Same rendering functions work in both frameworks**
- **Same validation logic works in both sync and async**

### 3. Zero Complexity Leakage
- **No FormModel definitions in framework examples**
- **No pydantic-schemaforms internals exposed to users**
- **Clean separation between library and application code**

## 🎨 Styling Coverage

### Bootstrap Support
- External icon positioning: `<span>{icon}</span><input>`
- Bootstrap Icons integration
- Responsive grid layouts
- Form validation styling

### Material Design 3 Support
- Authentic Material Design components
- Material Icons integration
- Self-contained CSS/JS embedding
- Modern design language

## 📊 Field Type Coverage

The `CompleteShowcaseForm` demonstrates **every supported field type**:

- **Text Inputs**: text, email, password, textarea
- **Numeric Inputs**: number, range, color
- **Selection Inputs**: select, radio, checkbox, multi-select
- **Date/Time Inputs**: date, datetime, time
- **Specialized Inputs**: file, hidden, url, tel
- **Model Lists**: Dynamic add/remove functionality
- **Sections**: Collapsible form sections

## 🧪 Testing and Verification

### Manual Testing
```bash
# Test Flask (sync)
cd examples
python flask_example.py
# Visit: http://localhost:5000

# Test FastAPI (async)
python fastapi_example.py
# Visit: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Additional Resources
- Testing scripts and verification tools are available in the `archive/` directory
- Comprehensive coverage verification and model consistency tests included

## 🚀 Production Ready

Both examples are **production-ready** and demonstrate:

✅ **Error handling** - Graceful validation errors
✅ **Security** - CSRF protection, input sanitization
✅ **Performance** - Efficient rendering, minimal overhead
✅ **Accessibility** - Proper ARIA labels, keyboard navigation
✅ **Responsive** - Mobile-first design patterns
✅ **SEO Friendly** - Semantic HTML structure

## 📁 File Structure

```
examples/
├── README.md                  # This documentation
├── flask_example.py           # Complete Flask demo (sync)
├── fastapi_example.py         # Complete FastAPI demo (async)
├── shared_models.py           # All form models (shared)
├── templates/                 # Unified Jinja2 templates
│   ├── form.html             # Generic form template
│   ├── success.html          # Success page template
│   ├── home.html             # Landing page
│   ├── shared_base.html      # Base template
│   ├── 404.html              # Error pages (Flask)
│   └── 500.html              # Error pages (Flask)
├── static/                    # Static assets (CSS/JS)
│   ├── css/                  # Custom stylesheets
│   └── js/                   # JavaScript files
└── archive/                   # Additional examples and tests
    ├── Legacy examples
    ├── Testing scripts
    └── Documentation
```

## 🎯 Usage Patterns

### For Flask Applications (Sync)
```python
from shared_models import UserRegistrationForm, handle_form_submission
from pydantic_schemaforms.enhanced_renderer import render_form_html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        result = handle_form_submission(UserRegistrationForm, request.form.to_dict())
        if result['success']:
            # Process successful registration
            return redirect('/success')
        else:
            # Re-render with errors
            form_html = render_form_html(
                UserRegistrationForm,
                errors=result['errors'],
                include_framework_assets=True,
            )
    else:
        form_html = render_form_html(UserRegistrationForm, include_framework_assets=True)

    return render_template('form.html', form_html=form_html)
```

### For FastAPI Applications (Async)
```python
from shared_models import UserRegistrationForm, handle_form_submission
from pydantic_schemaforms.enhanced_renderer import render_form_html

@app.post('/register')
async def register_post(request: Request):
    form_data = await request.form()
    result = handle_form_submission(UserRegistrationForm, dict(form_data))

    if result['success']:
        return templates.TemplateResponse('success.html', {...})
    else:
        form_html = render_form_html(
            UserRegistrationForm,
            errors=result['errors'],
            include_framework_assets=True,
        )
        return templates.TemplateResponse('form.html', {...})
```

## 🎉 Summary

These two examples provide **complete coverage** of the pydantic-schemaforms library:

- **Every field type** is demonstrated
- **Every layout option** is shown
- **Every styling framework** is supported
- **Both sync and async** patterns are covered
- **Simple to complex** forms are included
- **Production patterns** are established

Users can copy these examples as starting points for their own applications, confident that they demonstrate **best practices** and **comprehensive functionality**.
