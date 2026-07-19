# Copilot instructions for app teams using pydantic-schemaforms

Goal: generate correct application-side form integration quickly without reverse engineering library internals.

## Completion contract

Always return:

1. FormModel class.
2. GET/POST route implementation.
3. render_form_html invocation with explicit framework, layout, submit_url.
4. ValidationError to field-errors mapping.
5. Sticky form_data behavior.

Do not return partial snippets unless user explicitly asks for partial output.

## Preferred implementation pattern

1. Create a FormModel subclass.
2. Use pydantic_schemaforms.Field for UI metadata.
3. Render with render_form_html(ModelClass, submit_url=..., form_data=..., errors=..., framework=...).
4. Validate POST submissions by instantiating the model.
5. Convert ValidationError to a dictionary of field errors.
6. Re-render with submitted values and errors.

## Complete worked example (FastAPI)

Verified end-to-end (GET renders, invalid POST re-renders with errors, valid
POST succeeds). Use this as the template for new form endpoints instead of
inventing a different model/route shape:

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

Notes on this example:

- `FormModel` subclasses `pydantic.BaseModel` directly — no separate
  "form model" abstraction to design; the model *is* the schema, validator,
  and render target.
- `ui_element` only controls which HTML widget renders and hints browsers
  (e.g. `type="email"`). It does **not** add server-side format validation.
  Use the matching Pydantic type for that (`EmailStr` for email addresses,
  `AnyUrl`/`HttpUrl` for URLs) — `Field()` constraints (`min_length`, `ge`,
  `le`, `pattern`, ...) are what's actually enforced on `.validate()`.
- `EventRegistration.validate(data, submit_url=...)` returns a
  `ValidationResult`; `result.render_with_errors_async()` re-renders the
  same form with field errors and the submitted values preserved. Do not
  hand-roll a `try/except ValidationError` block when this exists.

## Supported ui_element values (authoritative)

This is the complete, current list. **Do not invent a `ui_element` value not
on this list** (for example "toggle" — real, but names like "switch" or
"chips" are not). An unrecognized `ui_element` string does not raise an
error — it silently renders a plain text input, which is easy to miss in
review. When unsure, use the closest match below or ask rather than guess.

| Category | Values |
|---|---|
| Text | `text`, `password`, `email`, `search`, `url`, `tel`, `textarea` |
| Formatted text | `ssn`, `phone`, `credit_card` (alias `card`/`cc_number`), `currency` (alias `money`) |
| Text collection | `tags` (chip/tag input for a list of short values) |
| Numeric | `number`, `range` |
| Specialized numeric | `percentage`, `decimal`, `integer`, `age`, `quantity` (ships +/- stepper buttons by default), `score`, `rating` (alias `rating_stars`; range-slider based), `star_rating` (individually clickable stars — a distinct widget from `rating`, not an alias of it), `slider`, `temperature` |
| Selection | `select`, `multiselect`, `radio`, `combobox`, `checkbox`, `checkbox_group` |
| Boolean toggle | `toggle` (alias `toggle_switch`/`checkbox_toggle`) — a styled on/off switch; functionally a checkbox |
| Date/time | `date`, `time`, `datetime` (alias `datetime-local`), `month`, `week` |
| Specialized date | `birthdate` (adds a computed age display) |
| File/color | `file`, `color` |
| Hidden/security | `hidden`, `csrf` (used internally by CSRF support), `honeypot` (spam-trap field; always renders empty on purpose), `captcha` (self-hosted arithmetic challenge; the answer is verified server-side via `verify_captcha()` and never sent to the client) |
| Structural (not a widget) | `model_list` (repeating sub-forms, see below), `layout` (composed layout primitives) |

Most forms only need the Text/Numeric/Selection/Date rows above. The
"Specialized numeric" and "Specialized date" rows add presentation behavior
(e.g. `percentage` adds a `%` placeholder and 0–100 bounds hint, `rating`
renders a star widget) on top of the base widget — they do not change what
Pydantic validates; validation still comes entirely from `Field()`
constraints.

## Intake modes

Copilot must support converting from:

- JSON payload sample
- JSON Schema
- Existing BaseModel
- Existing FormModel

If source is incomplete, keep unknowns explicit and do not invent hidden fields.

## Form configuration defaults

- Always include submit_url.
- Start with framework="bootstrap" unless app design requires material or none.
- Start with layout="vertical" and only switch when form complexity justifies it.
- Preserve submitted values in form_data after failed validation.
- Keep field labels in title, not hard-coded in templates.
- Keep one framework and one layout strategy per endpoint.

## Layout strategy

- layout="vertical": default for most forms.
- layout="tabbed": good for long multi-section forms.
- layout="side-by-side": useful for dense admin pages.
- Avoid custom layout primitives unless user explicitly asks for advanced composition.

### Complex-layout trigger

Use layout="tabbed" by default when at least one applies:

- More than 12 user-facing fields.
- Distinct business sections (for example profile + billing + preferences).
- High cognitive load workflows (onboarding, account setup, compliance forms).

## UI metadata strategy

- Select input widgets with ui_element, not custom HTML.
- See "Supported ui_element values (authoritative)" above for the full list
  — do not use a value that isn't on that list.
- min_length/max_length/pattern/ge/le/gt/lt are Field constraints, not
  ui_options. Set them on Field(...) directly so the renderer emits
  minlength/maxlength/pattern/min/max AND Pydantic actually enforces
  them server-side. ui_options versions of these only decorate the HTML
  with no real validation.
- enum/Literal fields auto-populate select/radio/multiselect options;
  only pass ui_options choices for non-enum fields.
- Use ui_options for per-widget options with no constraint equivalent:
	- text-like: autocomplete
	- textarea: rows, cols, wrap, resize
	- numeric: step
	- select-like: choices/options lists (non-enum only)
	- date/time-like: value (prefill only)
	- file: accept, multiple, capture

## Deterministic type mapping

Apply mapping precedence:

1. Source explicit widget hint
2. Semantic type
3. Name heuristic
4. Primitive fallback

Mapping baseline:

- str -> text
- long text -> textarea
- EmailStr/email-like name -> email
- bool -> checkbox
- int/float/Decimal -> number
- enum/Literal -> select
- lists with bounded options -> multiselect
- date/time/datetime -> date/time/datetime
- URL-like fields -> url

## FastAPI checklist

- Route supports GET and POST.
- POST uses submitted = dict(await request.form()).
- Validation errors map loc[0] -> msg.
- Response class is HTMLResponse.
- submit_url matches route path.
- Re-render includes both form_data and errors.

## Flask checklist

- Route supports GET and POST.
- POST uses submitted = request.form.to_dict().
- Validation errors map loc[0] -> msg.
- submit_url matches route path.
- Re-render includes both form_data and errors.

## Lower-boilerplate alternative: FormModel.validate()

`FormModel.validate(data, submit_url=..., framework=...)` returns a
ValidationResult that remembers submit_url/framework, so failure
handling needs no repeated arguments:

    result = MyForm.validate(parsed_data, submit_url="/submit")
    if result.is_valid:
        return success(result.data)
    return result.render_with_errors()  # or await result.render_with_errors_async()

Prefer this once a route re-renders the form from more than one branch
(e.g. CSRF failure and validation failure) — it removes the need to
thread submit_url/framework through every re-render call.

## CSRF checklist

For login, registration, or any state-changing/authenticated form:

- Issue a per-session CSRF token on GET; store it server-side.
- Pass csrf_mode="required-provider", csrf_token_provider=<token>,
  csrf_field_name to render_form_html/FormModel.validate.
- Verify the submitted token (constant-time compare) before validating
  form data; on mismatch, re-render with a form-level error and a fresh
  token.
- Treat this as part of the completion contract for stateful forms, not
  an optional extra.

## Repeating sub-forms and dual-use models

- For "add another item" requirements, define a nested FormModel and a
  list[ItemModel] field with ui_element="model_list" instead of hand-
  writing add/remove JavaScript. The item model resolves automatically
  from the list[ItemModel] annotation.
- Customize with Field() kwargs (named parameters, not ui_options):
  ui_add_button_label (button text), ui_item_title_template (per-item
  card title formatted against the item's own fields, e.g.
  "{name} (Lead: {lead})"), ui_collapsible_items=False (flat cards),
  ui_items_expanded=False (start collapsed).
- Bound item count with Field(min_length=..., max_length=...) on the list
  field itself — the same constraint mechanism as any other length
  bound, not a separate ui_options setting.
- Nested per-item errors from FormModel.validate() (keyed like
  "items[0].name") render inline on the matching item automatically.
- Run submitted data through parse_nested_form_data before validating.
- For a JSON API backed by the same fields, call
  `ApiSchema = MyForm.as_api_model()` once at module scope rather than
  duplicating the model — it strips ui_* metadata but keeps every
  constraint.

## Inline live validation checklist (optional, additive)

Only add this when the user asks for inline "validates on blur/type"
feedback without a full page reload. It layers on top of the normal
form; it does not replace POST validation:

- Build `validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True, ...))`.
- Prefer `validator.register_model_validator(MyForm)` so checks come from
  the FormModel's own Field constraints instead of being re-declared. Use
  `register_field_validator(...)` only for custom messages/logic the
  model constraints can't express.
- Embed `validator.render_htmx_script()` once per page.
- Render live-validated fields with
  `validator.render_field_with_live_validation(field_name, field_type=..., value=..., label=...)`.
- Add one `POST /validate/{field_name}` endpoint calling
  `validator.validate_field(field_name, value)` and returning a small
  HTML fragment with `validation_response_headers(field_name, result.is_valid)` headers
  (import from `pydantic_schemaforms.live_validation`, not the top-level package).
- Keep the real submit route validating with `FormModel.validate()`
  regardless — live validation is UX only.

## Do not do this

- Do not manually build full input HTML unless user explicitly asks for custom templates.
- Do not inspect or copy private internals from the package source.
- Do not omit submit_url.
- Do not lose form state after failed validation.
- Do not mix inconsistent layout modes in one endpoint without a clear requirement.
- Do not drop source constraints (min/max/regex/required) during conversion.
- Do not put min_length/max_length/pattern/ge/le in ui_options instead of
  as real Field constraints.
- Do not skip CSRF protection on forms that mutate state or sit behind auth.
- Do not treat HTMX live validation as a replacement for server-side
  validation on the real POST route.

## Good defaults

- framework="bootstrap" for most apps.
- Use title on fields for labels.
- Use ui_element for non-text inputs.
- Keep business validation in the Pydantic model.

## Conversion playbook (source -> FormModel)

Required conversion output:

1. A FormModel class with Field metadata.
2. ui_element per field.
3. ui_options for constraints/choices when relevant.
4. A complete GET/POST endpoint that renders and validates.

### Complex form mode

When schema has many fields or multiple domains:

- Use layout="tabbed" and name tabs clearly.
- Keep one framework and one layout strategy per endpoint.
- Preserve constraints from source model/schema.
- Return final code that is runnable without hand edits.

## Definition of done for Copilot output

- Code compiles/imports in target framework.
- Form submits to correct route.
- Validation errors show at field level.
- Submitted values survive failed POST.
- Widget selection aligns with data semantics.
- No manual HTML widgets unless explicitly requested.

### Copilot conversion prompt starters

- "Convert this Pydantic model into a FormModel + FastAPI form endpoint using pydantic-schemaforms. Keep bootstrap + vertical layout and full validation loop."
- "Convert this JSON schema into a tabbed pydantic-schemaforms FormModel and Flask route. Map every field to ui_element/ui_options, preserve constraints, and include sticky form_data + ValidationError mapping."

## Prompt starter for Copilot Chat

"Implement a [FastAPI/Flask] form route using pydantic-schemaforms. Use FormModel + Field metadata, choose framework and layout explicitly, render via render_form_html with explicit submit_url, validate POST data with the model, map ValidationError to field errors, and preserve posted values in form_data."
