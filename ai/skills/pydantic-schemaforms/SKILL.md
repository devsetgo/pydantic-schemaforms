---
name: pydantic-schemaforms
description: Build, change and fix server-rendered HTML forms with pydantic-schemaforms (FormModel, Field, render_form_html, FormModel.validate) in FastAPI, Flask or any Python web app. Use for any form work in an app that depends on pydantic-schemaforms - fields and inputs, validation and error messages, nested and repeating sub-forms, tabbed/accordion/wizard layouts, CSV import tables, live HTMX validation, CSRF, file uploads, styling, or a form that renders or validates wrongly.
---

# pydantic-schemaforms

pydantic-schemaforms turns a Pydantic model into a server-rendered HTML form and validates the
submission with the same model. This skill covers building and changing forms in an app.

Related skills, when installed: `schemaforms-create` (a new form from a short description),
`schemaforms-convert` (an existing model, schema or form library to a `FormModel`),
`schemaforms-upgrade` (code using removed APIs) and `schemaforms-document` (document an app's forms).

<!-- INCLUDE: _shared.md -->

## What to deliver

For a new or changed form, deliver all of these unless the user asks for less:

1. A `FormModel` with a `title` on every field and constraints on `Field()`.
2. Both routes: GET renders the form, POST validates it.
3. `render_form_html()` (or `render_form_html_async()` in an `async def` route) with
   `submit_url=` matching the route. Pass `framework=` and `layout=` when they aren't the defaults.
4. POST handled with `Model.validate(request_form, ...)` and, on failure,
   `result.render_with_errors()`. Never `Model(**data)` with `try/except ValidationError`.
5. Any HTML built around submitted data uses `html(t'...')`.
6. A sentence on each non-obvious choice (an input type, a layout, a validator).

## The pattern

Every form route looks like this. FastAPI:

<!-- INCLUDE-CODE: docs_src/tutorial/submissions/fastapi_app.py -->

Flask:

<!-- INCLUDE-CODE: docs_src/tutorial/submissions/flask_app.py -->

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

## Choosing inputs

Without `ui_element`, the input comes from the field's type:

| Type | Input |
|---|---|
| `str` | text box |
| `int`, `float` | number box (`float` accepts decimals) |
| `bool` | checkbox |
| `date`, `datetime`, `time` | date, date-and-time, time picker |
| `EmailStr`, `AnyUrl` | email box, URL box |
| `Enum`, `Literal[...]` | dropdown of the values; `list[...]` of either is a multi-select |
| `X \| None` | the same input, optional; an optional dropdown gets an empty first choice |
| another `FormModel` | a sub-form |
| `list[FormModel]` | a repeating sub-form with Add and Remove buttons |

Set `ui_element=` for anything else, for example `"textarea"`, `"password"`, `"radio"`,
`"toggle"`, `"tags"`, `"currency"`, `"phone"`, `"file"`, `"rating"`, `"color"`. The complete list,
with every `ui_options` key, is in [the inputs reference](references/inputs.md). Check it before
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

## Validation

- **Field rules:** Pydantic constraints on `Field()` (`min_length`, `ge`, `pattern`, ...) and the
  type itself (`EmailStr`, `date`, `Enum`).
- **Your own checks:** `@field_validator` for one field (its message goes under that field),
  `@model_validator(mode="after")` for rules across fields (its message is form-wide, under
  `"_errors"`). Raise `ValueError("message")`; the message is shown as written.
- **Errors your route finds after validation** (a taken username, a wrong password): render again
  with `render_form_html(Model, form_data=submitted, errors={"username": "..."}, ...)`, or
  `errors={"_errors": "..."}` for a message about the whole form.
- Live as-you-type checks, rule classes such as `PhoneRule`, and cross-field rule sets: see
  [the validation reference](references/validation.md).

## Pre-filling a form

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

## More

| Task | Reference |
|---|---|
| Every input, every `ui_options` key, every `Field()` setting | [inputs](references/inputs.md) |
| Sub-forms, optional sub-forms, repeating sub-forms, tabbed/accordion/side-by-side/wizard layouts | [complex forms](references/complex-forms.md) |
| Rule classes, live HTMX validation, the two error shapes | [validation](references/validation.md) |
| CSV import into an editable, validated table | [data tables](references/data-tables.md) |
| CSRF, captcha, honeypot, file uploads, safe HTML | [security](references/security.md) |
| Styling, assets, async rendering, JSON API from the same model, JSON Schema | [rendering](references/rendering.md) |
| A custom input or a custom composite control | [extending](references/extending.md) |

## Troubleshooting

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

## Before finishing

- `submit_url` matches the POST route, and both routes exist.
- Every `ui_element` and `ui_options` key used is in the inputs reference.
- Limits are `Field()` constraints, not `ui_options`.
- No import from a `pydantic_schemaforms.` submodule.
- No f-string or `.format()` around submitted values; `html(t'...')` instead.
- State-changing forms behind a login use CSRF protection (see the security reference).
- No hand-written input HTML, add/remove JavaScript or CSV upload handling for something the
  library already renders.
