# Live Validation (HTMX)

Live validation checks a field on the server while the user types or when
they leave the field, and shows the result next to the form without a page
reload. It uses [HTMX](https://htmx.org): the field posts its value to a small
endpoint and HTMX swaps the endpoint's answer into the page.

It's a convenience on top of normal validation, not a replacement: the submit
route still calls `validate()`, because JavaScript can be turned off.

## A complete example

Three files: the model and its live validator, a page template, and the routes.

```python title="models.py"
--8<-- "docs_src/advanced/live_validation/models.py"
```

```python title="page.py"
--8<-- "docs_src/advanced/live_validation/page.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/advanced/live_validation/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/advanced/live_validation/flask_app.py"
    ```

Typing "A" in the name and pausing shows "String should have at least 2
characters"; finishing the name shows "Looks good".

## How it works

1. **`LiveValidator.for_model(ContactForm)`** derives a check for every field
   from the model itself: its constraints, its type (`EmailStr`) and its
   `@field_validator`s. There's nothing to keep in sync.
2. **`ui_options=live("name")`** adds HTMX attributes to the input: post to
   `/validate/name` on blur and 600 ms after the user stops typing, and put
   the answer into `#name-feedback`. Any `ui_options` key that isn't a known
   option is written onto the input as an attribute.
3. **One endpoint serves every field.** `validate_field(name, value)` runs that
   field's check and returns a result with `is_valid` and `errors`. An unknown
   field name is reported as valid, so a stray request never breaks the page.
4. **`validation_response_headers()`** tells the script from
   `render_htmx_script()` the outcome, so it marks the input `is-valid` or
   `is-invalid` and copies the message into the input's tooltip.

The feedback is built with `html(t"...")` because a message can include what
the user typed: email-validator's "The domain name example.con does not
exist", for example. The feedback elements use `aria-live="polite"` so screen
readers announce the result.

## Checks that aren't in the model

`FieldValidator` builds a check from rules, with your own messages. Register
it after `for_model()` to replace that one field's check:

```python
from pydantic_schemaforms import CustomRule, FieldValidator

username = FieldValidator("username")
username.min_length(3, message="At least 3 characters")
username.add_rule(CustomRule(
    lambda value: not value.lower().startswith("admin"),
    message="Usernames can't start with 'admin'",
))
live_validator.register_field_validator(username)
```

The available rules are in [Validation Rules](../reference/validation-rules.md).

## Email addresses that can receive mail

`DeliverableEmailStr` is a drop-in replacement for `EmailStr` that also looks
up the domain's mail servers (MX records), so `ada@example.con` is rejected
with a message saying why. It works in `validate()` and in live validation
with nothing else to set up, and needs the `email` extra
(`pydantic-schemaforms[email]`).

It's a real DNS lookup, so it always runs on the server and takes a moment:
keep a debounce of at least 600 ms for it, or check it on blur only with
`live(...)` returning `"hx-trigger": "blur"` for that field.

## Triggers and debounce

`for_model(..., debounce_ms=600)` checks on blur and as the user types. For
other combinations, pass an `HTMXValidationConfig`:

```python
from pydantic_schemaforms import HTMXValidationConfig, LiveValidator

config = HTMXValidationConfig(
    validate_on_blur=True,
    validate_on_input=False,   # blur only
    validate_on_change=False,
    debounce_ms=400,
)
live_validator = LiveValidator.for_model(ContactForm, config=config)
```

The trigger written on the input (`hx-trigger`) is set by your `ui_options`,
so keep the two in step.

## Several forms, one endpoint

`LiveValidator.for_model(ContactForm, SignupForm)` covers several forms with
one validator and one `/validate/{field_name}` route. Field names must be
unique across those forms; for a repeated name, the last one registered wins.

## Styling the result

Bootstrap styles `is-valid` and `is-invalid` on inputs out of the box. For
Material or plain HTML, add your own rule:

```css
input.is-invalid { border-color: #dc3545; }
input.is-valid   { border-color: #198754; }
```

??? note "Rendering a single field by hand"

    `live_validator.render_field_with_live_validation("email", field_type="email", label="Email")`
    returns one labelled input with its HTMX attributes and its own feedback
    element, for pages where you build the markup yourself instead of
    rendering a whole `FormModel`.

The example app's `/live-validation` and `/email-dns-validation` pages run
these patterns live.
