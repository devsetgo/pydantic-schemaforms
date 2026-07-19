# Claude instructions for app teams using pydantic-schemaforms

When asked to build forms in an application using pydantic-schemaforms, follow this contract.

## Completion contract

Always return:

1. FormModel class.
2. Full GET/POST route.
3. render_form_html call with explicit framework, layout, and submit_url.
4. ValidationError mapping to field errors.
5. Sticky value preservation with form_data.

Do not stop at model generation only unless explicitly requested.

## Build contract

- Build forms from FormModel subclasses, not by manually authoring every input.
- Use Field metadata for UI behavior (title, ui_element, ui_placeholder, ui_options).
- Render with render_form_html and always pass submit_url.
- Preserve user input by passing submitted data to form_data on re-render.
- Validate by constructing the model and mapping ValidationError to field errors.
- Choose framework and layout explicitly for predictable output.

## Complete worked example (FastAPI)

Verified end-to-end (GET renders, invalid POST re-renders with errors, valid
POST succeeds). Use this as the template rather than designing a new
form-model abstraction:

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
  validator, and render target in one. Do not build a separate form-model
  wrapper or DTO around it.
- `ui_element` selects the widget and browser hint (`type="email"`, etc.)
  only — it adds no server-side format validation on its own. Use the
  matching Pydantic type for that (`EmailStr`, `AnyUrl`/`HttpUrl`);
  `Field()` constraints (`min_length`, `ge`, `le`, `pattern`, ...) are what
  `.validate()` actually enforces.
- `FormModel.validate(data, submit_url=...)` returns a `ValidationResult`;
  `result.render_with_errors_async()` re-renders with field errors and the
  submitted values preserved.

## Supported ui_element values (authoritative)

This is the complete, current list. **Never use a ui_element value not on
this list** (e.g. "toggle" is real; "switch" or "chips" are not). An
unrecognized value does not error — it silently renders a plain text input,
which is easy to miss in review. Prefer the closest listed primitive over
guessing at a plausible-sounding name.

| Category | Values |
|---|---|
| Text | `text`, `password`, `email`, `search`, `url`, `tel`, `textarea` |
| Formatted text | `ssn`, `phone`, `credit_card` (alias `card`/`cc_number`), `currency` (alias `money`) |
| Numeric | `number`, `range` |
| Specialized numeric | `percentage`, `decimal`, `integer`, `age`, `quantity`, `score`, `rating` (alias `rating_stars`), `slider`, `temperature` |
| Selection | `select`, `multiselect`, `radio`, `combobox`, `checkbox` |
| Boolean toggle | `toggle` (alias `toggle_switch`/`checkbox_toggle`) — styled on/off switch, functionally a checkbox |
| Date/time | `date`, `time`, `datetime` (alias `datetime-local`), `month`, `week` |
| Specialized date | `birthdate` (adds a computed age display) |
| File/color | `file`, `color` |
| Hidden/security | `hidden`, `csrf` (used internally by CSRF support), `honeypot` (spam-trap field; always renders empty by design) |
| Structural (not a real widget) | `model_list` (repeating sub-forms), `layout` (composed layout primitives) |

Most forms only need Text/Numeric/Selection/Date. Specialized numeric/date
rows add presentation behavior only (e.g. `percentage` shows a `%`
placeholder, `rating` renders stars) — validation still comes entirely from
`Field()` constraints, never from the widget choice.

## Input intake contract

Claude should support source input as:

- JSON payload example
- JSON Schema
- Existing BaseModel
- Existing FormModel

If the source has missing constraints, keep conversion conservative and do not fabricate strict validation rules.

## Configuration contract

- framework should be explicit: "bootstrap", "material", or "none".
- layout should be explicit when non-default: "vertical", "tabbed", or "side-by-side".
- submit_url must match the route that handles POST.
- title should provide user-facing labels.
- ui_placeholder should only be helper text, not required business information.
- Keep one coherent framework/layout strategy per endpoint.

## ui_element and ui_options contract

- Use ui_element to pick controls:
	- text-like: text, email, password, search, tel, url
	- long text: textarea
	- numeric: number, range
	- choice: select, multiselect, radio, combobox
	- boolean: checkbox, toggle
	- temporal: date, time, datetime, month, week
	- specialized: file, color, hidden
- min_length/max_length/pattern/ge/le/gt/lt are Field constraints, not
  ui_options. Set them on Field(...) directly — the renderer derives
  minlength/maxlength/pattern/min/max attributes from them AND Pydantic
  enforces them server-side. Putting them in ui_options instead only
  decorates the HTML with no real validation behind it.
- enum/Literal fields auto-populate select/radio/multiselect options from
  the type; only pass ui_options choices for non-enum fields.
- Use ui_options only for widget-level behavior with no constraint
  equivalent:
	- step for numeric/temporal widgets
	- rows/cols/wrap/resize for textarea
	- choices/options lists for select/radio/combobox (non-enum only)
	- autocomplete for text-like widgets
	- accept/multiple/capture for file widgets

## Deterministic mapping policy

Apply mapping precedence:

1. Explicit source hints
2. Semantic type information
3. Naming semantics
4. Primitive fallback

Mapping baseline:

- str -> text
- long free text -> textarea
- EmailStr/email semantics -> email
- AnyUrl/url semantics -> url
- bool -> checkbox
- numeric types -> number
- enum/Literal -> select
- list options -> multiselect
- date/time/datetime -> date/time/datetime

## Layout contract

- Use vertical layout by default.
- Use tabbed layout for long, sectioned forms.
- Use side-by-side layout for compact admin-style forms.
- For custom/advanced layouts, prefer library layout APIs over ad-hoc markup.

### Complex form trigger

Prefer tabbed layout when form size or domain complexity is high, such as:

- More than 12 user-facing fields.
- Multiple distinct business sections.
- Significant onboarding/compliance workflows.

## Expected route behavior

- GET returns rendered form HTML.
- POST reads submitted form data.
- POST validates with the model.
- On failure, re-render with errors and previous values.
- On success, proceed with app flow and optionally render success state.

## Error mapping guidance

- Use errors = {err["loc"][0]: err["msg"] for err in e.errors() if err.get("loc")}.
- Keep messages field-scoped unless there is a true global error.
- Preserve submitted values with form_data on each re-render.

### Lower-boilerplate alternative: FormModel.validate()

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

## Framework guidance

- FastAPI: await request.form().
- Flask: request.form.to_dict().
- Embed returned form HTML inside a full page template/layout.

## CSRF contract

For login, registration, or any state-changing/authenticated form:

- Issue a per-session CSRF token on GET; store it server-side.
- Pass csrf_mode="required-provider", csrf_token_provider=<token>, and
  csrf_field_name to render_form_html/FormModel.validate.
- Verify the submitted token with a constant-time comparison before
  running model validation; on mismatch, re-render with a form-level
  error and issue a fresh token.
- Do not skip CSRF just because the caller didn't ask for it explicitly
  — treat it as part of the completion contract for stateful forms.

## Repeating sub-forms and dual-use models

- For "add another item" style requirements, define a nested FormModel
  and a list[ItemModel] field with ui_element="model_list" instead of
  hand-writing add/remove JavaScript. The item model resolves
  automatically from the list[ItemModel] annotation.
- Customize the list with Field() kwargs (named parameters, not
  ui_options): ui_add_button_label (button text), ui_item_title_template
  (per-item card title formatted against the item's own fields, e.g.
  "{name} (Lead: {lead})"), ui_collapsible_items=False (flat instead of
  collapsible cards), ui_items_expanded=False (start collapsed).
- Bound item count with Field(min_length=..., max_length=...) on the list
  field itself, the same constraint mechanism as any other length bound
  — not a separate ui_options setting.
- Nested per-item errors from FormModel.validate() (keyed like
  "items[0].name") render inline on the matching item automatically.
- Run submitted data through parse_nested_form_data before validating so
  indexed keys reassemble into nested lists.
- When the same fields also need a JSON API, call
  `ApiSchema = MyForm.as_api_model()` once at module scope instead of
  duplicating the model — it strips ui_* metadata but keeps every
  validation constraint, so use it as the API request/response model.

## Inline live validation contract (optional, additive)

Only add this when asked for inline "validates on blur/type" feedback
without a full page reload. It is layered on top of the normal form, not
a substitute for POST validation:

- Build `validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True, ...))`.
- Prefer `validator.register_model_validator(MyForm)` so checks come
  straight from the FormModel's own Field constraints instead of being
  re-declared. Use `register_field_validator(...)` only for custom
  messages/logic the model constraints can't express.
- Embed `validator.render_htmx_script()` once per page.
- Render live-validated fields with
  `validator.render_field_with_live_validation(field_name, field_type=..., value=..., label=...)`.
- Add one `POST /validate/{field_name}` endpoint that calls
  `validator.validate_field(field_name, value)` and returns a small HTML
  fragment with `validation_response_headers(field_name, result.is_valid)` headers
  (import from `pydantic_schemaforms.live_validation`, not the top-level package).
- Keep validating with `FormModel.validate()` on the real submit route
  regardless — live validation is UX only and never replaces server-side
  validation on submit.

## Avoid

- Avoid reverse-engineering non-public package internals.
- Avoid dropping submit_url.
- Avoid form implementations that lose state after failed POST.
- Avoid custom HTML widget markup when ui_element can express the control.
- Avoid silently discarding constraints from source schema/model.
- Avoid putting min_length/max_length/pattern/ge/le in ui_options instead
  of as real Field constraints.
- Avoid skipping CSRF protection on forms that mutate state or sit behind auth.
- Avoid treating HTMX live validation as a replacement for server-side
  validation on the real POST route.

## Conversion workflow (JSON/Pydantic input)

Claude should accept source definitions in any of these forms:

- JSON example payload
- JSON Schema
- Existing Pydantic BaseModel/FormModel

Claude should produce:

- FormModel class using Field metadata
- ui_element and ui_options for each field
- Explicit framework and layout choice
- Complete route integration with GET/POST validation loop

### Strict conversion rules

- Preserve source fields and names unless user asks for renames.
- Keep required/optional semantics aligned with source.
- Preserve defaults where present.
- Reflect min/max/regex/enum constraints in field configuration.
- Explain any unavoidable mapping assumption in one short note.

### Mapping policy

- Preserve source constraints directly in field definitions.
- Prefer semantic widgets over generic text fields.
- For enums/literals, use select (or radio when explicitly requested).
- For long-form text, use textarea with rows in ui_options.
- For booleans, default to checkbox.

### Complexity policy

- For simple forms: use vertical layout.
- For large multi-section forms: use tabbed layout with named groups.
- For dense operational forms: consider side-by-side layout.
- Keep conversion deterministic: do not invent fields not present in source.

## Definition of done

- Route is runnable without placeholders.
- submit_url matches POST handler route.
- Validation errors render for affected fields.
- Submitted values persist across failed POST.
- Widget choices align to field semantics.
- No unnecessary manual HTML widget generation.

### Claude conversion prompt starters

- "Convert this model to a pydantic-schemaforms FormModel and FastAPI endpoint with bootstrap + vertical layout, sticky form_data, and field-level error mapping."
- "Convert this JSON schema to a complex tabbed pydantic-schemaforms form in Flask. Preserve constraints, choose ui_element/ui_options per field, and generate complete GET/POST code."

## Prompt starter for Claude

"Implement this form endpoint using pydantic-schemaforms with FormModel and Field metadata, explicit framework and layout, render_form_html with submit_url, POST validation via model instantiation, field-level error mapping from ValidationError, and sticky values via form_data."
