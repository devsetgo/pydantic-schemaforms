# Recipes

Copy-paste patterns for common form tasks. Each recipe is self-contained — combine them freely.

---

## Minimal form

The smallest possible form: define a `FormModel`, render it, handle submission.

```python
from pydantic_schemaforms import Field, FormModel, render_form_html

class LoginForm(FormModel):
    username: str = Field(..., ui_element="text", ui_placeholder="Username")
    password: str = Field(..., ui_element="password", ui_placeholder="Password")

html = render_form_html(LoginForm, submit_url="/login")
```

For async (FastAPI):

```python
from pydantic_schemaforms import render_form_html_async

html = await render_form_html_async(LoginForm, submit_url="/login")
```

---

## GET + POST route (FastAPI)

Full round-trip: render on GET, validate on POST, re-render with errors if invalid.

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic_schemaforms import Field, FormModel, render_form_html_async

class ContactForm(FormModel):
    name: str = Field(..., min_length=2, title="Full Name", ui_element="text")
    email: str = Field(..., title="Email", ui_element="email")
    message: str = Field(..., min_length=10, title="Message", ui_element="textarea")

app = FastAPI()

@app.api_route("/contact", methods=["GET", "POST"], response_class=HTMLResponse)
async def contact(request: Request):
    if request.method == "POST":
        data = dict(await request.form())
        result = ContactForm.validate(data, submit_url="/contact")
        if result.is_valid:
            # process result.data …
            return "<p>Thanks!</p>"
        form_html = await result.render_with_errors_async()
    else:
        form_html = await render_form_html_async(ContactForm, submit_url="/contact")

    return f"<html><body>{form_html}</body></html>"
```

---

## GET + POST route (Flask)

```python
from flask import Flask, request
from pydantic_schemaforms import Field, FormModel, render_form_html

app = Flask(__name__)

class ContactForm(FormModel):
    name: str = Field(..., min_length=2, title="Full Name", ui_element="text")
    email: str = Field(..., title="Email", ui_element="email")
    message: str = Field(..., min_length=10, title="Message", ui_element="textarea")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        result = ContactForm.validate(request.form.to_dict(), submit_url="/contact")
        if result.is_valid:
            return "Thanks!"
        form_html = result.render_with_errors()
    else:
        form_html = render_form_html(ContactForm, submit_url="/contact")

    return f"<html><body>{form_html}</body></html>"
```

---

## Jinja2 template embedding

Render form HTML server-side, pass it to the template, render with `| safe`.

```python
# route
form_html = await render_form_html_async(ContactForm, submit_url="/contact")
return templates.TemplateResponse("page.html", {"request": request, "form_html": form_html})
```

```html
<!-- page.html -->
<div class="container">
  {{ form_html | safe }}
</div>
```

---

## Field types

```python
from typing import Optional
from pydantic_schemaforms import Field, FormModel

class AllFieldsExample(FormModel):
    # Text inputs
    name:        str           = Field(..., ui_element="text",     ui_placeholder="Full name")
    email:       str           = Field(..., ui_element="email",    ui_placeholder="you@example.com")
    password:    str           = Field(..., ui_element="password", ui_placeholder="••••••••")
    phone:       Optional[str] = Field(None, ui_element="tel",    ui_placeholder="+1 555 000 0000")
    website:     Optional[str] = Field(None, ui_element="url",    ui_placeholder="https://")
    query:       Optional[str] = Field(None, ui_element="search", ui_placeholder="Search…")

    # Multi-line
    bio:         Optional[str] = Field(None, ui_element="textarea", ui_placeholder="Tell us about yourself")

    # Numeric
    age:         Optional[int]   = Field(None, ui_element="number", ge=13, le=120)
    satisfaction: Optional[int]  = Field(None, ui_element="range",  ge=1,  le=10)

    # Date / time
    birth_date:  Optional[str] = Field(None, ui_element="date")
    appt_time:   Optional[str] = Field(None, ui_element="time")

    # Colour picker
    theme_color: str = Field("#3498db", ui_element="color")

    # Select (explicit options list)
    plan: str = Field("free", ui_element="select",
                      json_schema_extra={"ui_options": {"choices": [
                          {"value": "free",  "label": "Free"},
                          {"value": "pro",   "label": "Pro"},
                          {"value": "team",  "label": "Team"},
                      ]}})

    # Boolean
    newsletter:  bool = Field(False, ui_element="checkbox", title="Subscribe to newsletter")
    agree:       bool = Field(False, ui_element="checkbox", title="I accept the terms")
```

---

## Optional fields

Use `Optional[T]` with a default of `None`. Pydantic won't require these; the form renders them without a `*` marker.

```python
from typing import Optional
from pydantic_schemaforms import Field, FormModel

class ProfileForm(FormModel):
    display_name: str           = Field(..., title="Display Name", ui_element="text")
    bio:          Optional[str] = Field(None, title="Bio",         ui_element="textarea")
    website:      Optional[str] = Field(None, title="Website",     ui_element="url")
```

---

## Select from a Python Enum

Enum members become select options automatically. The field value is the enum's `.value`.

```python
from enum import Enum
from pydantic_schemaforms import Field, FormModel

class Role(str, Enum):
    USER  = "user"
    ADMIN = "admin"
    MOD   = "moderator"

class InviteForm(FormModel):
    email: str  = Field(..., title="Email", ui_element="email")
    role:  Role = Field(Role.USER, title="Role", ui_element="select",
                        json_schema_extra={"ui_options": {"choices": [
                            {"value": r.value, "label": r.value.capitalize()} for r in Role
                        ]}})
```

---

## Cross-field validation (password confirmation)

Use `@field_validator` with `info.data` to read already-validated sibling fields.

```python
from pydantic import field_validator
from pydantic_schemaforms import Field, FormModel

class RegistrationForm(FormModel):
    username:         str = Field(..., min_length=3, title="Username",         ui_element="text")
    password:         str = Field(..., min_length=8, title="Password",         ui_element="password")
    confirm_password: str = Field(...,               title="Confirm Password", ui_element="password")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v
```

---

## Field-level @field_validator

Strip and sanitise a field value, or apply custom business rules.

```python
from pydantic import field_validator
from pydantic_schemaforms import Field, FormModel

class CommentForm(FormModel):
    username: str = Field(..., title="Username", ui_element="text")
    body:     str = Field(..., title="Comment",  ui_element="textarea", min_length=5)

    @field_validator("username")
    @classmethod
    def clean_username(cls, v: str) -> str:
        v = v.strip()
        if not v.isalnum():
            raise ValueError("Username may only contain letters and numbers")
        return v
```

---

## Bootstrap vs Material Design

Pass `framework` to change the CSS framework. The default is `"bootstrap"`.

```python
from pydantic_schemaforms import render_form_html_async

# Bootstrap (default)
html = await render_form_html_async(MyForm, submit_url="/submit")

# Material Design 3
html = await render_form_html_async(MyForm, submit_url="/submit", framework="material")
```

---

## Self-contained form (no CDN)

Inline all assets so the HTML chunk has zero external dependencies. Useful for email templates, offline apps, or sandboxed iframes.

```python
html = await render_form_html_async(
    MyForm,
    submit_url="/submit",
    self_contained=True,   # inlines Bootstrap CSS/JS + Bootstrap Icons woff2
)
```

---

## Repeating sub-forms (model list)

Let users add/remove items dynamically with a `model_list` field.

```python
from typing import List
from pydantic_schemaforms import Field, FormModel
from pydantic_schemaforms.form_field import FormField

class PhoneEntry(FormModel):
    label:  str = Field(..., title="Label",  ui_element="text",  ui_placeholder="Mobile / Home / Work")
    number: str = Field(..., title="Number", ui_element="tel",   ui_placeholder="+1 555 000 0000")

class PersonForm(FormModel):
    name:   str              = Field(..., title="Full Name", ui_element="text")
    phones: List[PhoneEntry] = FormField(
        default_factory=list,
        title="Phone Numbers",
        input_type="model_list",
        model_class=PhoneEntry,
        add_button_label="Add phone",
        min_length=0,
        max_length=5,
    )
```

Parse the submitted flat form data back into the nested structure:

```python
from pydantic_schemaforms import parse_nested_form_data

raw = dict(await request.form())
nested = parse_nested_form_data(raw)
result = PersonForm.validate(nested, submit_url="/person")
```

### Customizing the list with `Field()`

The item model is resolved automatically from the `list[ItemModel]` type
annotation — `model_class` is only needed with the `FormField` constructor
shown above. Using the recommended `Field()` constructor, the same list
can be customized with these `ui_*` keyword arguments:

```python
class PersonForm(FormModel):
    name:   str              = Field(..., title="Full Name", ui_element="text")
    phones: List[PhoneEntry] = Field(
        default_factory=list,
        title="Phone Numbers",
        ui_element="model_list",
        ui_add_button_label="Add phone",
        ui_item_title_template="{label}: {number}",
        ui_collapsible_items=False,   # render flat cards instead of collapsible ones
        ui_items_expanded=False,      # start collapsed (only relevant if collapsible)
        min_length=0,
        max_length=5,
    )
```

- `ui_item_title_template` is formatted against the item's own field values
  (here `{label}` and `{number}` from `PhoneEntry`), plus `{index}` (1-based).
- Item-count bounds (`min_length`/`max_length` above) are the same Pydantic
  constraint used for string length — they are not a separate `ui_options`
  setting.
- Nested per-item validation errors (keyed like `phones[0].number` by
  `FormModel.validate()`) render inline on the matching item automatically.

---

## Tabbed layout

Group fields into tabs. Users navigate between tabs without a page reload.

```python
from pydantic_schemaforms import Field, FormModel
from pydantic_schemaforms.form_layouts import TabbedLayout

class ProfileForm(FormModel):
    # Tab 1
    first_name: str = Field(..., title="First Name", ui_element="text")
    last_name:  str = Field(..., title="Last Name",  ui_element="text")
    # Tab 2
    bio:        str = Field("",  title="Bio",     ui_element="textarea")
    website:    str = Field("",  title="Website", ui_element="url")

    class FormConfig:
        layout = TabbedLayout(
            ("Personal", ["first_name", "last_name"]),
            ("Profile",  ["bio", "website"]),
        )
```

---

## Horizontal layout

Render label and input side-by-side (Bootstrap grid).

```python
from pydantic_schemaforms.form_layouts import HorizontalLayout

class SettingsForm(FormModel):
    display_name: str = Field(..., title="Display name", ui_element="text")
    timezone:     str = Field("UTC", title="Timezone",   ui_element="text")

    class FormConfig:
        layout = HorizontalLayout(label_cols=3, input_cols=9)
```

---

## CSRF protection

Generate a token on GET, verify it on POST with a constant-time compare.

```python
import hmac
import secrets
from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware
from pydantic_schemaforms import CSRFMode, render_form_html_async

app.add_middleware(SessionMiddleware, secret_key="change-me-in-production")

SESSION_KEY = "csrf_token"

@app.get("/form", response_class=HTMLResponse)
async def get_form(request: Request):
    token = secrets.token_urlsafe(32)
    request.session[SESSION_KEY] = token

    html = await render_form_html_async(
        MyForm,
        submit_url="/form",
        csrf_mode=CSRFMode.REQUIRED_PROVIDER,
        csrf_token_provider=token,
    )
    return f"<html><body>{html}</body></html>"

@app.post("/form", response_class=HTMLResponse)
async def post_form(request: Request):
    data = dict(await request.form())
    submitted = data.get("csrf_token", "")
    expected  = request.session.get(SESSION_KEY, "")

    if not hmac.compare_digest(submitted, expected):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    result = MyForm.validate(data, submit_url="/form")
    # …
```

---

## Dual-use: HTML form + JSON API from one model

`as_api_model()` strips `ui_*` keys so OpenAPI docs look hand-written, while all validation constraints are preserved.

```python
from pydantic_schemaforms import Field, FormModel

class ContactForm(FormModel):
    name:    str = Field(..., min_length=2, title="Name",    ui_element="text")
    email:   str = Field(...,               title="Email",   ui_element="email")
    message: str = Field(..., min_length=10, title="Message", ui_element="textarea")

# Derive once at module level — safe to use as response_model or body type.
ContactSchema = ContactForm.as_api_model()

# HTML route
@app.api_route("/contact", methods=["GET", "POST"], response_class=HTMLResponse)
async def contact_html(request: Request): ...

# JSON API route — same validation, clean OpenAPI schema
@app.post("/api/contact", response_model=ContactSchema)
async def contact_api(data: ContactSchema):
    return data
```

---

## JSON Schema output

`get_pydantic_json_schema()` returns the standard JSON Schema of the form's
underlying Pydantic model — with real `$defs`/`$ref` for nested `BaseModel`
and `List[BaseModel]` fields. Use this instead of `get_json_schema()`
(a flattened, UI-oriented shape meant for the renderer, which does not
represent nested fields) whenever you need a spec-compliant schema for an
external consumer (OpenAPI tooling, a JSON Schema validator, a code
generator, etc.):

```python
from typing import List
from pydantic_schemaforms import Field, FormModel

class Address(FormModel):
    street: str = Field(..., title="Street")
    city:   str = Field(..., title="City")

class PersonForm(FormModel):
    name:    str          = Field(..., title="Full Name", ui_element="text")
    address: Address      = Field(..., title="Address")
    aliases: List[str]    = Field(default_factory=list)

schema = PersonForm.get_pydantic_json_schema()
# schema["$defs"]["Address"] exists; schema["properties"]["address"] is a $ref

# Pass through Pydantic's own model_json_schema() options as needed:
openapi_schema = PersonForm.get_pydantic_json_schema(
    ref_template="#/components/schemas/{model}"
)
```

`get_pydantic_json_schema()` is built on `as_api_model()` (same UI-key
stripping as the dual-use pattern above), so it is always additive and safe
to call regardless of what UI metadata the form declares.

---

## Nested vs. flat form data

By default, `FormModel.validate()` returns `result.data` shaped exactly
like the underlying (possibly nested) Pydantic model — a `List[BaseModel]`
field like `pets` above comes back as a nested list of dicts, matching
`model_dump()`. Pass `flatten=True` to opt into bracket+dot flat keys
instead (the same notation used for `model_list` HTML field names and for
`parse_nested_form_data()`), for both the accepted input and the returned
`result.data`:

```python
nested = {"owner": "Casey", "pets": [{"name": "Fido", "is_active": True}]}

# Default: nested in, nested out — mirrors the Pydantic model shape.
result = PersonForm.validate(nested, submit_url="/people")
# result.data == {"owner": "Casey", "pets": [{"name": "Fido", "is_active": True}]}

# flatten=True: flat in (nested input is also accepted), flat out.
result = PersonForm.validate(nested, submit_url="/people", flatten=True)
# result.data == {"owner": "Casey", "pets[0].name": "Fido", "pets[0].is_active": True}

flat_input = {"owner": "Casey", "pets[0].name": "Fido", "pets[0].is_active": True}
result = PersonForm.validate(flat_input, submit_url="/people", flatten=True)
# same result — flatten=True un-flattens bracket+dot input before validating
```

`flatten_nested_data()` (the inverse of `parse_nested_form_data()`) is
available directly if you need to flatten data outside of `.validate()`:

```python
from pydantic_schemaforms import flatten_nested_data

flatten_nested_data({"pets": [{"name": "Fido"}]})
# {"pets[0].name": "Fido"}
```

---

## Custom date/time display formats

By default, `date`/`time`/`datetime` fields render as native HTML5 inputs
(`<input type="date">`, etc.) whose display is entirely controlled by the
browser's own locale — there's no way to force a custom display format on a
native control. Set `date_format`/`time_format`/`datetime_format` in
`ui_options` (standard `strftime`/`strptime` directives) to opt into a
custom shape instead — the field falls back to a live-formatted text input
so the display truly matches what you asked for:

```python
from datetime import date, datetime, time
from pydantic_schemaforms import Field, FormModel

class ShiftForm(FormModel):
    shift_date: date = Field(
        ..., title="Date", ui_element="date",
        ui_options={"date_format": "%d/%m/%Y"},       # 05/03/2026
    )
    start_time: time = Field(
        ..., title="Start Time", ui_element="time",
        ui_options={"time_format": "%H:%M"},           # 23:30 -- 24-hour ("military") time
    )
    logged_at: datetime = Field(
        ..., title="Logged At", ui_element="datetime",
        ui_options={"datetime_format": "%Y%m%d%H%M%S"},  # year-month-day-hour(24)-minute-second
    )
```

Without a `*_format` option, a field renders exactly as it always has. With
one set, the server still round-trips correctly either way: a submission in
the configured custom shape parses via that format first, and a plain ISO
string (e.g. from a JSON API client bypassing the HTML form entirely) still
validates too, since the custom-format parse attempt fails silently and
falls through to Pydantic's own ISO parser.

Switching to a text input doesn't lose the browser's native calendar/clock
picker UI — the field stays a single box with a small picker icon inside it
(`live_format=True`, the default) for any format a JS `Date` object can
supply a value for, which includes `%Y %y %m %d %H %I %M %S` as well as
`%p` (AM/PM) and `%B %b %A %a` (month/weekday names, via a hardcoded
English name table): clicking the icon opens the browser's own native
picker (via `showPicker()` on a hidden, non-submitting companion input) and
writes the selected value into the visible field, already converted to the
custom format. Only the rarer, non-`Date`-derivable directives (`%Z`, `%j`,
`%f`, week numbers, ...) omit the icon. Separately, live per-character
typing auto-punctuation only works for formats built *entirely* from
fixed-width numeric directives — `%p`/weekday/month-name formats still get
the picker icon, just not live-typing assistance.

This behavior is the same across every framework, including `material` — a
custom-formatted date/time/datetime field always uses this single-box
icon-toggle control, not a framework-specific widget.

For a much larger, live-runnable reference covering USA/Europe/Asia date
conventions, military (24-hour) time, and compact year-month-day-hour-
minute-second shapes — 21 formats across a 3-tab Date/Time/Datetime demo —
see `examples/date_time_formats_example.py` (`DateTimeFormatsShowcaseForm`),
wired up at the `/date-time-formats` route in `examples/fastapi_routes.py`.

---

## Live HTMX validation

Validate individual fields on blur without a page reload. Requires HTMX loaded in the page.

**Server setup:**

```python
from pydantic_schemaforms import (
    EmailRule, FieldValidator, HTMXValidationConfig, LiveValidator, MinLengthRule,
)
from pydantic_schemaforms.live_validation import validation_response_headers
from fastapi.responses import HTMLResponse

# Build once at module level.
validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True))

fv_name = FieldValidator("name")
fv_name.add_rule(MinLengthRule(2, message="At least 2 characters"))
validator.register_field_validator(fv_name)

fv_email = FieldValidator("email")
fv_email.add_rule(EmailRule())
validator.register_field_validator(fv_email)

VALIDATOR_SCRIPT = validator.render_htmx_script()

@app.post("/validate/{field_name}", response_class=HTMLResponse)
async def validate_field(field_name: str, request: Request):
    raw   = await request.form()
    value = str(raw.get(field_name, ""))
    result = validator.validate_field(field_name, value)

    if result.is_valid:
        feedback = '<span class="text-success">Looks good!</span>'
    else:
        errors   = "; ".join(result.errors)
        feedback = f'<span class="text-danger">{errors}</span>'

    return HTMLResponse(feedback, headers=validation_response_headers(field_name, result.is_valid))
```

**Template (Jinja2 / plain HTML):**

```html
<!-- Load HTMX -->
<script src="/vendor/htmx.min.js"></script>

<!-- Inline the LiveValidator JS (applies is-valid / is-invalid classes) -->
{{ validator_script | safe }}

<!-- Field with live validation -->
<input
  type="text" name="name" id="name"
  hx-post="/validate/name"
  hx-trigger="blur"
  hx-target="#name-feedback"
  hx-swap="innerHTML"
/>
<div id="name-feedback"></div>
```

Pass `validator_script=VALIDATOR_SCRIPT` in the template context.

---

## Multiple triggers (blur + debounced input)

Enable several triggers together; they are combined into one `hx-trigger` attribute.

```python
validator = LiveValidator(HTMXValidationConfig(
    validate_on_blur=True,
    validate_on_input=True,
    validate_on_change=False,
    debounce_ms=400,          # wait 400 ms after typing stops
))
```

This generates `hx-trigger="blur, input delay:400ms"` on each field.

---

## Validate a full Pydantic model field-by-field

Use `register_model_validator` when your validation rules live inside the Pydantic model itself rather than explicit `FieldValidator` rules. Each field is validated in isolation (other required fields are not needed).

```python
from pydantic import BaseModel
from pydantic_schemaforms import HTMXValidationConfig, LiveValidator

class OrderForm(BaseModel):
    quantity: int
    sku: str

validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True))
validator.register_model_validator(OrderForm)
# Now /validate/quantity and /validate/sku both work via validator.validate_field(...)
```

---

## Pre-populate form with existing data

Pass a `form_data` dict to render the form with values already filled in (useful for edit pages).

```python
existing = {"name": "Alice", "email": "alice@example.com", "message": "Hello"}

html = await render_form_html_async(
    ContactForm,
    submit_url="/contact",
    form_data=existing,
)
```

---

## Re-render with validation errors

After a failed POST, re-render showing field-level error messages.

```python
@app.post("/contact", response_class=HTMLResponse)
async def post_contact(request: Request):
    data   = dict(await request.form())
    result = ContactForm.validate(data, submit_url="/contact")

    if result.is_valid:
        return "<p>Sent!</p>"

    # result stores the submit URL; no need to pass it again.
    form_html = await result.render_with_errors_async()
    return f"<html><body>{form_html}</body></html>"
```
