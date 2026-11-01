<!-- GENERATED FILE -- do not edit directly. Source: ai/profiles/copilot.md + ai/_shared.md + ai/skills/. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
# Copilot instructions for app teams using pydantic-schemaforms

## Rules for any code that uses pydantic-schemaforms

These apply to every task. Read them before writing code.

1. **Treat the library as a dependency.** Never edit, copy or vendor its source into the app, and
   never import from its submodules (`pydantic_schemaforms.inputs`, `.rendering`, `.templates`,
   `.tstring`, `.validation`, `.live_validation`, ...). Everything app code needs is exported from
   the top level: `from pydantic_schemaforms import FormModel, Field, html, ...`. If a name won't
   import from there, re-check its spelling before looking anywhere else.
2. **A form is a `FormModel`.** It's a Pydantic `BaseModel` subclass, so the model is the form, its
   validation and its data. Ordinary Pydantic is expected: `@field_validator`,
   `@model_validator`, `EmailStr`, `Enum`, `Literal`, `Optional`, `create_model()`.
3. **Use what's built in before writing code.** Formatted inputs (phone, currency, tags, ratings,
   date formats, file upload), repeating sub-forms, layouts, wizards and CSV-import tables are all
   `Field(...)` settings or nested models, not HTML or JavaScript you write.
4. **Constraints validate; `ui_options` only decorates.** `min_length`, `max_length`, `pattern`,
   `ge`, `le`, `gt`, `lt` and `multiple_of` go on `Field()`: they're checked on submit, and most
   also become HTML attributes so the browser checks them first. The same value in `ui_options` is never checked on the server.
5. **Build HTML around user data with `html(t'...')`.** A value that passed `validate()` can still
   contain `<script>`. `html()` takes a Python 3.14 t-string and escapes every interpolated
   value; an f-string or `.format()` doesn't. Output the library rendered (`render_form_html()`,
   `render_with_errors()`) is already safe and can be placed as is.
6. **Mistakes fail silently, so check names.** An unknown `ui_element` renders a plain text box, an
   unknown `ui_options` key becomes an HTML attribute, and a misspelled `framework` falls back
   to another style. None of them raise. The frameworks are `"bootstrap"`, `"material"` and
   `"none"`.
7. **`EmailStr` needs the `email` extra** (`pydantic-schemaforms[email]`) just to define the
   model. Add it to the app's dependencies whenever a form has an email field typed `EmailStr`.

## pydantic-schemaforms

pydantic-schemaforms turns a Pydantic model into a server-rendered HTML form and validates the
submission with the same model. This skill covers building and changing forms in an app.

Related skills, when installed: `schemaforms-create` (a new form from a short description),
`schemaforms-convert` (an existing model, schema or form library to a `FormModel`),
`schemaforms-upgrade` (code using removed APIs) and `schemaforms-document` (document an app's forms).



### What to deliver

For a new or changed form, deliver all of these unless the user asks for less:

1. A `FormModel` with a `title` on every field and constraints on `Field()`.
2. Both routes: GET renders the form, POST validates it.
3. `render_form_html()` (or `render_form_html_async()` in an `async def` route) with
   `submit_url=` matching the route. Pass `framework=` and `layout=` when they aren't the defaults.
4. POST handled with `Model.validate(request_form, ...)` and, on failure,
   `result.render_with_errors()`. Never `Model(**data)` with `try/except ValidationError`.
5. Any HTML built around submitted data uses `html(t'...')`.
6. A sentence on each non-obvious choice (an input type, a layout, a validator).

### The pattern

Every form route looks like this. FastAPI:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, html, render_form_html_async


class SignupForm(FormModel):
    name: str = Field(title='Full name', min_length=2)
    email: str = Field(title='Email', ui_element='email')


app = FastAPI()
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/signup', response_class=HTMLResponse)
async def show_signup():
    return await render_form_html_async(SignupForm, submit_url='/signup', **RENDER_OPTIONS)


@app.post('/signup', response_class=HTMLResponse)
async def submit_signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup', **RENDER_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()

    name = result.data['name']
    return html(t'<p>Thanks for signing up, {name}!</p>')
```

Flask:

```python
from flask import Flask, request

from pydantic_schemaforms import Field, FormModel, html, render_form_html


class SignupForm(FormModel):
    name: str = Field(title='Full name', min_length=2)
    email: str = Field(title='Email', ui_element='email')


app = Flask(__name__)
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/signup')
def show_signup():
    return render_form_html(SignupForm, submit_url='/signup', **RENDER_OPTIONS)


@app.post('/signup')
def submit_signup():
    result = SignupForm.validate(request.form, submit_url='/signup', **RENDER_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()

    name = result.data['name']
    return html(t'<p>Thanks for signing up, {name}!</p>')
```

- **`validate()` takes the raw request form** (`await request.form()`, `request.form`) or a nested
  dict such as a JSON body. Don't convert it first: `dict(...)` and `to_dict()` drop repeated
  values from multi-selects and checkbox groups.
- **Pass the same render options to `validate()`** (`layout=`, `framework=`, `csrf_mode=`, ...).
  `render_with_errors()` reuses them, so the failed form comes back looking the same.
- **`include_framework_assets=True, asset_mode="cdn"`** makes the response a complete styled page.
  In an app whose base template already loads Bootstrap, drop both and put the form string into
  the template (`{{ form_html | safe }}` in Jinja).
- **`result.data`** is a plain dict nested like the model. `result.instance` is the validated
  model object. `result.errors` is nested the same way: `{"email": "..."}`,
  `{"address": {"city": "..."}}`, `{"pets": {1: {"name": "..."}}}`, plus `"_errors"` for
  form-wide messages.

### Choosing inputs

Without `ui_element`, the input comes from the field's type:

| Type | Input |
|---|---|
| `str` | text box |
| `int`, `float` | number box (`float` accepts decimals) |
| `bool` | checkbox |
| `Literal[True]` | checkbox that must be ticked ("I accept the terms"); `unchecked_message=` sets its error |
| `date`, `datetime`, `time` | date, date-and-time, time picker |
| `EmailStr`, `AnyUrl` | email box, URL box |
| `Enum`, `Literal[...]` | dropdown of the values; `list[...]` of either is a multi-select |
| `X \| None` | the same input, optional; an optional dropdown gets an empty first choice |
| another `FormModel` | a sub-form |
| `list[FormModel]` | a repeating sub-form with Add and Remove buttons |

Set `ui_element=` for anything else, for example `"textarea"`, `"password"`, `"radio"`,
`"toggle"`, `"tags"`, `"currency"`, `"phone"`, `"file"`, `"rating"`, `"color"`. The complete list,
with every `ui_options` key, is in the inputs reference (see "Inputs reference" below). Check it before
using a value: an unknown one silently renders a text box.

Field settings used most:

| `Field(...)` argument | Effect |
|---|---|
| `title="Full name"` | The label; without it, the field name is used |
| `description="..."` | Help text under the input |
| `ui_placeholder="..."` | Placeholder text |
| `ui_autofocus=True` | Cursor starts here |
| `ui_options={...}` | Settings for the chosen input (`rows`, `choices`, `language`, ...) |
| a default value | The value a fresh form starts with; a field without one is required |

### Validation

- **Field rules:** Pydantic constraints on `Field()` (`min_length`, `ge`, `pattern`, ...) and the
  type itself (`EmailStr`, `date`, `Enum`).
- **Your own checks:** `@field_validator` for one field (its message goes under that field),
  `@model_validator(mode="after")` for rules across fields (its message is form-wide, under
  `"_errors"`). Raise `ValueError("message")`; the message is shown as written.
- **Errors your route finds after validation** (a taken username, a wrong password): render again
  with `render_form_html(Model, form_data=submitted, errors={"username": "..."}, ...)`, or
  `errors={"_errors": "..."}` for a message about the whole form.
- Live as-you-type checks, rule classes such as `PhoneRule`, and cross-field rule sets: see
  the validation reference (see "Validation reference" below).

### Pre-filling a form

A fresh form starts from the field defaults. To edit saved data, pass it as `form_data`: dates,
`Enum` members and nested dicts can be passed as they are. Passed data is used as is, so fields
left out are empty, not defaulted.

```python
form_html = render_form_html(
    ProductForm,
    form_data={name: row[name] for name in ProductForm.model_fields},
    submit_url=f'/products/{product_id}/edit',
)
```

### More

| Task | Reference |
|---|---|
| Every input, every `ui_options` key, every `Field()` setting | inputs (see "Inputs reference" below) |
| Sub-forms, optional sub-forms, repeating sub-forms, tabbed/accordion/side-by-side/wizard layouts | complex forms (see "Complex forms reference" below) |
| Rule classes, live HTMX validation, the two error shapes | validation (see "Validation reference" below) |
| CSV import into an editable, validated table | data tables (see "Data tables reference" below) |
| CSRF, captcha, honeypot, file uploads, safe HTML | security (see "Security reference" below) |
| Styling, assets, async rendering, JSON API from the same model, JSON Schema | rendering (see "Rendering reference" below) |
| A custom input or a custom composite control | extending (see "Extending reference" below) |

### Troubleshooting

| Symptom | Cause and fix |
|---|---|
| The form has no styling | The page doesn't load the CSS framework. Load Bootstrap in the page template, or pass `include_framework_assets=True` (with `asset_mode="cdn"` or the default inlined files). |
| A field renders as a plain text box | Misspelled or unsupported `ui_element`, or a type with no inferred input. Check the inputs reference. |
| A failed submit comes back in a different layout or style | `layout=`/`framework=` were passed to `render_form_html()` but not to `validate()`. |
| `layout="tabbed"` raises `ValueError` | The grouped layouts arrange sub-forms. Split the fields into nested `FormModel`s. |
| A validator's message isn't next to the field | `@model_validator` messages are form-wide. Use `@field_validator` to attach it to one field. |
| A limit isn't enforced on the server | It's in `ui_options` instead of on `Field()`. |
| Values are missing from multi-selects or checkbox groups | The request form was converted with `dict()`/`to_dict()` before `validate()`. |
| `ImportError` mentioning `email-validator` | A field is typed `EmailStr`; install `pydantic-schemaforms[email]`. |
| `ImportError` or `FormLayoutRemovedError` naming a replacement | The code uses a removed API; follow the message, or use the `schemaforms-upgrade` skill. |

### Before finishing

- `submit_url` matches the POST route, and both routes exist.
- Every `ui_element` and `ui_options` key used is in the inputs reference.
- Limits are `Field()` constraints, not `ui_options`.
- No import from a `pydantic_schemaforms.` submodule.
- No f-string or `.format()` around submitted values; `html(t'...')` instead.
- State-changing forms behind a login use CSRF protection (see the security reference).
- No hand-written input HTML, add/remove JavaScript or CSV upload handling for something the
  library already renders.

## Complex forms reference

A bigger form is several `FormModel`s nested as fields of a parent `FormModel`. There are no
wrapper or layout classes: a sub-form is an ordinary typed field, and how the groups are shown is
one `layout=` argument.

### Sub-forms and repeating sub-forms

```python
from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)


class Pet(FormModel):
    name: str = Field(title='Name')
    age: int = Field(0, title='Age', ge=0)


class ProfileForm(FormModel):
    nickname: str = Field(title='Nickname')
    address: Address = Field(title='Home address')
    pets: list[Pet] = Field(
        default_factory=list,
        title='Pets',
        max_length=5,
        ui_add_button_label='Add a pet',
        ui_item_title_template='{name}',
    )
```

- **`address: Address`** renders the `Address` fields as a titled section, inputs named
  `address.street`, `address.city`. Its own rules apply as usual, and it can nest further.
- **`pets: list[Pet]`** renders one card per item with Add and Remove buttons. `min_length` and
  `max_length` on the list count items, are checked on submit, and are enforced by the buttons.
  With `min_length=n`, an empty list starts with `n` blank items.
- **Never hand-write add/remove JavaScript**; a `list[FormModel]` field already does it.

| Option on a sub-form field | Effect |
|---|---|
| `title="..."` | Section heading, and the tab, column, panel or step title in grouped layouts |
| `ui_help_text="..."` | Help text under the heading |
| `ui_collapsible=True` | Under `layout="vertical"`, a collapsible section |
| `ui_collapsed=True` | Starts collapsed; opens by itself when it contains an error |
| `ui_order=n` | Position among the groups (lower first) |
| `ui_step_title="..."` | Step title under `layout="wizard"` only |

| Option on a `list[FormModel]` field | Effect |
|---|---|
| `ui_add_button_label="Add a pet"` | Text of the Add button |
| `ui_item_title_template="{name}"` | Each card's title, filled from the item's fields; `{index}` is the 1-based position |
| `ui_collapsible_items=False` | Plain cards instead of collapsible ones |
| `ui_items_expanded=False` | Cards start collapsed |

These are `Field()` arguments, not `ui_options` keys.

### Optional sub-forms

A sub-form typed `Address | None` can be left empty. Its inputs aren't required in the browser,
and when every one of them comes back blank or still at its default, `validate()` returns `None`
for it. Once the user fills in part of it, the whole sub-form is validated. A common use is a
billing address that's only needed when it differs:

```python
from typing import Literal, Self

from pydantic import EmailStr, model_validator

from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)
    postal_code: str = Field(title='Postal code', pattern=r'^[A-Za-z0-9 -]{3,10}$')
    country: Literal['US', 'CA', 'GB', 'FR', 'DE'] = Field('US', title='Country')


class CheckoutForm(FormModel):
    email: EmailStr = Field(title='Email for the receipt')
    shipping: Address = Field(title='Shipping address')
    billing_same_as_shipping: bool = Field(True, title='Bill to the shipping address')
    billing: Address | None = Field(None, title='Billing address', ui_collapsed=True)

    @model_validator(mode='after')
    def billing_given(self) -> Self:
        if not self.billing_same_as_shipping and self.billing is None:
            raise ValueError('Enter a billing address, or bill to the shipping address')
        return self

    def billing_address(self) -> Address:
        return self.shipping if self.billing_same_as_shipping else self.billing
```

### Layouts

Pass `layout=` to `render_form_html()` **and** to `validate()`, so a failed submit comes back in
the same layout.

| `layout=` | Result |
|---|---|
| `"vertical"` (default) | The form's own fields, then each sub-form as a titled section |
| `"tabbed"` | One tab for the form's own fields, then one tab per sub-form |
| `"accordion"` | The same groups as collapsible panels, the first open |
| `"side-by-side"` | The same groups as columns in one row |
| `"wizard"` | The same groups as steps with Back and Next |

- The grouped layouts arrange **sub-forms**. On a form with only plain fields they raise
  `ValueError`: split the fields into nested models, one per section.
- The first group holds the parent's own plain fields, titled by
  `model_config = {"title": "..."}` or "General". Each sub-form (or list of sub-forms) is one
  group, in declaration order unless `ui_order` says otherwise.
- After a failed submit, the first tab, panel or step with an error opens.
- Use `tabbed` or `accordion` for long forms with distinct sections (account, profile,
  preferences), `side-by-side` for a few short groups, `wizard` for a flow filled in order
  (signup, onboarding, checkout, applications).

```python
from pydantic_schemaforms import Field, FormModel


class Contact(FormModel):
    email: str = Field(title='Email', ui_element='email')
    phone: str = Field('', title='Phone', ui_element='tel')


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City')


class Preferences(FormModel):
    newsletter: bool = Field(False, title='Send me the newsletter')
    language: str = Field(
        'en', title='Language', ui_element='select', ui_options={'choices': ['en', 'fr', 'de']}
    )


class AccountForm(FormModel):
    model_config = {'title': 'About you'}

    name: str = Field(title='Full name')
    contact: Contact = Field(title='Contact details')
    address: Address = Field(title='Address')
    preferences: Preferences = Field(title='Preferences', ui_order=1)
```

### Wizard

```python
from models import AccountForm

from pydantic_schemaforms import render_form_html

form_html = render_form_html(
    AccountForm,
    layout='wizard',
    wizard_options={'next_label': 'Continue', 'linear': True},
    submit_url='/account',
)
```

- **One `<form>`, one POST.** The routes are the same as for any layout. Never build a route per
  step or keep step state in the session.
- **Next checks the current step** with the browser's own validation; the server checks
  everything on submit. The submit button is on the last step. Without JavaScript, all steps show
  stacked.
- `wizard_options`: `linear` (default `True`; `False` lets the progress header jump to any step),
  `show_progress` (`True`), `back_label` (`"Back"`), `next_label` (`"Next"`). An unknown key
  raises `ValueError`. Pass it to `validate()` too.

### Nested data and errors

`result.data` is nested exactly like the model:

```python
{
    'nickname': 'mk',
    'address': {'street': '1 Main', 'city': 'Paris'},
    'pets': [{'name': 'Rex', 'age': 3}],
}
```

`result.errors` is nested the same way, so an error sits at the same path as its value:

```python
{
    'address': {'city': 'String should have at least 2 characters'},
    'pets': {1: {'age': 'Must be 0 or greater'}},
}
```

- A list's errors are keyed by item index; only failing items appear.
- A message about a whole list or sub-form (such as too many items) is a string at its key, or
  under `"_errors"` there when its children also have errors. Form-wide messages are under the
  top-level `"_errors"`.
- A node can be a string or a dict, so read defensively:
  `result.errors.get("address", {}).get("city")` only works when `address` has child errors.
- `result.error_list()` gives a flat `[{"loc": ["pets", 1, "age"], "msg": "..."}]` list for logs
  and API responses.
- Pre-fill nested forms with nested data:
  `form_data={"address": {"city": "Paris"}, "pets": [{"name": "Rex"}]}`.
- Inputs are named `address.city` and `pets[0].name` in the HTML. The library builds and decodes
  those names; **never construct or parse them in app code**, and never decode the form yourself
  before `validate()`.

## Data tables reference

`DataTableLayout` imports a CSV file into an editable, validated table inside a form: file
upload, a review step, per-row errors, search, sorting and paging. Don't hand-build the upload
UI, per-row validation or load/submit branching.

### Complete example (FastAPI)

```python
from enum import Enum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import EmailStr

from pydantic_schemaforms import DataTableLayout, Field, FormModel, html, render_form_html_async


class Department(str, Enum):
    engineering = 'engineering'
    sales = 'sales'
    support = 'support'


class EmployeeImport(DataTableLayout):
    name: str = Field(..., input_type='text')
    email: EmailStr = Field(..., input_type='email')
    department: Department = Field(Department.engineering, input_type='select')

    model_config = {
        'buttons': ['csv', 'copy'],
        'page_length': 25,
        'csv_template': True,
        'style': {'striped': True, 'bordered': True},
    }


class EmployeeImportForm(FormModel):
    employees: Any = Field(
        default_factory=dict,
        title='Employees',
        input_type='layout',
        layout_handler='datatable',
    )


saved_rows: list[dict] = []  # stand-in for a database
app = FastAPI()


async def render_page(*, rows=None, row_errors=None, reviewing=False, notice='') -> str:
    table = EmployeeImport.as_layout_value(
        rows=saved_rows if rows is None else rows,
        row_errors=row_errors,
        reviewing=reviewing,
        notice=notice,
        discard_url='/employees/import',
    )
    return await render_form_html_async(
        EmployeeImportForm,
        form_data={'employees': table},
        submit_url='/employees/import',
        include_submit_button=False,  # the table has its own Submit
        include_framework_assets=True,
        asset_mode='cdn',
    )


@app.get('/employees/import', response_class=HTMLResponse)
async def show_import():
    return await render_page()


@app.post('/employees/import', response_class=HTMLResponse)
async def import_or_save(request: Request):
    result = await EmployeeImport.handle_import_post(await request.form(max_fields=200_000))

    if result.action == 'load':  # a CSV was loaded for review; nothing saved yet
        return await render_page(
            rows=result.rows, row_errors=result.row_errors, reviewing=True, notice=result.notice
        )
    if result.has_errors:  # keep reviewing until every row is valid
        return await render_page(rows=result.rows, row_errors=result.row_errors)

    saved_rows[:] = result.rows
    count = len(result.rows)
    return html(t'<p>Saved {count} rows.</p>')


@app.get('/employees/import/template.csv')
def download_template() -> Response:
    return Response(
        content=EmployeeImport.csv_template_bytes(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="employees_template.csv"'},
    )
```

### Rules

- Subclass `DataTableLayout` with one field per table column. A column declared with
  `Field(..., input_type=...)` renders as a real editable widget per cell (e.g. a dropdown
  for an `Enum`); a plain field with no `input_type` renders as read-only, escaped text (still
  round-trips correctly on submit via a hidden input per cell).
- Embed it as a layout field on a plain `FormModel`: `Any = Field(default_factory=dict,
  input_type="layout", layout_handler="datatable")`, built via
  `YourImportModel.as_layout_value(rows=..., row_errors=...)`. Pass
  `include_submit_button=False` to `render_form_html_async()` — the rendered field already
  includes its own file input and "Load CSV"/"Submit" buttons when `model_config["csv_upload"]`
  is on (the default).
- Table behaviour is `model_config` on the `DataTableLayout` subclass: `csv_upload` (default
  `True`; `False` drops the file input and Load/Submit buttons for a browse-only table),
  `editable` (default `True`; see the `"reload"` action below), `search` (`True`), `paging`
  (`True`), `page_length` (`10`), `length_menu` (`[10, 25, 50, 100]`), `buttons` (`[]`;
  `"csv"` and `"copy"` add export buttons, `"pdf"` is accepted but raises `NotImplementedError`), `csv_template` (`False`;
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
  CSV file first"); `discard_url=` adds a "discard and start over" link. `table_id` defaults to
  one derived from the embedding field's name, so you rarely need it.
- Several `DataTableLayout` fields can share one page or form: each table's inputs and buttons
  are namespaced by its own field, so loading a CSV into one leaves the others alone. If two of
  them use the *same* row model, pass the embedding field's name to tell them apart:
  `await EmployeeImport.handle_import_post(form, field="joining")` (same `field=` on
  `parse_submitted_rows()`). With one table per row model, leave `field` out.
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
  (WSGI, sync) — Flask's uploaded file is a sync `FileStorage` whose `.read()` is
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

A different kind of composite control (not a table): see the extending reference.

## Extending reference

Reach for these only after checking the inputs reference and the existing composites
(`list[FormModel]` repeating sub-forms, `DataTableLayout`): most "custom" needs are a
`ui_element`, a `ui_options` key or a nested model.

### A custom input

Subclass an existing input and register it once at import time, before the app serves requests.
Subclassing a built-in keeps its escaping, label, help text, error message and accessibility
wiring; override `render()` to adjust attributes and hand off to `super().render()`.

```python
from typing import Any

from pydantic_schemaforms import Field, FormModel, TextInput, register_input_class, render_form_html


class ExtensionInput(TextInput):
    """A phone extension: up to six digits, with a numeric keypad on phones."""

    ui_element = 'extension'

    def render(self, **kwargs: Any) -> str:
        kwargs.setdefault('inputmode', 'numeric')
        kwargs.setdefault('pattern', r'\d{1,6}')
        kwargs.setdefault('maxlength', 6)
        return super().render(**kwargs)


register_input_class(ExtensionInput, aliases=('phone_extension',))


class DirectoryEntry(FormModel):
    name: str = Field(title='Name')
    extension: str = Field('', title='Extension', ui_element='extension')


form_html = render_form_html(DirectoryEntry, submit_url='/directory')
```

- `register_input_class(cls, aliases=(...))` registers it under its `ui_element` and any aliases;
  `register_inputs([...])` registers several; `reset_input_registry()` removes custom ones (tests).
- If `render()` writes its own HTML, build it with `html(t'...')`, never an f-string, and pass
  `aria-*` keyword arguments through to the control. Prefer `FormInput.render_with_label()` over
  writing your own label markup; `build_label()`, `build_help_text()` and
  `build_error_message()` produce markup matching the built-ins.
- Base classes: `BaseInput`, `FormInput`, `NumericInput`, `SelectInputBase`, `FileInputBase`.

### A custom composite control

Something bigger than one input (a board, a matrix, a custom picker) is a layout renderer, the
same mechanism `DataTableLayout` and repeating sub-forms are built on. Don't invent another.

```python
from pydantic_schemaforms import Field, FormModel, LayoutEngine, SafeHTML, html, render_form_html


@LayoutEngine.layout_renderer('step_list', builtin=False)
def render_step_list(field_name, field_schema, value, ui_info, context, engine) -> str:
    items = SafeHTML(''.join(html(t'<li>{step}</li>') for step in (value or [])))
    return html(t'<ol class="step-list" data-field="{field_name}">{items}</ol>')


class OnboardingForm(FormModel):
    steps: list[str] = Field(
        ['Account', 'Billing', 'Review'],
        title='Steps',
        input_type='layout',
        layout_handler='step_list',
    )


form_html = render_form_html(OnboardingForm, submit_url='/onboarding')
```

- The renderer is called with exactly `(field_name, field_schema, value, ui_info, context,
  engine)`. The field's own error is `context.error`; its nested errors are
  `context.child_errors` (a `RenderContext`).
- App code registers with `builtin=False`.
- A renderer that outputs its own file input must pass `requires_multipart=` so the form gets
  `enctype="multipart/form-data"`.
- When the composite's own fields are its structure (table columns, board lanes), subclass
  `CompositeLayoutModel` for that class instead of `FormModel`.
- Build every piece of HTML with `html(t'...')`.

## Inputs reference

Every `ui_element` value, every `ui_options` key and every `Field()` setting. Pass input settings
as `Field(..., ui_element="...", ui_options={...})`.

### Supported ui_element values (authoritative)

This is the complete, current list of valid `ui_element` strings. **Do not invent a value not
on this list.** An unrecognized `ui_element` does not raise an error — it silently falls back to
a plain text input, which is easy to miss in review. If a field's semantics don't match anything
below, use the closest primitive rather than guessing at a plausible-sounding name — see the
extending reference if nothing genuinely fits.

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
date" rows add presentation behavior only (e.g. `percentage` shows a `%` placeholder, `star_rating`
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

### Field cookbook: inputs that need more than a bare ui_element

These are the widgets most likely to tempt an assistant into hand-rolling something the library
already does declaratively. Copy the shape and adjust the values.

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
budget: Decimal = Field(..., ui_element='currency', ui_options={'currency_symbol': '$'})
```

On a `Decimal`, `float` or `int` field, `validate()` strips the currency symbol and thousands
separators the input adds while typing (`$1,234.50` → `Decimal("1234.50")`). On a `str` field
the formatted text is kept as typed.

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

**file upload** (drag-and-drop on by default). Type the field `Any`: the upload arrives as the
framework's own file object (Starlette's `UploadFile`, Werkzeug's `FileStorage`), and `validate()`
passes it through. Check the file yourself (chosen at all, extension, size) and add your message
to the errors. Flask keeps files apart from fields, so combine them before validating:

```python
from typing import Any

document: Any = Field(
    None, title='Document', ui_element='file', ui_options={'accept': '.pdf,.docx'}
)

# FastAPI: form = await request.form(); upload = form.get('document')  (starlette.datastructures.UploadFile)
# Flask:   form = CombinedMultiDict([request.form, request.files])  (werkzeug.datastructures)
```

`render_form_html()` sets `enctype="multipart/form-data"` by itself when a form has a file field.
The browser can't keep a chosen file across a re-render, so after an error the user picks it
again. See the security reference for checking uploads.

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


### Every widget option (`ui_options` keys)

Pass these as `Field(..., ui_options={...})`. Defaults are what you get without the key. The
live demo's widget gallery (https://pydantic-schemaforms.devsetgo.com/gallery) shows every row
of this table.

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

The `segmented`/`button_group` variants ship their own CSS; override the classes
(`radio-item-segmented`, `checkbox-item-button-group`) to restyle them.

### Field-level options (work on every widget)

These are `Field()` keyword arguments, not `ui_options` keys:

| Keyword | Effect |
|---|---|
| `title=` | Label text (also the tab/step/section heading for a sub-form field) |
| `description=` or `ui_help_text=` | Help text under the input |
| `ui_placeholder=` | Placeholder attribute |
| `icon=` | Icon name shown before the label (`"envelope"`, `"person"`, ...), mapped per framework |
| `ui_order=` | Position among the fields/groups; lower first, default is declaration order |
| `unchecked_message=` | The error shown when a required checkbox (`Literal[True]`, or `bool` with no default) is left unticked |
| `ui_content=` | The text of a `ui_element="content"` block or `"consent"` field. Escaped; use `html(t'...')` for links or lists. Add `ui_options={"scrollable": True}` for long text. Declare a block as `intro: None = Field(ui_element="content", ui_content="...")`: it submits nothing and isn't in `result.data`. A consent field is a checkbox, so type it `Literal[True]` when it must be ticked |
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

#### The widget classes behind the strings

Each `ui_element` value maps to an exported input class (`TextInput`, `TextArea`, `SelectInput`,
`RadioGroup`, `CheckboxGroup`, `MultiSelectInput`, `ComboBoxInput`, `DateInput`, `FileInput`,
`ToggleSwitch`, `TagsInput`, `CurrencyInput`, ...). App code names the string on the field and
never instantiates these, with two exceptions: subclassing one for `register_input_class` (see the extending reference), and rendering a lone input outside any model,
`TextInput().render_with_label(name="q", label="Search", framework="bootstrap")`. Inside a
custom widget's `render()`, `build_label(field_name, label, required, icon, framework)`,
`build_help_text(field_name, text)` and `build_error_message(field_name, error)` return the
framework-correct label/help/error markup so it matches the built-ins. `BaseInput`/`FormInput`,
`NumericInput`, `SelectInputBase` and `FileInputBase` are the base classes. `DateRangeInput`,
`TimeRangeInput`, `ImageInput`, `ButtonInput`, `SubmitInput`, `ResetInput` and `RadioInput` are
exported but **not registered as `ui_element` values** — they only work through
`register_input_class` or a direct `.render()`.

A custom composite renderer's `context` argument (see the extending reference) is a `RenderContext` (top-level export) carrying `form_data`, `schema_defs`,
`error` (the field's own message) and `child_errors` (its nested error tree).

## Rendering reference

### `render_form_html()` options

`render_form_html(Model, form_data=None, errors=None, framework="bootstrap", *, submit_url, ...)`
returns the `<form>` with its fields, error summary, submit button and the small scripts its
inputs need. It's a fragment for a page, not a whole page. `render_form_html_async()` takes the
same arguments and renders in a worker thread; use it in `async def` routes.
`Model.render_form(...)` is the same as `render_form_html(Model, ...)`.

| Option | Default | Effect |
|---|---|---|
| `submit_url` | required | The form's `action`; never guessed |
| `form_data` | `None` | Values to show; `None` starts from field defaults |
| `errors` | `None` | Messages shaped like the data; `"_errors"` for the whole form |
| `framework` | `"bootstrap"` | `"bootstrap"`, `"material"` or `"none"` |
| `material_variant` | `None` | `"outlined"` (the default look) or `"filled"`; only with `framework="material"` |
| `layout` | `"vertical"` | See the complex forms reference |
| `wizard_options` | `None` | With `layout="wizard"` |
| `method` | `"POST"` | The form's method |
| `include_submit_button` | `True` | `False` when the form is submitted another way |
| `csrf_mode`, `csrf_token_provider`, `csrf_field_name` | `"off"` | See the security reference |
| `include_framework_assets` | `False` | Add the framework's CSS and JavaScript |
| `asset_mode` | `"vendored"` | With assets: `"vendored"` inlines packaged copies, `"cdn"` links pinned CDN URLs |
| `self_contained` | `False` | Assets inlined, Bootstrap Icons included: no external requests at all |
| `show_timing` / `debug` / `enable_logging` | `False` | Render time under the form / a debug panel / DEBUG log lines |
| `include_html_markers` | `True` | `<!--- Start/End Pydantic-SchemaForms -->` comments around the output |
| `inject_layout_styles` | `True` | The small stylesheet that makes the form fill its container |

Any other keyword becomes an attribute of the `<form>` tag (`id="signup"`,
`**{"hx-post": "/signup"}`). A form with a file input gets `enctype="multipart/form-data"`.

### Styling and assets

- **`framework="bootstrap"`** (default) uses Bootstrap 5 classes; `data-bs-theme="dark"` on an
  ancestor gives its dark mode, and `--sf-*` tokens re-color the library's widgets, tabs, accordion
  and wizard. **`"material"`** is a
  self-contained Material Design 3 style with its own CSS; it needs no external framework.
  `material_variant="filled"` gives filled text fields, `data-md-theme="dark"` on an ancestor
  gives the dark scheme, and overriding `--md-sys-color-*` on `.md-form` re-colors it.
  **`"none"`** is plain semantic HTML with no framework classes.
- By default **no framework CSS is included**: the app's page template is expected to load it.
  `include_framework_assets=True` adds it (inlined by default, or `asset_mode="cdn"`).
- Use the same `framework=` in `validate()`, so the failed form comes back in the same style.
- HTMX (live validation) and IMask are not included by `render_form_html()`. Load them in the
  page, or serve the packaged copies:
  `read_asset_text("assets/vendor/htmx/htmx.min.js")`.

### Putting the form in a page template

`render_form_html()` returns trusted HTML, so mark it safe in the template and nothing else:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sign up</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body>
  <main class="container py-4" style="max-width: 40rem">
    <h1>Sign up</h1>
    {% if name %}
      <div class="alert alert-success">Welcome aboard, {{ name }}!</div>
    {% endif %}
    {{ form_html | safe }}
  </main>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models import SignupForm

from pydantic_schemaforms import render_form_html_async

app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


@app.get('/signup', response_class=HTMLResponse)
async def show_signup(request: Request):
    form_html = await render_form_html_async(SignupForm, submit_url='/signup')
    return templates.TemplateResponse(request, 'signup.html', {'form_html': form_html})


@app.post('/signup', response_class=HTMLResponse)
async def signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup')
    if not result.is_valid:
        form_html = await result.render_with_errors_async()
        return templates.TemplateResponse(
            request, 'signup.html', {'form_html': form_html}, status_code=422
        )
    form_html = await render_form_html_async(SignupForm, submit_url='/signup')
    context = {'form_html': form_html, 'name': result.data['name']}
    return templates.TemplateResponse(request, 'signup.html', context)
```

### One model for an HTML form and a JSON API

```python
from pydantic_schemaforms import Field, FormModel


class ContactForm(FormModel):
    name: str = Field(title='Full name', min_length=2, examples=['Ada Lovelace'], ui_autofocus=True)
    email: str = Field(title='Email', examples=['ada@example.com'], ui_element='email')
    message: str = Field(title='Message', min_length=10, ui_element='textarea')
```

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ContactForm

from pydantic_schemaforms import html, render_form_html_async

ContactSchema = ContactForm.as_api_model()  # same fields and rules, no ui_* settings
app = FastAPI()


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return await render_form_html_async(ContactForm, submit_url='/contact')


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), submit_url='/contact')
    if not result.is_valid:
        return await result.render_with_errors_async()
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')


@app.post('/api/contact', response_model=ContactSchema)
async def api_contact(contact: ContactSchema):
    return contact
```

- `as_api_model()` returns a plain Pydantic model with the same fields and validation but none of
  the form settings, for request bodies and `response_model`. Create it once at import time.
- `validate()` also accepts a parsed JSON body and returns the same nested errors, so a non-FastAPI
  API route can answer with `result.errors` and status 422.
- `get_pydantic_json_schema()` returns standard JSON Schema with sub-forms as `$defs`; Pydantic's
  `model_json_schema()` options pass through (for example
  `ref_template="#/components/schemas/{model}"`). `get_json_schema()` is the renderer's internal
  shape, form settings included.

### Other tools

- `EnhancedFormRenderer(framework=..., include_framework_assets=..., asset_mode=...)` with
  `.render_form_from_model(Model, data, errors, submit_url=..., layout=...)` renders many forms
  with one set of options.
- `GridLayout`, `ResponsiveGridLayout`, `HorizontalLayout`, `VerticalLayout`, `CardLayout`,
  `TabLayout`, `AccordionLayout` and `ModalLayout` arrange **already-rendered HTML** on a page
  (for example two forms side by side). They are not how a form's own fields are grouped; that's
  nested models and `layout=`.

## Security reference

### HTML built around submitted data

The library escapes everything it renders. HTML that app code writes around submitted values
must be escaped too, even after `validate()` succeeded: a valid `str` can be
`<script>alert(1)</script>`.

```python
from pydantic_schemaforms import SafeHTML, html

name = result.data['name']
page = html(t'<p>Thanks, {name}!</p>')  # name is escaped

form = SafeHTML(form_html)  # library output: trusted, not escaped again
page = html(t'<main>{form}</main>')
```

- `html()` takes a t-string (`t"..."`, Python 3.14) and returns a `SafeHTML` (a `str`).
- Never build HTML from user data with an f-string, `.format()` or `+`.
- Wrap only HTML you trust in `SafeHTML(...)`: library output, or your own constant markup.
- In Jinja templates, `{{ form_html | safe }}` for the library's output only; everything else stays
  auto-escaped.

### CSRF

Forms that change something on a site with cookie logins need a CSRF token. The library renders
the hidden field; the app creates the token, keeps it in the session and checks it.

```python
import hmac
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from pydantic_schemaforms import Field, FormModel, html, render_form_html_async


class TransferForm(FormModel):
    to_account: str = Field(title='To account')
    amount: int = Field(title='Amount', ge=1)


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='change-me')  # load from your settings


def issue_csrf_token(request: Request) -> str:
    token = secrets.token_urlsafe(32)
    request.session['csrf_token'] = token
    return token


def csrf_token_is_valid(request: Request, submitted: object) -> bool:
    expected = request.session.get('csrf_token')
    return bool(expected and isinstance(submitted, str)) and hmac.compare_digest(
        expected, submitted
    )


def form_options(request: Request) -> dict:
    return {
        'submit_url': '/transfer',
        'csrf_mode': 'required-provider',
        'csrf_token_provider': issue_csrf_token(request),
        'include_framework_assets': True,
        'asset_mode': 'cdn',
    }


@app.get('/transfer', response_class=HTMLResponse)
async def show_transfer(request: Request):
    return await render_form_html_async(TransferForm, **form_options(request))


@app.post('/transfer', response_class=HTMLResponse)
async def submit_transfer(request: Request):
    form = await request.form()
    if not csrf_token_is_valid(request, form.get('csrf_token')):
        raise HTTPException(status_code=403, detail='Invalid or expired form; reload the page.')

    result = TransferForm.validate(form, **form_options(request))
    if not result.is_valid:
        return await result.render_with_errors_async()

    amount = result.data['amount']
    return html(t'<p>Transferred {amount}.</p>')
```

- `csrf_mode="required-provider"` with `csrf_token_provider=` (the token or a function returning
  it) renders a hidden `csrf_token` field and refuses to render without a token.
  `csrf_field_name=` renames the field.
- Check the token **before** validating, with `hmac.compare_digest`, and answer 403 (or re-render
  with `errors={"_errors": "..."}`) when it doesn't match.
- Pass the same options to `validate()`, so a re-rendered form gets a new token.
- Never declare the token as a model field. `validate()` drops unknown keys.
- `csrf_mode="field-only"` is for debugging and raises `ValueError` unless `debug=True`. Don't
  generate it for real routes.
- Keep the session secret out of code; serve the site over HTTPS.

### Spam protection

- **Honeypot:** `website: str = Field('', ui_element='honeypot')` renders an input people can't
  see. When it comes back filled in, answer as if the submission worked and drop it.
- **Captcha:** a self-hosted arithmetic question. Declare only the answer field; the signed token
  is added for you. Check it in the route before validating:

```python
from pydantic_schemaforms import Field, FormModel, verify_captcha


class SignupForm(FormModel):
    captcha_answer: str = Field('', ui_element='captcha', ui_options={'secret_key': CAPTCHA_SECRET})


# in the POST route:
form = await request.form()
if not verify_captcha(
    token=form.get('captcha_answer_token'),
    answer=form.get('captcha_answer'),
    secret_key=CAPTCHA_SECRET,
):
    ...  # re-render with errors={"captcha_answer": "Wrong answer"}; a new question is generated
```

Load `CAPTCHA_SECRET` from the app's configuration, never a literal in code.

### File uploads

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ALLOWED_TYPES, MAX_BYTES, UploadForm
from starlette.datastructures import UploadFile

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/upload', 'include_framework_assets': True, 'asset_mode': 'cdn'}


def check_upload(upload: object) -> tuple[str | None, bytes]:
    if not isinstance(upload, UploadFile) or not upload.filename:
        return 'Choose a file to upload', b''
    if Path(upload.filename).suffix.lower() not in ALLOWED_TYPES:
        return 'Upload a PDF or Word document', b''
    content = upload.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        return 'The file is larger than 5 MB', b''
    return None, content


@app.get('/upload', response_class=HTMLResponse)
async def show_upload():
    return await render_form_html_async(UploadForm, **FORM_OPTIONS)


@app.post('/upload', response_class=HTMLResponse)
async def upload(request: Request):
    form = await request.form()
    result = UploadForm.validate(form, **FORM_OPTIONS)
    file_error, content = check_upload(form.get('document'))
    if not result.is_valid or file_error:
        errors = {**result.errors, **({'document': file_error} if file_error else {})}
        return await render_form_html_async(
            UploadForm, form_data={'title': form.get('title')}, errors=errors, **FORM_OPTIONS
        )
    size = len(content)
    return html(t'<p>Stored "{result.data["title"]}" ({size} bytes).</p>')
```

- Type the file field `Any`; `validate()` passes the upload object through. In FastAPI it's
  `starlette.datastructures.UploadFile` (not `fastapi.UploadFile`, so `isinstance` against the
  FastAPI class fails). In Flask, validate `CombinedMultiDict([request.form, request.files])`;
  the file is a `FileStorage`, and set `app.config["MAX_CONTENT_LENGTH"]`.
- Check that a file was chosen (`upload.filename`), its extension and its size, reading at most
  one byte more than the limit. `accept` in `ui_options` only filters the file picker.
- Store files outside the web root under names you generate; never show a file name in HTML
  without `html(t'...')`.

### Accessibility

Every built-in input is tested with axe-core against WCAG 2.0–2.2 A and AA: each control has a
label, help and errors are linked with `aria-describedby`, and invalid fields get
`aria-invalid="true"`. Keep it that way:

- Give every field a meaningful `title`; it's the label.
- Don't remove or rewrite the `id`/`aria-*` attributes in rendered HTML.
- The page around the form is the app's job: `<html lang>`, one `<h1>`, `<main>`, contrast.
- Don't call the app WCAG, ADA or Section 508 compliant: the library is tested, not certified.

## Validation reference

Validation comes from the model first: the field types, `Field()` constraints and Pydantic
validators. The rule classes and live HTMX checks below are extras for when the model isn't
enough. All names are imported from the top-level package.

### Constraints and validators on the model

```python
from datetime import date
from typing import Literal

from pydantic import ValidationInfo, field_validator, model_validator

from pydantic_schemaforms import Field, FormModel


class RegistrationForm(FormModel):
    username: str = Field(title='Username', min_length=3, max_length=20, pattern=r'^[a-z0-9_]+$')
    password: str = Field(title='Password', ui_element='password', min_length=8)
    confirm_password: str = Field(title='Confirm password', ui_element='password')
    age: int = Field(title='Age', ge=13, le=120)
    start_date: date = Field(title='Start date')
    end_date: date = Field(title='End date')
    accept_terms: Literal[True] = Field(
        title='I accept the terms',
        unchecked_message='You must accept the terms to register',
    )

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
- A required checkbox ("I accept the terms"): type it `Literal[True]` and pass
  `unchecked_message="..."` to `Field()` for the error shown when it's left unticked. Don't use a
  `@field_validator` on a `bool` with no default: an unticked box sends nothing, so it never runs.

### Rule-based validation

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

### Live validation (HTMX)

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

### Two error shapes

| From | `.errors` is |
|---|---|
| `Model.validate()` → `ValidationResult` | a nested tree shaped like the data: `{"email": "...", "address": {"city": "..."}, "_errors": "..."}` |
| `LiveValidator.validate_field()` / `FieldValidator.validate()` → `ValidationResponse` or tuple | a `list[str]` of messages for one field |
| `FormValidator.validate()` | `{field: [messages]}` |

Don't index one shape as if it were another. `render_with_errors(errors=...)` and
`render_form_html(errors=...)` accept the tree and the `{field: [messages]}` form.

## Convert to pydantic-schemaforms

Turn an existing model, schema or form into a `FormModel` and routes, without losing a field or a
validation rule. The output works the same as before, with the library rendering the form.



### Steps

1. **Inventory the source.** List every field with its type, required/optional, default, choices,
   limits, help text, label and custom validation. Also note where the form is rendered and
   handled (routes, templates, CSRF).
2. **Map each field** with the tables below, in this order of precedence: an explicit hint in the
   source (a widget, a format), then the type, then the field's name, then the plain type.
3. **Carry every rule over** as a `Field()` constraint, a type, or a validator. Never drop one and
   never move one into `ui_options`.
4. **Keep the structure.** Groups or fieldsets become nested `FormModel`s (and a `layout=` if
   they were tabs or steps); repeated groups become `list[ItemForm]`.
5. **Replace the handling code**: render with `render_form_html()`, validate with
   `Model.validate(request_form, ...)`, re-render with `result.render_with_errors()`. Remove the
   old form object, template field loops and error plumbing.
6. **Show a mapping table** in your reply: source field → new field, type, input and rules, plus
   anything that couldn't be carried over exactly.
7. **Test** that the page renders, an invalid POST keeps the values and shows each error under the
   right field, and a valid POST produces the same data as before.

Don't invent fields that aren't in the source. When the source is ambiguous (a sample payload),
keep its structure and say what you assumed.

### From a Pydantic model or dataclass

Don't duplicate an existing Pydantic model: inherit from it, `FormModel` first, and redeclare only
the fields that need form settings.

```python
from pydantic import BaseModel
from pydantic import Field as PydanticField

from pydantic_schemaforms import Field, FormModel, render_form_html


# The app's existing model, used elsewhere (an API, the database layer). Leave it as it is.
class User(BaseModel):
    name: str = PydanticField(min_length=2, title='Name')
    email: str
    bio: str = ''


# FormModel first, then the existing model: every field and constraint is inherited.
# Redeclare only the fields that need form settings.
class UserForm(FormModel, User):
    email: str = Field(title='Email', ui_element='email')
    bio: str = Field('', title='About you', max_length=500, ui_element='textarea')


form_html = render_form_html(UserForm, submit_url='/users/new')
```

A standard-library dataclass has no constraints to inherit: write a `FormModel` with the same
fields, adding constraints the code checks elsewhere.

### From WTForms / Flask-WTF

```python
from datetime import date
from typing import Literal

from pydantic import EmailStr, ValidationInfo, field_validator

from pydantic_schemaforms import Field, FormModel


# Converted from:
#   class SignupForm(FlaskForm):
#       username = StringField('Username', [DataRequired(), Length(min=3, max=25)])
#       email = EmailField('Email', [DataRequired(), Email()])
#       password = PasswordField('Password', [DataRequired(), Length(min=12)])
#       confirm = PasswordField('Repeat password', [EqualTo('password')])
#       plan = SelectField('Plan', choices=[('free', 'Free'), ('pro', 'Pro')])
#       birthday = DateField('Birthday', [Optional()])
#       newsletter = BooleanField('Send me the newsletter')
class SignupForm(FormModel):
    username: str = Field(title='Username', min_length=3, max_length=25)
    email: EmailStr = Field(title='Email')
    password: str = Field(title='Password', ui_element='password', min_length=12)
    confirm: str = Field(title='Repeat password', ui_element='password')
    plan: Literal['free', 'pro'] = Field('free', title='Plan')
    birthday: date | None = Field(None, title='Birthday')
    newsletter: bool = Field(False, title='Send me the newsletter')

    @field_validator('confirm')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value
```

| WTForms | FormModel |
|---|---|
| `StringField` | `str` |
| `TextAreaField` | `str`, `ui_element="textarea"` |
| `PasswordField` | `str`, `ui_element="password"` |
| `EmailField` / `Email()` | `EmailStr` |
| `URLField` / `URL()` | `AnyUrl` |
| `IntegerField`, `DecimalField`, `FloatField` | `int`, `Decimal`, `float` |
| `BooleanField` | `bool` with a `False` default; with `DataRequired()`, `Literal[True]` |
| `SelectField(choices=...)` | `Literal[...]` or an `Enum`; `ui_options={"choices": [{"value": ..., "label": ...}]}` when labels differ from values |
| `RadioField` | the same, `ui_element="radio"` |
| `SelectMultipleField` | `list[Literal[...]]` |
| `DateField`, `DateTimeLocalField`, `TimeField` | `date`, `datetime`, `time` |
| `FileField` / `MultipleFileField` | `Any`, `ui_element="file"`; check the file in the route |
| `HiddenField` | the type, `ui_hidden=True` |
| `FormField(Sub)` | a nested `FormModel` |
| `FieldList(FormField(Item))` | `list[ItemForm]`; `min_entries` → `min_length` |
| `DataRequired()` / `InputRequired()` | no default |
| `Optional()` | `X \| None = None` |
| `Length(min, max)` | `min_length`, `max_length` |
| `NumberRange(min, max)` | `ge`, `le` |
| `Regexp(p)` | `pattern=p` |
| `AnyOf([...])` | `Literal[...]` |
| `EqualTo("password")` | a `@field_validator` comparing with `info.data` |
| `validate_<field>()` | `@field_validator("<field>")` |
| label, `description` | `title`, `description` |

Route changes: `form.validate_on_submit()` → `result = Model.validate(request.form, ...)` and
`result.is_valid`; `form.data` → `result.data`; `form.errors` → `result.errors` (nested);
template field loops → `{{ form_html | safe }}`. Flask-WTF's CSRF → `csrf_mode="required-provider"`
with the token in the session (see the `pydantic-schemaforms` skill's security reference).

### From Django forms

| Django | FormModel |
|---|---|
| `CharField(max_length=n)` | `str`, `max_length=n` |
| `CharField(widget=Textarea)` | `str`, `ui_element="textarea"` |
| `EmailField`, `URLField` | `EmailStr`, `AnyUrl` |
| `IntegerField(min_value, max_value)` | `int`, `ge`, `le` |
| `DecimalField(max_digits, decimal_places)` | `Decimal`, `max_digits`, `decimal_places` |
| `BooleanField(required=False)` | `bool = False` |
| `BooleanField()` (required, so it must be ticked) | `Literal[True]`; `unchecked_message=` for its error |
| `ChoiceField(choices=...)` / `TypedChoiceField` | `Literal[...]` or an `Enum` |
| `MultipleChoiceField` | `list[Literal[...]]` |
| `ModelChoiceField(queryset)` | choices built at runtime: `ui_options={"choices": [...]}` from the query, or `create_model()` |
| `DateField`, `DateTimeField`, `TimeField` | `date`, `datetime`, `time` |
| `FileField`, `ImageField` | `Any`, `ui_element="file"` |
| `required=False` | a default (`None` with `X \| None`) |
| `label`, `help_text`, `initial` | `title`, `description`, the default |
| `clean_<field>()` | `@field_validator("<field>")` |
| `clean()` | `@model_validator(mode="after")` (message goes to `"_errors"`) |
| formsets | `list[ItemForm]` |

A `ModelForm` maps the model's fields the same way, through their form field types. Django's
CSRF middleware still applies; render its token into the page or use `csrf_mode` with Django's
token as `csrf_token_provider`.

### From JSON Schema or a sample JSON payload

| JSON Schema | FormModel |
|---|---|
| `"type": "string"` | `str`; `minLength`/`maxLength`/`pattern` → `min_length`/`max_length`/`pattern` |
| `"format": "email"`, `"uri"`, `"date"`, `"date-time"`, `"time"` | `EmailStr`, `AnyUrl`, `date`, `datetime`, `time` |
| `"type": "integer"` / `"number"` | `int` / `float`; `minimum`/`maximum` → `ge`/`le`; `exclusiveMinimum` → `gt`; `multipleOf` → `multiple_of` |
| `"type": "boolean"` | `bool`; with `"const": true`, `Literal[True]` |
| `"enum": [...]` | `Literal[...]` or an `Enum` |
| `"type": "array"` of enum | `list[Literal[...]]` |
| `"type": "array"` of objects | `list[ItemForm]`; `minItems`/`maxItems` → `min_length`/`max_length` |
| `"type": "object"` / `$ref` | a nested `FormModel` |
| not in `required` | a default, or `X \| None = None` |
| `title`, `description`, `default`, `examples` | the same `Field()` arguments |

From a sample payload, infer types from the values (an ISO date string is a `date`, a list of
objects is a repeating sub-form) and mark every field required unless told otherwise.

### Fields known only at runtime

When the fields come from data (a database table of questions, a config file), build the model
with Pydantic's `create_model` and `__base__=FormModel`. It renders, validates and re-renders like
a declared class:

```python
from pydantic import create_model

from pydantic_schemaforms import Field, FormModel, render_form_html

# Loaded from a database or a config file at runtime
FIELDS = [
    {'name': 'name', 'title': 'Your name', 'ui_element': 'text', 'required': True},
    {'name': 'email', 'title': 'Email', 'ui_element': 'email', 'required': True},
    {'name': 'rating', 'title': 'Rating', 'ui_element': 'rating', 'required': False},
    {'name': 'comments', 'title': 'Comments', 'ui_element': 'textarea', 'required': False},
]


def build_form(fields: list[dict]) -> type[FormModel]:
    return create_model(
        'FeedbackForm',
        __base__=FormModel,
        **{
            spec['name']: (
                str,
                Field(
                    ... if spec['required'] else '',
                    title=spec['title'],
                    ui_element=spec['ui_element'],
                ),
            )
            for spec in fields
        },
    )


FeedbackForm = build_form(FIELDS)
form_html = render_form_html(FeedbackForm, submit_url='/feedback')
```

Build it once (at startup, or cached per definition), not on every request.

### Keeping an API in step

If the same data also has a JSON API, don't keep a second model: `ApiModel = Form.as_api_model()`
gives a plain Pydantic model with the same fields and rules and no form settings, for request
bodies and `response_model`.

## Upgrade pydantic-schemaforms code

Bring an app's form code up to the installed version. Every removed API raises an error naming
its replacement; this skill has the full mapping and the order to do it in.



### Steps

1. **Find the installed version**: `python -c "import importlib.metadata as m; print(m.version('pydantic-schemaforms'))"`.
2. **Find every use of a removed API.** Search the app (not the virtual environment) for the names
   in the tables below, for example:
   `grep -rnE "FormBuilder|create_(login|registration|contact)_form|create_form_from_model|render_form_page|handle_form|FormIntegration|form_validator|TabbedLayout|ListLayout|SectionDesign|FormDesign|FormLayoutBase|flatten=|parse_nested_form_data|pydantic_schemaforms\.(layouts|integration|form_layouts)|ReactJSONSchemaFormAdapter|VueFormulateAdapter|\"general\"" --include=*.py --include=*.html .`
3. **Upgrade one form at a time**: the model, then its routes, then everything that reads its data
   or errors (templates, saving code, tests). Data shapes change with nested forms, so check every
   consumer of `result.data`.
4. **Run the app's tests after each form.** Add a test that renders the form and posts an invalid
   submission if there isn't one.
5. **Report** what changed per form, and anything that behaves differently (for example data now
   nested under a sub-form's name).

### 26.4.4: Material Design 3

`framework="material"` was rebuilt on Material Design 3. Forms keep working with no code change;
only customizations of the Material style need attention. Search the app for `MaterialEmbeddedTheme`,
`materialize`, and CSS or tests that target Material markup.

| Changed | Replace with |
|---|---|
| CSS or tests written against the old Material markup | The new markup; the form keeps its `md-form` class. Color overrides use `--md-sys-color-*` tokens on `form.md-form` |
| `MaterialEmbeddedTheme` | `MaterialTheme` |
| Materialize, and `framework_css_tag()`/`framework_js_tag()` for `"material"` | Nothing: both now return nothing for `"material"`, and the page needs no Materialize |

### 26.4.3: one way to build a form

The builder API, the React and Vue adapters and `@form_validator` are removed. Importing a removed
name raises `ImportError: pydantic_schemaforms.<name> was removed. <what to do instead>`.

| Removed | Replacement |
|---|---|
| `FormBuilder`, `AutoFormBuilder`, `create_form_from_model`, `FormDefinition`, `FormSection`, `ModernFormRenderer` | A `FormModel` class rendered with `render_form_html()`. For fields known only at runtime, `create_model(name, __base__=FormModel, **fields)`. |
| `create_login_form`, `create_registration_form`, `create_contact_form` | Declare the `FormModel` (see the example below, or the `schemaforms-create` skill's catalogue) |
| `render_form_page` | `render_form_html()` inside the app's own page template |
| `FormIntegration`, `handle_form`, `handle_form_async` | `result = Model.validate(request_form, submit_url=...)`, then `result.is_valid`, `result.data`, `result.render_with_errors()` |
| `@form_validator` (it never ran) | `@model_validator(mode="after")` on the model (message under `"_errors"`), or `FormValidator.add_cross_field_rule()` |
| `ReactJSONSchemaFormAdapter`, `VueFormulateAdapter`, `map_ui_element_to_framework`, `convert_validation_rules` | `Model.get_pydantic_json_schema()` for a JSON Schema, `Model.as_api_model()` for a plain Pydantic model |
| `DataTableLayout` inputs named `rows[i].col`, `csv_file`, `datatable_action` | Named under the embedding field: `employees.rows[i].col`, `employees.csv_file`. Only code that reads these keys directly or posts them in tests changes; `handle_import_post()` finds them itself. With two tables on the same row model, pass `field="employees"`. |

Before and after for a builder-made form:

```python
# before
form = create_registration_form(framework='bootstrap')
html_out = form.render(data=submitted, errors=errors)


# after
class RegistrationForm(FormModel):
    username: str = Field(title='Username', min_length=3)
    email: EmailStr = Field(title='Email')
    password: str = Field(title='Password', ui_element='password', min_length=12)
    confirm_password: str = Field(title='Confirm password', ui_element='password')

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value


html_out = render_form_html(RegistrationForm, submit_url='/register')
```

### Upgrading to nested forms

Version 26.4.1 removed the older ways of combining forms. Code using them fails with
`FormLayoutRemovedError` (a `TypeError`) at class definition or call time.

| Removed | Replace with |
|---|---|
| `TabbedLayout`, `VerticalLayout`, `HorizontalLayout` wrapper classes (`form = X` attributes, `_get_layouts()` overrides) | One nested `FormModel` field per wrapped form, plus `layout="tabbed"` / `"vertical"` / `"side-by-side"` on render and validate |
| A parent field like `tabs: MyTabs = Field(default_factory=MyTabs, input_type="layout")` | Delete it; the sub-form fields go directly on the parent |
| `ListLayout(Item, min_items=..., max_items=..., add_button_text=...)` | `items: list[Item] = Field(default_factory=list, min_length=..., max_length=..., ui_add_button_label=...)` |
| `SectionDesign(section_title=..., section_description=..., collapsible=...)` | `Field(title=..., ui_help_text=..., ui_collapsible=True)` on the sub-form field |
| `FormDesign(...)` | Arguments to `render_form_html(...)` and the app's own page template |
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

**Data changes shape:** each sub-form's values arrive under its field name
(`result.data["contact"]["email"]`, not `result.data["email"]`). Update everything that reads
`result.data`, saves it, or pre-fills `form_data`, and pre-fill with the same nested shape:
`form_data={"contact": {"email": ...}}`. Saved records may need a migration or a mapping layer.

### Behaviour changes worth checking after any upgrade

- A fresh form now starts from the field defaults; code that passed defaults in `form_data` by
  hand can drop them.
- Inputs are inferred from more types (`date`, `Enum`, `Literal`, `EmailStr`, `AnyUrl`,
  `Optional`). Hand-built `ui_options={"choices": [...]}` for an `Enum` field can be removed.
- Validator messages are shown without Pydantic's "Value error, " prefix; update tests that
  assert the old text.
- A checkbox that defaults to `True` now validates as `False` when unticked.
- An optional sub-form left blank validates to `None` instead of failing.

### Copilot conversion prompt starters

- "Convert this Pydantic model into a FormModel + FastAPI form endpoint using pydantic-schemaforms. Keep bootstrap + vertical layout and full validation loop."
- "Convert this JSON schema into a tabbed pydantic-schemaforms FormModel and Flask route. Map every field to ui_element/ui_options, preserve constraints, and include sticky form_data + ValidationError mapping."

## Prompt starter for Copilot Chat

"Implement a [FastAPI/Flask] form route using pydantic-schemaforms. Use FormModel + Field metadata, choose framework and layout explicitly, render via render_form_html with explicit submit_url, validate POST data with the model, map ValidationError to field errors, and preserve posted values in form_data. Treat pydantic_schemaforms as an external dependency — never edit its source or import from its internal submodules, and never hand-write a widget/validator the library already provides."
