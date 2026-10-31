# Inputs reference

Every `ui_element` value, every `ui_options` key and every `Field()` setting. Pass input settings
as `Field(..., ui_element="...", ui_options={...})`.

## Supported ui_element values (authoritative)

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

## Field cookbook: inputs that need more than a bare ui_element

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


## Every widget option (`ui_options` keys)

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

## Field-level options (work on every widget)

These are `Field()` keyword arguments, not `ui_options` keys:

| Keyword | Effect |
|---|---|
| `title=` | Label text (also the tab/step/section heading for a sub-form field) |
| `description=` or `ui_help_text=` | Help text under the input |
| `ui_placeholder=` | Placeholder attribute |
| `icon=` | Icon name shown before the label (`"envelope"`, `"person"`, ...), mapped per framework |
| `ui_order=` | Position among the fields/groups; lower first, default is declaration order |
| `unchecked_message=` | The error shown when a required checkbox (`Literal[True]`, or `bool` with no default) is left unticked |
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
