Goal: produce complete, runnable form integrations without reverse-engineering package internals.

## Output contract (always deliver all items)

1. A FormModel class with field metadata.
2. A full route handler with GET and POST flow.
3. render_form_html call with explicit framework, layout, and submit_url.
4. Validation loop that maps ValidationError to field errors.
5. Sticky form values via form_data.
6. A short explanation of mapping choices for non-obvious fields.

Do not return partial snippets unless the user explicitly asks for partial output.

## Library boundary — treat pydantic-schemaforms as a dependency, not app code

This is the single most important rule in this document. Read it before writing any code.

**`pydantic_schemaforms` is an external library. Never edit, copy, or vendor its source files
into the app repo, and never import from its internal submodules** —
`pydantic_schemaforms.inputs.*`, `pydantic_schemaforms.rendering.*`,
`pydantic_schemaforms.templates`, `pydantic_schemaforms.tstring`, and similar. The only supported
import surface for app code is the top-level package: `from pydantic_schemaforms import ...`.
(`pydantic_schemaforms.live_validation` is the one documented exception — see the HTMX section
below.)

**Before writing any custom Python or HTML for a form field, check whether an existing
`ui_element`, `ui_options` key, or `Field()` constraint already does it.** The "Supported
ui_element values" table and "Field cookbook" sections below cover the overwhelming majority of
real-world form fields — formatted text (phone/currency/SSN/credit card), tags, ratings, sliders,
file upload with drag-and-drop, captcha, repeating sub-forms, and custom date/time display
formats are all declarative `Field(...)` configuration, not code you write.

**This is not a rule against using Pydantic — it is the opposite.** `FormModel` subclasses
`pydantic.BaseModel` directly, so ordinary Pydantic features are completely normal and expected
on a `FormModel` subclass, and are the *correct* tool for anything not already covered below:

- **Cross-field/business validation** (e.g. "password confirmation must match", "end date must
  be after start date") → a standard Pydantic `@model_validator` on the `FormModel` subclass, no
  library-specific step needed:

  ```python
  from pydantic import model_validator
  from pydantic_schemaforms import Field, FormModel


  class SignupForm(FormModel):
      password: str = Field(..., ui_element='password')
      password_confirm: str = Field(..., ui_element='password')

      @model_validator(mode='after')
      def passwords_match(self):
          if self.password != self.password_confirm:
              raise ValueError('Passwords do not match')
          return self
  ```

  `.validate()` surfaces this as a normal validation error automatically — no extra wiring.

The rule is specifically about *not reimplementing what this library already provides on top of
Pydantic* (hand-rolled widget HTML/JS instead of `ui_element`, a bespoke validation-result/form-
submission pipeline instead of `.validate()`/`ValidationResult`, hand-written add/remove-item
JavaScript instead of `model_list`) and *not reaching into the library's private internals* as if
they were part of the app's own codebase to extend or monkeypatch. When a genuinely custom
*rendering* need falls outside everything built in, the library has one supported extension
point — use it, do not invent something else:

- **A genuinely new widget with no matching `ui_element`** → subclass `BaseInput` (or
  `FormInput`) and register it once, at app startup, before serving any requests — do not
  hand-write `<input>` HTML in a route or template:

   ```python
   from pydantic_schemaforms.inputs.base import FormInput
   from pydantic_schemaforms.inputs.registry import register_input_class
   from pydantic_schemaforms.tstring import html


   class ColorSwatchInput(FormInput):
       ui_element = 'color_swatch'

       def get_input_type(self) -> str:
           return 'text'

       def render(self, **kwargs) -> str:
           value = kwargs.get('value', '')
           name = kwargs.get('name', '')
           return html(t'<input type="text" name="{name}" value="{value}" class="color-swatch">')


   register_input_class(ColorSwatchInput, aliases=['color_swatch'])
   ```

  Do this once at module import time (e.g. in the module that defines your `FormModel`s, before
  the app starts serving requests) — then use `ui_element="color_swatch"` in any `Field(...)`
  exactly like a built-in widget. This is genuinely the exception, not the default path: reach
  for it only after confirming nothing in the "Supported ui_element values" table fits.

For the optional HTMX live-validation subsystem specifically (not the primary `.validate()`
path — see that section below), a reusable custom check is `CustomRule(func)` from
`pydantic_schemaforms`, registered on a `FieldValidator`/`FormValidator`. Do not reach for this
for ordinary server-side validation — `Field()` constraints and `@model_validator` above cover
that.

An unrecognized `ui_element` value does not raise an error — it silently falls back to a plain
text input, which is easy to miss in review. If a field's semantics don't cleanly match anything
in the table below, use the closest built-in primitive rather than guessing at a plausible-
sounding custom name, and only write a real custom widget (`register_input_class`, above) if the
mismatch actually matters to the user.

## Complete worked example (FastAPI)

Verified end-to-end (GET renders, invalid POST re-renders with errors, valid POST succeeds). Use
this as the template for new form endpoints instead of inventing a different model/route shape:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel

app = FastAPI()


class EventRegistration(FormModel):
    full_name: str = Field(..., min_length=2, max_length=80, title='Full Name', ui_element='text')
    email: EmailStr = Field(..., title='Email Address', ui_element='email')
    age: int = Field(..., ge=13, le=120, title='Age', ui_element='number')
    ticket_type: str = Field(
        ...,
        title='Ticket Type',
        ui_element='select',
        ui_options={'choices': ['standard', 'vip', 'student']},
    )
    dietary_notes: str = Field(
        '', title='Dietary Notes', ui_element='textarea', ui_options={'rows': 3}
    )
    newsletter_opt_in: bool = Field(False, title='Subscribe to newsletter', ui_element='checkbox')


@app.get('/register', response_class=HTMLResponse)
async def register_get():
    form_html = await EventRegistration.render_form_async(
        submit_url='/register', framework='bootstrap'
    )
    return f'<html><body>{form_html}</body></html>'


@app.post('/register', response_class=HTMLResponse)
async def register_post(request: Request):
    submitted = dict(await request.form())
    result = EventRegistration.validate(submitted, submit_url='/register', framework='bootstrap')
    if result.is_valid:
        return HTMLResponse(f'<h1>Thanks, {result.data["full_name"]}!</h1>')
    form_html = await result.render_with_errors_async()
    return HTMLResponse(f'<html><body>{form_html}</body></html>')
```

Notes:

- `FormModel` subclasses `pydantic.BaseModel` directly — it is the schema, the validator, and
  the render target. There is no separate form-model abstraction to design or invent.
- `ui_element` picks the widget and browser hint (`type="email"`, etc.) — it does not add
  server-side format validation. Use the matching Pydantic type for that (`EmailStr`,
  `AnyUrl`/`HttpUrl`); `Field()` constraints (`min_length`, `ge`, `le`, `pattern`, ...) are what
  `.validate()` actually enforces.
- `FormModel.validate(data, submit_url=...)` returns a `ValidationResult`;
  `result.render_with_errors_async()` re-renders with field errors and the submitted values
  preserved — don't hand-roll try/except ValidationError when this exists.

## Supported ui_element values (authoritative)

This is the complete, current list of valid `ui_element` strings. **Do not invent a value not
on this list.** An unrecognized `ui_element` does not raise an error — it silently falls back to
a plain text input, which is easy to miss in review. If a field's semantics don't match anything
below, use the closest primitive rather than guessing at a plausible-sounding name — see the
"Library boundary" section above for what to do if nothing genuinely fits.

| Category | Values |
|---|---|
| Text | `text`, `password`, `email`, `search`, `url`, `tel`, `textarea` |
| Formatted text | `ssn`, `phone`, `credit_card` (alias `card`/`cc_number`), `currency` (alias `money`) |
| Text collection | `tags` (chip/tag input for a list of short values) |
| Numeric | `number`, `range` |
| Specialized numeric | `percentage`, `decimal`, `integer`, `age`, `quantity` (ships +/- stepper buttons by default), `score`, `rating` (alias `rating_stars`; range-slider based), `star_rating` (individually clickable stars — a distinct widget from `rating`, not an alias of it), `slider`, `temperature` |
| Selection | `select`, `multiselect`, `radio`, `combobox`, `checkbox`, `checkbox_group` |
| Boolean toggle | `toggle` (alias `toggle_switch`/`checkbox_toggle`) — styled on/off switch, functionally a checkbox |
| Date/time | `date`, `time`, `datetime` (alias `datetime-local`), `month`, `week` |
| Specialized date | `birthdate` (adds a computed age display) |
| File/color | `file`, `color` |
| Hidden/security | `hidden`, `csrf` (used internally by CSRF support), `honeypot` (spam-trap field; always renders empty by design), `captcha` (self-hosted arithmetic challenge; the answer is verified server-side via `verify_captcha()` and never sent to the client) |
| Structural (not a real widget) | `model_list` (repeating sub-forms), `layout` (composed layout primitives) |

Most forms only need Text/Numeric/Selection/Date. The "Specialized numeric" and "Specialized
date" rows add presentation behavior only (e.g. `percentage` shows a `%` placeholder, `rating`
renders stars) — validation still comes entirely from `Field()` constraints, not the widget
choice. The full authoritative reference with every ui_options key lives at
<https://devsetgo.github.io/pydantic-schemaforms/inputs/> — check it before assuming an option
doesn't exist.

## Field cookbook: widgets that need more than a bare ui_element

These are the widgets most likely to tempt an assistant into hand-rolling something the library
already does declaratively. Every example below is verified against the library's own docs, not
guessed — copy the shape, adjust the values.

**Custom date/time display format** (military time, DD/MM/YYYY, or any other locale/shape) — the
field still validates as a normal `date`/`time`/`datetime` Python type; only the *displayed and
submitted string shape* changes, using standard `strftime`/`strptime` directives:

```python
from datetime import date, time


class ShiftForm(FormModel):
    shift_date: date = Field(..., ui_element='date', ui_options={'date_format': '%d/%m/%Y'})
    start_time: time = Field(
        ..., ui_element='time', ui_options={'time_format': '%H:%M'}
    )  # 24-hour/"military" time
```

Do not write JavaScript or a custom widget for this — `date_format`/`time_format`/
`datetime_format` in `ui_options` is the built-in mechanism. Without it, fields render exactly as
the browser's native picker; with it, the server still accepts a plain ISO string too (e.g. from
a JSON API caller bypassing the HTML form).

**tags** — a chip/tag editor backed by a single `str` field (not `list[str]`), joined by a
separator:

```python
skills: str = Field(
    '', ui_element='tags', ui_options={'placeholder': 'Add a skill and press Enter'}
)
```

**rating vs. star_rating** — two distinct widgets with *different option names*, easy to mix up:

```python
satisfaction: int = Field(
    3, ui_element='rating', ui_options={'max_rating': 5}
)  # slider + ★★★☆☆ readout
quality_stars: int = Field(
    4, ui_element='star_rating', ui_options={'max_stars': 5}
)  # individually clickable stars
```

**phone / currency** — optional live-formatting masks as the user types (display only; always
validate the submitted value server-side with a real `Field()` constraint):

```python
contact_phone: str = Field(..., ui_element='phone', ui_options={'phone_format': '(###) ###-####'})
budget: str = Field(..., ui_element='currency', ui_options={'currency_symbol': '$'})
```

**captcha** — renders an arithmetic challenge; verify it at the route level with the library's
own `verify_captcha()`, before model validation, and declare only the answer field (not a
separate token field — one is generated automatically):

```python
from pydantic_schemaforms import verify_captcha

SECRET = 'change-me-and-load-from-app-config'


class SignupForm(FormModel):
    captcha_answer: str = Field('', ui_element='captcha', ui_options={'secret_key': SECRET})


# in the POST route, before validating the model:
form_dict = dict(await request.form())
token = form_dict.pop('captcha_answer_token', None)
if not verify_captcha(token=token, answer=form_dict.get('captcha_answer'), secret_key=SECRET):
    ...  # re-render with a form-level error; a fresh challenge renders automatically
```

**file with drag-and-drop** — on by default, no extra wiring needed:

```python
attachments: str = Field(
    ..., ui_element='file', ui_options={'accept': '.pdf,.docx,image/*', 'multiple': True}
)
```

**quantity** — ships +/- stepper buttons automatically:

```python
seats: int = Field(1, ui_element='quantity', ui_options={'min': 1, 'max': 10})
```

## Accepted input sources

- JSON sample payload
- JSON Schema
- Existing Pydantic BaseModel
- Existing FormModel to be refactored/extended

When input is ambiguous, preserve source structure and avoid inventing fields.

## Deterministic field mapping

Apply this order of precedence when converting models/schemas:

1. Explicit source hint (existing ui_element, widget annotation, schema format)
2. Strong semantic type (EmailStr, date, datetime, bool, enum)
3. Naming heuristic (field names like email, phone, website)
4. Fallback by primitive type

### Primitive and semantic mapping

- str -> text
- long descriptive str -> textarea
- EmailStr or email-like field -> email
- AnyUrl or URL-like field -> url
- bool -> checkbox
- int/float/Decimal -> number
- enum/Literal -> select
- list with constrained options -> multiselect
- date -> date
- time -> time
- datetime -> datetime
- bytes/file-like metadata -> file (when upload is intended)

### Constraints vs. ui_options — do not confuse these

min_length, max_length, pattern, ge/le/gt/lt are Pydantic Field constraints, not ui_options. Set
them directly on Field(...) and the renderer auto-derives minlength/maxlength/pattern/min/max
HTML attributes AND real server-side validation from them:

- Field(min_length=2, max_length=50) -> minlength/maxlength + enforced length
- Field(pattern=r'^[A-Z]') -> pattern attribute + enforced regex
- Field(ge=1, le=5) -> min/max attributes + enforced numeric range

Putting these in ui_options instead only decorates the HTML — it does NOT validate anything
server-side. Never use ui_options as a substitute for a real Field constraint; that produces a
form that looks validated but silently accepts out-of-range or malformed data on POST.

Similarly, enum/Literal fields auto-populate select/radio/multiselect options from the type
itself — only pass ui_options choices for plain str/int fields that aren't already an
enum/Literal.

## Form configuration checklist

- Always pass submit_url and keep it route-matched.
- Set framework explicitly: "bootstrap" (recommended), "material", or "none".
- Use layout explicitly for non-default structure: "vertical" (default), "tabbed", or "side-by-side".
- Pass form_data on both GET defaults and failed POST validation so fields are sticky.
- Pass errors as a field-name keyed dictionary.
- Keep one coherent framework/layout strategy per endpoint.
- For first pass implementations, prefer readability over over-customized markup.

## Layout guidance

- Use layout="vertical" for most CRUD and simple forms.
- Use layout="tabbed" for long forms grouped by topic, or when at least one applies: more than 12
  user-facing fields, distinct business sections (Account/Profile/Preferences/Security/Billing),
  or high cognitive load workflows (onboarding, account setup, compliance forms).
- Use layout="side-by-side" when labels/inputs should align horizontally (dense admin pages).
- Use advanced layout primitives only when required (grid, accordion, cards, custom layout fields).
- Prefer predictable, explicit grouping over heuristic grouping for critical workflows — place
  required identity fields in early groups, optional/advanced settings later.

## Framework route contract

### FastAPI

- Route supports both GET and POST.
- Read POST data with submitted = dict(await request.form()).
- Validate with FormModel(**submitted) or FormModel.validate(submitted, ...).
- Re-render with errors + form_data on failure.
- Return HTMLResponse.

### Flask

- Route supports both GET and POST.
- Read POST data with submitted = request.form.to_dict().
- Validate with FormModel(**submitted) or FormModel.validate(submitted, ...).
- Re-render with errors + form_data on failure.
- Return HTML markup or template response.

## Lower-boilerplate alternative: FormModel.validate()

`FormModel.validate(data, submit_url=..., framework=...)` wraps the same validation and returns
a ValidationResult that remembers submit_url and framework, so re-rendering on failure needs no
repeated arguments:

    result = MyForm.validate(parsed_data, submit_url="/submit")
    if result.is_valid:
        return success(result.data)
    return result.render_with_errors()  # or await result.render_with_errors_async()

Prefer this over the manual try/except ValidationError pattern once a route re-renders the same
form in more than one place (e.g. a shared CSRF-failure branch and a validation-failure branch)
— it removes the need to thread submit_url/framework through every re-render call.

## CSRF protection

For any form that changes state (login, registration, anything behind auth, anything mutating
data), add CSRF protection instead of skipping it:

- Issue a per-session token on GET, store it server-side (session/cache).
- Pass csrf_mode="required-provider", csrf_token_provider=<token>, and csrf_field_name to
  render_form_html/FormModel.render_form/FormModel.validate.
- On POST, verify the submitted token against the stored one with a constant-time comparison
  before validating form data.
- On mismatch, re-render with a form-level error (not a field error) and issue a fresh token; do
  not proceed to model validation.
- csrf_mode accepts "off" (no token), "field-only" (renders a field but does not require server
  verification), and "required-provider" (renders + the app must verify it) — default to
  "required-provider" for anything beyond a throwaway demo form.
- Treat this as part of the completion contract for stateful forms, not an optional extra — do
  not skip it just because it wasn't explicitly requested.

## Repeating sub-forms (model_list)

When a form needs a user-editable list of sub-records (e.g. "add another item"), do not hand-
build add/remove JavaScript. Use the library's model_list support instead:

- Define a nested FormModel for one item, then a field typed list[ItemModel] with
  ui_element="model_list" (or input_type="model_list"). The item model class is resolved
  automatically from the list[ItemModel] annotation.
- The renderer produces add/remove controls and repeats the sub-form automatically. Customize it
  with these Field() kwargs (not ui_options — they are named Field parameters, same pattern as
  ui_help_text):
  - ui_add_button_label — custom "Add ..." button text.
  - ui_item_title_template — per-item card title, formatted against the item's own field names,
    e.g. "{name} (Lead: {lead})".
  - ui_collapsible_items=False — render items flat instead of collapsible cards.
  - ui_items_expanded=False — start collapsible items collapsed.
- Bound the number of items with Field(min_length=..., max_length=...) on the list field itself
  — same constraint mechanism as string/number bounds, not a separate ui_options setting.
- Nested per-item validation errors (keyed like "items[0].name" from FormModel.validate())
  render inline on the matching item automatically.
- On POST, run submitted form data through parse_nested_form_data before validating, so
  bracketed/indexed keys (e.g. items[0][name]) are reassembled into nested lists/dicts.

## Dual-use JSON + HTML models (as_api_model)

When the same data also needs a JSON API endpoint (not just an HTML form), do not maintain two
separate models:

- Define one FormModel with ui_* metadata for the HTML form.
- Call `ApiSchema = MyForm.as_api_model()` once at module scope to get a plain Pydantic
  BaseModel with the same fields/constraints/examples but ui_* keys stripped — use it as the
  JSON request/response model (e.g. FastAPI's response_model) so OpenAPI docs stay clean.
- All validation constraints (min_length, ge, pattern, etc.) apply identically to both, since
  as_api_model() only strips UI metadata.

## Inline live validation via HTMX (optional, additive)

Use this only when asked for inline "validates as you type/blur" feedback without a full page
reload. It is a separate rendering path layered on top of the normal form, not a replacement for
POST validation:

- Build `validator = LiveValidator.for_model(MyForm, debounce_ms=600)` — one call that derives
  every field's live check straight from the FormModel's own Field constraints/types (no
  duplicated rules) and checks as-you-type (debounced) rather than only on blur. Pass more than
  one model class to serve several forms' fields from one validator/endpoint:
  `LiveValidator.for_model(FormA, FormB, debounce_ms=600)`. Use
  `validator.register_field_validator(...)` on the returned validator — optionally with a
  `CustomRule(func)` from the "Library boundary" section above for logic the model constraints
  can't express — only for custom messages/logic beyond what the model already enforces. Pass
  `config=HTMXValidationConfig(...)` instead of `debounce_ms=` for anything beyond the debounce
  interval, e.g. blur-only checking.
- Embed `validator.render_htmx_script()` once per page.
- Render fields that need live feedback with
  `validator.render_field_with_live_validation(field_name, field_type=..., value=..., label=...)`.
- Add one endpoint per validated field, e.g. `POST /validate/{field_name}`, that reads the
  submitted value, calls `validator.validate_field(field_name, value)`, and returns a small HTML
  fragment with headers from `validation_response_headers(field_name, result.is_valid)` (import
  from `pydantic_schemaforms.live_validation`, not the top-level package).
- Keep the real POST submit route validating with `FormModel.validate()` regardless — live
  validation is UX sugar; it never replaces server-side validation on submit (JS can be disabled
  or bypassed).
- For an email field, add a DNS/MX deliverability check (catches typo'd/non-existent domains, not
  just format) by typing the field `DeliverableEmailStr` instead of `EmailStr` — it's a drop-in
  type, so `LiveValidator.for_model(MyForm)` above picks it up automatically with no extra
  FieldValidator code. Reach for `FieldValidator("email").required().email(check_deliverability=True)`
  instead only if you're building a validator imperatively (FormBuilder, no typed model). Either
  way this needs the optional `email-validator` package (`pip install pydantic-schemaforms[email-dns]`)
  and always runs server-side only — there is no way to do a real DNS lookup from browser JS.

### Complete worked example (FastAPI, live validation)

Verified end-to-end (GET renders with the HTMX wiring in place, POST /validate/{field} returns
correct pass/fail HTML for both a plain constraint and a DNS/MX check). Use this as the template
instead of inventing a different validator/endpoint shape:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import (
    DeliverableEmailStr,
    Field,
    FormModel,
    LiveValidator,
    render_form_html_async,
)
from pydantic_schemaforms.live_validation import validation_response_headers

app = FastAPI()


class SignupForm(FormModel):
    name: str = Field(..., min_length=2, title='Full Name', ui_element='text')
    email: DeliverableEmailStr = Field(  # EmailStr + a real DNS/MX lookup, both live-checked below
        ...,
        title='Email',
        ui_element='email',
        ui_options={
            'hx-post': '/validate/email',
            'hx-trigger': 'blur, input delay:600ms',
            'hx-target': '#email-feedback',
            'hx-swap': 'innerHTML',
            'data-validate-endpoint': 'true',
        },
    )


# Module scope, built once: derives a live check for every field on SignupForm
# straight from its Field() constraints/types -- no FieldValidator to hand-write.
live_validator = LiveValidator.for_model(SignupForm, debounce_ms=600)
VALIDATOR_SCRIPT = live_validator.render_htmx_script()  # embed once per page


@app.get('/signup', response_class=HTMLResponse)
async def signup_get():
    form_html = await render_form_html_async(SignupForm, submit_url='/signup')
    return f'<html><body>{form_html}{VALIDATOR_SCRIPT}</body></html>'


@app.post('/validate/{field_name}', response_class=HTMLResponse)
async def validate_field(field_name: str, request: Request):
    # One route serves every field on the model -- validate_field() dispatches
    # by name, so adding a field to SignupForm needs no new route here.
    raw = await request.form()
    value = str(raw.get(field_name, ''))
    result = live_validator.validate_field(field_name, value)
    feedback = (
        '<span class="text-success">Looks good!</span>'
        if result.is_valid
        else f'<span class="text-danger">{result.errors[0]}</span>'
    )
    return HTMLResponse(feedback, headers=validation_response_headers(field_name, result.is_valid))


@app.post('/signup', response_class=HTMLResponse)
async def signup_post(request: Request):
    data = dict(await request.form())
    result = SignupForm.validate(data, submit_url='/signup')  # the real safety net -- always runs
    if result.is_valid:
        return '<p>Signed up!</p>'
    return await result.render_with_errors_async()
```

The `email` field needs an empty `<div id="email-feedback"></div>` on the page for the response
to swap into (it does not have to sit immediately next to the input — hovering the input itself
also shows the same text as a tooltip, since the bundled JS mirrors the swapped feedback into the
input's `title` attribute). `name` has no `ui_options` here, so it has no live feedback target;
add the same `ui_options` block (with its own `hx-target`) to give it one too.

## Conversion workflows (JSON or Pydantic -> FormModel)

You can provide either a JSON payload/schema or an existing Pydantic model and ask the assistant
to convert it.

- Input accepted: JSON example payload, JSON Schema, or BaseModel/FormModel code.
- Output expected:
	- A FormModel class using Field metadata.
	- ui_element choices for each field.
	- ui_options where needed (choices, min/max, rows, pattern, etc.).
	- A working FastAPI or Flask GET/POST route using render_form_html.

### Complex form expectations

For complex requests, also provide:

- Explicit layout choice (tabbed or side-by-side when appropriate).
- Section grouping rationale (for example Account, Profile, Preferences).
- Field-level constraints mirrored from model/schema (min_length, max_length, ge, le,
  regex/pattern).
- Sticky value handling and field error mapping.

## Quality gates before completion

- Generated code is runnable with no placeholder TODO blocks.
- submit_url and route path align.
- Every rendered field exists in model definition.
- Every required field has sensible label/title metadata.
- No manual field-by-field HTML when schema-driven rendering is enough.
- No import from a `pydantic_schemaforms` internal submodule (see "Library boundary" above).

## Common mistakes to avoid

- Do not extend, monkeypatch, or reimplement anything inside `pydantic_schemaforms` — see
  "Library boundary" above. Standard Pydantic (`@field_validator`, `@model_validator`, etc.) on
  your own `FormModel` subclass is fine; rewriting what the library already provides is not.
- Do not hand-build each input manually when render_form_html already handles model fields.
- Do not omit submit_url.
- Do not use a plain Pydantic BaseModel when you need ui_element metadata, validate(), or
  as_api_model() — subclass FormModel instead.
- Do not discard submitted form values on validation error.
- Do not silently drop source constraints during conversion.
- Do not mix multiple conflicting layout styles in one endpoint.
- Do not put min_length/max_length/pattern/ge/le in ui_options — set them as real Field
  constraints so they are actually enforced server-side.
- Do not skip CSRF protection on forms that mutate state or sit behind auth.
- Do not hand-write add/remove list JavaScript — use ui_element="model_list".
- Do not hand-roll custom date/time formatting (military time, locale-specific shapes) — use
  ui_options date_format/time_format/datetime_format.
