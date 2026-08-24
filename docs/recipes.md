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

## Code and structured-data fields (JSON, YAML, TOML, Bash, Python)

A `textarea` field can opt into a "Format" button, Tab-key indentation, and
light syntax highlighting for a specific language — still a plain
`<textarea>` under the hood (not an embedded code-editor component), and
fully functional with JavaScript disabled.

```python
from pydantic_schemaforms import Field, FormModel

class ServiceConfigForm(FormModel):
    name: str = Field(..., ui_element="text")
    config: str = Field(
        "{}",
        title="Config (JSON)",
        ui_element="textarea",
        ui_options={"language": "json", "rows": 10},
    )
```

`language` accepts `"json"`, `"yaml"`, `"toml"`, `"bash"`, or `"python"`.
Three more `ui_options` toggle the pieces independently — all default `True`
and only take effect once `language` is set:

| Option              | Effect when `False`                          |
|---------------------|-----------------------------------------------|
| `code_format`        | Hides the Format button                        |
| `code_highlight`      | Hides the syntax-highlight overlay              |
| `code_tab_indent`      | Tab moves focus instead of inserting indentation |

`indent_size` (default `2`) controls both the indent width used by the
formatter and the textarea's `tab-size`.

**What "Format" actually does per language** — this varies, and the button's
label reflects it:

- **JSON** — real reserialization via the browser's native `JSON.parse`/
  `JSON.stringify`, no extra download.
- **YAML** / **TOML** — real parse-and-reserialize, using `js-yaml` /
  `smol-toml` respectively (vendored, loaded only for fields using that
  language — see `docs/index.md`'s offline-assets notes for the general
  vendoring policy).
- **Bash** / **Python** — whitespace-only cleanup (tabs → spaces, trailing
  whitespace trimmed, extra blank lines collapsed). The button reads "Clean
  up whitespace," not "Format" — there's no small, dependency-free
  JavaScript equivalent to `black`/`shfmt` for real reformatting, so don't
  expect syntax-aware reindentation for these two.

Invalid input on Format (e.g. malformed JSON) never throws — the field gets
a `code-invalid` CSS class plus an inline error message, and the textarea's
content is left untouched until it's edited again.

```python
# All five languages, with highlighting off for the two whitespace-only ones
class ScriptsForm(FormModel):
    settings: str = Field("{}", ui_element="textarea", ui_options={"language": "json"})
    manifest: str = Field("", ui_element="textarea", ui_options={"language": "yaml"})
    pyproject: str = Field("", ui_element="textarea", ui_options={"language": "toml"})
    setup_sh: str = Field(
        "", ui_element="textarea", ui_options={"language": "bash", "code_highlight": False}
    )
    hook_py: str = Field(
        "", ui_element="textarea", ui_options={"language": "python", "code_highlight": False}
    )
```

---

<!-- BEGIN GENERATED: input-type-reference (scripts/generate_input_type_reference.py) -->

## Every input type

Every registered `ui_element`, generated from `examples/input_type_reference.py` (the same data backing the FastAPI demo's `/input-types` page). Run `python scripts/generate_input_type_reference.py` after changing that file to regenerate this section.

### Text Inputs

**`text`** — Single-line free text. The default when no ui_element is given.
```python
name: str = Field(..., ui_element='text', ui_placeholder='Full name')
```

**`textarea`** — Multi-line free text. Add language= for a Format button, Tab-key indentation, and syntax highlighting (json/yaml/toml/bash/python).
```python
bio: str = Field('', ui_element='textarea', ui_options={'rows': 4})
config: str = Field('{}', ui_element='textarea',
                    ui_options={'language': 'json', 'rows': 8})
```

**`email`** — Email input with built-in browser validation and a numeric-friendly mobile keyboard.
```python
email: str = Field(..., ui_element='email', ui_placeholder='you@example.com')
```

**`password`** — Password input; autocomplete defaults to 'new-password' so browsers don't offer to autofill a saved password.
```python
password: str = Field(..., ui_element='password')
```

**`search`** — Search input with a search-oriented mobile keyboard.
```python
query: str = Field('', ui_element='search', ui_placeholder='Search...')
```

**`url`** — URL input with browser validation and a default http(s):// pattern.
```python
website: str = Field('', ui_element='url', ui_placeholder='https://example.com')
```

**`tel`** — Plain telephone input, no formatting applied.
```python
phone: str = Field('', ui_element='tel')
```

**`phone`** (also accepts: `phone_number`) — Telephone input with a live-formatting mask as the user types.
```python
phone: str = Field('', ui_element='phone',
                   ui_options={'phone_format': '(###) ###-####'})
```

**`ssn`** (also accepts: `social_security_number`) — Social Security Number input, formatted 123-45-6789 with a numeric keyboard.
```python
ssn: str = Field('', ui_element='ssn')
```

**`credit_card`** (also accepts: `card`, `cc_number`) — Credit card number input, grouped 1234 5678 9012 3456.
```python
card_number: str = Field('', ui_element='credit_card')
```

**`currency`** (also accepts: `money`) — Currency input with live thousands-separator formatting as the user types.
```python
price: str = Field('', ui_element='currency',
                   ui_options={'currency_symbol': '$'})
```

### Numeric Inputs

**`number`** — Plain HTML number input.
```python
count: int = Field(0, ui_element='number')
```

**`integer`** — Number input constrained to whole numbers (step=1).
```python
quantity: int = Field(1, ui_element='integer')
```

**`decimal`** — Number input with a configurable decimal precision (sets step from it).
```python
price: float = Field(0.0, ui_element='decimal',
                     ui_options={'decimal_places': 2})
```

**`percentage`** — Number input clamped to 0-100 by default.
```python
discount: float = Field(0, ui_element='percentage')
```

**`age`** — Integer input with sensible age bounds (0-150) pre-filled.
```python
age: int = Field(..., ui_element='age')
```

**`quantity`** — Integer input for carts/inventory: min=1, placeholder '1'.
```python
qty: int = Field(1, ui_element='quantity')
```

**`score`** — Number input with a configurable min/max range (default 0-100).
```python
score: float = Field(0, ui_element='score',
                     ui_options={'min_score': 0, 'max_score': 10})
```

**`range`** — Native HTML range slider.
```python
volume: int = Field(50, ui_element='range', ge=0, le=100)
```

**`slider`** — Range slider with min/max value labels shown alongside it.
```python
opacity: int = Field(100, ui_element='slider', ge=0, le=100)
```

**`rating`** (also accepts: `rating_stars`) — Range slider styled to show a 1-N star rating (default max 5).
```python
rating: int = Field(3, ui_element='rating', ui_options={'max_rating': 5})
```

**`temperature`** — Number input with a unit indicator (celsius/fahrenheit).
```python
temp: float = Field(20.0, ui_element='temperature',
                    ui_options={'unit': 'celsius'})
```

### Date/Time Inputs

**`date`** — Native HTML date picker (YYYY-MM-DD).
```python
birth_date: date = Field(..., ui_element='date')
```

**`time`** — Native HTML time picker.
```python
appt_time: time = Field(..., ui_element='time')
```

**`datetime`** (also accepts: `datetime-local`) — Native HTML datetime-local picker.
```python
starts_at: datetime = Field(..., ui_element='datetime')
```

**`month`** — Native HTML month picker (YYYY-MM).
```python
billing_month: str = Field(..., ui_element='month')
```

**`week`** — Native HTML week picker (YYYY-Www).
```python
sprint_week: str = Field(..., ui_element='week')
```

**`birthdate`** — Date input pre-configured with sane birthdate bounds.
```python
dob: date = Field(..., ui_element='birthdate')
```

### Selection Inputs

**`checkbox`** — Single boolean checkbox.
```python
agree: bool = Field(False, ui_element='checkbox', title='I accept the terms')
```

**`toggle`** (also accepts: `toggle_switch`, `checkbox_toggle`) — Single boolean rendered as a modern switch instead of a checkbox.
```python
enabled: bool = Field(True, ui_element='toggle')
```

**`checkbox_group`** — Multiple booleans from one field, rendered as a group of checkboxes.
```python
channels: list[str] = Field(default_factory=list, ui_element='checkbox_group',
                            ui_options={'choices': ['email', 'sms', 'push']})
```

**`radio`** — Single choice from a set of mutually-exclusive options.
```python
size: str = Field('medium', ui_element='radio',
                  ui_options={'choices': ['small', 'medium', 'large']})
```

**`select`** — Native HTML <select> dropdown, single choice.
```python
plan: str = Field('free', ui_element='select',
                  ui_options={'choices': [
                      {'value': 'free', 'label': 'Free'},
                      {'value': 'pro', 'label': 'Pro'},
                  ]})
```

**`multiselect`** — Multi-choice dropdown, enhanced with a searchable chips UI over the real <select multiple>.
```python
tags: list[str] = Field(default_factory=list, ui_element='multiselect',
                        ui_options={'options': [
                            {'value': 'py', 'label': 'Python'},
                            {'value': 'rs', 'label': 'Rust'},
                        ]})
```

**`combobox`** — Text input with a suggestion dropdown (native <datalist>) -- free text is still allowed, unlike select.
```python
city: str = Field('', ui_element='combobox',
                  ui_options={'choices': ['New York', 'London', 'Tokyo']})
```

### Files & Specialized Inputs

**`file`** — File upload input.
```python
files: str = Field(..., ui_element='file',
                   ui_options={'accept': '.pdf,.docx', 'multiple': True})
```

**`color`** — Native HTML color picker.
```python
theme_color: str = Field('#3498db', ui_element='color')
```

**`hidden`** — Hidden input, not shown to the user but submitted with the form.
```python
session_id: str = Field(..., ui_element='hidden')
```

**`tags`** — Chip/tag entry: press Enter or comma to add a tag, Backspace to remove the last one; a hidden input carries the joined value.
```python
keywords: str = Field('', ui_element='tags',
                      ui_help_text='Press Enter or comma to add a tag')
```

**`star_rating`** — Individually clickable stars (contrast with rating, which is a slider).
```python
stars: int = Field(0, ui_element='star_rating', ui_options={'max_rating': 5})
```

**`captcha`** — Simple math-challenge CAPTCHA for spam resistance without a third-party service.
```python
captcha: str = Field('', ui_element='captcha')
```

**`honeypot`** — Invisible trap field for bots -- real users never see or fill it; a filled honeypot means reject the submission.
```python
website_url: str = Field('', ui_element='honeypot')
```

**`csrf`** — Hidden CSRF token field -- typically added by the framework integration, not hand-declared per form.
```python
csrf_token: str = Field(..., ui_element='csrf')
```

<!-- END GENERATED: input-type-reference -->

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

## CSV import to a table (DataTableLayout)

`DataTableLayout` is a `FormModel` whose fields describe table columns
instead of one instance's inputs: fields declared with
`FormField(..., input_type=...)` render as real, editable widgets per cell
(a dropdown for an `Enum`, etc.); plain fields render as read-only,
formatted text. The table is progressively enhanced client-side by a
vendored copy of [DataTables.js](https://datatables.net) (MIT-licensed, no
jQuery required) for search/sort/paging, plus optional `csv`/`copy` export
buttons. Since CSV import is what this class is *for*,
`model_config["csv_upload"]` defaults to `True`: the rendered table already
comes with a file input and "Load CSV"/"Submit" buttons built in — nobody
declares a separate file field or hand-builds that markup.

```python
from enum import Enum
from pydantic_schemaforms.datatable_layout import DataTableLayout
from pydantic_schemaforms.schema_form import Field as FormField

class Color(str, Enum):
    red = "red"
    blue = "blue"
    green = "green"

class ContactImport(DataTableLayout):
    name: str
    address: str
    favorite_color: Color = FormField(Color.red, input_type="select")

    model_config = {"buttons": ["csv", "copy"], "search": True, "csv_template": True}
```

It is **not** rendered on its own — it's embedded as one *layout field* on
a plain `FormModel`, exactly like `TabbedLayout`/any other layout (see
`docs/plugin_hooks.md`), and rendered through the same
`render_form_html_async()` call every other form in this library uses.
That embedding `FormModel` needs nothing but the one field:

```python
from typing import Any
from pydantic_schemaforms import render_form_html_async
from pydantic_schemaforms.schema_form import Field, FormModel

class ContactsPage(FormModel):
    rows: Any = Field(
        default_factory=dict, title="Contacts",
        input_type="layout", layout_handler="datatable",
    )

html = await render_form_html_async(
    ContactsPage,
    form_data={"rows": ContactImport.as_layout_value(rows=current_rows, row_errors=row_errors)},
    submit_url="/contacts/import",
    include_submit_button=False,  # ContactImport renders its own Submit -- see below
)
```

`layout_handler="datatable"` is registered automatically the moment you
import anything from `pydantic_schemaforms.datatable_layout` — no manual
registration step needed. The embedding `FormModel`'s framework
(`bootstrap`/`material`/`none`), `debug`, and `show_timing` all apply to the
table automatically — there's nothing DataTableLayout-specific to configure
for those; they're just `render_form_html_async()`'s own parameters, same
as any other form.

### Why `include_submit_button=False`?

Because `csv_upload` is on, `ContactImport`'s own rendered output already
includes a "Submit" button right below the table — pass
`include_submit_button=False` so the embedding form doesn't *also* render
its own generic one, which would leave two redundant "Submit"-ish controls
on the page. This is safe without a nested `<form>`: a `<button
type="submit">`/`<input type="file">` living inside this field's own slot
still submits/attaches to whatever `<form>` the *embedding* FormModel
opened — only a `<form>` nested inside another `<form>` is silently
dropped by the browser's HTML parser, and DataTableLayout never renders
one of its own (calling `ContactImport.render_form()` directly raises
`NotImplementedError`, inherited from `CompositeLayoutModel` — see
`docs/plugin_hooks.md` if you're building a similar composite of your own).

If you don't want the built-in upload UI at all (e.g. a read-only display
table, or your own custom upload flow), set `"csv_upload": False` in
`model_config` — the embedding form's own default submit button then
becomes "Submit" for the table's own editable cells, exactly like any other
layout field.

### Load, review, then Submit — don't commit a CSV on one click

A single submit button that immediately saves whatever CSV you chose gives
you no chance to catch and fix bad rows (a typo'd address, an invalid
color) before they land in your database. So the built-in UI is **two**
buttons: "Load CSV" parses the chosen file and re-renders the table with
those rows *for review* — validation errors show up highlighted, nothing
is saved yet — and "Submit" saves whatever the table is currently showing.

`handle_import_post()` on the model itself replaces hand-rolled
load-vs-submit branching: it reads which button was clicked, parses
accordingly (`parse_csv_rows()` for "Load", `parse_submitted_rows()` for
"Submit" — the same default a plain fallback submit uses, so nothing is
silently ignored), and returns an `ImportResult` with rows/row_errors
already merged back into their original order (`merge_rows()` — an invalid
row keeps its raw, as-typed values instead of vanishing):

```python
form = await request.form()
result = await ContactImport.handle_import_post(form)

if result.action == "load":
    # Preview only -- nothing committed. Re-render with reviewing=True so
    # "Load CSV" relabels to "Reload CSV" and an info banner explains that.
    return render_page(rows=result.rows, row_errors=result.row_errors, reviewing=True, notice=result.notice)

save_to_database(result.rows)  # only "Submit" (result.action == "submit") ever gets here
if result.has_errors:
    return render_page(rows=result.rows, row_errors=result.row_errors)  # keep reviewing
return show_success_page(result.rows)
```

Every cell renders as its own named `<input>` (read-only columns get a
hidden one too, see below), so a submit's field count is *rows times
columns*, not row count. Starlette/FastAPI's `Request.form()` rejects a
request over its default `max_fields=1000` with a 400 ("Too many fields") —
a plain 5-column table already exceeds that at 200 rows. Size a higher
`max_fields` to your largest expected import: `await
request.form(max_fields=200_000)`.

No server-side "staging" storage is needed to connect Load and Submit: the
rows a CSV load rendered for review are already sitting in the table's own
form fields (both the editable cells and the read-only cells' hidden
inputs — see below), so whatever the browser submits on the *next* click
already reflects any hand-fixes made in between.

Every read-only column also carries forward a hidden input with its
current value, alongside its escaped display text — without that, a real
browser submit would only include genuinely-editable cells' own inputs,
and any read-only *required* field (like `name` above) would vanish from
the submission and fail that row's validation on every save.

`as_layout_value()`'s `reviewing`/`notice`/`discard_url` parameters only
affect the built-in upload UI: `reviewing=True` relabels the button and
shows the info banner described above; `notice=` shows a one-off warning
banner instead (`handle_import_post()` returns one in `result.notice` when
"Load" is clicked with no file chosen); `discard_url=` adds a "discard and
start over" link to the reviewing banner.

### `model_config` keys

Recognized by `DataTableLayout` (any other key is ignored — pydantic does
not reject unknown `model_config` keys at runtime):

| Key | Default | Meaning |
|---|---|---|
| `buttons` | `[]` | Export buttons: `"csv"`, `"copy"`. `"pdf"` is accepted but raises `NotImplementedError` at render time (pdfmake isn't vendored yet). |
| `search` | `True` | Show the DataTables search box. |
| `paging` | `True` | Enable client-side paging. |
| `page_length` | `10` | Default rows per page. Always included as a choice in the "entries per page" dropdown, even if not listed in `length_menu`. |
| `length_menu` | `[10, 25, 50, 100]` | Choices offered in the "entries per page" dropdown. |
| `csv_template` | `False` | Render a "Download CSV template" link above the table, as a `data:` URI built from `ContactImport.csv_template_bytes()` — no server route needed. |
| `csv_upload` | `True` | Render the built-in file input + "Load CSV"/"Submit" buttons described above. Set `False` for a bare table with no upload UI (see above). |
| `editable` | `True` | Whether cells declared with `FormField(..., input_type=...)` actually render as editable widgets. Set `False` to force every cell read-only regardless of its own `input_type` — see below. |
| `style` | see below | Table-appearance flags (dict) — see next section. |

### `editable: False` — a bulk-replace-only table, no in-place edits

Set `model_config["editable"] = False` when the table should only ever be
replaced wholesale by re-uploading a CSV — every cell renders read-only no
matter what `input_type` a column declares, and the built-in UI drops
"Submit" entirely, leaving one "Reload CSV" button that both parses *and*
commits in a single click (`handle_import_post()` returns
`action="reload"`) — there's no separate review-then-Submit step to wait on
when nothing in the table can be hand-corrected anyway:

```python
class ReadOnlyImport(DataTableLayout):
    name: str
    favorite_color: Color = Field(Color.red, input_type="select")  # ignored -- always read-only

    model_config = {"editable": False}
```

```python
result = await ReadOnlyImport.handle_import_post(await request.form())
# result.action is always "reload" here -- treat it the same as "submit":
save_to_database(result.rows)
```

**Performance:** every editable cell (a column declared with `input_type=`,
with `editable` left at its default `True`) renders as a real `<select>`/
`<input>` widget, with no virtualization — row count drives DOM size
directly. Past roughly 100 rows this gets noticeably slower to render,
paginate, and submit than plain read-only cells (escaped text plus a
lightweight hidden input for round-tripping). For imports past that size,
prefer a read-only presentation — either `model_config["editable"] = False`
if a bulk-replace-only flow fits (above), or declare the columns without
`input_type` if you still want the normal Load-then-Submit review step, just
without any cell being hand-editable.

### Table appearance (`style`)

`model_config["style"]` maps to Bootstrap's own `table-*` utility classes.
It's a partial dict — any flag you omit keeps its default, so
`{"striped": True}` alone only changes striping and leaves the rest as-is:

| Style flag | Default | Bootstrap class added |
|---|---|---|
| `striped` | `False` | `table-striped` |
| `bordered` | `False` | `table-bordered` |
| `hover` | `True` | `table-hover` |
| `compact` | `False` | `table-sm` |

```python
model_config = {"style": {"striped": True, "bordered": True, "compact": True}}
```

These are Bootstrap-specific classes: they have no visible effect under
`framework="none"` (a deliberately bare table) and there's no dedicated
Material variant yet — `framework="material"` currently gets the same
Bootstrap-ish classes as `framework="bootstrap"`.

### Performance: large imports

> **Note:** imports over roughly 10,000 rows can feel slow. Rendering
> (not CSV parsing) dominates at that scale — every editable cell (any
> column declared with `FormField(..., input_type=...)`) instantiates and
> renders its own input widget class, so cost scales with
> `rows × editable columns`, not just row count. Representative numbers
> from `tests/test_benchmarks.py` (one editable `select` column out of
> three, plain Bootstrap styling, buttons enabled), measured server-side
> only:
>
> | Rows | `parse_csv_rows` | table render |
> |---|---|---|
> | 10 | ~0.03 ms | ~0.2 ms |
> | 100 | ~0.3 ms | ~1.9 ms |
> | 1,000 | ~4 ms | ~21 ms |
> | 10,000 | ~45 ms | ~220 ms |
>
> That's server render time alone — a 10,000-row table is also several MB
> of HTML, and the *browser* then has to parse that markup, build
> 10,000+ DOM rows, and hand them to DataTables for client-side
> sort/search/paging, which is usually the slower part in practice. Run
> `pytest tests/test_benchmarks.py -k datatable` yourself to reproduce
> these numbers on your own hardware/model shape.
>
> If you regularly expect imports in this range: keep as many columns
> read-only (plain fields, no `FormField(input_type=...)`) as your UI can
> tolerate — read-only cells are a cheap `str()`/escape, not a full widget
> render; and consider validating/importing in a background task instead
> of inline in the request/response cycle for the largest files.

### Complete example: one field, one route

A trimmed copy of `examples/datatable_import_example.py` (which also adds
sample CSV files at 10/100/1,000/10,000 rows for trying the performance
behavior above yourself) — run `python examples/main.py` and open
`/employees/import`. Note how little of this is actually about the
CSV-import mechanics: no file field, no button HTML, no load-vs-submit
branching, no merge logic -- `EmployeeImport` and `handle_import_post()`
own all of that.

```python
from enum import Enum
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import EmailStr

from pydantic_schemaforms import render_form_html_async
from pydantic_schemaforms.datatable_layout import DataTableLayout
from pydantic_schemaforms.schema_form import Field, FormModel

class Department(str, Enum):
    engineering = "engineering"
    sales = "sales"
    support = "support"

class EmployeeImport(DataTableLayout):
    name: str = Field(..., input_type="text")
    email: EmailStr = Field(..., input_type="email")
    department: Department = Field(Department.engineering, input_type="select")

    model_config = {
        "buttons": ["csv", "copy"],
        "search": True,
        "page_length": 25,
        "csv_template": True,
        "style": {"striped": True, "bordered": True},
    }

class EmployeeImportForm(FormModel):
    """One field -- EmployeeImport's own rendered output already includes
    the file input and Load/Submit buttons (csv_upload defaults to True)."""
    employees: Any = Field(
        default_factory=dict, title="Employees",
        input_type="layout", layout_handler="datatable",
    )

# Stand-in for a real database.
_ROWS: list[dict] = []
_ROW_ERRORS: dict[int, dict[str, str]] = {}

router = APIRouter(prefix="/employees")

async def _render_page(style: str, *, rows=None, row_errors=None, reviewing=False, notice="") -> str:
    return await render_form_html_async(
        EmployeeImportForm, framework=style,
        form_data={"employees": EmployeeImport.as_layout_value(
            rows=_ROWS if rows is None else rows,
            row_errors=_ROW_ERRORS if row_errors is None else row_errors,
            reviewing=reviewing, notice=notice, discard_url="/employees/import",
        )},
        submit_url="/employees/import", include_submit_button=False,
    )

@router.get("/import", response_class=HTMLResponse)
async def show_import(style: str = "bootstrap"):
    return await _render_page(style)

@router.post("/import", response_class=HTMLResponse)
async def import_or_save(request: Request, style: str = "bootstrap"):
    global _ROWS, _ROW_ERRORS
    result = await EmployeeImport.handle_import_post(await request.form())

    if result.action == "load":
        return await _render_page(
            style, rows=result.rows, row_errors=result.row_errors,
            reviewing=True, notice=result.notice,
        )

    _ROWS, _ROW_ERRORS = result.rows, result.row_errors
    if result.has_errors:
        return await _render_page(style)  # keep reviewing until it's all valid
    return show_success_page(result.rows)  # your own success page

@router.get("/import/template.csv")
def download_template() -> Response:
    return Response(
        content=EmployeeImport.csv_template_bytes(), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="employees_template.csv"'},
    )
```

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

## Live Validation

"Live validation" means a field is checked server-side the moment the user
blurs it or pauses typing — no page reload, no full form submit. It's built
on three pieces that always work together the same way:

1. **`LiveValidator`** holds a dict of `{field_name: check_function}` and a
   `HTMXValidationConfig` (which triggers fire, how long to debounce, which
   CSS classes to toggle).
2. **HTMX attributes** on the `<input>` (`hx-post`, `hx-trigger`,
   `hx-target`) POST the field's current value to a small endpoint whenever
   a trigger fires, and swap the endpoint's HTML response into a feedback
   element — all without JavaScript you have to write.
3. **A tiny endpoint** (one per app, not one per field — see below) calls
   `validator.validate_field(name, value)` and turns the `ValidationResponse`
   into an HTML fragment.

The end-to-end request cycle: user blurs the field (or pauses typing for
`debounce_ms`) → HTMX POSTs the value → the endpoint calls
`validate_field()` → the response HTML is swapped into `#{field}-feedback`
→ an `HX-Trigger: validationResult` header tells the bundled JS to add
`is-valid`/`is-invalid` to the input and mirror the feedback text into the
input's `title` attribute (a native tooltip — see "Showing *why* it failed"
below). The real POST submit route still calls `FormModel.validate()`
independently; live validation is UX sugar layered on top, not a
replacement — JavaScript can be disabled or bypassed.

### Quickest start: `LiveValidator.for_model()`

For a `FormModel` (or plain `BaseModel`), one call derives a live check for
*every* field straight from the model's own `Field()` constraints and
types — nothing to duplicate, checking as-you-type (debounced) rather than
only on blur:

```python
from pydantic_schemaforms import DeliverableEmailStr, Field, FormModel, LiveValidator
from pydantic_schemaforms.live_validation import validation_response_headers
from fastapi.responses import HTMLResponse

class ContactForm(FormModel):
    name: str = Field(..., min_length=2, title="Full Name")
    email: DeliverableEmailStr = Field(..., title="Email")  # real DNS/MX check, see below

live_validator = LiveValidator.for_model(ContactForm, debounce_ms=600)
VALIDATOR_SCRIPT = live_validator.render_htmx_script()  # embed once per page

@app.post("/validate/{field_name}", response_class=HTMLResponse)
async def validate_field(field_name: str, request: Request):
    raw = await request.form()
    value = str(raw.get(field_name, ""))
    result = live_validator.validate_field(field_name, value)

    feedback = (
        '<span class="text-success">✓ Looks good!</span>'
        if result.is_valid
        else f'<span class="text-danger">{result.errors[0]}</span>'
    )
    return HTMLResponse(feedback, headers=validation_response_headers(field_name, result.is_valid))
```

That single `/validate/{field_name}` route serves every field on the model —
`validate_field()` dispatches by name against whatever was registered, so
adding a field to the model is enough; there's no per-field route to add.
Passing an unregistered name returns `is_valid=True` with a warning rather
than a 404/500, so a stray field on the page never breaks the endpoint.

### Rendering the field: two ways

**A. `render_field_with_live_validation()`** — builds a complete
`<input>` + `<label>` + feedback `<div>`, with the `hx-trigger` string
computed for you from the config (e.g. `"blur, input delay:600ms"`):

```python
field_html = live_validator.render_field_with_live_validation(
    "email", field_type="email", label="Email", value=""
)
```

```html
<script src="/vendor/htmx.min.js"></script>
{{ validator_script | safe }}   {# the string from render_htmx_script() #}

{{ field_html | safe }}
```

**B. `ui_options` on a `Field()`** — when the field is rendered through the
normal `render_form_html_async(MyForm, framework=...)` pipeline (so it gets
Bootstrap/Material/Plain HTML styling, debug panel, timing, etc. — see the
[Bootstrap vs Material Design](#bootstrap-vs-material-design) recipe),
attach the same HTMX attributes directly via `ui_options`; any key that
isn't a recognized layout option (`choices`, `options`, ...) passes through
as a literal HTML attribute on the rendered `<input>`, identically across
every framework:

```python
class ContactForm(FormModel):
    email: DeliverableEmailStr = Field(
        ..., title="Email", ui_element="email",
        ui_options={
            "hx-post": "/validate/email",
            "hx-trigger": "blur, input delay:600ms",
            "hx-target": "#email-feedback",
            "hx-swap": "innerHTML",
            "data-validate-endpoint": "true",
        },
    )
```

You then need one empty `<div id="email-feedback"></div>` somewhere on the
page for the response to swap into — it doesn't have to sit immediately
next to the input (see the tooltip note below).

### Deriving checks from the model vs. hand-built rules

`register_model_validator()` (what `for_model()` calls internally) reads a
model's own `Field()` constraints — `min_length`, `EmailStr`,
`DeliverableEmailStr`'s DNS/MX lookup, any `@field_validator` — so there's
one source of truth. Reach for `FieldValidator` + `register_field_validator()`
instead when the check isn't expressible as a model constraint, or you want
different wording than Pydantic's own error text:

```python
from pydantic_schemaforms import CustomRule, FieldValidator

fv = FieldValidator("username")
fv.min_length(3, message="At least 3 characters")
fv.add_rule(CustomRule(
    lambda v: not v.lower().startswith("admin"),
    message="Usernames can't start with 'admin'",
))
live_validator.register_field_validator(fv)  # overrides the model-derived check for this field only
```

Both live on the same `LiveValidator` instance without conflict — the last
`register_*` call for a given field name wins, so you can call
`for_model(MyForm)` first for the bulk of your fields and then override just
the one or two that need custom logic/messages.

### Live DNS/MX email checks with `DeliverableEmailStr`

`DeliverableEmailStr` (see the [Validation Guide](validation_guide.md#email-dnsmx-deliverability-checks)
for the full writeup) is a drop-in `EmailStr` replacement that performs a
real DNS lookup for the domain's MX records — `for_model()` live-checks it
automatically, no extra registration:

```python
class SignupForm(FormModel):
    email: DeliverableEmailStr = Field(..., title="Email")

live_validator = LiveValidator.for_model(SignupForm, debounce_ms=600)
# /validate/email now rejects typo'd/non-existent domains, not just malformed syntax
```

Because it's a real network call, this check always runs server-side —
there is no way to do a DNS/MX lookup from browser JavaScript. The error
text is `email-validator`'s own specific reason (`"The domain name X does
not exist."`, `"...does not accept email."`, a reserved-TLD message, ...),
so the user sees *why*, not one generic string. 600ms is a reasonable
default debounce for a field that triggers a network call per check; if
your DNS resolution is slow, either raise `debounce_ms` for the whole form:

```python
live_validator = LiveValidator.for_model(SignupForm, debounce_ms=1500)
```

or drop that one field back to blur-only by overriding its rendered
`hx-trigger` directly — `register_field_validator`/`for_model` control which
checks run, not the HTML trigger, which lives on the field's own
`ui_options` (see "Rendering the field" above) or a
`render_field_with_live_validation()` call:

```python
email: DeliverableEmailStr = Field(
    ..., ui_element="email", ui_options={"hx-trigger": "blur", ...},
)
```

### Multiple forms, one validator

`for_model()` accepts more than one model class, so several forms on the
same app (or several fields of a comparison demo) can share a single
validator and a single `/validate/{field_name}` endpoint:

```python
live_validator = LiveValidator.for_model(ContactForm, SignupForm, debounce_ms=600)
```

Field names must be unique across the combined set of models — the
validators dict is keyed by name only, so two different models both using a
field called `email` would collide (the later `for_model`/`register_*` call
wins).

### Tuning triggers and debounce

`HTMXValidationConfig`'s three boolean triggers combine into one
`hx-trigger` attribute; `debounce_ms` only applies to `validate_on_input`:

```python
from pydantic_schemaforms import HTMXValidationConfig, LiveValidator

config = HTMXValidationConfig(
    validate_on_blur=True,     # -> "blur"
    validate_on_input=True,    # -> "input delay:400ms"
    validate_on_change=False,
    debounce_ms=400,
)
live_validator = LiveValidator.for_model(ContactForm, config=config)
# hx-trigger="blur, input delay:400ms"
```

Passing `config=` opts fully out of `for_model()`'s debounced-by-default
config rather than layering on top of it — use it to go back to blur-only
(`HTMXValidationConfig(validate_on_input=False)`) for expensive checks like
DNS lookups, or to disable a trigger entirely.

### Showing *why* it failed

The bundled JS (`render_htmx_script()`) already does two things beyond
toggling `is-valid`/`is-invalid` on the input: it mirrors the swapped
feedback text into the input's `title` attribute, so hovering the field (or
its validity icon, where the framework draws one) shows a native tooltip
with the exact reason — useful when the visible feedback element isn't
immediately next to the input, or the page is narrow. Two things to be
aware of when styling the result yourself:

- **Framework CSS scope**: `is-valid`/`is-invalid` are plain CSS classes
  the JS adds to the raw `<input>`; only Bootstrap's own CSS paints a
  border+icon for them out of the box, and only when the input also has
  Bootstrap's `.form-control` class (i.e. rendered with `framework="bootstrap"`).
  Under Material or Plain HTML rendering, add your own rule if you want a
  visual indicator:

  ```css
  input.is-invalid { border-color: #dc3545; }
  input.is-valid   { border-color: #198754; }
  ```

- **Custom `message=`**: passing a fixed `message` to a rule (e.g.
  `EmailDeliverabilityRule(message="...")`) always shows that text instead
  of the specific reason — useful for consistent tone, at the cost of the
  detail.

### Full runnable examples

Two complete, live demos ship in the example app:

- `GET /live-validation` — a 3-field contact form, `LiveValidator.for_model(ContactForm, debounce_ms=600)`.
- `GET /email-dns-validation` — two email fields side by side, one
  `EmailStr` and one `DeliverableEmailStr`, so you can watch the same
  address pass one and fail the other.

See `examples/fastapi_routes.py` (routes + model definitions) and
`examples/templates/live_validation.html` / `email_dns_validation.html`
(templates) for the full wiring, including the debug panel/timing/style-
switcher/submit handling every other demo in the app has.

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
