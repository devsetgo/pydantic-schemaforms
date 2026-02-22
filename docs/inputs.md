# Inputs (UI Elements)

This page documents the **supported** `ui_element` values and their expected options.

Where you set these:

- Preferred: `pydantic_schemaforms.Field(..., ui_element="...")`
- Or directly via `json_schema_extra={"ui_element": "..."}`

```python
from pydantic_schemaforms import Field, FormModel


class Example(FormModel):
    email: str = Field(..., ui_element="email")
```

## Supported `ui_element` values

These map to concrete input components in `pydantic_schemaforms.inputs.*`.

### Text

- `text` (default)
- `password`
- `email`
- `search`
- `textarea`
- `url`
- `tel`

Notes:

- Long string fields may auto-infer to `textarea`.
- `password` preserves the value if you supply one (use with care).

### Numbers

- `number`
- `range`

### Selection

- `select`
- `multiselect`
- `checkbox`
- `radio`
- `toggle` (aliases: `toggle_switch`, `checkbox_toggle`)
- `combobox`

Options for selection widgets:

- Provide choices via `ui_options={"options": [...]}` or `ui_options={"choices": [...]}`.
- Or use JSON Schema enums (e.g. `Literal[...]` / `Enum`) and the renderer will infer options.

Example:

```python
class Preferences(FormModel):
    favorite_color: str = Field(
        ...,
        ui_element="select",
        ui_options={
            "options": [
                {"value": "red", "label": "Red"},
                {"value": "blue", "label": "Blue"},
            ]
        },
    )
```

### Date/time

- `date`
- `time`
- `datetime` (alias: `datetime-local`)
- `month`
- `week`

### Specialized

- `file`
- `color`
- `hidden`
- `ssn` (alias: `social_security_number`)
- `phone` (alias: `phone_number`)
- `credit_card` (aliases: `card`, `cc_number`)
- `currency` (alias: `money`)

These specialized elements are opt-in and will not override normal `text` fields.
Use them explicitly when you want built-in formatting/pattern behavior.

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
