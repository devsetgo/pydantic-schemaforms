# Pydantic SchemaForms app integration instructions

Use these rules when generating form code in an application that depends on pydantic-schemaforms.

Goal: produce complete, runnable form integrations without reverse-engineering package internals.

## Output contract (always deliver all items)

1. A FormModel class with field metadata.
2. A full route handler with GET and POST flow.
3. render_form_html call with explicit framework, layout, and submit_url.
4. Validation loop that maps ValidationError to field errors.
5. Sticky form values via form_data.
6. A short explanation of mapping choices for non-obvious fields.

## Accepted input sources

- JSON sample payload
- JSON Schema
- Existing Pydantic BaseModel
- Existing FormModel to be refactored/extended

When input is ambiguous, preserve source structure and avoid inventing fields.

## Complete worked example (FastAPI)

Verified end-to-end (GET renders, invalid POST re-renders with errors, valid
POST succeeds). Use this as the template for new form endpoints:

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
        return HTMLResponse(f"<h1>Thanks, {result.data['full_name']}!</h1>")
    form_html = await result.render_with_errors_async()
    return HTMLResponse(f'<html><body>{form_html}</body></html>')
```

Notes:

- `FormModel` subclasses `pydantic.BaseModel` directly — it is the schema,
  the validator, and the render target. There is no separate form-model
  abstraction to design or invent.
- `ui_element` picks the widget and browser hint (`type="email"`, etc.) —
  it does not add server-side format validation. Use the matching Pydantic
  type for that (`EmailStr`, `AnyUrl`/`HttpUrl`); `Field()` constraints
  (`min_length`, `ge`, `le`, `pattern`, ...) are what `.validate()` actually
  enforces.
- `FormModel.validate(data, submit_url=...)` returns a `ValidationResult`;
  `result.render_with_errors_async()` re-renders with field errors and the
  submitted values preserved — don't hand-roll try/except ValidationError
  when this exists.

## Supported ui_element values (authoritative)

This is the complete, current list of valid `ui_element` strings. **Do not
invent a value not on this list.** An unrecognized `ui_element` does not
raise an error — it silently falls back to a plain text input, which is
easy to miss in review. If a field's semantics don't match anything below,
use the closest primitive rather than guessing at a plausible-sounding name.

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

Most forms only need Text/Numeric/Selection/Date. The "Specialized numeric"
and "Specialized date" rows add presentation behavior only (e.g.
`percentage` shows a `%` placeholder, `rating` renders stars) — validation
still comes entirely from `Field()` constraints, not the widget choice.

## Core integration pattern

1. Define a class that inherits from FormModel.
2. Use pydantic_schemaforms.Field for field metadata.
3. Render with render_form_html(ModelClass, ...).
4. Always provide submit_url.
5. On POST, parse request form data and pass it back through form_data so values persist when validation fails.
6. Convert Pydantic validation errors into an errors dictionary keyed by field name.

## Framework route contract

### FastAPI

- Route supports both GET and POST.
- Read POST data with submitted = dict(await request.form()).
- Validate with FormModel(**submitted).
- Re-render with errors + form_data on failure.
- Return HTMLResponse.

### Flask

- Route supports both GET and POST.
- Read POST data with submitted = request.form.to_dict().
- Validate with FormModel(**submitted).
- Re-render with errors + form_data on failure.
- Return HTML markup or template response.

## Field hints

- Use ui_element for control type (email, password, textarea, checkbox, select, etc.).
- Use title for human-facing labels.
- Use ui_placeholder for placeholder text.
- Use ui_options for select/radio choices when needed.

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

min_length, max_length, pattern, ge/le/gt/lt are Pydantic Field constraints,
not ui_options. Set them directly on Field(...) and the renderer
auto-derives minlength/maxlength/pattern/min/max HTML attributes AND
real server-side validation from them:

- Field(min_length=2, max_length=50) -> minlength/maxlength + enforced length
- Field(pattern=r'^[A-Z]') -> pattern attribute + enforced regex
- Field(ge=1, le=5) -> min/max attributes + enforced numeric range

Putting these in ui_options instead only decorates the HTML — it does
NOT validate anything server-side. Never use ui_options as a substitute
for a real Field constraint; that produces a form that looks validated
but silently accepts out-of-range or malformed data on POST.

Similarly, enum/Literal fields auto-populate select/radio/multiselect
options from the type itself — only pass ui_options choices for plain
str/int fields that aren't already an enum/Literal.

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
- Use layout="tabbed" for long forms grouped by topic.
- Use layout="side-by-side" when labels/inputs should align horizontally.
- Use advanced layout primitives only when required (grid, accordion, cards, custom layout fields).
- Prefer predictable, explicit grouping over heuristic grouping for critical workflows.

### Grouping strategy for large forms

- Group by user intent (Account, Profile, Preferences, Security, Billing).
- Keep each group focused and balanced.
- Place required identity fields in early groups.
- Place optional and advanced settings later.

## ui_element quick guide

See "Supported ui_element values (authoritative)" near the top of this file
for the full list. Quick picks for the common cases:

- text, email, password, search, tel, url for common string inputs.
- textarea for longer free text.
- number or range for numeric values.
- select, multiselect, radio, combobox when choosing from options.
- checkbox or toggle for booleans.
- date, time, datetime, month, week for temporal fields.
- file, color, hidden for specialized inputs.

### Accessibility and UX defaults

- Always set title for visible labels.
- Use placeholders as examples, not as the only label.
- Preserve browser-native validation helpers where possible.
- Prefer select/radio only when options are known and bounded.

## ui_options patterns

Reserve ui_options for widget behavior that has no Field-constraint
equivalent (do not repeat minlength/maxlength/pattern/min/max here — see
above):

- text-like fields: autocomplete.
- textarea: rows, cols, wrap, resize.
- number/range: step.
- select/radio/combobox: options or choices list (non-enum fields only).
- date/time-like inputs: value (default/demo prefill only).
- file: accept, multiple, capture.

## Validation and error policy

- Validate server-side via model instantiation on each POST.
- Keep field-level errors keyed by field name.
- Preserve all submitted values when re-rendering after failures.
- Do not suppress model constraints to force rendering success.
- Keep any cross-field/business rules in the model layer where possible.

## Validation flow

- Validate submitted data by instantiating the FormModel.
- If validation fails, map e.errors() entries to field-level messages.
- Re-render the same form with form_data + errors.

### Lower-boilerplate alternative: FormModel.validate()

`FormModel.validate(data, submit_url=..., framework=...)` wraps the same
validation and returns a ValidationResult that remembers submit_url and
framework, so re-rendering on failure needs no repeated arguments:

    result = MyForm.validate(parsed_data, submit_url="/submit")
    if result.is_valid:
        return success(result.data)
    return result.render_with_errors()  # or await result.render_with_errors_async()

Prefer this over the manual try/except ValidationError pattern once a
route re-renders the same form in more than one place (e.g. a shared
CSRF-failure branch and a validation-failure branch) — it removes the
need to thread submit_url/framework through every re-render call.

- The library returns form markup; the app should embed that in a full page template.
- Keep submit_url explicit and route-matched.
- Choose framework="bootstrap", framework="material", or framework="none" intentionally.
- Use host-page framework assets unless you intentionally use self-contained rendering.

## CSRF protection

For any form that changes state (login, registration, anything behind
auth, anything mutating data), add CSRF protection instead of skipping it:

- Issue a per-session token on GET, store it server-side (session/cache).
- Pass csrf_mode="required-provider", csrf_token_provider=<token>, and
  csrf_field_name to render_form_html/FormModel.render_form/FormModel.validate.
- On POST, verify the submitted token against the stored one with a
  constant-time comparison before validating form data.
- On mismatch, re-render with a form-level error (not a field error) and
  issue a fresh token; do not proceed to model validation.
- csrf_mode accepts "off" (no token), "field-only" (renders a field but
  does not require server verification), and "required-provider"
  (renders + the app must verify it) — default to "required-provider"
  for anything beyond a throwaway demo form.

## Repeating sub-forms (model_list)

When a form needs a user-editable list of sub-records (e.g. "add another
item"), do not hand-build add/remove JavaScript. Use the library's
model_list support instead:

- Define a nested FormModel for one item, then a field typed
  list[ItemModel] with ui_element="model_list" (or input_type="model_list").
  The item model class is resolved automatically from the list[ItemModel]
  annotation.
- The renderer produces add/remove controls and repeats the sub-form
  automatically. Customize it with these Field() kwargs (not ui_options —
  they are named Field parameters, same pattern as ui_help_text):
  - ui_add_button_label — custom "Add ..." button text.
  - ui_item_title_template — per-item card title, formatted against the
    item's own field names, e.g. "{name} (Lead: {lead})".
  - ui_collapsible_items=False — render items flat instead of collapsible
    cards.
  - ui_items_expanded=False — start collapsible items collapsed.
- Bound the number of items with Field(min_length=..., max_length=...) on
  the list field itself — same constraint mechanism as string/number
  bounds, not a separate ui_options setting.
- Nested per-item validation errors (keyed like "items[0].name" from
  FormModel.validate()) render inline on the matching item automatically.
- On POST, run submitted form data through parse_nested_form_data before
  validating, so bracketed/indexed keys (e.g. items[0][name]) are
  reassembled into nested lists/dicts.

## Dual-use JSON + HTML models (as_api_model)

When the same data also needs a JSON API endpoint (not just an HTML
form), do not maintain two separate models:

- Define one FormModel with ui_* metadata for the HTML form.
- Call `ApiSchema = MyForm.as_api_model()` once at module scope to get a
  plain Pydantic BaseModel with the same fields/constraints/examples but
  ui_* keys stripped — use it as the JSON request/response model
  (e.g. FastAPI's response_model) so OpenAPI docs stay clean.
- All validation constraints (min_length, ge, pattern, etc.) apply
  identically to both, since as_api_model() only strips UI metadata.

## Inline live validation via HTMX (optional, additive)

Use this only when asked for inline "validates as you type/blur" feedback
without a full page reload. It is a separate rendering path layered on
top of the normal form, not a replacement for POST validation:

- Build `validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True, ...))`.
- Prefer `validator.register_model_validator(MyForm)` to derive per-field
  checks straight from the FormModel's own Field constraints (no
  duplicated rules). Use `validator.register_field_validator(...)` only
  for custom messages/logic the model constraints can't express.
- Embed `validator.render_htmx_script()` once per page.
- Render fields that need live feedback with
  `validator.render_field_with_live_validation(field_name, field_type=..., value=..., label=...)`.
- Add one endpoint per validated field, e.g. `POST /validate/{field_name}`,
  that reads the submitted value, calls
  `validator.validate_field(field_name, value)`, and returns a small HTML
  fragment with headers from `validation_response_headers(field_name, result.is_valid)`
  (import from `pydantic_schemaforms.live_validation`, not the top-level package).
- Keep the real POST submit route validating with `FormModel.validate()`
  regardless — live validation is UX sugar; it never replaces server-side
  validation on submit (JS can be disabled or bypassed).

## Conversion workflows (JSON or Pydantic -> FormModel)

You can provide either a JSON payload/schema or an existing Pydantic model and ask the assistant to convert it.

- Input accepted: JSON example payload, JSON Schema, or BaseModel/FormModel code.
- Output expected:
	- A FormModel class using Field metadata.
	- ui_element choices for each field.
	- ui_options where needed (choices, min/max, rows, pattern, etc.).
	- A working FastAPI or Flask GET/POST route using render_form_html.

### Mapping defaults

- string -> text
- EmailStr or email-like field name -> email
- bool -> checkbox
- int/float -> number
- list[enum]/list[str] with choices -> multiselect
- enum or Literal choices -> select
- long text descriptions -> textarea
- date/datetime/time types -> date/datetime/time

### Complex form expectations

For complex requests, require the assistant to also provide:

- Explicit layout choice (tabbed or side-by-side when appropriate).
- Section grouping rationale (for example Account, Profile, Preferences).
- Field-level constraints mirrored from model/schema (min_length, max_length, ge, le, regex/pattern).
- Sticky value handling and field error mapping.

## Quality gates before completion

- Generated code is runnable with no placeholder TODO blocks.
- submit_url and route path align.
- Every rendered field exists in model definition.
- Every required field has sensible label/title metadata.
- No manual field-by-field HTML when schema-driven rendering is enough.

## Common mistakes to avoid

- Do not hand-build each input manually when render_form_html already handles model fields.
- Do not omit submit_url.
- Do not use a plain Pydantic BaseModel when you need ui_element metadata,
  validate(), or as_api_model() — subclass FormModel instead.
- Do not discard submitted form values on validation error.
- Do not silently drop source constraints during conversion.
- Do not mix multiple conflicting layout styles in one endpoint.
- Do not put min_length/max_length/pattern/ge/le in ui_options — set them
  as real Field constraints so they are actually enforced server-side.
- Do not skip CSRF protection on forms that mutate state or sit behind auth.
- Do not hand-write add/remove list JavaScript — use ui_element="model_list".

### Prompt templates

- Simple conversion:
	"Convert this model into a pydantic-schemaforms FormModel and render route. Keep layout vertical, framework bootstrap, and include full GET/POST validation flow."

- Complex conversion:
	"Convert this schema into a pydantic-schemaforms FormModel for a production form. Group fields into tabbed layout sections, choose ui_element and ui_options per field, preserve all constraints, and generate a full [FastAPI/Flask] endpoint with sticky form_data and field-level errors."

## Suggested request prompt

"Use pydantic-schemaforms in this app. Build a FormModel, render with render_form_html, validate POST data with the model, map ValidationError to field errors, and preserve submitted values in form_data. Keep submit_url explicit."
