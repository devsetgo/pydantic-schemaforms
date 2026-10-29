<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/pydantic-schemaforms/references/validation.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
# Validation reference

Validation comes from the model first: the field types, `Field()` constraints and Pydantic
validators. The rule classes and live HTMX checks below are extras for when the model isn't
enough. All names are imported from the top-level package.

## Constraints and validators on the model

```python
from datetime import date

from pydantic import ValidationInfo, field_validator, model_validator

from pydantic_schemaforms import Field, FormModel


class RegistrationForm(FormModel):
    username: str = Field(title='Username', min_length=3, max_length=20, pattern=r'^[a-z0-9_]+$')
    password: str = Field(title='Password', ui_element='password', min_length=8)
    confirm_password: str = Field(title='Confirm password', ui_element='password')
    age: int = Field(title='Age', ge=13, le=120)
    start_date: date = Field(title='Start date')
    end_date: date = Field(title='End date')

    @field_validator('username', mode='before')
    @classmethod
    def lowercase_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value

    @model_validator(mode='after')
    def end_after_start(self) -> 'RegistrationForm':
        if self.end_date < self.start_date:
            raise ValueError('The end date must be after the start date')
        return self
```

| Constraint | Applies to | In the browser |
|---|---|---|
| `min_length`, `max_length` | text (characters), lists (items) | `minlength`, `maxlength` |
| `pattern` | text | `pattern` |
| `ge`, `le` | numbers | `min`, `max` |
| `gt`, `lt` | numbers | server only |
| `multiple_of` | numbers | `step` |

- `@field_validator("name")` attaches its message to that field. `mode="before"` runs on the raw
  submitted value first, for cleaning it up (trim, lowercase).
- `@model_validator(mode="after")` is for rules across fields. Its message is form-wide, under
  `result.errors["_errors"]`, shown at the top of the form.
- A check that needs the request (a username already taken, a wrong password, a failed captcha)
  belongs in the route after `validate()`: render again with
  `render_form_html(Model, form_data=submitted, errors={"username": "That username is taken"}, ...)`.
- A required checkbox ("I accept the terms") with a custom message: give it a `False` default,
  `validate_default=True`, and a `@field_validator` that raises when it's `False`. An unticked
  box sends nothing, so without `validate_default` the validator never runs.

## Rule-based validation

`FormValidator` holds a set of rules that run on the submitted data alongside the model. Use it
for a ready-made check that isn't a Pydantic type (`PhoneRule`), rules switched per route, or the
same rules behind live validation and the submit route.

```python
from pydantic_schemaforms import Field, FormModel, FormValidator, PhoneRule


class SignupForm(FormModel):
    username: str = Field(title='Username', min_length=3)
    phone: str = Field('', title='Phone', ui_element='tel')
    age: int = Field(title='Age', ge=0)
    parental_consent: bool = Field(False, title='A parent agrees')


def minors_need_consent(data: dict) -> tuple[bool, dict]:
    age = data.get('age')
    if age is not None and int(age) < 18 and not data.get('parental_consent'):
        return False, {'parental_consent': 'A parent must agree for anyone under 18'}
    return True, {}


rules = FormValidator()
rules.field('phone').add_rule(PhoneRule())
rules.add_cross_field_rule(minors_need_consent)
```

Run the rules on `result.original_data` (the decoded submission, nested like the model) and
merge both sets of errors into one re-render:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import SignupForm, rules

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()


@app.get('/signup', response_class=HTMLResponse)
async def show_signup():
    return await render_form_html_async(SignupForm, submit_url='/signup')


@app.post('/signup', response_class=HTMLResponse)
async def submit_signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup')
    rules_ok, rule_errors = rules.validate(result.original_data)
    if not (result.is_valid and rules_ok):
        return await result.render_with_errors_async(errors={**rule_errors, **result.errors})
    username = result.data['username']
    return html(t'<p>Welcome, {username}!</p>')
```

| Rule | Checks |
|---|---|
| `RequiredRule(message=...)` | Present and not blank |
| `MinLengthRule(n)` / `MaxLengthRule(n)` | Length (there is no `LengthRule`) |
| `RegexRule(pattern, message)` | Matches the pattern |
| `EmailRule()` | Email format |
| `EmailDeliverabilityRule()` | The domain exists and accepts mail (a DNS lookup, server only, needs the `email` extra) |
| `PhoneRule()` | Phone-number shape |
| `NumericRangeRule(min_value=, max_value=)` | Number in range (keywords are `min_value`/`max_value`) |
| `DateRangeRule(min_date=, max_date=)` | Date in range (`date` objects or ISO strings) |
| `CustomRule(func, message)` | `func(value)` returns `True`, or `(is_valid, message)` |

- Every rule takes `message=` to replace its default text.
- Rules other than `RequiredRule` pass an empty value, so optional fields are only checked when
  filled in. A `CustomRule` function is called for empty values too.
- `rules.field("x")` returns that field's `FieldValidator`. It also has a fluent form:
  `FieldValidator("username").required().min_length(3).max_length(20)`.
- A cross-field rule gets the whole data dict and returns `(is_valid, {field: "message"})`: one
  string per field, not a list. Ready-made ones:
  `CrossFieldRules.password_confirmation(password_field="password", confirm_field="confirm_password")`
  and `CrossFieldRules.date_range_validation(start_field, end_field)`.
- `rules.validate(data)` returns `(is_valid, {field: [messages]})`: a list per field, unlike the
  model's errors.

## Live validation (HTMX)

Checks fields on the server while the user types, without reloading the page. It's an addition
to submit-time validation, never a replacement: the POST route still calls `validate()`.

```python
from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel, LiveValidator


def live(field: str) -> dict[str, str]:
    """HTMX attributes that send the field to /validate/<field> as the user types."""
    return {
        'hx-post': f'/validate/{field}',
        'hx-trigger': 'blur, input delay:600ms',
        'hx-target': f'#{field}-feedback',
        'hx-swap': 'innerHTML',
    }


class ContactForm(FormModel):
    name: str = Field(title='Full name', min_length=2, ui_options=live('name'))
    email: EmailStr = Field(title='Email', ui_options=live('email'))


live_validator = LiveValidator.for_model(ContactForm, debounce_ms=600)
```

```python
from models import live_validator

from pydantic_schemaforms import SafeHTML, html

VALIDATOR_SCRIPT = SafeHTML(live_validator.render_htmx_script())


def page(form_html: str) -> str:
    form = SafeHTML(form_html)  # trusted HTML from the library
    return html(t"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Contact</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <script src="https://unpkg.com/htmx.org@2.0.7"></script>
  {VALIDATOR_SCRIPT}
</head>
<body>
  <main class="container my-5">
    {form}
    <div id="name-feedback" aria-live="polite"></div>
    <div id="email-feedback" aria-live="polite"></div>
  </main>
</body>
</html>""")


def feedback(errors: list[str]) -> str:
    if not errors:
        return html(t'<span class="text-success">Looks good</span>')
    message = '; '.join(errors)  # may echo what the user typed: html() escapes it
    return html(t'<span class="text-danger">{message}</span>')
```

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ContactForm, live_validator
from page import feedback, page

from pydantic_schemaforms import html, render_form_html_async, validation_response_headers

app = FastAPI()


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return page(await render_form_html_async(ContactForm, submit_url='/contact'))


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), submit_url='/contact')
    if not result.is_valid:
        return page(await result.render_with_errors_async())
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')


@app.post('/validate/{field_name}', response_class=HTMLResponse)
async def validate_field(field_name: str, request: Request):
    value = str((await request.form()).get(field_name, ''))
    result = live_validator.validate_field(field_name, value)
    return HTMLResponse(
        feedback(result.errors),
        headers=validation_response_headers(field_name, result.is_valid),
    )
```

- **`LiveValidator.for_model(Model, debounce_ms=600)`** checks each field against the model's own
  types and constraints, so there are no rules to repeat. Pass several models to serve several
  forms from one validator.
- **The `hx-*` attributes go in `ui_options`**; any key an input doesn't use becomes an HTML
  attribute. Each `hx-target` needs an element on the page to receive the feedback.
- **The page loads HTMX** and includes `live_validator.render_htmx_script()` once.
- **One endpoint serves every field**: `live_validator.validate_field(name, value)` returns a
  `ValidationResponse`. Build the feedback with `html(t'...')`, since a message can repeat what
  the user typed, and send `validation_response_headers(name, result.is_valid)` with it.
- `register_field_validator(FieldValidator(...))` adds rules beyond the model's; pass
  `config=HTMXValidationConfig(...)` instead of `debounce_ms` to change when checks run
  (`validate_on_blur`, `validate_on_change`, `validate_on_input`).
- For an email field, the type `DeliverableEmailStr` adds a DNS/MX check to both live and submit
  validation.

## Two error shapes

| From | `.errors` is |
|---|---|
| `Model.validate()` → `ValidationResult` | a nested tree shaped like the data: `{"email": "...", "address": {"city": "..."}, "_errors": "..."}` |
| `LiveValidator.validate_field()` / `FieldValidator.validate()` → `ValidationResponse` or tuple | a `list[str]` of messages for one field |
| `FormValidator.validate()` | `{field: [messages]}` |

Don't index one shape as if it were another. `render_with_errors(errors=...)` and
`render_form_html(errors=...)` accept the tree and the `{field: [messages]}` form.
