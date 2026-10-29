# Rule-Based Validation

Most forms need nothing beyond the Pydantic validation in the
[Validation](../tutorial/validation.md) chapter. The library also has a
rule-based layer, `FormValidator`, for three situations:

- **A ready-made check** that isn't a Pydantic type, such as `PhoneRule`.
- **Rules you switch on or off per route** without changing the model, for
  example a stricter check on an admin page.
- **The same rules for live validation and the submit route**; see
  [Live Validation](live-validation.md).

Rules run on the submitted data alongside the model's own validation, and
their errors are shown the same way.

## Model and rules together

```python title="models.py"
--8<-- "docs_src/advanced/rule_validation/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/advanced/rule_validation/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/advanced/rule_validation/flask_app.py"
    ```

The route validates with the model first, then runs the rules on
`result.original_data`, the submission decoded into the same nested shape as
the model. If either fails, both sets of errors are passed to
`render_with_errors(errors=...)`, so the user sees every problem at once.

Rules skip empty values, so an optional field is only checked when it's
filled in; add `RequiredRule()` when a value must be present.

## Field rules

`rules.field("phone")` returns that field's rule list; `add_rule()` adds to it
and returns it again, so rules chain:

```python
rules.field("username").add_rule(MinLengthRule(3)).add_rule(MaxLengthRule(20))
```

Every rule takes an optional `message=` to replace its default text. The full
list (`RequiredRule`, `MinLengthRule`, `MaxLengthRule`, `EmailRule`,
`EmailDeliverabilityRule`, `PhoneRule`, `NumericRangeRule`, `DateRangeRule`,
`RegexRule`, `CustomRule`) is in [Validation Rules](../reference/validation-rules.md).

`CustomRule` wraps any function that returns `True` for a valid value:

```python
from pydantic_schemaforms import CustomRule

rules.field("username").add_rule(
    CustomRule(lambda value: not value.lower().startswith("admin"),
               message="Usernames can't start with 'admin'")
)
```

## Cross-field rules

`add_cross_field_rule()` takes a function that gets all the data and returns
`(is_valid, errors)`, where `errors` maps a field name to its message. That
puts the message on the field the user has to change, like
`minors_need_consent` above.

## Running rules on their own

`rules.validate(data)` returns `(is_valid, errors)` without a model, with
each field's messages as a list:

```python
is_valid, errors = rules.validate({"phone": "abc", "age": 15})
# (False, {"phone": ["Please enter a valid phone number"],
#          "parental_consent": ["A parent must agree for anyone under 18"]})
```

??? note "Quick standalone checks"

    `create_email_validator()` and `create_password_strength_validator()`
    return functions that check a single value and give back a
    `ValidationResponse` with `is_valid`, `errors`, and for passwords also
    `warnings` and `suggestions` ("Add a number (0-9)"). They're handy for an
    API endpoint or a live check of one field.
