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

#### number

Required:

- Numeric field type + ui_element="number"

Optional:

- Pydantic constraints: ge, le, gt, lt, multiple_of
- ui_options: min, max, step, inputmode

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

### Selection

- `select`
- `multiselect`
- `checkbox`
- `radio`
- `toggle` (aliases: `toggle_switch`, `checkbox_toggle`)
- `combobox`

#### select

Required:

- ui_element="select"
- ui_options with choices/options list, or schema enum

Optional:

- ui_options: options, choices, size, class, style

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

#### multiselect

Required:

- ui_element="multiselect"
- ui_options with choices/options list, or schema enum

Optional:

- ui_options: options, choices, size

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

#### radio

Required:

- ui_element="radio"
- ui_options with choices/options list, or schema enum

Optional:

- ui_options: options, choices, legend, class, style

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
- ui_options: options, choices

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

Selection note:

- Provide choices via ui_options={"options": [...]} or ui_options={"choices": [...]}.
- Or use JSON Schema enums (for example Literal[...] or Enum) and options are inferred.

### Date/time

- `date`
- `time`
- `datetime` (alias: `datetime-local`)
- `month`
- `week`

#### date

Required:

- date-like field + ui_element="date"

Optional:

- ui_options: min, max, value

```python
from datetime import date


class DateExample(FormModel):
    start_date: date = Field(
        ...,
        ui_element="date",
        ui_options={"min": date(2026, 1, 1), "max": date(2026, 12, 31)},
    )
```

#### time

Required:

- time-like field + ui_element="time"

Optional:

- ui_options: min, max, step, value

```python
from datetime import time


class TimeExample(FormModel):
    start_time: time = Field(
        ...,
        ui_element="time",
        ui_options={"min": time(9, 0), "max": time(18, 0), "step": 900},
    )
```

#### datetime (alias: datetime-local)

Required:

- datetime-like field + ui_element="datetime"

Optional:

- ui_options: min, max, value, auto_set_current, with_set_now_button

```python
from datetime import datetime


class DatetimeExample(FormModel):
    appointment_at: datetime = Field(
        ...,
        ui_element="datetime",
        ui_options={"auto_set_current": True, "with_set_now_button": True},
    )
```

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

### Specialized

- `file`
- `color`
- `hidden`
- `ssn` (alias: `social_security_number`)
- `phone` (alias: `phone_number`)
- `credit_card` (aliases: `card`, `cc_number`)
- `currency` (alias: `money`)

#### file

Required:

- string field + ui_element="file"

Optional:

- ui_options: accept, multiple, capture, show_preview

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
- ui_options: country_code, autocomplete

```python
class PhoneExample(FormModel):
    contact_phone: str = Field(
        ...,
        ui_element="phone",
        ui_placeholder="555 123 4567",
        ui_options={"country_code": "+1", "autocomplete": "tel"},
    )
```

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

- ui_options: currency_symbol

```python
class CurrencyExample(FormModel):
    budget: str = Field(
        ...,
        ui_element="currency",
        ui_options={"currency_symbol": "$"},
    )
```

These specialized elements are opt-in and will not override normal `text` fields.
Use them explicitly when you want built-in formatting/pattern behavior.

## Complete Example (All Documented UI Elements)

Use this model if you want one copy-paste block that exercises every documented ui_element.

```python
from datetime import date, datetime, time

from pydantic_schemaforms import Field, FormModel


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
```

Alias note:

- datetime-local is an alias for datetime
- toggle_switch and checkbox_toggle are aliases for toggle
- social_security_number is an alias for ssn
- phone_number is an alias for phone
- card and cc_number are aliases for credit_card
- money is an alias for currency

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
