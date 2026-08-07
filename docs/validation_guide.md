# Unified Validation Engine Guide

_Complete guide to validation in pydantic-schemaforms: server-side, real-time HTMX, and cross-field patterns._

## Overview

The pydantic-schemaforms validation system is consolidated into a single, unified engine that works seamlessly across:
- **Server-side validation** via `validate_form_data()` and `FormValidator`
- **Real-time HTMX validation** via `LiveValidator` and field-level validators
- **Cross-field validation** via form-level rules
- **Convenience validators** for common patterns (email, password strength)

All validation rules live in `pydantic_schemaforms/validation.py`, re-exported from `pydantic_schemaforms/live_validation.py` for convenience, eliminating code duplication and ensuring consistency across all validation flows.

---

## Core Concepts

### ValidationResponse

The canonical response object for all validation operations (server-side or HTMX):

```python
from pydantic_schemaforms import ValidationResponse

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
from pydantic_schemaforms.validation import ValidationSchema, FieldValidator

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
from pydantic_schemaforms.validation import FormValidator

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

### Using FormModel.validate()

The recommended way to validate submitted data is `FormModel.validate()`. Pass `submit_url`
(and optionally `framework` plus any other render kwargs) once; on failure, call
`render_with_errors()` with no arguments — the result re-renders itself:

```python
from pydantic_schemaforms import FormModel, FormField

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

# Validate — stores submit_url so render_with_errors() needs no args
result = RegistrationForm.validate(
    {"username": "alice", "email": "alice@example.com", "password": "SecurePass123!"},
    submit_url="/register",
)

if result.is_valid:
    print(f"Valid! Data: {result.data}")
else:
    print(f"Invalid! Errors: {result.errors}")
    html = result.render_with_errors()          # sync (Flask / scripts)
    # html = await result.render_with_errors_async()  # async (FastAPI)
```

`result` always exposes `.is_valid`, `.data`, and `.errors` regardless of the path.

By default `.data` mirrors the underlying Pydantic model's shape — nested
`BaseModel`/`List[BaseModel]` fields come back as nested dicts/lists, matching
`model_dump()`. Pass `flatten=True` to get (and accept) bracket+dot flat keys
instead (e.g. `"pets[0].name"`), the same notation used for `model_list` HTML
field names:

```python
result = RegistrationForm.validate(data, submit_url="/register", flatten=True)
# result.data uses flat "field[0].sub" keys instead of nested dicts/lists
```

See [Nested vs. flat form data](recipes.md#nested-vs-flat-form-data) in the
recipes guide for a full nested-model example, and
[JSON Schema output](recipes.md#json-schema-output) for
`get_pydantic_json_schema()`, which returns the standard, `$defs`-aware JSON
Schema of the form's underlying Pydantic model (as opposed to
`get_json_schema()`'s flattened UI shape).

### Using validate_form_data() directly

`validate_form_data()` is the lower-level function used by `FormModel.validate()`. It is
still available for cases where you only need the validation result and do not intend to
re-render the form from the result object:

```python
from pydantic_schemaforms import validate_form_data

result = validate_form_data(RegistrationForm, submitted_data)
if result.is_valid:
    process(result.data)
```

### Using FormValidator with Pydantic Models

For validation with additional custom rules:

```python
from pydantic_schemaforms.validation import FormValidator

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

Use `LiveValidator` for server-side validation triggered via HTMX on blur/input/change events:

```python
from pydantic_schemaforms import LiveValidator, HTMXValidationConfig, FieldValidator, EmailRule, MinLengthRule

# Configure HTMX behavior — any combination of triggers may be enabled.
# When multiple are True, the generated hx-trigger combines them:
#   validate_on_blur=True + validate_on_change=True  →  hx-trigger="blur, change"
config = HTMXValidationConfig(
    validate_on_blur=True,           # Validate when field loses focus
    validate_on_input=False,         # Validate on every keystroke (with debounce)
    validate_on_change=True,         # Validate on value change (select, checkbox)
    debounce_ms=300,                 # Debounce delay for validate_on_input
    show_success_indicators=True,    # Apply success_class on valid input
    success_class="is-valid",        # Bootstrap / custom CSS classes
    error_class="is-invalid",
    warning_class="has-warning",
    loading_class="is-validating",
)

live_validator = LiveValidator(config)

# Register field validators
email_fv = FieldValidator("email")
email_fv.add_rule(EmailRule())
live_validator.register_field_validator(email_fv)

password_fv = FieldValidator("password")
password_fv.add_rule(MinLengthRule(8))
live_validator.register_field_validator(password_fv)
```

### HTML Integration with HTMX

Use `hx-swap="innerHTML"` so HTMX replaces only the *content* of the feedback container,
keeping the element's `id` stable for future swaps:

```html
<!-- Form field with HTMX validation -->
<input
    type="email"
    name="email"
    id="email"
    class="form-control"
    placeholder="you@example.com"
    hx-post="/validate/email"
    hx-trigger="blur, change"
    hx-target="#email-feedback"
    hx-swap="innerHTML"
    data-validate-endpoint="true"
/>

<!-- Validation feedback container -->
<div id="email-feedback"></div>
```

> **`data-validate-endpoint="true"`** — the script emitted by `render_htmx_script()` uses
> this attribute to attach loading-indicator and focus-clear behaviour automatically.

### FastAPI Endpoint for HTMX Validation

A single parameterised endpoint handles all fields. `validate_field()` returns a
`ValidationResponse`; `validation_response_headers()` emits the `HX-Trigger` header that
the bundled JS uses to apply `is-valid` / `is-invalid` CSS classes to the input.

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from pydantic_schemaforms import LiveValidator, HTMXValidationConfig, FieldValidator, EmailRule, MinLengthRule
from pydantic_schemaforms.live_validation import validation_response_headers

live_validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True))

email_fv = FieldValidator("email")
email_fv.add_rule(EmailRule())
live_validator.register_field_validator(email_fv)

@app.post("/validate/{field_name}", response_class=HTMLResponse)
async def htmx_validate(field_name: str, request: Request):
    data = await request.form()
    value = str(data.get(field_name, ""))
    result = live_validator.validate_field(field_name, value)

    if result.is_valid:
        feedback = '<span class="valid-feedback">✓ Looks good!</span>'
    else:
        feedback = f'<span class="invalid-feedback">{"; ".join(result.errors)}</span>'

    headers = validation_response_headers(field_name, result.is_valid)
    return HTMLResponse(feedback, headers=headers)
```

Include the init script in your template so the `validationResult` event updates CSS classes:

```python
# Pass to template context
validator_script = live_validator.render_htmx_script()
```

```html
<!-- In your base template, after HTMX is loaded -->
<script src="/vendor/htmx.min.js"></script>
{{ validator_script | safe }}
```

### Building LiveValidator from ValidationSchema

```python
from pydantic_schemaforms import FieldValidator, EmailRule
from pydantic_schemaforms.validation import ValidationSchema

schema = ValidationSchema()

email_fv = FieldValidator("email")
email_fv.add_rule(EmailRule())
schema.add_field(email_fv)

# Converts the schema to a ready-to-use LiveValidator
live_validator = schema.build_live_validator()
```

### Email DNS/MX Deliverability Checks

Pydantic's own `EmailStr` is a format check — `user@thisdomaindoesnotexist.zzz` passes
it. `DeliverableEmailStr` is a drop-in replacement that additionally performs a real DNS
lookup for the domain's MX records, catching typo'd or non-existent domains before you
send mail to them (useful, for example, when onboarding a client account and you want to
know the domain can actually receive mail). It requires the optional
[`email-validator`](https://pypi.org/project/email-validator/) package:

```bash
pip install pydantic-schemaforms[email-dns]
# or: pip install email-validator
```

Use it exactly like `EmailStr` — it's just a type, so there's no validator to construct,
register, or keep in sync with the field:

```python
from pydantic_schemaforms import DeliverableEmailStr, Field, FormModel

class SignupForm(FormModel):
    email: DeliverableEmailStr = Field(..., title="Email")
```

That one line is enough for `FormModel.validate()`, `as_api_model()`'s JSON endpoint, and
`LiveValidator.register_model_validator()` (next section) to all enforce and live-check
the DNS/MX rule identically, since it's now part of the field's own type rather than a
separate rule you register by hand. Because it's a real network call, the check always
runs server-side — there's no way to do a DNS/MX lookup from browser JavaScript.

Unless you pass a fixed `message`, the error text is `email-validator`'s own specific
reason for the failure rather than one generic string, so the user sees *why* the
address didn't pass — a typo'd/non-existent domain, a domain with no mail server, and a
reserved TLD all produce different text:

```text
The domain name gmial.con does not exist.
The domain name example.com does not accept email.
The part after the @-sign is a special-use or reserved name that cannot be used with email.
```

> **Careful with `example.com`/`example.org` in your own tests** — those RFC 2606
> reserved placeholder domains (used everywhere else in this guide) have no MX record,
> so `DeliverableEmailStr` correctly *rejects* them. Use a real domain (like
> `gmail.com`) or a domain you control when trying this out.

See a runnable side-by-side comparison in the FastAPI example app at
`GET /email-dns-validation` (`examples/fastapi_routes.py` /
`examples/templates/email_dns_validation.html`) — two live email fields, one plain
`EmailStr` and one `DeliverableEmailStr`, so you can see the same address pass one and
fail the other.

#### Lower-level building blocks

`DeliverableEmailStr` is built on `EmailDeliverabilityRule`, which you can reach for
directly if you need a custom `timeout`, a fixed error `message`, or you're building a
field imperatively rather than through a typed model:

```python
from pydantic_schemaforms.validation import EmailDeliverabilityRule

EmailDeliverabilityRule(message="We couldn't verify that domain accepts mail.", timeout=5)
```

`FieldValidator.email(check_deliverability=True)`, `FormBuilder.email_input(check_deliverability=True)`,
and `create_email_validator(check_deliverability=True)` all expose the same rule for the
`FieldValidator`/`FormBuilder`/factory-function styles of building validation instead of
a `FormModel` type annotation:

```python
from pydantic_schemaforms import FieldValidator

email_fv = FieldValidator("email").required().email(check_deliverability=True, dns_timeout=5)
```

If `email-validator` isn't installed, `EmailDeliverabilityRule.validate()` (and so
`DeliverableEmailStr`) raises `ImportError` with install instructions rather than
silently skipping the check or treating every address as valid.

### Validating Pydantic Model Fields

`register_model_validator()` registers a validator for every field in a Pydantic model.
Each field is validated in isolation using `validate_assignment`, so valid fields are never
marked invalid just because other required fields are absent:

```python
from pydantic import BaseModel
from pydantic_schemaforms import LiveValidator

class ProfileModel(BaseModel):
    name: str
    age: int

live_validator = LiveValidator()
live_validator.register_model_validator(ProfileModel)

# Only the age field's own constraints are checked — name being absent is irrelevant
result = live_validator.validate_field("age", "not-a-number")
# result.is_valid == False, result.errors == ["Input should be a valid integer..."]

result = live_validator.validate_field("age", 25)
# result.is_valid == True
```

This is also the recommended way to wire up live validation for a whole `FormModel` at
once instead of building a `FieldValidator` per field by hand — one
`register_model_validator(MyForm)` call derives every field's live check straight from
the model's own `Field()` constraints and types (`min_length`, `EmailStr`,
`DeliverableEmailStr`'s DNS/MX lookup, ...), so there's nothing to duplicate or keep in
sync:

```python
class ContactForm(FormModel):
    name: str = Field(..., min_length=2)
    email: DeliverableEmailStr = Field(...)

live_validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True))
live_validator.register_model_validator(ContactForm)  # that's the whole setup
```

---

## Cross-Field Validation

### Form-Level Rules

Validate fields that depend on other fields:

```python
from pydantic_schemaforms.validation import FormValidator

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
from pydantic_schemaforms.validation import create_email_validator

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
from pydantic_schemaforms.validation import create_password_strength_validator

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
| `MinLengthRule(n)` | Minimum string length | Username ≥ 3 chars |
| `MaxLengthRule(n)` | Maximum string length | Username ≤ 20 chars |
| `EmailRule()` | Valid email format | Email field |
| `PhoneRule()` | Valid phone number | Phone field |
| `NumericRangeRule(min, max)` | Numeric value range | Age 0–150 |
| `DateRangeRule(min_date, max_date)` | Date within range | Future date only |
| `RegexRule(pattern)` | Custom regex pattern | Custom format validation |
| `CustomRule(func)` | Custom validation function | Complex logic |

### Example: Complete Field Validation

```python
from pydantic_schemaforms import FieldValidator, EmailRule, MinLengthRule, MaxLengthRule
from pydantic_schemaforms.validation import RequiredRule, NumericRangeRule, FormValidator

# Email field validator
email_validator = FieldValidator("email")
email_validator.add_rule(RequiredRule("Email is required"))
email_validator.add_rule(EmailRule())

# Username field validator (fluent API: .min_length() / .max_length())
username_validator = FieldValidator("username")
username_validator.add_rule(RequiredRule("Username is required"))
username_validator.add_rule(MinLengthRule(3, message="Minimum 3 characters"))
username_validator.add_rule(MaxLengthRule(20, message="Maximum 20 characters"))

# Age field validator
age_validator = FieldValidator("age")
age_validator.add_rule(NumericRangeRule(min=13, max=150, message="Must be 13+"))

# Use in form validator
form_validator = FormValidator()
form_validator.field("email").add_rule(EmailRule())
form_validator.field("username").add_rule(MinLengthRule(3)).add_rule(MaxLengthRule(20))
form_validator.field("age").add_rule(NumericRangeRule(min=13, max=150))
```

---

## Sync + HTMX Validation Flow

### End-to-End Example

Here's a complete registration form with both server validation and real-time HTMX feedback:

#### 1. Define Form Model

```python
from pydantic_schemaforms import FormModel, FormField

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
from pydantic_schemaforms import FieldValidator, EmailRule, MinLengthRule, MaxLengthRule, LiveValidator
from pydantic_schemaforms.validation import FormValidator, NumericRangeRule

# Create form validator with all rules
form_validator = FormValidator()

# Field validators
form_validator.field("username").add_rule(MinLengthRule(3, message="3–20 characters")).add_rule(MaxLengthRule(20))
form_validator.field("email").add_rule(EmailRule())
form_validator.field("password").add_rule(MinLengthRule(8, message="Minimum 8 characters"))
form_validator.field("age").add_rule(NumericRangeRule(min=13, max=150, message="Must be 13+"))

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
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic_schemaforms import render_form_html_async

app = FastAPI()

@app.get("/register", response_class=HTMLResponse)
async def show_registration():
    return await render_form_html_async(
        RegistrationForm, framework="bootstrap", submit_url="/register"
    )

@app.post("/register", response_class=HTMLResponse)
async def handle_registration(request: Request):
    form_data = await request.form()
    result = RegistrationForm.validate(
        dict(form_data), submit_url="/register", framework="bootstrap"
    )

    if result.is_valid:
        return JSONResponse({
            "success": True,
            "message": "Registration successful!"
        })
    else:
        return await result.render_with_errors_async()

# HTMX validation — one parameterised endpoint handles every field
@app.post("/validate/{field_name}", response_class=HTMLResponse)
async def htmx_validate(field_name: str, request: Request):
    from pydantic_schemaforms.live_validation import validation_response_headers
    data = await request.form()
    value = str(data.get(field_name, ""))
    result = live_validator.validate_field(field_name, value)

    if result.is_valid:
        feedback = '<span class="valid-feedback">✓ Looks good!</span>'
    else:
        feedback = f'<span class="invalid-feedback">{"; ".join(result.errors)}</span>'

    headers = validation_response_headers(field_name, result.is_valid)
    return HTMLResponse(feedback, headers=headers)
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
            hx-swap="innerHTML"
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
            hx-swap="innerHTML"
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
from pydantic_schemaforms.validation import (
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

The layout smoke tests in `tests/test_layouts.py` verify that initial tab content renders correctly for both Bootstrap and Material frameworks:

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
python -m pytest tests/test_validation.py -v
python -m pytest tests/test_layouts.py -v
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
- `tests/test_validation.py` — All validation tests (144 tests)
- `tests/test_layouts.py` — Layout/tab rendering verification including async
- `examples/fastapi_routes.py` — Real-world FastAPI integration
