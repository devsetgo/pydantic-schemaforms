<!-- GENERATED FILE -- do not edit directly. Source: _shared_instructions.md + _profile_copilot.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
# Copilot instructions for app teams using pydantic-schemaforms

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
`pydantic_schemaforms.templates`, `pydantic_schemaforms.tstring`, and similar — **even for names
that are actually defined there**. `SafeHTML`, `html`, `FormTemplates`, `TemplateString`,
`FormInput`/`BaseInput`, `register_input_class`, `LayoutEngine`, and everything else this document
references are all re-exported at the top level specifically so app code never needs the internal
path: `from pydantic_schemaforms import html, SafeHTML, FormInput, register_input_class,
LayoutEngine`. If a name you need doesn't import from the top-level package, that's a signal to
re-check the name/spelling before reaching into an internal module as a workaround.
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
   from pydantic_schemaforms import FormInput, html, register_input_class


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
  for it only after confirming nothing in the "Supported ui_element values" table fits. `render()`
  must build HTML through `html(t'...')` (a t-string), never an f-string or `.format()` — that's
  what auto-escapes `value`/`name`; the same rule that applies to route handlers below applies
  here.

- **A genuinely new composite control** (something bigger than one input — a whole table, a
  repeating wizard, anything that doesn't fit a single `ui_element`) → this is what
  `DataTableLayout` (see its own section below) and `model_list` are themselves built on, and
  it's the same mechanism you should reuse rather than hand-rolling a bespoke rendering path.
  Register via the `LayoutEngine` class (top-level export):

  ```python
  from pydantic_schemaforms import LayoutEngine


  @LayoutEngine.layout_renderer('kanban_board', builtin=False)
  def render_kanban_board(
      field_name, field_schema, value, ui_info, context, engine
  ) -> str: ...  # build and return the composite's HTML with html(t'...')
  ```

  The engine calls the renderer with exactly these six positional arguments; the field's own
  error message is `context.error` and its nested errors are `context.child_errors`. Then
  declare the field as `Field(default_factory=dict, input_type="layout",
  layout_handler="kanban_board")` and build its value with your own class method (mirroring
  `DataTableLayout.as_layout_value()`'s convention) — the field's *value* carries whatever the
  renderer needs. `builtin=False` is correct for an app-level renderer like this (only the
  library's own shipped renderers use `builtin=True`). If the composite's own fields ARE its
  structure (table columns, board lanes — not a `list[ItemModel]` like `model_list`), subclass
  `CompositeLayoutModel` (also a top-level export) instead of `FormModel` for that structure
  class; it disables `render_form()` since a composite isn't meant to render as one standalone
  instance's inputs. This is a deep extension point — reach for it only when the "Supported
  ui_element values" table and existing composites (`DataTableLayout`, `model_list`) genuinely
  don't fit, and prefer sticking with those two over inventing a new composite when either
  already covers the need.

For the optional HTMX live-validation subsystem specifically (not the primary `.validate()`
path — see that section below), a reusable custom check is `CustomRule(func)` from
`pydantic_schemaforms`, registered on a `FieldValidator`/`FormValidator`. Do not reach for this
for ordinary server-side validation — `Field()` constraints and `@model_validator` above cover
that.

There is also a separate, standalone **imperative validation subsystem** (`ValidationSchema`,
`FormValidator`, `FieldValidator`'s fluent API, `ValidationResponse`, plus convenience factories
`create_email_validator()`/`create_password_strength_validator()`/`create_validator()`) for
building/composing validation rules at runtime rather than through `Field()` constraints on a
typed model — e.g. `FieldValidator("email").required().email(check_deliverability=True)`,
cross-field rules via `FormValidator`, or conditional validation. This is the same subsystem the
HTMX live-validation section reaches for `CustomRule`/`FieldValidator` from. **Default to `Field()`
constraints + `@model_validator` on a `FormModel` for anything with a known schema — that's what
every other section of this document assumes** — and reach for this fluent API only when you
genuinely don't have (or don't want) a typed model for the validation rules themselves, e.g. rules
assembled dynamically or shared across forms that aren't the same `FormModel`. All of these names
are top-level exports; the full API is documented in `docs/validation_guide.md`, not repeated here.

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

from pydantic_schemaforms import Field, FormModel, html

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
    result = EventRegistration.validate(
        await request.form(), submit_url='/register', framework='bootstrap'
    )
    if result.is_valid:
        return HTMLResponse(html(t'<h1>Thanks, {result.data["full_name"]}!</h1>'))
    form_html = await result.render_with_errors_async()
    return HTMLResponse(f'<html><body>{form_html}</body></html>')
```

Notes:

- **Never interpolate submitted/validated data into HTML with an f-string or `.format()`,
  even after `.validate()` succeeded** — validation confirms the value satisfies Pydantic type/
  constraint rules, it does not make the value safe to place in HTML (a `full_name` of
  `<script>...</script>` is a perfectly valid `str`). Wrap any hand-built HTML that includes such
  a value in `html(t'...')` (a t-string, not an f-string) as shown above — this is the library's
  structural XSS defense and it applies to every byte of hand-written HTML in your route code,
  not just to what the library itself renders. `form_html`/`VALIDATOR_SCRIPT`-style variables that
  are *already-rendered output from this library* (e.g. `result.render_with_errors_async()`'s
  return value) are safe to drop into an f-string as-is — they're pre-escaped HTML, not raw user
  input.
- `FormModel` subclasses `pydantic.BaseModel` directly — it is the schema, the validator, and
  the render target. There is no separate form-model abstraction to design or invent.
- `ui_element` picks the widget and browser hint (`type="email"`, etc.) — it does not add
  server-side format validation. Use the matching Pydantic type for that (`EmailStr`,
  `AnyUrl`/`HttpUrl`); `Field()` constraints (`min_length`, `ge`, `le`, `pattern`, ...) are what
  `.validate()` actually enforces.
- `EmailStr` (used above, and in every email field in this document) requires the optional
  `email-validator` package **just to define the model class**, not only to validate a value —
  a `FormModel` with an `EmailStr` field raises `ImportError` at class-definition time without
  it. If the app you're generating has any email field, add
  `pydantic-schemaforms[email]` to its dependencies (or plain `email-validator`) rather than
  assuming the base `pydantic-schemaforms` install covers it.
- `FormModel.validate(data, submit_url=...)` returns a `ValidationResult`;
  `result.render_with_errors_async()` re-renders with field errors and the submitted values
  preserved — don't hand-roll try/except ValidationError when this exists.

### Alternative entry point: the builder DSL (FormBuilder)

Everything above uses `FormModel` — a typed Pydantic subclass you author. The library also ships
a second, officially-supported path for *programmatic* form construction where you don't want a
named model class up front: `FormBuilder`/`AutoFormBuilder` plus `create_form_from_model()`,
`create_login_form()`, `create_registration_form()`, `create_contact_form()`, and
`FormIntegration`/`handle_form()`/`handle_form_async()` for wiring the result into a route (all
top-level exports). **Default to `FormModel` for anything you're generating from a spec/schema/
description** — it gives you a real, reusable, type-checked class other code can reference. Reach
for the builder DSL specifically when the caller already has a form built imperatively at runtime
(e.g. an admin tool that assembles a form's fields from data, not from a fixed schema known ahead
of time) and explicitly asks for that pattern — don't switch to it as a shortcut for a form you
could just as well define as a `FormModel`.

## Supported ui_element values (authoritative)

This is the complete, current list of valid `ui_element` strings. **Do not invent a value not
on this list.** An unrecognized `ui_element` does not raise an error — it silently falls back to
a plain text input, which is easy to miss in review. If a field's semantics don't match anything
below, use the closest primitive rather than guessing at a plausible-sounding name — see the
"Library boundary" section above for what to do if nothing genuinely fits.

| Category | Values |
|---|---|
| Text | `text`, `password`, `email`, `search`, `url`, `tel`, `textarea` |
| Formatted text | `ssn` (alias `social_security_number`), `phone` (alias `phone_number`), `credit_card` (alias `card`/`cc_number`), `currency` (alias `money`) |
| Text collection | `tags` (chip/tag input for a list of short values) |
| Numeric | `number`, `range` |
| Specialized numeric | `percentage`, `decimal`, `integer`, `age`, `quantity` (ships +/- stepper buttons by default), `score`, `rating` (alias `rating_stars`; range-slider based), `star_rating` (individually clickable stars — a distinct widget from `rating`, not an alias of it), `slider`, `temperature` |
| Selection | `select`, `multiselect`, `radio`, `combobox`, `checkbox`, `checkbox_group` |
| Boolean toggle | `toggle` (alias `toggle_switch`/`checkbox_toggle`) — styled on/off switch, functionally a checkbox |
| Date/time | `date`, `time`, `datetime` (alias `datetime-local`), `month`, `week` |
| Specialized date | `birthdate` (adds a computed age display) |
| File/color | `file`, `color` |
| Hidden/security | `hidden` (a bare `<input type="hidden">` with no label; `ui_hidden=True` on any field does the same), `csrf` (used internally by CSRF support), `honeypot` (spam-trap field; always renders empty by design), `captcha` (self-hosted arithmetic challenge; the answer is verified server-side via `verify_captcha()` and never sent to the client) |
| Structural (not a real widget) | `nested_model` (a sub-form: inferred automatically for a field typed as another `FormModel`, never declare it), `model_list` (repeating sub-forms: inferred automatically for a `list[FormModel]` field), `layout` (a registered custom composite such as `DataTableLayout`) |

Most forms only need Text/Numeric/Selection/Date. The "Specialized numeric" and "Specialized
date" rows add presentation behavior only (e.g. `percentage` shows a `%` placeholder, `rating`
renders stars) — validation still comes entirely from `Field()` constraints, not the widget
choice. Every ui_options key each widget accepts is listed in "Every widget option" below —
check it before assuming an option doesn't exist, and before inventing one (an unknown key is
not an error: it is written onto the `<input>` as an HTML attribute).

**Do not trust `pydantic_schemaforms.NUMERIC_INPUTS`/`TEXT_INPUTS`/`SELECTION_INPUTS`/
`DATETIME_INPUTS`/`SPECIALIZED_INPUTS` (top-level exported constants) as a way to double-check
this table at runtime.** They currently include several category names with no actual registered
widget behind them (a coarser categorization used elsewhere in the library's own code, not a live
registry listing) — using one of those non-widget names as a `ui_element` value produces the
exact silent plain-text fallback this section warns about. The table above, not those constants,
is the accurate, current source of real `ui_element` values.

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
form = await request.form()
token = form.get('captcha_answer_token')
if not verify_captcha(token=token, answer=form.get('captcha_answer'), secret_key=SECRET):
    ...  # re-render with errors={"_errors": "..."}; a fresh challenge renders automatically
```

**file with drag-and-drop** — on by default, no extra wiring needed:

```python
attachments: str = Field(
    ..., ui_element='file', ui_options={'accept': '.pdf,.docx,image/*', 'multiple': True}
)
```

The model field's own type is `str` (a filename, an identifier, whatever you assign it after
saving the upload) — **the actual uploaded file never goes through `.validate()`/Pydantic at
all**, so pop it out of the submitted data before calling `.validate()`:

```python
form = await request.form()  # FastAPI/Starlette: an UploadFile object for the file key
upload = form.get('attachments')  # UploadFile, not a str -- do not pass this into .validate()
submitted = {k: v for k, v in form.items() if k != 'attachments'}
if upload and upload.filename:
    contents = await upload.read()  # bytes -- save it, then put a filename/path/id into submitted
    submitted['attachments'] = save_uploaded_file(upload.filename, contents)  # -> str for the model
result = MyForm.validate(submitted, submit_url='/submit')
```

Rendering with a file field also requires `enctype="multipart/form-data"` on the `<form>` tag —
`render_form_html()` sets this automatically whenever a `file` field is present, so this is only
worth knowing if you're hand-assembling a `<form>` tag around library-rendered field HTML instead
of using `render_form_html()`'s own complete output (the recommended path — don't do this). Flask
uses a different API for the same upload (`request.files['attachments']`, a `FileStorage`, not
`request.form`) — mixing it into `dict(request.form.to_dict())` the way other fields are read
will not pick up the file at all.

**quantity** — ships +/- stepper buttons automatically:

```python
seats: int = Field(1, ui_element='quantity', ui_options={'min': 1, 'max': 10})
```

**select with a forced placeholder** — without this, a `select` with no current value
renders with no `<option selected>` at all, so the browser silently highlights the
first real option as if it had been chosen — a common source of "the user never
touched this dropdown but it submitted a value anyway" bugs:

```python
plan: str = Field(
    ...,
    ui_element='select',
    ui_options={'placeholder': 'Choose a plan...', 'choices': ['free', 'pro', 'enterprise']},
)
```

Renders a disabled, empty-value first option that's `selected` only until a real
choice is made (once a real value is set, the placeholder stays present and disabled
— unselectable again — but is no longer the selected one). Combined with the
`required` attribute this library already adds for a required field, native browser
validation blocks submission on the placeholder alone. Opt-in only — omitting
`placeholder` renders exactly as before. Works the same on every framework
(`bootstrap`/`plain`/`none`/`material`). Only for `select`, not `multiselect`/
`radio`/`checkbox_group`/`combobox` — none of those have this native
auto-select-first-option problem.

**collapsible `checkbox_group`/`radio`** — group related options under a toggle so a
long list doesn't take up space until opened (e.g. a burger-builder form's
"Vegetables"/"Condiments"/"Extra" toppings):

```python
vegetables: list[str] = Field(
    default_factory=list,
    ui_element='checkbox_group',
    ui_options={'choices': ['Lettuce', 'Pickle'], 'collapsible': True, 'collapsed': True},
)
```

Turns the fieldset's `<legend>` into a clickable toggle; `collapsed=True` starts it
closed (default: open). **Purely presentational** — do not reach for this expecting
it to change which fields are required. It never touches validation: fields inside
keep exactly whatever required-ness their own `Field(...)` declaration already gives
them, collapsed or not. Opt-in only — omitting `collapsible` renders exactly as
before. Works the same on every framework. Only for `checkbox_group`/`radio`, not
`select`/`multiselect`/`combobox`.

**code/structured-data editor** (JSON, YAML, TOML, Bash, or Python) — still a plain `textarea`
field (a `str`), with an optional "Format"/"Clean up whitespace" button, Tab-key indentation, and
light syntax highlighting layered on client-side:

```python
config: str = Field(
    '{}', title='Config (JSON)', ui_element='textarea', ui_options={'language': 'json', 'rows': 10}
)
```

`language` accepts `"json"`, `"yaml"`, `"toml"`, `"bash"`, or `"python"`. Only JSON/YAML/TOML get
a real reserialize-on-Format (native `JSON.parse`/`JSON.stringify` for JSON; vendored `js-yaml`/
`smol-toml` for the other two); Bash/Python only get whitespace cleanup (no small dependency-free
equivalent to `black`/`shfmt` exists), so don't promise real code formatting for those two.
Invalid input on Format never throws — it flags the field with a CSS class and inline error
instead, leaving the textarea's content untouched.

## Every widget option (`ui_options` keys)

Pass these as `Field(..., ui_options={...})`. Defaults are what you get without the key. The
example app's widget gallery (`/gallery`) renders every row of this table.

| ui_element | Key | Default | Effect |
|---|---|---|---|
| any | `placeholder`, `autocomplete`, `data-*`, `hx-*`, any other scalar | — | Any key not listed below becomes an HTML attribute on the input (how HTMX attributes are attached). Lists/dicts are skipped. |
| `textarea` | `rows` | browser default | Visible lines |
| `textarea` | `resize` | — | CSS `resize` value, e.g. `"none"` or `"vertical"` |
| `textarea` | `language` | — | `json`/`yaml`/`toml`/`bash`/`python`: code editor with a Format button, Tab indentation, syntax highlighting |
| `textarea` | `code_format` / `code_highlight` / `code_tab_indent` | `True` | Turn off the Format button / highlighting / Tab-key indentation (with `language`) |
| `textarea` | `indent_size` | `2` | Spaces per indent level (with `language`) |
| `phone` | `phone_format` | — | Mask with `#` per digit, e.g. `"(###) ###-####"` |
| `phone` | `country_code` | — | Prefix such as `"+44"` added to the value/placeholder |
| `phone`, `currency`, `date`, `time`, `datetime` | `live_format` | `True` | `False` applies the format on blur instead of while typing |
| `currency` | `currency_symbol` | `"$"` | Symbol shown and stripped on submit |
| `tags` | `separator` | `","` | Join character for the submitted string |
| `number`, `integer`, `decimal`, `percentage`, `age`, `score`, `temperature` | `show_stepper` | `False` | +/- buttons beside the input |
| `quantity` | `show_stepper` | `True` | `False` removes its default +/- buttons |
| `decimal` | `decimal_places` | `2` | Sets the input's `step` (e.g. 4 → `0.0001`) |
| `score` | `min_score`, `max_score` | `0`, `100` | Bounds |
| `temperature` | `unit` | `"celsius"` | `"fahrenheit"`/`"kelvin"`: sets the placeholder (`68°F`, `293K`) and the absolute-zero minimum |
| `range`, `slider`, `rating`, `color` | `show_value` | `True` | Hide the live value readout (hex readout for `color`) |
| `slider` | `show_labels` | `True` | Hide the min/max labels under the slider |
| `rating` | `max_rating` | `5` | Number of stars (slider based) |
| `star_rating` | `max_stars` | `5` | Number of clickable stars (note: not `max_rating`) |
| `date` / `time` / `datetime` | `date_format` / `time_format` / `datetime_format` | native picker | `strftime` display format, e.g. `"%m/%d/%Y"`, `"%I:%M %p"`; the field still validates as `date`/`time`/`datetime` |
| `datetime` | `with_set_now_button` | `False` | Adds a "Set Now" button |
| `datetime` | `auto_set_current` | `False` | Fills the current time when the field is empty on load |
| `birthdate` | `show_age` | `True` | Hide the computed-age line |
| `file` | `accept` | — | e.g. `".pdf,.docx"` or `"image/*"` |
| `file` | `multiple` | `False` | Allow several files |
| `file` | `capture` | — | `"environment"`/`"user"`: open the camera on mobile |
| `file` | `show_preview` | `True` | Hide the chosen-file list / image thumbnails |
| `file` | `enable_drag_drop` | `True` | Plain file input without the drop zone |
| `select`, `multiselect`, `radio`, `checkbox_group`, `combobox` | `choices` (or `options`) | — | `["a", "b"]` or `[{"value": "a", "label": "A"}]`; an `Enum`-typed field needs neither |
| `select` | `placeholder` | — | Disabled blank first option that forces a real choice |
| `multiselect` | `searchable` | `True` | `False`: chips without the search box |
| `multiselect` | `search_placeholder` | `"Search..."` | Text in the search box |
| `multiselect` | `enhanced` | `True` | `False`: a native `<select multiple>` |
| `combobox` | `filter_mode` | `"contains"` | `"startswith"` matches from the start of each option |
| `combobox` | `min_chars` | `0` | Characters typed before suggestions appear |
| `radio` | `variant` | `"stacked"` | `"segmented"`: options as an adjacent button row |
| `checkbox_group` | `variant` | `"stacked"` | `"button_group"`: options as an adjacent button row |
| `radio`, `checkbox_group` | `collapsible` | `False` | The legend toggles the options open/closed |
| `radio`, `checkbox_group` | `collapsed` | `False` | Start closed (with `collapsible`) |

The `segmented`/`button_group` variants only add CSS classes (`radio-item-segmented`,
`checkbox-item-button-group`); the app styles them. The gallery route in
`examples/fastapi_routes.py` has a copyable stylesheet.

## Field-level options (work on every widget)

These are `Field()` keyword arguments, not `ui_options` keys:

| Keyword | Effect |
|---|---|
| `title=` | Label text (also the tab/step/section heading for a sub-form field) |
| `description=` or `ui_help_text=` | Help text under the input |
| `ui_placeholder=` | Placeholder attribute |
| `icon=` | Icon name shown before the label (`"envelope"`, `"person"`, ...), mapped per framework |
| `ui_order=` | Position among the fields/groups; lower first, default is declaration order |
| `ui_disabled=True` | Disabled: not editable and **not submitted** |
| `ui_readonly=True` | Read-only: not editable but submitted |
| `ui_hidden=True` | Rendered as a bare hidden input (same as `ui_element="hidden"`) |
| `ui_autofocus=True` | Focused on load (one field per page) |
| `ui_class=` / `ui_style=` | Extra CSS class / inline style on the input |
| `ui_element=` (`input_type=` and `ui_widget=` are accepted aliases) | The widget; see the table above |
| `ui_collapsible=True` / `ui_collapsed=True` | On a sub-form field: render it as a collapsible section (vertical layout), optionally starting closed; it opens itself when it holds an error |
| `ui_step_title=` | On a sub-form field: the step label under `layout="wizard"` (falls back to `title=`) |
| `ui_add_button_label=`, `ui_item_title_template=`, `ui_collapsible_items=`, `ui_items_expanded=` | On a `list[FormModel]` field: see "Repeating sub-forms" |

Every keyword Pydantic's own `Field()` doesn't know (all of the above plus anything else) is
stored in the field's `json_schema_extra`, so they combine freely with Pydantic constraints.

### The widget classes behind the strings

Each `ui_element` value maps to an exported input class (`TextInput`, `TextArea`, `SelectInput`,
`RadioGroup`, `CheckboxGroup`, `MultiSelectInput`, `ComboBoxInput`, `DateInput`, `FileInput`,
`ToggleSwitch`, `TagsInput`, `CurrencyInput`, ...). App code names the string on the field and
never instantiates these, with two exceptions: subclassing one for `register_input_class` (see
"Library boundary"), and rendering a lone input outside any model,
`TextInput().render_with_label(name="q", label="Search", framework="bootstrap")`. Inside a
custom widget's `render()`, `build_label(field_name, label, required, icon, framework)`,
`build_help_text(field_name, text)` and `build_error_message(field_name, error)` return the
framework-correct label/help/error markup so it matches the built-ins. `BaseInput`/`FormInput`,
`NumericInput`, `SelectInputBase` and `FileInputBase` are the base classes. `DateRangeInput`,
`TimeRangeInput`, `ImageInput`, `ButtonInput`, `SubmitInput`, `ResetInput` and `RadioInput` are
exported but **not registered as `ui_element` values** — they only work through
`register_input_class` or a direct `.render()`.

A custom composite renderer's `context` argument (see the `LayoutEngine` sample in "Library
boundary") is a `RenderContext` (top-level export) carrying `form_data`, `schema_defs`,
`error` (the field's own message) and `child_errors` (its nested error tree).

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

**The reverse mistake is just as real and easier to miss**: a numeric `select`/`radio` with
explicit `ui_options={'choices': [...]}` *and* a `ge`/`le` constraint must keep both in sync. If
`choices` ever lists a value outside the `ge`/`le` range (e.g. adding a 4th option to a field still
constrained to `le=3`), that option renders as a normal, selectable, apparently-valid choice —
and then fails validation on submit with a confusing error, since picking it looked completely
legitimate. This isn't hypothetical — it's an easy edit-time drift (add a choice, forget to widen
the range) worth double-checking whenever either one changes.

Similarly, `Literal[...]` fields auto-populate select/radio/multiselect options from the type
itself — only pass ui_options choices for plain str/int fields that aren't already `Literal`.

**A real `enum.Enum`/`StrEnum` field does NOT auto-populate, despite looking like it should —
verified directly, not assumed.** Pydantic's JSON schema for a `Literal[...]` field inlines its
values straight into the field's own schema entry, which is what the auto-population check reads;
for an actual `Enum` class, Pydantic instead emits a `$ref` pointing at a separate `$defs` entry,
and this library does no `$ref` resolution before that same check runs. The result isn't a wrong
label or a plain-text fallback — it's a silently empty `<select>` with an HTML comment
(`<!-- Warning: No options provided for select field '...' -->`) where the options should be,
which is easy to miss in review. Always pass `ui_options={'choices': [e.value for e in MyEnum]}`
explicitly for a real `Enum` field — never rely on it auto-populating the way `Literal` does. If a
field's semantics don't require pinning specific literal string values in the type itself, prefer
`Literal[...]` over `Enum` for this exact reason.

**A second, subtler trap with `Enum` fields**: if `Field(..., title=X)`'s title is set to the
exact same string as the Enum class's own name-derived title (e.g. a class `Size` with
`Field(title='Size', ...)`), Pydantic omits the property-level `title` from the schema entirely as
a redundancy optimization — even with the `choices` fix above. Every widget's label/legend falls
back to a name synthesized from the field's own Python attribute name when `title` is missing
(`field_name.replace('_', ' ').title()`), so this is silently masked whenever that synthesized
text happens to match the real title anyway (a field literally named `size` synthesizes back to
"Size" by coincidence) — verified this genuinely affects `select`'s outer `<label>` too, not just
`checkbox_group`/`radio`'s `<legend>`, once the field's name doesn't coincidentally match (e.g. a
field named `sz` titled `'Size'` renders the label "Sz"). It becomes obviously wrong inside a
`model_list` item specifically, because the name synthesis there uses the item's full indexed
field name, not just the attribute name (field `size` inside list field `items` renders
`<legend>Items[0].Size</legend>`, never coincidentally correct). Fix by passing
`ui_options={'legend': '...'}` (for `checkbox_group`/`radio`) explicitly rather than relying on
`title=` alone — this sidesteps the schema-title question entirely. (`select`/other widgets have
no equivalent `ui_options` override for their outer label — for those, avoid giving an `Enum`
field's `Field(title=...)` the exact same text as its `Enum` class's name instead.)

## Form configuration checklist

- Always pass submit_url and keep it route-matched.
- Set framework explicitly: "bootstrap" (recommended), "material", "plain", or "none". `"plain"`
  and `"none"` both render with no framework CSS classes (bring your own styling); they are two
  separate registered styles today but currently produce equivalent output, so either is fine —
  prefer `"none"` since it's the one already documented elsewhere in this file and in `docs/`. An
  unrecognized framework string silently falls back to this same unstyled rendering rather than
  raising an error, so a typo (e.g. `"boostrap"`) fails silently, not loudly — double check the
  spelling against this list.
- Use layout explicitly for non-default structure: "vertical" (default), "tabbed", "side-by-side",
  "accordion", or "wizard". The last four arrange sub-forms, so they need a form built from nested
  `FormModel` fields (see "Composing complex forms" below).
- Pass form_data on both GET defaults and failed POST validation so fields are sticky.
- Pass errors as the nested error tree `.validate()` returns (see "Data and errors are nested
  JSON" below); `result.render_with_errors()` does this for you.
- Keep one coherent framework/layout strategy per endpoint.
- For first pass implementations, prefer readability over over-customized markup.
- Prefer the synchronous `render_form_html()`/`FormModel.render_form()` inside a sync route
  handler, and the `_async` variant inside an `async def` route — the async variant runs the
  (CPU-bound, synchronous) rendering work in the default executor so it doesn't block the event
  loop, which matters most for larger forms/tables; for a small form the difference is
  negligible either way, so match the variant to whether the route itself is `async def`, not to
  form size.
- By default, `render_form_html()`/`render_form_html_async()` include **no** framework CSS/JS tags
  at all in the returned HTML — the assumption is your own page template already loads Bootstrap/
  Material itself (the pattern every worked example in this document uses: the app's own
  `<html>`/base template provides the CDN `<link>`/`<script>` tags, separately from the form
  fragment this library returns). Pass `include_framework_assets=True` to have the library emit
  those tags itself instead, with `asset_mode="cdn"` (default once enabled — loads from a public
  CDN) or `asset_mode="vendored"` (serves the library's own bundled copy, no third-party request).
  For an air-gapped deployment, a strict CSP blocking third-party origins, or embedding the form's
  HTML completely standalone with no other page assets, pass `self_contained=True` instead — it
  implies `include_framework_assets=True` and inlines the CSS/JS directly into the returned HTML
  (no extra request of any kind, vendored or CDN).
- To serve the vendored assets from your own routes instead, the top-level helpers are
  `read_asset_text("assets/vendor/htmx/htmx.min.js")` (any file under the package's
  `assets/vendor/`), `bootstrap_icons_css_tag(asset_mode=...)` / `bootstrap_icons_css_content()`
  (the icon font used by `icon=`), and `wrap_with_schemaforms_markers(html)` (wraps a fragment
  in `<!--- Start/End Pydantic-SchemaForms -->` comments; `render_form_html()` already does this
  unless `include_html_markers=False`).
- Other render options, all keyword arguments to `render_form_html()`/`render_form()`/
  `validate()`: `include_submit_button=False` (a composite such as `DataTableLayout` renders its
  own buttons), `method=`, `wizard_options=` (see "Composing complex forms"), `debug=True` (adds a
  collapsed panel with the rendered HTML, model source, schema, and errors; also the only mode
  that allows `csrf_mode="field-only"`), `show_timing=True` (prints the render time under the
  form), `enable_logging=True` (logs it), `inject_layout_styles=False` (omit the small layout
  support `<style>`). Any other keyword becomes an attribute on the `<form>` tag; `enctype` is set
  to `multipart/form-data` automatically when the model (or a sub-form) has a `file` field.

## Layout guidance

- Use layout="vertical" for most CRUD and simple forms.
- For long forms (more than about 12 user-facing fields), distinct business sections
  (Account/Profile/Preferences/Security/Billing), or high cognitive load workflows (onboarding,
  account setup, compliance), split the form into one `FormModel` per section, nest them as
  fields of a parent `FormModel`, and render with layout="tabbed" (or "accordion"). Each
  sub-form becomes a tab titled by its field's `title=`, in declaration order.
- Use layout="side-by-side" to show a few short sub-forms as columns (dense admin pages).
- Use layout="wizard" for a linear flow the user should fill in order (signup, onboarding,
  checkout): one step per sub-form, Back/Next, submit on the last step. It is still one `<form>`
  and one POST, so the route is identical to any other layout; do not build per-step routes or
  session state for it. Next checks only the browser's HTML5 constraints for the current step;
  Pydantic validates everything on submit.
- Order groups by declaring fields in the order you want, or with `ui_order=`. Put required
  identity sections first and optional/advanced settings last.
- Use the lower-level layout primitives only when required: `GridLayout`,
  `ResponsiveGridLayout`, `HorizontalLayout`, `VerticalLayout`, `CardLayout`, `TabLayout`,
  `AccordionLayout`, `WizardLayout`, `ModalLayout` (all top-level exports) wrap already-rendered
  HTML fragments; they are not how forms are composed — see `docs/layouts.md`.

## Framework route contract

### FastAPI

- Route supports both GET and POST.
- Pass the request form straight to validation: FormModel.validate(await request.form(), ...).
  Do not convert it with `dict(...)` first: that drops repeated values (multi-selects, checkbox
  groups). See "Lower-boilerplate alternative" below for why `.validate()` is the default, not
  the manual `FormModel(**submitted)` + try/except path.
- Re-render with errors + form_data on failure.
- Return HTMLResponse.

### Flask

- Route supports both GET and POST.
- Pass the request form straight to validation: FormModel.validate(request.form, ...). Do not
  call `request.form.to_dict()` first: that drops repeated values.
- Re-render with errors + form_data on failure.
- Return HTML markup or template response.

### Complete worked example (Flask)

Verified end-to-end (GET renders, invalid POST re-renders with errors, valid POST succeeds — same
three checks as the FastAPI example). A trimmed `EventRegistration` model wired into a sync Flask
route — `FormModel.render_form()`/`.validate()` are already synchronous, so there is no `_async`
variant to reach for here (that's a FastAPI/async-route-only concern, see the "Form configuration
checklist" section above):

```python
from flask import Flask, request

from pydantic_schemaforms import Field, FormModel, html

app = Flask(__name__)


class EventRegistration(FormModel):
    full_name: str = Field(..., min_length=2, max_length=80, title='Full Name', ui_element='text')
    email: str = Field(..., title='Email Address', ui_element='email')  # use EmailStr for real
    # server-side format validation, as the FastAPI example above does (needs email-validator) --
    # plain str here only to keep this second example dependency-free.
    ticket_type: str = Field(
        ...,
        title='Ticket Type',
        ui_element='select',
        ui_options={'choices': ['standard', 'vip', 'student']},
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        result = EventRegistration.validate(
            request.form, submit_url='/register', framework='bootstrap'
        )
        if result.is_valid:
            return html(t'<h1>Thanks, {result.data["full_name"]}!</h1>')
        return result.render_with_errors()  # sync -- no "_async" suffix on the Flask path
    form_html = EventRegistration.render_form(submit_url='/register', framework='bootstrap')
    return f'<html><body>{form_html}</body></html>'
```

The same XSS caution from the FastAPI example applies here identically: `result.data["full_name"]`
is user-submitted text, so it goes through `html(t'...')`, never an f-string, the moment it's
placed into hand-written HTML — Flask's `render_template_string`/Jinja2 auto-escapes by default
if you use a real template instead, but a plain returned string like this one does not.

## Lower-boilerplate alternative: FormModel.validate()

**Prefer `FormModel.validate()` over `FormModel(**submitted)` + manual `try/except
ValidationError` as the default for every route, not just an optional shortcut.** The manual path
means hand-reimplementing this library's own work yourself: decoding the submitted input names
into nested data, and turning Pydantic's `ValidationError.errors()` into the nested error tree
the renderer understands, plus a form-level (non-field) error convention (see "Form-level errors"
below). `.validate()` already does all of that:

    result = MyForm.validate(await request.form(), submit_url="/submit")
    if result.is_valid:
        return success(result.data)
    return result.render_with_errors()  # or await result.render_with_errors_async()

`FormModel.validate(data, submit_url=..., framework=..., layout=...)` wraps the same validation
and returns a `ValidationResult` that remembers `submit_url`/`framework`, so re-rendering on
failure needs no repeated arguments — this matters even more once a route re-renders the same
form in more than one place (e.g. a shared CSRF-failure branch and a validation-failure branch).
Reach for the manual `FormModel(**submitted)` + try/except route only if you specifically need the
raw Pydantic model instance and are prepared to build your own error-rendering path — it is not
the recommended default despite being listed first in some framework quick-reference bullets.

`result.data` is a plain nested `dict`, not a `FormModel` instance. If you need the validated
model object itself (e.g. to pass to an ORM constructor), use `result.instance`, which is set
when `result.is_valid` is `True`.

## FormModel and ValidationResult at a glance

`FormModel` adds to a Pydantic `BaseModel`:

- `Model.render_form(data=None, errors=None, framework="bootstrap", *, submit_url, **render_kwargs)` and `render_form_async(...)` — same as `render_form_html(Model, ...)`; `layout=`, `wizard_options=`, `csrf_mode=` and the rest go in `render_kwargs`.
- `Model.validate(data, *, submit_url=None, framework="bootstrap", **render_kwargs)` — the POST
  path; `render_kwargs` such as `layout=`/`wizard_options=` are remembered for re-rendering.
- `Model.as_api_model()` — the same fields without UI metadata, for JSON endpoints.
- `Model.get_json_schema()` — the JSON schema with the `ui_*` keys kept (what the renderer reads);
  `Model.model_json_schema()` is Pydantic's.
- `Model.get_example_form_data()` — plausible sample values per field, handy for demo pages
  and tests.
- `Model.register_field(name, annotation=..., field=...)` — add a field at runtime (advanced:
  forms whose fields come from configuration).

`validate_form_data(Model, data)` is the function form of `Model.validate(data)` and also
accepts a plain Pydantic `BaseModel` class. `EnhancedFormRenderer(framework=...,
include_framework_assets=..., asset_mode=...)` with `.render_form_from_model(Model, data,
errors, submit_url=..., layout=...)` is the object behind `render_form_html()`; use it to render
several forms through one configured renderer.

`ValidationResult` (from `validate()`): `is_valid`, `data`, `errors`, `error_list()`,
`original_data`, `instance`, `render_with_errors(framework=None, *, submit_url=None, errors=None,
**render_kwargs)` and `render_with_errors_async(...)`.

## Data and errors are nested JSON

`FormModel.validate()` accepts the raw request form (`await request.form()` in FastAPI,
`request.form` in Flask), a list of `(name, value)` pairs, or an already nested dict such as a
JSON API body (`MyForm.validate(await request.json())`). It always returns:

- `result.data`: nested exactly like the model. Sub-forms are dicts, lists of sub-forms are
  lists: `result.data["address"]["city"]`, `result.data["pets"][0]["name"]`. Keys that are not
  fields of the model (CSRF tokens, honeypots) are dropped at every level.
- `result.errors`: nested exactly like `result.data`. A node is either a message string or a
  dict of child errors. A list's errors are a dict keyed by item index (only failing items
  appear; JSON turns the keys into strings), so `result.errors["pets"][1]["name"]` sits where
  `result.data["pets"][1]["name"]` does. A message about a whole list or sub-form (e.g.
  `min_length` on the list) is a plain string, or sits under the reserved key `"_errors"` when
  that container also has child errors. Form-wide messages (e.g. from a `@model_validator`) are
  under the top-level `"_errors"`.
- `result.error_list()`: the same errors as a flat `[{"loc": ["pets", 1, "name"], "msg": ...}]`
  list, for API responses and logging.
- `result.original_data`: the decoded submission before validation, nested like the model and
  including fields that failed — what `render_with_errors()` uses for sticky values, and what to
  hand to a rule-based `FormValidator` (see "Rule-based validation").
- `result.instance`: the validated model object, set only when `result.is_valid`.

`render_form_html(errors=...)` also accepts the older `{"errors": [{"name": "address.city",
"message": "..."}]}` contract and a `SchemaFormValidationError` carrying it; both are converted to
the tree. Prefer the tree in new code.

Read errors defensively, since a node can be a string or a dict:
`result.errors.get("address", {}).get("city")` only works when `address` has child errors.

HTML inputs are named `address.city` and `pets[0].name` on the wire; the library builds and
decodes those names itself. **Never construct or parse those names in app code**, and never call
`parse_nested_form_data()` before `.validate()`: pass the request form straight in.
`DataTableLayout.handle_import_post()` likewise takes the raw request form.

## Two different `errors` shapes — do not conflate them

Two different result types both have an `.errors` attribute with **incompatible shapes** — mixing
them up produces a `TypeError` or silently wrong text, not a clean failure:

- `ValidationResult.errors` (from `FormModel.validate()`, the primary server-side path) is a
  **nested error tree** shaped like the data (see above): a top-level field's message is
  `result.errors.get("email")`, a sub-form field's is `result.errors["address"]["city"]`, plus
  `"_errors"` for form-level errors (see below).
- `ValidationResponse.errors` (from `LiveValidator`/`FieldValidator`, the HTMX live-validation
  path — see that section below) is a **`list[str]`** — zero or more messages for the one field
  that response is about. Access the first message with `result.errors[0]` (as the HTMX worked
  example below does) — indexing a `ValidationResult.errors` value the same way is a bug (it
  would index into a message *string*, not a list of messages).

If you write one shared error-rendering helper meant to serve both paths, branch on which result
type you actually have rather than assuming a shape.

## Form-level (non-field) errors

Some failures aren't about any one field — a CSRF mismatch, a rate limit, a backend outage. Report
these with the reserved `"_errors"` key in the errors passed to `render_form_html()`
(`errors={"_errors": "Session expired, please try again."}`) rather than attaching the message to
an arbitrary field. `"_errors"` is where `.validate()` itself puts form-wide errors (such as a
`@model_validator` failure), and the error summary shows it as "Form: ...".

## Rule-based validation (FormValidator and the rule classes)

`Field()` constraints and `@field_validator`/`@model_validator` are the default and cover most
forms. The rule-based layer exists for three cases: a `FormBuilder` form with no typed model, a
reusable rule set shared between the HTMX live-validation endpoint and the POST route, or a
check that is awkward as a Pydantic validator (a DNS lookup, a cross-field rule you want to
toggle per route). All names are top-level exports.

| Rule | Checks |
|---|---|
| `RequiredRule(message=...)` | Non-empty |
| `MinLengthRule(n)` / `MaxLengthRule(n)` | String length (there is no `LengthRule`) |
| `RegexRule(pattern, message)` | Full-match against a pattern |
| `EmailRule()` | Email format |
| `EmailDeliverabilityRule()` | Format plus a DNS/MX lookup of the domain (`pip install pydantic-schemaforms[email]`); reserved names like `.invalid` fail without a lookup |
| `PhoneRule()` | Phone-number shape |
| `NumericRangeRule(min_value=, max_value=)` | Numeric bounds (keywords are `min_value`/`max_value`, not `min`/`max`) |
| `DateRangeRule(min_date=, max_date=)` | Date bounds; accepts `date` objects or ISO strings |
| `CustomRule(func, message)` | `func(value) -> bool` or `-> (bool, message)` |

```python
from datetime import date

from pydantic_schemaforms import (
    DateRangeRule,
    EmailRule,
    FormValidator,
    NumericRangeRule,
    PhoneRule,
    RequiredRule,
)

rules = FormValidator()
rules.field('phone').add_rule(RequiredRule('Phone is required')).add_rule(PhoneRule())
rules.field('backup_email').add_rule(EmailRule())
rules.field('budget').add_rule(NumericRangeRule(min_value=100, max_value=10000))
rules.field('start_date').add_rule(DateRangeRule(min_date=date(2025, 1, 1)))


def end_after_start(data: dict) -> tuple[bool, dict[str, str]]:
    # Return one message per field (a string, not a list).
    if data.get('end_date') and data.get('end_date') <= data.get('start_date', ''):
        return False, {'end_date': 'End date must be after the start date'}
    return True, {}


rules.add_cross_field_rule(end_after_start)

is_valid, errors = rules.validate({'phone': '123', 'budget': '50'})
# errors == {"phone": ["Please enter a valid phone number"], "budget": ["Must be between 100 and 10000"]}
```

`FieldValidator("email").required().email()` is the fluent equivalent for one field, and
`validator.to_schema()`/`ValidationSchema` bundle validators for `LiveValidator`. Two cross-field
rules come ready-made: `CrossFieldRules.password_confirmation(password_field="password",
confirm_field="confirm_password")` and `CrossFieldRules.date_range_validation(start_field,
end_field)`, each returning a function for `add_cross_field_rule()`. For a reusable rule with
client-side support, subclass `ValidationRule` (implement `rule_name`, `validate(value) ->
(bool, message)` and optionally `get_client_validation()`); `CustomRule` is the shortcut when a
plain function is enough.

To run rules on a submission a `FormModel` also validates, give them `result.original_data` (the
decoded submission, nested like the model) and merge the two error sets; `render_form_html()`
accepts either shape in one tree:

```python
result = ProfileForm.validate(await request.form(), submit_url='/profile')
rules_ok, rule_errors = rules.validate(result.original_data)
if not (result.is_valid and rules_ok):
    html_out = result.render_with_errors(errors={**rule_errors, **result.errors})
```

The example app's `/validation` page shows every rule class, every `Field()` constraint, and
both validator decorators failing on one form.

## CSRF protection

For any form that changes state (login, registration, anything behind auth, anything mutating
data), add CSRF protection instead of skipping it:

- Issue a per-session token on GET, store it server-side (session/cache).
- Pass csrf_mode="required-provider", csrf_token_provider=<token>, and csrf_field_name to
  render_form_html/FormModel.render_form/FormModel.validate.
- **Do not declare a CSRF token field on the `FormModel` itself** — it's injected/rendered by the
  library based on `csrf_mode`/`csrf_token_provider`, the same way `captcha`'s answer field is
  declared but its accompanying token is not (see the Field cookbook's captcha entry). `FormModel`
  uses Pydantic's `extra='ignore'`, so an unexpected token field in submitted data is harmless
  either way, but don't add one as if it were a normal form field.
- On POST, verify the submitted token against the stored one with a constant-time comparison
  before validating form data.
- On mismatch, re-render with a form-level error (`errors={"_errors": "..."}`, see above — not a
  field error) and issue a fresh token; do not proceed to model validation.
- csrf_mode accepts the `CSRFMode` enum (`CSRFMode.OFF`/`FIELD_ONLY`/`REQUIRED_PROVIDER`, a
  top-level export) or its string values: "off" (no token), "field-only" (renders a field but does not require server
  verification — **only allowed when `debug=True`**; passing it explicitly outside `debug=True`
  raises `ValueError`, so never generate `csrf_mode="field-only"` for anything but a throwaway
  local demo route), and "required-provider" (renders + the app must verify it) — default to
  "required-provider" for anything beyond a throwaway demo form.
- Treat this as part of the completion contract for stateful forms, not an optional extra — do
  not skip it just because it wasn't explicitly requested.

## Composing complex forms from multiple FormModels

A complex form is several `FormModel`s nested as fields of a parent `FormModel`. There are no
wrapper or layout classes: a sub-form is an ordinary typed field, and its presentation is one
`layout=` argument.

```python
from pydantic_schemaforms import Field, FormModel, html, render_form_html_async


class Contact(FormModel):
    email: str = Field(..., title='Email', ui_element='email')
    phone: str = Field('', title='Phone', ui_element='tel')


class Address(FormModel):
    street: str = Field(..., title='Street')
    city: str = Field(..., title='City', min_length=2)


class Pet(FormModel):
    name: str = Field(..., title='Pet name', min_length=1)
    age: int = Field(0, title='Age', ge=0)


class ProfileForm(FormModel):
    nickname: str = Field(..., title='Nickname')  # plain field
    contact: Contact = Field(title='Contact details')  # sub-form
    address: Address = Field(title='Home address', ui_collapsible=True)  # sub-form
    pets: list[Pet] = Field(default_factory=list, title='Pets', min_length=1)  # repeating sub-form


@app.get('/profile', response_class=HTMLResponse)
async def profile_get():
    return await render_form_html_async(ProfileForm, layout='tabbed', submit_url='/profile')


@app.post('/profile', response_class=HTMLResponse)
async def profile_post(request: Request):
    result = ProfileForm.validate(await request.form(), submit_url='/profile', layout='tabbed')
    if result.is_valid:
        save_profile(
            result.data
        )  # {"nickname": ..., "contact": {...}, "address": {...}, "pets": [...]}
        return HTMLResponse(html(t'<h1>Saved {result.data["nickname"]}</h1>'))
    return HTMLResponse(await result.render_with_errors_async())
```

- `layout=`: `"vertical"` (default; sub-forms as titled sections), `"tabbed"` (a "General" tab
  for the parent's plain fields, then one tab per sub-form), `"side-by-side"` (columns), or
  `"accordion"` (collapsible panels), or `"wizard"` (one step per group with Back/Next; options
  `wizard_options={"linear": True, "show_progress": True, "back_label": "Back",
  "next_label": "Next"}`). Pass the same `layout=` (and `wizard_options=`) to `.validate()` so
  `render_with_errors()` re-renders identically; it opens the first tab, panel, or step
  containing an error.
- Groups follow field declaration order; `ui_order=n` on a field reorders it. The "General"
  group is always first and is titled by the parent's `model_config = {"title": ...}`, else
  "General".
- Per sub-form options go on its field: `title=`, `ui_help_text=`, `ui_collapsible=True`,
  `ui_collapsed=True` (opens automatically when it holds an error), `ui_order=`, and
  `ui_step_title=` (wizard step label, falls back to `title=`).
- The grouped layouts need sub-forms: `layout="tabbed"` on a form with only plain fields raises
  `ValueError`. Split the form into sub-forms instead of hoping fields get grouped.
- Nest as deep as needed: a sub-form can contain a list of sub-forms whose items contain
  sub-forms. Data and errors keep the same nesting.

## Upgrading to nested forms

Version 26.4.1 removed the older ways of combining forms. Code using them fails with
`FormLayoutRemovedError` (a `TypeError`) at class definition or call time, and the error message
points here. Convert each pattern as follows.

| Removed | Replace with |
|---|---|
| `TabbedLayout`, `VerticalLayout`, `HorizontalLayout` wrapper classes (`form = X` attributes, `_get_layouts()` overrides) | One nested `FormModel` field per wrapped form, plus `layout="tabbed"` / `"vertical"` / `"side-by-side"` on render and validate |
| A parent field like `tabs: MyTabs = Field(default_factory=MyTabs, input_type="layout")` | Delete it; the sub-form fields go directly on the parent |
| `ListLayout(Item, min_items=..., max_items=..., add_button_text=...)` | `items: list[Item] = Field(default_factory=list, min_length=..., max_length=..., ui_add_button_label=...)` |
| `SectionDesign(section_title=..., section_description=..., collapsible=...)` | `Field(title=..., ui_help_text=..., ui_collapsible=True)` on the sub-form field |
| `FormDesign(...)` | Arguments to `render_form_html(...)` / `render_form_page(...)` and the app's own page template |
| `parse_nested_form_data(...)` / `dict(await request.form())` before validating | `Model.validate(await request.form(), ...)` |
| `validate(..., flatten=True)` | Removed. `result.data` is always nested |
| Error keys like `result.errors["pets[0].name"]` or `result.errors["city"]` for a sub-form field | `result.errors["pets"][0]["name"]`, `result.errors["address"]["city"]` |
| `errors={"general": ...}` | `errors={"_errors": ...}` |
| `layout="tabbed"` on a flat form (fields grouped by name keywords) | Split the fields into sub-forms; each sub-form is a tab |
| Several `input_type="layout"` fields that auto-rendered as tabs | Nested sub-form fields plus explicit `layout="tabbed"` |
| `from pydantic_schemaforms.layouts import ...` | `from pydantic_schemaforms import ...` (top-level `VerticalLayout`/`HorizontalLayout` are now the plain flex layout primitives) |

Before:

```python
class ContactTab(VerticalLayout):
    form = Contact


class AddressTab(VerticalLayout):
    form = Address


class ProfileTabs(TabbedLayout):
    contact = ContactTab()
    address = AddressTab()


class ProfileForm(FormModel):
    tabs: ProfileTabs = Field(default_factory=ProfileTabs, input_type='layout')


data = parse_nested_form_data(dict(await request.form()))
result = ProfileForm.validate(data, submit_url='/profile')
city_error = result.errors.get('city')
email = result.data['email']
```

After:

```python
class ProfileForm(FormModel):
    contact: Contact = Field(title='Contact')
    address: Address = Field(title='Address')


html_out = await render_form_html_async(ProfileForm, layout='tabbed', submit_url='/profile')
result = ProfileForm.validate(await request.form(), submit_url='/profile', layout='tabbed')
city_error = result.errors.get('address', {}).get('city')
email = result.data['contact']['email']
```

Data shape changes too: each sub-form's values now arrive under its field name
(`result.data["contact"]["email"]`, not `result.data["email"]`). Update anything that reads
`result.data`, saves it, or pre-fills `form_data`. Prefill with the same nested shape:
`render_form_html(ProfileForm, form_data={"contact": {"email": ...}}, ...)`.

## Repeating sub-forms (model_list)

When a form needs a user-editable list of sub-records (e.g. "add another item"), do not hand-
build add/remove JavaScript. Use the library's model_list support instead:

- Define a nested FormModel for one item, then a field typed list[ItemModel]. It renders as a
  repeating sub-form automatically (`ui_element="model_list"` is optional). The item model class
  is resolved from the list[ItemModel] annotation.
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
- Per-item validation errors (`result.errors["items"][0]["name"]`) render inline on the
  matching item automatically.
- On POST, pass the request form straight to `.validate()`; `result.data["items"]` comes back
  as a list of dicts.

## CSV import to a table (DataTableLayout)

When a form needs to import a CSV file into an editable/reviewable table (not just a single
`file` upload field), do not hand-build the upload UI, per-row validation, or load/submit
branching. Use `DataTableLayout` (a top-level export) instead:

- Subclass `DataTableLayout` with one field per table column. A column declared with
  `FormField(..., input_type=...)` renders as a real editable widget per cell (e.g. a dropdown
  for an `Enum`); a plain field with no `input_type` renders as read-only, escaped text (still
  round-trips correctly on submit via a hidden input per cell — see performance note below).
- Embed it as a layout field on a plain `FormModel`: `Any = Field(default_factory=dict,
  input_type="layout", layout_handler="datatable")`, built via
  `YourImportModel.as_layout_value(rows=..., row_errors=...)`. Pass
  `include_submit_button=False` to `render_form_html_async()` — the rendered field already
  includes its own file input and "Load CSV"/"Submit" buttons when `model_config["csv_upload"]`
  is on (the default).
- Table behaviour is `model_config` on the `DataTableLayout` subclass: `csv_upload` (default
  `True`; `False` drops the file input and Load/Submit buttons for a browse-only table),
  `editable` (default `True`; see the `"reload"` action below), `search` (`True`), `paging`
  (`True`), `page_length` (`10`), `length_menu` (`[10, 25, 50, 100]`), `buttons` (`["csv",
  "copy"]`; `"pdf"` is accepted but raises `NotImplementedError`), `csv_template` (`False`;
  `True` links a downloadable header-only CSV), and `style` (`{"striped", "bordered", "hover",
  "compact"}` booleans). Per-row errors are `dict[int, dict[str, str]]` (row index →
  field → message), the shape `ImportResult.row_errors` and `as_layout_value(row_errors=...)`
  share; `RowError(row_index, errors, raw)` is the per-row record `parse_submitted_rows()`
  returns.
- `as_layout_value()`'s full signature is `as_layout_value(rows=None, row_errors=None, *,
  table_id=None, asset_mode="vendored", include_assets=True, reviewing=False, notice="",
  discard_url=None)`. The keyword-only ones control the built-in review UI specifically: pass
  `reviewing=True` after a "Load CSV" click so the button relabels to "Reload CSV" and an info
  banner explains nothing is saved yet; `notice=` shows a one-off warning banner (e.g. "Choose a
  CSV file first"); `discard_url=` adds a "discard and start over" link. `table_id` only matters
  if you embed more than one `DataTableLayout` field on the same page (each needs a distinct id).
- On POST, call `await YourImportModel.handle_import_post(await request.form(max_fields=...))`
  instead of hand-rolling load-vs-submit branching — it parses/validates, merges rows back into
  their original order (an invalid row keeps its raw values instead of vanishing), and returns
  an `ImportResult` with `action: Literal["load", "submit", "reload"]`. Handle it as: `"load"` —
  preview only, nothing committed, re-render with `reviewing=True`; `"submit"` — a normal
  Load-then-Submit commit; `"reload"` — commit exactly like `"submit"` (this is the action
  `model_config["editable"] = False` tables always return instead of `"submit"`, since there's no
  separate review step for them — see the performance note below). **Branching on only `"load"`
  vs `"submit"` and ignoring `"reload"` means an `editable=False` table's imports silently never
  get committed.**
- `handle_import_post()` is `async def`-only (it awaits the uploaded file's `.read()`), which
  assumes a Starlette/FastAPI-style async `UploadFile`. **It does not work unmodified on Flask**
  (WSGI, sync) — Flask's `request.files['csv_file']` is a sync `FileStorage` whose `.read()` is
  not awaitable. `DataTableLayout` is a FastAPI/Starlette-oriented feature; for a Flask app that
  needs CSV import, either run it under an ASGI adapter or handle the CSV upload/parsing
  yourself with `DataTableLayout.parse_csv_rows(raw_bytes)` (sync, safe to call directly) instead
  of `handle_import_post()`.
- Pass a real `max_fields` to `request.form()` — every cell is its own named form field, so
  field count is rows × columns, not row count; Starlette/FastAPI's default `max_fields=1000`
  rejects a plain 5-column table past ~200 rows.
- Treat a `result.action == "submit"` with zero rows and no errors as "nothing to submit," not
  as a successful save of an empty table — `handle_import_post()` reports what was submitted
  faithfully; deciding whether an empty result is meaningful is the app's job.
- Past roughly 100 rows, editable per-cell widgets (real `<select>`/`<input>` per cell, no
  virtualization) get noticeably slower to render/submit than read-only cells. For larger
  imports, prefer declaring columns without `input_type` (keeps the Load-then-Submit review
  step, just with no cell hand-editable), or `model_config["editable"] = False` for a
  bulk-replace-only table with no review step at all (single "Reload CSV" button that parses
  and commits in one click — see the `"reload"` action above).
- Need a genuinely new composite control instead (not a table)? See "A genuinely new composite
  control" in the Library boundary section above — `DataTableLayout` and `model_list` are both
  built on that same `LayoutEngine` mechanism, not a special case of their own.

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
  fragment with headers from `validation_response_headers(field_name, result.is_valid)` (a
  top-level export).
- Keep the real POST submit route validating with `FormModel.validate()` regardless — live
  validation is UX sugar; it never replaces server-side validation on submit (JS can be disabled
  or bypassed).
- For an email field, add a DNS/MX deliverability check (catches typo'd/non-existent domains, not
  just format) by typing the field `DeliverableEmailStr` instead of `EmailStr` — it's a drop-in
  type, so `LiveValidator.for_model(MyForm)` above picks it up automatically with no extra
  FieldValidator code. Reach for `FieldValidator("email").required().email(check_deliverability=True)`
  instead only if you're building a validator imperatively (FormBuilder, no typed model). Either
  way this needs the optional `email-validator` package (`pip install pydantic-schemaforms[email]`)
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
    validation_response_headers,
)

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
    result = SignupForm.validate(await request.form(), submit_url='/signup')  # the real safety net
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

- One `FormModel` per section, nested as fields of a parent `FormModel` (for example Account,
  Profile, Preferences), with an explicit `layout=` ("tabbed", "accordion", or "side-by-side").
- Section grouping rationale.
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
- No f-string/`.format()` interpolation of submitted or validated user data into HTML anywhere in
  the generated route code — always `html(t'...')` for that (see the flagship worked example).
- Any `DataTableLayout`/`ImportResult.action` handling covers all three values (`"load"`,
  `"submit"`, `"reload"`), not just `"load"`/`"submit"`.
- Every `ui_options` key used appears in "Every widget option" for that widget — an unknown or
  misspelled key is written onto the input as an HTML attribute, never reported.
- Every `ui_element` value used appears in the "Supported ui_element values" table — an unknown
  one silently renders a plain text input.

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
- Do not pass `csrf_mode="field-only"` outside a `debug=True` throwaway route — it raises
  `ValueError` otherwise.
- Do not hand-write add/remove list JavaScript — use ui_element="model_list".
- Do not hand-roll custom date/time formatting (military time, locale-specific shapes) — use
  ui_options date_format/time_format/datetime_format.
- Do not use an f-string/`.format()` to interpolate a submitted or validated field value into
  hand-written HTML — even after `.validate()` succeeds, use `html(t'...')` instead (structural
  XSS protection; see the flagship worked example's notes).
- Do not use `TabbedLayout`, `VerticalLayout`/`HorizontalLayout` wrapper subclasses, `ListLayout`,
  `FormLayoutBase`, `SectionDesign`, or `FormDesign` — they were removed and raise `FormLayoutRemovedError`. Nest
  `FormModel`s as fields and pass `layout=` (see "Upgrading to nested forms").
- Do not call `parse_nested_form_data()`, `dict(await request.form())`, or
  `request.form.to_dict()` before `.validate()`, and do not pass `flatten=` — pass the request
  form itself and read nested `result.data`/`result.errors`.
- Do not build or parse wire-format input names (`"pets[0].name"`, `"address.city"`) in app code.
- Do not index `ValidationResult.errors` (a nested error tree, from `.validate()`) like a list, or
  index `ValidationResponse.errors` (a `list[str]`, from `LiveValidator`/`FieldValidator`) like a
  dict — they are unrelated shapes that happen to share an attribute name.
- Do not hand-build a CSV-import table's upload UI, per-row validation, or load/submit branching —
  use `DataTableLayout`/`handle_import_post()`, and handle all three `ImportResult.action` values
  (`"load"`, `"submit"`, `"reload"` — the last needs the same commit handling as `"submit"`).
- Do not pass `max_rating` to `star_rating` (it takes `max_stars`), `min=`/`max=` to
  `NumericRangeRule` (it takes `min_value=`/`max_value=`), or return a list of messages from a
  cross-field rule (one string per field).
- Do not use the exported `@form_validator` decorator for cross-field checks: nothing in the
  library invokes a method decorated with it, so the check silently never runs. Use Pydantic's
  `@model_validator(mode="after")` on the `FormModel` (its message lands in `"_errors"`), or
  `FormValidator.add_cross_field_rule` for the rule-based layer.
- Do not start new code from the compatibility surfaces that are still exported:
  `ModernFormRenderer`, `FormDefinition`, `FormSection`, `LayoutComposer`, `LayoutFactory`, and
  the `TextField`/`EmailField`/`SelectField`/... shorthands. Declare a `FormModel` with
  `Field(ui_element=...)`; `FormBuilder` is the supported path for forms with no typed model.
- Do not invent a new composite rendering mechanism for a table/wizard/repeating structure — use
  `LayoutEngine.layout_renderer`/`register_layout_renderer` (see "Library boundary" above), the
  same mechanism `DataTableLayout` and `model_list` are themselves built on.

### Copilot conversion prompt starters

- "Convert this Pydantic model into a FormModel + FastAPI form endpoint using pydantic-schemaforms. Keep bootstrap + vertical layout and full validation loop."
- "Convert this JSON schema into a tabbed pydantic-schemaforms FormModel and Flask route. Map every field to ui_element/ui_options, preserve constraints, and include sticky form_data + ValidationError mapping."

## Prompt starter for Copilot Chat

"Implement a [FastAPI/Flask] form route using pydantic-schemaforms. Use FormModel + Field metadata, choose framework and layout explicitly, render via render_form_html with explicit submit_url, validate POST data with the model, map ValidationError to field errors, and preserve posted values in form_data. Treat pydantic_schemaforms as an external dependency — never edit its source or import from its internal submodules, and never hand-write a widget/validator the library already provides."
