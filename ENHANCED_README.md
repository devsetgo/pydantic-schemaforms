# Pydantic Forms - Enhanced Form System

A powerful Pydantic 2.x+ based form system that provides UI element specifications similar to React JSON Schema Forms, but for Python HTML generation.

## Features

✅ **Pydantic 2.x+ Integration** - Built on modern Pydantic with full type safety  
✅ **UI Element Specifications** - Define form UI elements directly in Pydantic Field definitions  
✅ **Multiple CSS Frameworks** - Bootstrap, Material Design, or custom styling  
✅ **Advanced Validation** - Built-in Pydantic validation plus custom form validators  
✅ **Rich Input Types** - Text, password, email, textarea, number, date, file, color, and more  
✅ **Error Handling** - Comprehensive validation error display and handling  
✅ **Flexible Layouts** - Support for different form layouts and styling  
✅ **Framework Integration** - Easy integration with Flask, FastAPI, and other web frameworks

## Quick Start

### Basic Usage

```python
from pydantic_forms.schema_form import FormModel, Field

class ContactForm(FormModel):
    name: str = Field(
        ...,
        title="Full Name",
        description="Enter your full name",
        min_length=2,
        ui_autofocus=True
    )
    
    email: str = Field(
        ...,
        title="Email Address",
        description="We'll never share your email",
        ui_element="email"
    )
    
    message: str = Field(
        ...,
        title="Message",
        description="Your message (minimum 10 characters)",
        min_length=10,
        max_length=1000,
        ui_element="textarea",
        ui_options={"rows": 5}
    )

# Render the form
form_html = ContactForm.render_form(framework="bootstrap")
print(form_html)
```

### Advanced Usage with Validation

```python
from pydantic import model_validator
from pydantic_forms.enhanced_renderer import SchemaFormValidationError

class UserRegistrationForm(FormModel):
    username: str = Field(
        ...,
        title="Username",
        description="Choose a unique username (3-20 characters)",
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9]+$",
        ui_autofocus=True
    )
    
    password: str = Field(
        ...,
        title="Password",
        description="At least 8 characters with uppercase, lowercase, number, and special character",
        min_length=8,
        ui_element="password"
    )
    
    confirm_password: str = Field(
        ...,
        title="Confirm Password",
        description="Re-enter your password to confirm",
        ui_element="password"
    )
    
    bio: str = Field(
        ...,
        title="Biography",
        description="Tell us about yourself",
        max_length=500,
        ui_element="textarea",
        ui_options={"rows": 4}
    )
    
    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise SchemaFormValidationError([{
                "name": "confirm_password",
                "property": ".confirm_password",
                "message": "Passwords do not match"
            }])
        return self
    
    model_config = {"populate_by_name": True}

# Render with validation errors
sample_errors = {
    "confirm_password": "Passwords do not match"
}

form_html = UserRegistrationForm.render_form(
    errors=sample_errors,
    framework="bootstrap"
)
```

## UI Elements

The `ui_element` parameter supports these input types:

- **text** - Standard text input
- **password** - Password input (masked)
- **email** - Email input with validation
- **number** - Numeric input with step controls
- **range** - Range slider
- **textarea** - Multi-line text area
- **select** - Dropdown selection (requires options)
- **checkbox** - Checkbox input
- **radio** - Radio button group (requires options)
- **date** - Date picker
- **time** - Time picker
- **datetime-local** - Date and time picker
- **file** - File upload
- **color** - Color picker
- **search** - Search input
- **url** - URL input with validation
- **tel** - Telephone input
- **hidden** - Hidden input

## UI Options

Additional UI configuration options:

```python
Field(
    ...,
    ui_element="textarea",
    ui_autofocus=True,              # Auto-focus this field
    ui_placeholder="Enter text...", # Placeholder text
    ui_options={"rows": 6},         # Element-specific options
    ui_class="custom-class",        # Additional CSS classes
    ui_style="border: 2px solid blue;", # Inline CSS styles
    ui_disabled=True,               # Disable the field
    ui_readonly=True,               # Make field read-only
    ui_hidden=True                  # Hide the field
)
```

## CSS Frameworks

### Bootstrap 5 (default)
```python
form_html = MyForm.render_form(framework="bootstrap")
```

### Material Design
```python
form_html = MyForm.render_form(framework="material")
```

### No Framework (plain HTML)
```python
form_html = MyForm.render_form(framework="none")
```

## Framework Integration

### Flask Integration

```python
from flask import Flask, request, render_template_string
from pydantic_forms.render_form import render_form_html

app = Flask(__name__)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            # Validate form data
            form_data = ContactForm(**request.form.to_dict())
            # Process valid data
            return "Success!"
        except Exception as e:
            # Handle validation errors
            errors = {}  # Extract errors from e
            
    form_html = render_form_html(
        ContactForm, 
        form_data=request.form if request.method == 'POST' else None,
        framework="bootstrap"
    )
    return render_template_string('''
        <html>
        <head>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                {{ form_html|safe }}
            </div>
        </body>
        </html>
    ''', form_html=form_html)
```

### FastAPI Integration

```python
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/register", response_class=HTMLResponse)
async def show_registration_form():
    form_html = UserRegistrationForm.render_form(framework="bootstrap")
    return f"""
    <html>
    <head>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            {form_html}
        </div>
    </body>
    </html>
    """

@app.post("/register")
async def process_registration(request: Request):
    form_data = await request.form()
    try:
        user_data = UserRegistrationForm(**form_data)
        # Process valid data
        return {"status": "success", "user_id": 123}
    except Exception as e:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(e))
```

## Error Handling

The system supports comprehensive error handling:

```python
# Using SchemaFormValidationError for custom validation
from pydantic_forms.enhanced_renderer import SchemaFormValidationError

@model_validator(mode="after")
def custom_validation(self):
    errors = []
    
    # Check custom business rules
    if "admin" in self.username.lower():
        errors.append({
            "name": "username",
            "property": ".username",
            "message": "Username cannot contain 'admin'"
        })
    
    if errors:
        raise SchemaFormValidationError(errors)
    return self

# Rendering with errors
form_html = MyForm.render_form(
    data=form_data,
    errors={"username": "This username is already taken"},
    framework="bootstrap"
)
```

## Advanced Features

### Field Ordering
```python
Field(..., ui_order=1)  # Lower numbers appear first
```

### Conditional Fields
```python
Field(..., ui_hidden=True)  # Hide based on conditions
```

### Custom Styling
```python
Field(
    ..., 
    ui_class="fancy-input bordered",
    ui_style="background: linear-gradient(45deg, #ff0, #f0f);"
)
```

## API Reference

### FormModel

Base class for all form models. Extends Pydantic BaseModel with form rendering capabilities.

**Methods:**
- `render_form(**kwargs)` - Render form as HTML
- `get_json_schema()` - Get enhanced JSON schema with UI information

### Field()

Enhanced Field function that supports UI parameters in addition to standard Pydantic field options.

**UI Parameters:**
- `ui_element: str` - Input type (text, password, email, etc.)
- `ui_widget: str` - Alias for ui_element
- `ui_autofocus: bool` - Auto-focus this field
- `ui_options: dict` - Element-specific options
- `ui_placeholder: str` - Placeholder text
- `ui_help_text: str` - Help text override
- `ui_order: int` - Field display order
- `ui_disabled: bool` - Disable the field
- `ui_readonly: bool` - Make field read-only
- `ui_hidden: bool` - Hide the field
- `ui_class: str` - Additional CSS classes
- `ui_style: str` - Inline CSS styles

### EnhancedFormRenderer

Main form rendering engine.

**Methods:**
- `render_form_from_model(model_cls, data=None, errors=None, **kwargs)`

### SchemaFormValidationError

Exception class for custom validation errors.

```python
SchemaFormValidationError([
    {
        "name": "field_name",
        "property": ".field_name", 
        "message": "Error message"
    }
])
```

## Compatibility

- **Python**: 3.8+
- **Pydantic**: 2.0+
- **CSS Frameworks**: Bootstrap 5, Material Design, or custom
- **Web Frameworks**: Flask, FastAPI, Django, or any Python web framework

## Examples

See `example_usage.py` and `comprehensive_example.py` for complete working examples.

## Architecture

The system consists of several key components:

1. **FormModel** - Enhanced Pydantic BaseModel with UI capabilities
2. **Field()** - Enhanced Field function with UI parameters  
3. **EnhancedFormRenderer** - Core rendering engine
4. **Input Components** - Modular input type implementations
5. **Framework Support** - CSS framework integration

This architecture provides a clean separation of concerns while maintaining ease of use and flexibility.

---

This implementation provides a React JSON Schema Forms-like experience for Python developers, with the power and type safety of Pydantic 2.x+.