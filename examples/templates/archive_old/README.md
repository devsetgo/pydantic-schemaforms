# Unified Template System

This directory contains the unified Jinja2 template system that works with both Flask and FastAPI frameworks.

## Template Architecture

### Base Templates
- `shared_base.html` - Main base template with framework-agnostic styling and CSS variables
- `base.html` - Legacy base template (kept for compatibility)

### Form Templates
- `home.html` - Landing page with framework detection and demo links
- `login.html` - Login form template with framework-specific features
- `user.html` - User registration form template
- `pets.html` - Pet registration form with dynamic lists
- `dynamic.html` - Dynamic form with conditional fields

### Utility Templates
- `404.html` - Error page for not found
- `500.html` - Error page for server errors
- `layouts.html` - Layout demonstrations

## Framework Detection

All templates use framework detection via template variables:

```jinja2
{% if framework == "fastapi" %}
    <!-- FastAPI-specific content -->
{% else %}
    <!-- Flask-specific content -->
{% endif %}

{% if framework_type == "material" %}
    <!-- Material Design styling -->
{% else %}
    <!-- Bootstrap styling -->
{% endif %}
```

## Template Variables

Templates expect these variables from the backend:

- `framework` - "flask" or "fastapi"
- `framework_name` - Display name for the framework
- `framework_type` - "bootstrap" or "material" for styling
- `renderer_info` - Information about the form renderer
- `form_html` - Generated form HTML from pydantic-schemaforms
- `success` - Boolean for success state
- `errors` - Validation errors
- Form data variables for success display

## CSS Framework Integration

The unified system supports both Bootstrap 5 and Material Design 3:

### Bootstrap Mode
```css
--demo-primary-color: #667eea;
--demo-secondary-color: #764ba2;
--demo-accent-color: #f093fb;
```

### Material Design Mode
```css
--demo-primary-color: #6750a4;
--demo-secondary-color: #625b71;
--demo-accent-color: #7f5af0;
```

## Usage Pattern

Backend frameworks should pass the framework detection variables:

```python
# Flask example
return render_template('user.html',
                     framework="flask",
                     framework_name="Flask",
                     framework_type="bootstrap",
                     form_html=form_html)

# FastAPI example
return templates.TemplateResponse("user.html", {
    "request": request,
    "framework": "fastapi",
    "framework_name": "FastAPI",
    "framework_type": "material",
    "form_html": form_html
})
```

## Archived Templates

Old duplicate templates are in `archive_old/`:
- `flask_*.html` - Old Flask-specific templates
- `fastapi_*.html` - Old FastAPI-specific templates
- `bootstrap_*.html` - Old Bootstrap-specific templates
- `material_*.html` - Old Material-specific templates

These have been replaced by the unified system.
