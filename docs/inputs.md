# Inputs (UI Elements)

This page documents the supported ui_element values and gives copy-paste examples.
Each element includes:

- Required: minimum setup to render that element
- Optional: supported field metadata and ui_options values

Where you set these:

- Preferred: `pydantic_schemaforms.Field(..., ui_element="...")`
- Or directly via `json_schema_extra={"ui_element": "..."}`

```python
from pydantic_schemaforms import Field, FormModel


class Example(FormModel):
    email: str = Field(..., ui_element="email")
```

## Common Field Metadata (Optional)

These are available on any element type:

- ui_placeholder
- ui_help_text
- ui_disabled
- ui_readonly
- ui_hidden
- ui_autofocus
- ui_class
- ui_style
- ui_order
- ui_options (widget-specific attributes)

## Pydantic Field Options Are Also Supported

UI metadata is additive. You can use standard Pydantic Field options together with ui_element.

Common Pydantic options you can combine with UI elements:

- title, description, examples
- default, default_factory
- alias
- min_length, max_length, pattern
- gt, ge, lt, le, multiple_of, strict
- validate_default, exclude, frozen
- any additional supported Field kwargs via passthrough

```python
from pydantic_schemaforms import Field, FormModel


class PydanticAndUiExample(FormModel):
    username: str = Field(
        ...,
        title="Username",
        description="Public handle shown on profile",
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_]+$",
        examples=["jane_doe"],
        ui_element="text",
        ui_placeholder="jane_doe",
        ui_options={"autocomplete": "username"},
    )

    age: int = Field(
        18,
        ge=13,
        le=120,
        strict=True,
        validate_default=True,
        ui_element="number",
        ui_options={"step": 1},
    )
```

## Copy-Paste Examples By ui_element

Use this import block for the examples below:

```python
from pydantic_schemaforms import Field, FormModel
```

## Supported `ui_element` values

These map to concrete input components in pydantic_schemaforms.inputs.*.

### Text

- `text` (default)
- `password`
- `email`
- `search`
- `textarea`
- `url`
- `tel`

#### text

Required:

- Field type + ui_element="text"

Optional:

- ui_placeholder
- ui_options: minlength, maxlength, pattern, autocomplete, inputmode

```python
class TextExample(FormModel):
    username: str = Field(
        ...,
        ui_element="text",
        ui_placeholder="jane_doe",
        ui_options={"minlength": 3, "maxlength": 32, "autocomplete": "username"},
    )
```

#### password

Required:

- Field type + ui_element="password"

Optional:

- ui_options: minlength, maxlength, autocomplete (defaults to new-password)

```python
class PasswordExample(FormModel):
    password: str = Field(
        ...,
        ui_element="password",
        ui_placeholder="Enter a strong password",
        ui_options={"minlength": 12, "autocomplete": "new-password"},
    )
```

#### email

Required:

- Field type + ui_element="email"

Optional:

- ui_placeholder
- ui_options: autocomplete, pattern, maxlength

```python
class EmailExample(FormModel):
    email: str = Field(
        ...,
        ui_element="email",
        ui_placeholder="name@company.com",
        ui_options={"autocomplete": "email", "maxlength": 254},
    )
```

#### search

Required:

- Field type + ui_element="search"

Optional:

- ui_placeholder
- ui_options: maxlength, autocomplete

```python
class SearchExample(FormModel):
    q: str = Field(
        ...,
        ui_element="search",
        ui_placeholder="Search products",
        ui_options={"maxlength": 120, "autocomplete": "off"},
    )
```

#### textarea

Required:

- Field type + ui_element="textarea"

Optional:

- ui_placeholder
- ui_options: rows, cols, wrap, resize, minlength, maxlength

```python
class TextAreaExample(FormModel):
    bio: str = Field(
        ...,
        ui_element="textarea",
        ui_placeholder="Tell us about yourself",
        ui_options={"rows": 5, "cols": 60, "wrap": "soft", "resize": "vertical"},
    )
```

#### url

Required:

- Field type + ui_element="url"

Optional:

- ui_placeholder
- ui_options: pattern, autocomplete

```python
class UrlExample(FormModel):
    website: str = Field(
        ...,
        ui_element="url",
        ui_placeholder="https://example.com",
        ui_options={"pattern": r"https?://.+", "autocomplete": "url"},
    )
```

#### tel

Required:

- Field type + ui_element="tel"

Optional:

- ui_placeholder
- ui_options: pattern, autocomplete, maxlength

```python
class TelExample(FormModel):
    phone: str = Field(
        ...,
        ui_element="tel",
        ui_placeholder="+1 555 123 4567",
        ui_options={"autocomplete": "tel", "maxlength": 20},
    )
```

Notes:

- Long string fields may auto-infer to textarea.
- password preserves the value if you supply one (use with care).

### Numbers

- `number`
- `range`
- `percentage`, `decimal`, `integer`, `age`, `quantity`, `score`, `temperature` (see [Specialized numeric elements](#specialized-numeric-elements))
- `rating` (alias: `rating_stars`), `star_rating`, `slider` (see [Rating & sliders](#rating-sliders))

#### number

Required:

- Numeric field type + ui_element="number"

Optional:

- Pydantic constraints: ge, le, gt, lt, multiple_of
- ui_options: min, max, step, inputmode, show_stepper

```python
class NumberExample(FormModel):
    quantity: int = Field(
        ...,
        ge=1,
        le=100,
        ui_element="number",
        ui_options={"step": 1, "inputmode": "numeric"},
    )
```

Set `ui_options={"show_stepper": True}` to render +/- buttons on either side of
the input instead of relying on the browser's native number spinner. The
buttons dispatch real `input`/`change` events, so they work with any other
JS listening on the field. `quantity` (below) turns this on by default.

#### range

Required:

- Numeric field type + ui_element="range"

Optional:

- ui_options: min, max, step, value, show_value

```python
class RangeExample(FormModel):
    satisfaction: int = Field(
        ...,
        ge=0,
        le=10,
        ui_element="range",
        ui_options={"min": 0, "max": 10, "step": 1, "value": 7, "show_value": True},
    )
```

### Specialized numeric elements

These all build on `number` and accept the same `ui_options` (min, max, step,
show_stepper) plus their own defaults/kwargs listed below.

| `ui_element` | Purpose | Extra `ui_options` |
| --- | --- | --- |
| `percentage` | Adds a `%` placeholder, defaults min/max/step to 0-100/0.1 | -- |
| `decimal` | Step derived from `decimal_places` | `decimal_places` (int, default 2) |
| `integer` | Forces step=1, numeric keyboard | -- |
| `age` | Integer with min/max defaulted to 0-150 | -- |
| `quantity` | Integer with min=1 and `show_stepper=True` by default | -- |
| `score` | Free min/max range (defaults 0-100) | `min_score`, `max_score` |
| `temperature` | Unit-aware placeholder/min/max | `unit` ("celsius" \| "fahrenheit" \| "kelvin") |

```python
class SpecializedNumericExample(FormModel):
    discount: float = Field(..., ui_element="percentage")
    price: float = Field(..., ui_element="decimal", ui_options={"decimal_places": 2})
    attendees: int = Field(..., ui_element="integer")
    applicant_age: int = Field(..., ui_element="age")
    cart_quantity: int = Field(1, ui_element="quantity")  # ships the +/- stepper by default
    exam_score: float = Field(..., ui_element="score", ui_options={"min_score": 0, "max_score": 100})
    room_temp: float = Field(..., ui_element="temperature", ui_options={"unit": "fahrenheit"})
```

### Rating & sliders

- `rating` (alias: `rating_stars`): a range slider that also renders a live
  `★★★☆☆`-style text readout. Accepts `ui_options={"max_rating": 5}`
  (defaults to 5). Good for a compact, keyboard/touch-friendly rating input.
- `star_rating`: individually clickable stars (not a slider) -- contrast with
  `rating` above. Accepts `ui_options={"max_stars": 5}` (note the different
  option name from `rating`'s `max_rating`).
- `slider`: `range` with min/max value labels shown below the track.
  Accepts `ui_options={"show_labels": True}` (default) plus the usual
  min/max/step.

```python
class RatingAndSliderExample(FormModel):
    satisfaction: int = Field(3, ui_element="rating", ui_options={"max_rating": 5})
    quality_stars: int = Field(4, ui_element="star_rating", ui_options={"max_stars": 5})
    volume: int = Field(50, ui_element="slider", ui_options={"min": 0, "max": 100, "step": 5})
```

### Selection

- `select`
- `multiselect`
- `checkbox`
- `checkbox_group`
- `radio`
- `toggle` (aliases: `toggle_switch`, `checkbox_toggle`)
- `combobox`

#### select

Required:

- ui_element="select"
- ui_options with choices/options list, or schema enum

Optional:

- ui_options: options, choices, size, class, style, placeholder

```python
class SelectExample(FormModel):
    region: str = Field(
        ...,
        ui_element="select",
        ui_options={
            "options": [
                {"value": "na", "label": "North America"},
                {"value": "eu", "label": "Europe"},
            ],
            "size": 1,
        },
    )
```

`ui_options={"placeholder": "..."}` renders a disabled, empty-value first
option forcing a genuine choice, instead of the browser silently
highlighting the first real option as if it were already picked:

```python
class PlanExample(FormModel):
    plan: str = Field(
        ...,
        title="Plan",
        ui_element="select",
        ui_options={"choices": ["free", "pro", "enterprise"], "placeholder": "Choose a plan..."},
    )
```

The placeholder option is only ever the initially-shown, `selected` one when
nothing has been chosen yet -- once a real value is set (a default, a
previous submission, a validation-error re-render), the placeholder stays in
the list but loses `selected` and remains `disabled`, so it can't be picked
again. Combined with the `required` attribute this library already adds for
required fields, native browser validation blocks submission until a real
option is chosen -- no extra server-side validation needed for
Enum/Literal-backed or `min_length`-constrained fields, since an empty
string already fails those. Works identically on `bootstrap`/`plain`/`none`
and `material` frameworks.

#### multiselect

Required:

- ui_element="multiselect"
- ui_options with choices/options list, or schema enum

Optional:

- ui_options: options, choices, size, enhanced (default True), searchable (default True), search_placeholder

```python
class MultiSelectExample(FormModel):
    tags: list[str] = Field(
        ...,
        ui_element="multiselect",
        ui_options={
            "options": [
                {"value": "backend", "label": "Backend"},
                {"value": "frontend", "label": "Frontend"},
                {"value": "infra", "label": "Infra"},
            ],
            "size": 4,
        },
    )
```

The real `<select multiple>` is always rendered -- it's what the form
actually submits, JS or not. By default (`enhanced=True`) it's layered with a
chips + search UI that reads its option data straight off the `<select>`,
and only hides the native control once the enhanced UI has built
successfully, so a JS load failure never leaves the field invisible. Set
`ui_options={"enhanced": False}` to render the plain native multi-select
instead, or `ui_options={"searchable": False}` to keep the chips UI without
the search box.

#### checkbox

Required:

- bool field type + ui_element="checkbox"

Optional:

- ui_options: value, checked, label

```python
class CheckboxExample(FormModel):
    terms_accepted: bool = Field(
        ...,
        ui_element="checkbox",
        ui_help_text="I agree to the terms and privacy policy",
        ui_options={"value": "1", "checked": False},
    )
```

#### checkbox_group

Required:

- list field type + ui_element="checkbox_group"
- ui_options with choices/options list, or schema enum

Optional:

- ui_options: options, choices, legend, variant ("stacked" default, or "button_group")

```python
class CheckboxGroupExample(FormModel):
    notify_via: list[str] = Field(
        default_factory=list,
        ui_element="checkbox_group",
        ui_options={
            "choices": [
                {"value": "email", "label": "Email"},
                {"value": "sms", "label": "SMS"},
                {"value": "push", "label": "Push"},
            ],
            "legend": "Notify me via",
        },
    )
```

Use this instead of `multiselect` when you want independent on/off
checkboxes laid out directly on the page rather than a dropdown -- both
submit a list of selected values. `variant="button_group"` adds
`checkbox-group-button-group`/`checkbox-item-button-group` modifier classes
for styling the options as an adjacent button row; it's presentation only,
your app's CSS still does the actual visual styling (removing borders
between items, etc.).

#### radio

Required:

- ui_element="radio"
- ui_options with choices/options list, or schema enum

Optional:

- ui_options: options, choices, legend, variant ("stacked" default, or "segmented"), class, style

```python
class RadioExample(FormModel):
    plan: str = Field(
        ...,
        ui_element="radio",
        ui_options={
            "choices": [
                {"value": "free", "label": "Free"},
                {"value": "pro", "label": "Pro"},
            ],
            "legend": "Subscription plan",
        },
    )
```

`variant="segmented"` adds `radio-group-segmented`/`radio-item-segmented`
modifier classes for styling the options as adjacent buttons instead of
stacked radios -- presentation only, same caveat as `checkbox_group`'s
`button_group` variant above.

#### toggle (aliases: toggle_switch, checkbox_toggle)

Required:

- bool field type + ui_element="toggle"

Optional:

- ui_options: label, checked, class

```python
class ToggleExample(FormModel):
    marketing_opt_in: bool = Field(
        ...,
        ui_element="toggle",
        ui_options={"label": "Receive product updates", "checked": True},
    )
```

#### combobox

Required:

- ui_element="combobox"
- ui_options with choices/options list, or schema enum

Optional:

- ui_placeholder
- ui_options: options, choices, filter_mode ("contains" default, or "startswith"), min_chars

```python
class ComboBoxExample(FormModel):
    city: str = Field(
        ...,
        ui_element="combobox",
        ui_placeholder="Select or type a city",
        ui_options={
            "options": [
                {"value": "nyc", "label": "New York"},
                {"value": "ldn", "label": "London"},
                {"value": "tky", "label": "Tokyo"},
            ]
        },
    )
```

Renders a text input backed by a native `<datalist>` (the no-JS fallback)
plus a JS-filtered dropdown listbox with arrow-key navigation and
click-to-select, built from the same option data as the datalist -- nothing
to keep in sync. `filter_mode="startswith"` restricts matches to the
beginning of each option's label instead of matching anywhere in it.

Selection note:

- Provide choices via ui_options={"options": [...]} or ui_options={"choices": [...]}.
- Or use JSON Schema enums (for example Literal[...] or Enum) and options are inferred.

### Date/time

- `date`
- `time`
- `datetime` (alias: `datetime-local`)
- `month`
- `week`
- `birthdate`

#### date

Required:

- date-like field + ui_element="date"

Optional:

- ui_options: min, max, value, date_format

```python
from datetime import date


class DateExample(FormModel):
    start_date: date = Field(
        ...,
        ui_element="date",
        ui_options={"min": date(2026, 1, 1), "max": date(2026, 12, 31)},
    )
```

Set `ui_options={"date_format": "%d/%m/%Y"}` to display and submit the field
in a custom shape using standard `strftime`/`strptime` directives, instead of
the browser's own locale-controlled date picker. This renders as a
live-formatted text input (native `<input type="date">` can't show a custom
display format -- the browser always controls it). Without `date_format`,
the field renders exactly as before. The server still parses and validates
the submitted value; a plain ISO `YYYY-MM-DD` string (e.g. from a JSON API
caller bypassing the HTML form) is still accepted regardless of the
configured display format. `BirthdateInput` (`ui_element="birthdate"`)
inherits `date_format` support the same way.

A custom-format field stays a single visible box (`live_format=True`, the
default). Two independent capabilities layer on top of it:

- **Picker icon button**: for any format built from directives a JS `Date`
  object can supply a value for (`%Y %y %m %d %H %I %M %S %p %B %b %A %a`),
  a small calendar icon button appears inside the field -- clicking it calls
  the browser's native `showPicker()` on a visually-hidden, non-submitting
  companion `<input type="date">` behind the scenes, and selecting a date
  writes it into the visible field already converted to the custom format
  (including AM/PM and month/weekday names, via a hardcoded English name
  table). Only truly exotic directives (`%Z`, `%j`, `%f`, week numbers, ...)
  omit the icon entirely.
- **Live per-character typing mask**: for formats built *entirely* from
  fixed-width numeric directives (`%Y %y %m %d %H %I %M %S`), digits are
  auto-punctuated as the user types. Formats using a variable-width
  directive (`%p`, weekday/month names, ...) don't get this -- there's no
  safe way to live-mask "AM"/"PM" or a month name character by character --
  but the picker icon above still works for them.

#### time

Required:

- time-like field + ui_element="time"

Optional:

- ui_options: min, max, step, value, time_format

```python
from datetime import time


class TimeExample(FormModel):
    start_time: time = Field(
        ...,
        ui_element="time",
        ui_options={"min": time(9, 0), "max": time(18, 0), "step": 900},
    )
```

Set `ui_options={"time_format": "%H:%M"}` for 24-hour ("military") time, or
any other `strftime` shape -- same mechanism as `date_format` above (falls
back to a live-formatted text input with a picker icon button; native
`<input type="time">` can't be forced into a custom display format).
`step` only applies to the native time picker and is not used once a
custom `time_format` is set.

#### datetime (alias: datetime-local)

Required:

- datetime-like field + ui_element="datetime"

Optional:

- ui_options: min, max, value, auto_set_current, with_set_now_button, datetime_format

```python
from datetime import datetime


class DatetimeExample(FormModel):
    appointment_at: datetime = Field(
        ...,
        ui_element="datetime",
        ui_options={"auto_set_current": True, "with_set_now_button": True},
    )
```

Set `ui_options={"datetime_format": "%Y%m%d%H%M%S"}` for an arbitrary custom
shape (e.g. year-month-day-hour(24)-minute-second) -- same mechanism as
`date_format`/`time_format`, including the picker icon button (also
available for `%p`/`%B`/etc., see above). When both `datetime_format` and
`with_set_now_button` are set, the Set Now button writes a value matching
the custom format instead of the default ISO-ish shape, using the same
JS-Date-derivable directive set as the picker icon -- omitted entirely only
for the rarer directives that set omits too (`%Z`, `%j`, `%f`, ...).

> **Known limitation**: the standalone `FieldValidator(...).date_range()`
> rule (as opposed to `ui_options={"min": ..., "max": ...}` above) always
> expects ISO `YYYY-MM-DD` values and is not aware of `date_format`/
> `time_format`/`datetime_format`. Use the `min`/`max` `ui_options` shown
> above for range constraints on a custom-formatted field -- they're
> already format-aware.

See `examples/date_time_formats_example.py` for a live-runnable showcase of
21 date/time/datetime formats (USA, Europe, Asia, military time, and
compact year-month-day-hour-minute-second shapes) across all three input
types, wired up at the `/date-time-formats` route in the FastAPI example app.

#### month

Required:

- date/datetime/string field + ui_element="month"

Optional:

- ui_options: min, max, value (YYYY-MM)

```python
class MonthExample(FormModel):
    billing_month: str = Field(
        ...,
        ui_element="month",
        ui_options={"min": "2026-01", "max": "2026-12", "value": "2026-04"},
    )
```

#### week

Required:

- date/datetime/string field + ui_element="week"

Optional:

- ui_options: value (YYYY-W##)

```python
class WeekExample(FormModel):
    sprint_week: str = Field(
        ...,
        ui_element="week",
        ui_options={"value": "2026-W17"},
    )
```

#### birthdate

Required:

- date-like field + ui_element="birthdate"

Optional:

- ui_options: min, max (defaults to today and 150 years ago), show_age (default True)

```python
from datetime import date


class BirthdateExample(FormModel):
    date_of_birth: date = Field(..., ui_element="birthdate")
```

`show_age` renders a live "You are N years old" readout below the field,
computed client-side and updated as the date changes. Set
`ui_options={"show_age": False}` to render a plain date input with
birthdate-appropriate min/max defaults but no age display.

### Specialized

- `file`
- `color`
- `hidden`
- `ssn` (alias: `social_security_number`)
- `phone` (alias: `phone_number`)
- `credit_card` (aliases: `card`, `cc_number`)
- `currency` (alias: `money`)
- `tags`

#### file

Required:

- string field + ui_element="file"

Optional:

- ui_options: accept, multiple, capture, show_preview, enable_drag_drop (default True)

```python
class FileExample(FormModel):
    attachments: str = Field(
        ...,
        ui_element="file",
        ui_options={
            "accept": ".pdf,.docx,image/*",
            "multiple": True,
            "show_preview": True,
        },
    )
```

Drag-and-drop is on by default: the input renders inside a drop zone that
accepts dragged files and feeds them into the same `change`/preview handling
as a click-selected file, so no extra wiring is needed. Set
`ui_options={"enable_drag_drop": False}` to render a plain file input.

#### color

Required:

- string field + ui_element="color"

Optional:

- default value (for initial color)
- ui_options: show_value

```python
class ColorExample(FormModel):
    accent_color: str = Field(
        "#0EA5E9",
        ui_element="color",
        ui_options={"show_value": True},
    )
```

#### hidden

Required:

- field + ui_element="hidden"

Optional:

- default value

```python
class HiddenExample(FormModel):
    account_id: str = Field(
        "acct_123",
        ui_element="hidden",
    )
```

#### ssn (alias: social_security_number)

Required:

- string field + ui_element="ssn"

Optional:

- ui_placeholder override

```python
class SsnExample(FormModel):
    ssn: str = Field(
        ...,
        ui_element="ssn",
        ui_placeholder="123-45-6789",
    )
```

#### phone (alias: phone_number)

Required:

- string field + ui_element="phone"

Optional:

- ui_placeholder
- ui_options: country_code, autocomplete, phone_format, live_format (default True)

```python
class PhoneExample(FormModel):
    contact_phone: str = Field(
        ...,
        ui_element="phone",
        ui_placeholder="555 123 4567",
        ui_options={"country_code": "+1", "autocomplete": "tel"},
    )
```

Set `ui_options={"phone_format": "(###) ###-####"}` to get a live-formatting
mask -- `#` marks each digit position, and any other character is inserted
literally as the user types. Without `phone_format`, the field renders
exactly as before (no mask). This is display formatting only; it is not a
substitute for server-side validation of the submitted value.

#### credit_card (aliases: card, cc_number)

Required:

- string field + ui_element="credit_card"

Optional:

- ui_placeholder override

```python
class CreditCardExample(FormModel):
    card_number: str = Field(
        ...,
        ui_element="credit_card",
        ui_placeholder="1234 5678 9012 3456",
    )
```

#### currency (alias: money)

Required:

- string/decimal-like field + ui_element="currency"

Optional:

- ui_options: currency_symbol, live_format (default True)

```python
class CurrencyExample(FormModel):
    budget: str = Field(
        ...,
        ui_element="currency",
        ui_options={"currency_symbol": "$"},
    )
```

`live_format` inserts thousands separators as the user types (on by default).
Set `ui_options={"live_format": False}` to disable it. As with `phone`, this
is display formatting only -- validate the submitted value server-side.

#### tags

Required:

- string field + ui_element="tags"

Optional:

- ui_options: placeholder, separator (default ",")

```python
class TagsExample(FormModel):
    skills: str = Field(
        "",
        title="Skills",
        ui_element="tags",
        ui_options={"placeholder": "Add a skill and press Enter", "separator": ","},
    )
```

Renders a chip-style tags editor backed by a single hidden input that stores
the joined, separator-delimited string -- so the field type stays a plain
`str`, not a `list[str]`. Typing a separator character or pressing Enter
turns the current text into a chip; Backspace on an empty input removes the
last chip.

These specialized elements are opt-in and will not override normal `text` fields.
Use them explicitly when you want built-in formatting/pattern behavior.

## Security / anti-spam elements

### captcha

Required:

- string field + ui_element="captcha"
- ui_options with a `secret_key`

```python
from pydantic_schemaforms.inputs.specialized_inputs import verify_captcha

SECRET = "change-me-and-load-from-your-app-config"


class SignupForm(FormModel):
    captcha_answer: str = Field(
        "",
        title="Verify you are human",
        ui_element="captcha",
        ui_options={"secret_key": SECRET},
    )
```

`captcha` renders a small arithmetic question ("What is 4 + 7?") plus a
hidden, HMAC-signed challenge token -- the correct sum is never sent to the
browser. Verify it at the route level, before model validation, since the
token only exists in the raw submitted form data:

```python
form_dict = dict(await request.form())
token = form_dict.pop("captcha_answer_token", None)
if not verify_captcha(token=token, answer=form_dict.get("captcha_answer"), secret_key=SECRET):
    # re-render with a form-level error; a fresh challenge is generated
    # automatically since the widget re-renders on every request
    ...
```

Only declare the visible answer field on your model -- do not also declare a
separate `..._token` field for it. A new question/token pair is generated on
every render, so the token in the page always matches the question shown.

### honeypot

Required:

- string field + ui_element="honeypot"

```python
class SignupForm(FormModel):
    website_url: str = Field("", ui_element="honeypot")
```

Renders a field that is hidden from real users (`display: none`, `tabindex="-1"`)
but still visible to bots that fill in every input they find. If the
submitted value is non-empty, treat the submission as spam -- most apps fake
a success response rather than revealing that a trap caught it:

```python
if form_dict.get("website_url"):
    return success_response()  # pretend it worked; don't process the submission
```

### csrf

`csrf` is rendered by the library's own CSRF handling rather than declared
directly as a model field -- pass `csrf_mode="required-provider"` (or
`"field-only"` for local debugging) and a `csrf_token_provider` to
`render_form_html()`/`render_form_from_model()`. See
[docs/csrf.md](csrf.md) for the full guide, including how tokens are
generated, stored, and verified.

## Complete Example (All Documented UI Elements)

Use this model if you want one copy-paste block that exercises every documented ui_element.

```python
from datetime import date, datetime, time

from pydantic_schemaforms import Field, FormModel

# Load from app config in real code -- never hardcode a captcha secret.
ALL_UI_ELEMENTS_CAPTCHA_SECRET = "change-me"


class AllUiElementsExample(FormModel):
    # Text
    text_name: str = Field(
        ...,
        title="Full name",
        description="Customer display name",
        min_length=2,
        max_length=60,
        examples=["Jane Doe"],
        ui_element="text",
        ui_placeholder="Jane Doe",
        ui_options={"minlength": 2, "maxlength": 60},
    )
    text_password: str = Field(
        ...,
        title="Password",
        description="Must contain at least 12 characters",
        min_length=12,
        ui_element="password",
        ui_placeholder="Choose a password",
        ui_options={"minlength": 12, "autocomplete": "new-password"},
    )
    text_email: str = Field(
        ...,
        title="Email",
        description="Primary account email",
        max_length=254,
        examples=["jane@example.com"],
        ui_element="email",
        ui_placeholder="jane@example.com",
        ui_options={"maxlength": 254, "autocomplete": "email"},
    )
    text_search: str = Field(
        ...,
        ui_element="search",
        ui_placeholder="Search products",
        ui_options={"maxlength": 120},
    )
    text_area: str = Field(
        ...,
        ui_element="textarea",
        ui_placeholder="Write notes",
        ui_options={"rows": 4, "cols": 60, "wrap": "soft", "resize": "vertical"},
    )
    text_url: str = Field(
        ...,
        ui_element="url",
        ui_placeholder="https://example.com",
        ui_options={"pattern": r"https?://.+"},
    )
    text_tel: str = Field(
        ...,
        ui_element="tel",
        ui_placeholder="+1 555 123 4567",
        ui_options={"autocomplete": "tel", "maxlength": 20},
    )

    # Numbers
    number_quantity: int = Field(
        ...,
        title="Quantity",
        description="Order quantity",
        ge=1,
        le=100,
        strict=True,
        ui_element="number",
        ui_options={"step": 1, "inputmode": "numeric"},
    )
    number_range: int = Field(
        ...,
        title="Satisfaction",
        description="Satisfaction score from 0 to 10",
        ge=0,
        le=10,
        multiple_of=1,
        ui_element="range",
        ui_options={"min": 0, "max": 10, "step": 1, "value": 5, "show_value": True},
    )
    number_stepper_quantity: int = Field(
        1,
        title="Cart quantity",
        description="Ships a +/- stepper by default",
        ge=1,
        ui_element="quantity",
    )
    number_percentage: float = Field(
        ...,
        title="Discount",
        description="Percentage discount to apply",
        ge=0,
        le=100,
        ui_element="percentage",
    )
    number_temperature: float = Field(
        ...,
        title="Room temperature",
        ui_element="temperature",
        ui_options={"unit": "fahrenheit"},
    )

    # Rating & sliders
    rating_satisfaction: int = Field(
        3,
        title="Satisfaction rating",
        description="Slider-based rating with a live star readout",
        ui_element="rating",
        ui_options={"max_rating": 5},
    )
    rating_stars: int = Field(
        4,
        title="Quality",
        description="Individually clickable stars",
        ui_element="star_rating",
        ui_options={"max_stars": 5},
    )
    slider_volume: int = Field(
        50,
        title="Volume",
        ui_element="slider",
        ui_options={"min": 0, "max": 100, "step": 5},
    )

    # Selection
    select_region: str = Field(
        ...,
        title="Region",
        description="Primary operating region",
        examples=["na"],
        ui_element="select",
        ui_options={
            "options": [
                {"value": "na", "label": "North America"},
                {"value": "eu", "label": "Europe"},
            ]
        },
    )
    select_tags: list[str] = Field(
        default_factory=list,
        title="Tags",
        description="Select one or more team tags",
        ui_element="multiselect",
        ui_options={
            "choices": [
                {"value": "backend", "label": "Backend"},
                {"value": "frontend", "label": "Frontend"},
                {"value": "infra", "label": "Infra"},
            ],
            "size": 4,
        },
    )
    select_terms: bool = Field(
        ...,
        title="Terms accepted",
        description="Must be accepted before submit",
        ui_element="checkbox",
        ui_help_text="I agree to the terms",
        ui_options={"value": "1", "checked": False},
    )
    select_notify_via: list[str] = Field(
        default_factory=list,
        title="Notify me via",
        description="Independent checkboxes laid out on the page",
        ui_element="checkbox_group",
        ui_options={
            "choices": [
                {"value": "email", "label": "Email"},
                {"value": "sms", "label": "SMS"},
                {"value": "push", "label": "Push"},
            ]
        },
    )
    select_plan: str = Field(
        ...,
        title="Plan",
        description="Choose a subscription plan",
        ui_element="radio",
        ui_options={
            "choices": [
                {"value": "free", "label": "Free"},
                {"value": "pro", "label": "Pro"},
            ],
            "legend": "Plan",
        },
    )
    select_toggle: bool = Field(
        ...,
        title="Enable alerts",
        description="Turn notifications on or off",
        ui_element="toggle",
        ui_options={"label": "Enable alerts", "checked": True},
    )
    select_city: str = Field(
        ...,
        title="City",
        description="Choose from known cities or type your own",
        ui_element="combobox",
        ui_placeholder="Select or type a city",
        ui_options={
            "options": [
                {"value": "nyc", "label": "New York"},
                {"value": "ldn", "label": "London"},
                {"value": "tky", "label": "Tokyo"},
            ]
        },
    )

    # Date/time
    dt_date: date = Field(
        ...,
        title="Start date",
        description="Project start date",
        ui_element="date",
        ui_options={"min": date(2026, 1, 1), "max": date(2026, 12, 31)},
    )
    dt_time: time = Field(
        ...,
        title="Start time",
        description="Daily start time",
        ui_element="time",
        ui_options={"min": time(9, 0), "max": time(18, 0), "step": 900},
    )
    dt_datetime: datetime = Field(
        ...,
        title="Appointment",
        description="Appointment date and time",
        ui_element="datetime",
        ui_options={"auto_set_current": True, "with_set_now_button": True},
    )
    dt_month: str = Field(
        ...,
        title="Billing month",
        description="Month in YYYY-MM format",
        pattern=r"^\d{4}-\d{2}$",
        ui_element="month",
        ui_options={"min": "2026-01", "max": "2026-12", "value": "2026-04"},
    )
    dt_week: str = Field(
        ...,
        title="Sprint week",
        description="ISO week in YYYY-W## format",
        pattern=r"^\d{4}-W\d{2}$",
        ui_element="week",
        ui_options={"value": "2026-W17"},
    )
    dt_birthdate: date = Field(
        ...,
        title="Date of birth",
        description="Shows a live computed-age readout",
        ui_element="birthdate",
    )

    # Specialized
    sp_file: str = Field(
        ...,
        title="Attachments",
        description="Upload one or more files",
        ui_element="file",
        ui_options={"accept": ".pdf,.docx,image/*", "multiple": True, "show_preview": True},
    )
    sp_color: str = Field(
        "#0EA5E9",
        title="Accent color",
        description="Primary UI accent color",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        ui_element="color",
        ui_options={"show_value": True},
    )
    sp_hidden: str = Field(
        "acct_123",
        exclude=True,
        ui_element="hidden",
    )
    sp_ssn: str = Field(
        ...,
        title="Social security number",
        description="US SSN format",
        pattern=r"^\d{3}-\d{2}-\d{4}$",
        ui_element="ssn",
        ui_placeholder="123-45-6789",
    )
    sp_phone: str = Field(
        ...,
        title="Phone",
        description="Primary contact number",
        ui_element="phone",
        ui_placeholder="555 123 4567",
        ui_options={"country_code": "+1", "autocomplete": "tel"},
    )
    sp_credit_card: str = Field(
        ...,
        title="Card number",
        description="Card number with spaces",
        min_length=13,
        max_length=19,
        ui_element="credit_card",
        ui_placeholder="1234 5678 9012 3456",
    )
    sp_currency: str = Field(
        ...,
        title="Budget",
        description="Amount in selected currency",
        ui_element="currency",
        ui_options={"currency_symbol": "$"},
    )
    sp_tags: str = Field(
        "",
        title="Skills",
        description="Chip-style tags editor; stores a separator-joined string",
        ui_element="tags",
        ui_options={"placeholder": "Add a skill and press Enter"},
    )

    # Security / anti-spam
    sec_honeypot: str = Field(
        "",
        title="Website",
        ui_element="honeypot",
    )
    sec_captcha: str = Field(
        "",
        title="Verify you are human",
        ui_element="captcha",
        ui_options={"secret_key": ALL_UI_ELEMENTS_CAPTCHA_SECRET},
    )
```

`ALL_UI_ELEMENTS_CAPTCHA_SECRET` must be a module-level constant you load
from app config (not hardcoded) -- see the [captcha](#captcha) section above
for the full verification flow this field needs at the route level.

Alias note:

- datetime-local is an alias for datetime
- toggle_switch and checkbox_toggle are aliases for toggle
- social_security_number is an alias for ssn
- phone_number is an alias for phone
- card and cc_number are aliases for credit_card
- money is an alias for currency
- rating_stars is an alias for rating (the slider-based widget -- not the
  same as the separate `star_rating` element, which is clickable stars)

## Pseudo elements

These are handled specially by the renderer (not standard inputs):

- `layout`: layout-only schema fields (see [docs/layouts.md](layouts.md))
- `model_list`: repeatable nested model items

## Unknown elements

If you set `ui_element` to an unsupported value, the renderer falls back to a basic text input.

If you need a custom widget:

- Implement a `BaseInput` subclass
- Register it at runtime via `pydantic_schemaforms.inputs.registry.register_input_class()`

(Then you can use your custom `ui_element` key in schemas.)
