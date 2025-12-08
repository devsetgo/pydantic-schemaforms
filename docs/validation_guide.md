# Unified Validation Engine Guide

_Complete guide to validation in pydantic-forms: server-side, real-time HTMX, and cross-field patterns._

## Overview

The pydantic-forms validation system is consolidated into a single, unified engine that works seamlessly across:
- **Server-side validation** via `validate_form_data()` and `FormValidator`
- **Real-time HTMX validation** via `LiveValidator` and field-level validators
- **Cross-field validation** via form-level rules
- **Convenience validators** for common patterns (email, password strength)

All validation rules live in `pydantic_forms/validation.py`, re-exported from `pydantic_forms/live_validation.py` for convenience, eliminating code duplication and ensuring consistency across all validation flows.

---

## Core Concepts

### ValidationResponse

The canonical response object for all validation operations (server-side or HTMX):

```python
from pydantic_forms import ValidationResponse

response = ValidationResponse(
    field_name="email",
    is_valid=True,
    errors=[],                          # List of error messages
    warnings=[],                        # List of warnings (non-blocking)
    suggestions=["Example: user@example.com"],  # Helpful hints
    value="user@example.com",           # The validated value
    formatted_value="user@example.com"  # Optionally formatted (e.g., lowercase)
)

# Serialize for HTMX responses
json_str = response.to_json()
dict_response = response.to_dict()
```

### ValidationSchema & FieldValidator

Build reusable validation schemas from individual field validators:

```python
from pydantic_forms.validation import ValidationSchema, FieldValidator

# Create a schema with multiple fields
schema = ValidationSchema()

# Add field validators
email_validator = FieldValidator("email")
email_validator.add_rule(EmailRule())
schema.add_field(email_validator)

password_validator = FieldValidator("password")
password_validator.add_rule(
    LengthRule(min=8, message="Minimum 8 characters required")
)
schema.add_field(password_validator)

# Build HTMX live validator from schema
live_validator = schema.build_live_validator()
```

### FormValidator

Validate entire forms with both field-level and cross-field rules:

```python
from pydantic_forms.validation import FormValidator

form_validator = FormValidator()

# Add field validators
form_validator.field("age").add_rule(NumericRangeRule(min=0, max=150))
form_validator.field("email").add_rule(EmailRule())

# Add cross-field validation
def validate_age_and_consent(data):
    age = data.get("age")
    consent = data.get("parental_consent")

    if age is not None and age < 18 and not consent:
        return False, {
            "parental_consent": ["Parental consent required for users under 18"]
        }
    return True, {}

form_validator.add_cross_field_rule(validate_age_and_consent)

# Validate form data
is_valid, errors = form_validator.validate({
    "age": 16,
    "email": "teen@example.com",
    "parental_consent": False
})
```

---

## Server-Side Validation

### Using validate_form_data()

For simple synchronous validation against a Pydantic `FormModel`:

```python
from pydantic_forms import FormModel, FormField, validate_form_data

class RegistrationForm(FormModel):
    username: str = FormField(
        title="Username",
        min_length=3,
        max_length=20
    )
    email: str = FormField(
        title="Email Address",
        input_type="email"
    )
    password: str = FormField(
        title="Password",
        input_type="password",
        min_length=8
    )

# Validate incoming form data
result = validate_form_data(RegistrationForm, {
    "username": "alice",
    "email": "alice@example.com",
    "password": "SecurePass123!"
})

if result.is_valid:
    print(f"Valid! Data: {result.data}")
else:
    print(f"Invalid! Errors: {result.errors}")
    # Result has: result.is_valid, result.data, result.errors
```

### Using FormValidator with Pydantic Models

For validation with additional custom rules:

```python
from pydantic_forms.validation import FormValidator

form_validator = FormValidator()
form_validator.field("username").add_rule(LengthRule(min=3, max=20))
form_validator.field("email").add_rule(EmailRule())
form_validator.field("password").add_rule(LengthRule(min=8))

# Validate and get results
is_valid, errors = form_validator.validate({
    "username": "alice",
    "email": "alice@example.com",
    "password": "SecurePass123!"
})

# Also validate against Pydantic model
is_valid, errors = form_validator.validate_pydantic_model(
    RegistrationForm,
    request_data
)
```

---

## Real-Time HTMX Validation

### LiveValidator Setup

Use `LiveValidator` for server-side validation triggered via HTMX on blur/change events:

```python
from pydantic_forms.live_validation import LiveValidator, HTMXValidationConfig
from pydantic_forms.validation import FieldValidator, EmailRule

# Configure HTMX behavior
config = HTMXValidationConfig(
    validate_on_blur=True,           # Validate when field loses focus
    validate_on_input=False,         # Don't validate on every keystroke
    validate_on_change=True,         # Validate when value changes
    debounce_ms=300,                 # Wait 300ms before validation request
    show_success_indicators=True,    # Visual feedback on valid input
    show_warnings=True,              # Display warnings
    show_suggestions=True,           # Show helpful hints
    success_class="is-valid",        # Bootstrap/custom CSS classes
    error_class="is-invalid",
    warning_class="has-warning",
    loading_class="is-validating"
)

live_validator = LiveValidator(config)

# Register field validators
email_validator = FieldValidator("email")
email_validator.add_rule(EmailRule())
live_validator.register_field_validator(email_validator)

password_validator = FieldValidator("password")
password_validator.add_rule(LengthRule(min=8))
live_validator.register_field_validator(password_validator)
```

### HTML Integration with HTMX

In your template, set up HTMX triggers for real-time validation:

```html
<!-- Form field with HTMX validation -->
<input
    type="email"
    name="email"
    id="email"
    class="form-control"
    placeholder="you@example.com"
    hx-post="/validate/email"
    hx-trigger="blur, change delay:300ms"
    hx-target="#email-feedback"
    hx-swap="outerHTML"
/>

<!-- Validation feedback container -->
<div id="email-feedback"></div>
```

### FastAPI Endpoint for HTMX Validation

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic_forms.live_validation import LiveValidator
from pydantic_forms.validation import FieldValidator, EmailRule

app = FastAPI()
live_validator = LiveValidator()

# Register validators
email_validator = FieldValidator("email")
email_validator.add_rule(EmailRule())
live_validator.register_field_validator(email_validator)

@app.post("/validate/email", response_class=HTMLResponse)
async def validate_email(request: Request):
    data = await request.form()
    value = data.get("email", "")

    # Get validator for this field
    validator = live_validator.get_field_validator("email")
    response = validator.validate(value)

    # Render feedback HTML
    if response.is_valid:
        return f"""
        <div id="email-feedback" class="valid-feedback">
            ✓ Email looks good
        </div>
        """
    else:
        errors_html = "".join([f"<li>{e}</li>" for e in response.errors])
        return f"""
        <div id="email-feedback" class="invalid-feedback">
            <ul>{errors_html}</ul>
        </div>
        """
```

### Building LiveValidator from ValidationSchema

Automatically convert a schema to HTMX-ready validators:

```python
from pydantic_forms.validation import ValidationSchema, FieldValidator, EmailRule

schema = ValidationSchema()

email_validator = FieldValidator("email")
email_validator.add_rule(EmailRule())
schema.add_field(email_validator)

# Create HTMX live validator from schema
live_validator = schema.build_live_validator()

# Now use live_validator in HTMX endpoints
```

---

## Cross-Field Validation

### Form-Level Rules

Validate fields that depend on other fields:

```python
from pydantic_forms.validation import FormValidator

form_validator = FormValidator()

# Individual field rules
form_validator.field("age").add_rule(NumericRangeRule(min=0, max=150))
form_validator.field("parental_consent").add_rule(RequiredRule())

# Cross-field validation
def validate_minor_consent(data):
    """Minors must have parental consent."""
    age = data.get("age")
    consent = data.get("parental_consent")

    if age is not None and age < 18 and not consent:
        return False, {
            "parental_consent": [
                "Parental consent is required for users under 18 years old"
            ]
        }
    return True, {}

form_validator.add_cross_field_rule(validate_minor_consent)

# Validate returns both field and cross-field errors
is_valid, errors = form_validator.validate({
    "age": 16,
    "parental_consent": False
})

# errors = {"parental_consent": ["Parental consent is required..."]}
```

### Conditional Field Validation

Validate a field only if another field has a certain value:

```python
def validate_emergency_contact(data):
    """Emergency contact required if no direct phone provided."""
    has_phone = bool(data.get("phone"))
    has_emergency_contact = bool(data.get("emergency_contact"))

    if not has_phone and not has_emergency_contact:
        return False, {
            "emergency_contact": [
                "Either a phone number or emergency contact is required"
            ]
        }
    return True, {}

form_validator.add_cross_field_rule(validate_emergency_contact)
```

### Password Matching Validation

```python
def validate_passwords_match(data):
    """Ensure password and confirm_password match."""
    password = data.get("password", "")
    confirm = data.get("confirm_password", "")

    if password and confirm and password != confirm:
        return False, {
            "confirm_password": ["Passwords do not match"]
        }
    return True, {}

form_validator.add_cross_field_rule(validate_passwords_match)
```

---

## Convenience Validators

### Email Validator

```python
from pydantic_forms.validation import create_email_validator

email_validator = create_email_validator()

response = email_validator("user@example.com")
# ValidationResponse(field_name="email", is_valid=True, ...)

response = email_validator("invalid-email")
# ValidationResponse(
#     field_name="email",
#     is_valid=False,
#     errors=["Please enter a valid email address"],
#     suggestions=["Example: user@example.com"],
#     value="invalid-email"
# )
```

### Password Strength Validator

```python
from pydantic_forms.validation import create_password_strength_validator

password_validator = create_password_strength_validator(min_length=8)

response = password_validator("WeakPass")
# ValidationResponse(
#     field_name="password",
#     is_valid=False,
#     errors=["Password must be at least 8 characters long"],
#     warnings=[
#         "Password should contain at least one uppercase letter",
#         "Password should contain at least one number"
#     ],
#     suggestions=[
#         "Add an uppercase letter (A-Z)",
#         "Add a number (0-9)"
#     ],
#     value="WeakPass"
# )

response = password_validator("SecurePass123!")
# ValidationResponse(field_name="password", is_valid=True, ...)
```

---

## Common Validation Rules

### Built-in Rules

The validation system includes pre-built rules for common patterns:

| Rule | Purpose | Example |
|------|---------|---------|
| `RequiredRule()` | Field must have a value | Required name field |
| `LengthRule(min, max)` | String length constraints | 3–20 char username |
| `EmailRule()` | Valid email format | Email field |
| `PhoneRule()` | Valid phone number | Phone field |
| `NumericRangeRule(min, max)` | Numeric value range | Age 0–150 |
| `DateRangeRule(min_date, max_date)` | Date within range | Future date only |
| `RegexRule(pattern)` | Custom regex pattern | Custom format validation |
| `CustomRule(func)` | Custom validation function | Complex logic |

### Example: Complete Field Validation

```python
from pydantic_forms.validation import (
    FieldValidator,
    EmailRule,
    LengthRule,
    NumericRangeRule
)

# Email field validator
email_validator = FieldValidator("email")
email_validator.add_rule(RequiredRule("Email is required"))
email_validator.add_rule(EmailRule())

# Username field validator
username_validator = FieldValidator("username")
username_validator.add_rule(RequiredRule("Username is required"))
username_validator.add_rule(LengthRule(min=3, max=20, message="3–20 characters"))

# Age field validator
age_validator = FieldValidator("age")
age_validator.add_rule(NumericRangeRule(min=13, max=150, message="Must be 13+"))

# Use in form validator
form_validator = FormValidator()
form_validator.field("email").add_rule(EmailRule())
form_validator.field("username").add_rule(LengthRule(min=3, max=20))
form_validator.field("age").add_rule(NumericRangeRule(min=13, max=150))
```

---

## Sync + HTMX Validation Flow

### End-to-End Example

Here's a complete registration form with both server validation and real-time HTMX feedback:

#### 1. Define Form Model

```python
from pydantic_forms import FormModel, FormField

class RegistrationForm(FormModel):
    username: str = FormField(
        title="Username",
        input_type="text",
        min_length=3,
        max_length=20,
        help_text="3–20 alphanumeric characters"
    )

    email: str = FormField(
        title="Email Address",
        input_type="email",
        help_text="We'll send a confirmation link"
    )

    password: str = FormField(
        title="Password",
        input_type="password",
        min_length=8,
        help_text="Must be at least 8 characters"
    )

    confirm_password: str = FormField(
        title="Confirm Password",
        input_type="password",
        help_text="Re-enter your password"
    )

    age: int = FormField(
        title="Age",
        input_type="number",
        ge=13,
        le=150,
        help_text="Must be 13 or older"
    )
```

#### 2. Set Up Validation

```python
from pydantic_forms.validation import (
    FormValidator,
    FieldValidator,
    EmailRule,
    LengthRule,
    NumericRangeRule
)

# Create form validator with all rules
form_validator = FormValidator()

# Field validators
form_validator.field("username").add_rule(
    LengthRule(min=3, max=20, message="3–20 characters")
)
form_validator.field("email").add_rule(EmailRule())
form_validator.field("password").add_rule(
    LengthRule(min=8, message="Minimum 8 characters")
)
form_validator.field("age").add_rule(
    NumericRangeRule(min=13, max=150, message="Must be 13+")
)

# Cross-field rules
def validate_passwords_match(data):
    if data.get("password") != data.get("confirm_password"):
        return False, {"confirm_password": ["Passwords do not match"]}
    return True, {}

form_validator.add_cross_field_rule(validate_passwords_match)

# Live validator for HTMX
live_validator = form_validator.build_live_validator()
```

#### 3. FastAPI Endpoints

```python
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic_forms import render_form, validate_form_data

app = FastAPI()

@app.get("/register")
def show_registration():
    form = RegistrationForm()
    return render_form(form, framework="bootstrap")

@app.post("/register")
async def handle_registration(request: Request):
    # Get form data
    form_data = await request.form()

    # Server-side validation
    result = validate_form_data(RegistrationForm, dict(form_data))

    if result.is_valid:
        # Process registration
        return JSONResponse({
            "success": True,
            "message": "Registration successful!"
        })
    else:
        # Return form with errors
        form = RegistrationForm()
        return render_form(
            form,
            framework="bootstrap",
            errors=result.errors
        )

# HTMX validation endpoints
@app.post("/validate/username")
async def validate_username(request: Request):
    data = await request.form()
    value = data.get("username", "")

    validator = form_validator.field("username")
    response = validator.validate(value)

    if response.is_valid:
        return HTMLResponse(
            f'<div class="valid-feedback">✓ Available</div>'
        )
    else:
        errors = "".join([f"<li>{e}</li>" for e in response.errors])
        return HTMLResponse(
            f'<div class="invalid-feedback"><ul>{errors}</ul></div>'
        )

@app.post("/validate/email")
async def validate_email(request: Request):
    data = await request.form()
    value = data.get("email", "")

    response = form_validator.field("email").validate(value)

    if response.is_valid:
        return HTMLResponse(
            f'<div class="valid-feedback">✓ Valid email</div>'
        )
    else:
        errors = "".join([f"<li>{e}</li>" for e in response.errors])
        return HTMLResponse(
            f'<div class="invalid-feedback"><ul>{errors}</ul></div>'
        )
```

#### 4. HTML Template

```html
<form hx-post="/register" hx-target="#form-result">
    <!-- Username field with HTMX validation -->
    <div class="form-group">
        <label for="username">Username</label>
        <input
            type="text"
            id="username"
            name="username"
            class="form-control"
            placeholder="3–20 characters"
            hx-post="/validate/username"
            hx-trigger="blur, change delay:300ms"
            hx-target="#username-feedback"
            hx-swap="outerHTML"
        />
        <div id="username-feedback"></div>
    </div>

    <!-- Email field with HTMX validation -->
    <div class="form-group">
        <label for="email">Email Address</label>
        <input
            type="email"
            id="email"
            name="email"
            class="form-control"
            placeholder="you@example.com"
            hx-post="/validate/email"
            hx-trigger="blur, change delay:300ms"
            hx-target="#email-feedback"
            hx-swap="outerHTML"
        />
        <div id="email-feedback"></div>
    </div>

    <!-- Other fields... -->

    <button type="submit" class="btn btn-primary">Register</button>
    <div id="form-result"></div>
</form>
```

---

## Testing Your Validators

The test suite includes comprehensive coverage. Use these patterns in your tests:

```python
import pytest
from pydantic_forms.validation import (
    FormValidator,
    FieldValidator,
    EmailRule,
    ValidationResponse
)

def test_email_validation():
    email_validator = FieldValidator("email")
    email_validator.add_rule(EmailRule())

    # Valid email
    response = email_validator.validate("user@example.com")
    assert response.is_valid
    assert response.errors == []

    # Invalid email
    response = email_validator.validate("not-an-email")
    assert not response.is_valid
    assert len(response.errors) > 0

def test_cross_field_validation():
    form_validator = FormValidator()

    def validate_passwords(data):
        if data.get("password") != data.get("confirm"):
            return False, {"confirm": ["Passwords don't match"]}
        return True, {}

    form_validator.add_cross_field_rule(validate_passwords)

    is_valid, errors = form_validator.validate({
        "password": "secret",
        "confirm": "different"
    })

    assert not is_valid
    assert "confirm" in errors
```

---

## Layout Demo & Tab Rendering Verification

The `tests/test_layout_demo_smoke.py` smoke test verifies that initial tab content renders correctly for both Bootstrap and Material frameworks:

```python
def test_layout_demo_bootstrap_initial_tab_renders():
    """Verify Bootstrap tabs show initial tab content."""
    response = client.get("/layouts")
    assert response.status_code == 200
    assert "Tab 1 Content" in response.text
    # Assert tab buttons exist
    assert 'class="nav-link active"' in response.text

def test_layout_demo_material_initial_tab_renders():
    """Verify Material tabs show initial tab content."""
    response = client.get("/layouts?style=material")
    assert response.status_code == 200
    # Assert initial content and Material tab classes
    assert "Initial Tab Content" in response.text
    assert 'data-toggle="tab"' in response.text
```

This coverage ensures that tab layouts work correctly across frameworks.

---

## Pydantic v2 Deprecation Resolution

As of this release, all Pydantic v2 deprecation warnings have been resolved:

✅ **Resolved Deprecations:**
- `min_items`/`max_items` → `min_length`/`max_length` in all FormField calls
- Extra kwargs on `Field()` → properly use `json_schema_extra`
- Starlette `TemplateResponse` signature updated to new parameter order

**Result:** Deprecation warnings reduced from 23 → 8 (removed 15 Pydantic deprecations). The remaining 8 warnings are intentional migration guides (`form_layouts` deprecation notice) and informational (JSON schema hints).

Run validation tests:
```bash
python -m pytest tests/test_validation_consolidation.py -v
python -m pytest tests/test_layout_demo_smoke.py -v
```

---

## Summary

The unified validation engine provides:

1. **Canonical ValidationResponse** for all validation flows
2. **Single code path** via `validation.py` with re-exports from `live_validation.py`
3. **Flexible rule composition** via `FieldValidator` and `FormValidator`
4. **HTMX integration** via `LiveValidator` with configurable behavior
5. **Cross-field validation** for dependent fields and complex rules
6. **Convenience validators** for common patterns (email, password strength)
7. **Full async support** for FastAPI and async frameworks
8. **Pydantic v2 compatibility** with zero deprecation warnings in critical paths

For questions or examples, see:
- `tests/test_validation_consolidation.py` — Consolidated validation tests (10 tests)
- `tests/test_layout_demo_smoke.py` — Layout/tab rendering verification
- `examples/fastapi_example.py` — Real-world FastAPI integration
