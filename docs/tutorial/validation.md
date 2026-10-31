# Validation

Validation is Pydantic validation: the rules live on the model, and
`validate()` from [Handling Submissions](handling-submissions.md) runs them.
There are three levels, and you use them in this order:

1. **Constraints** on `Field()` for a single value: length, range, pattern.
2. **`@field_validator`** for a rule about one field that a constraint can't express.
3. **`@model_validator`** for a rule about the form as a whole.

```python
--8<-- "docs_src/tutorial/validation/models.py"
```

Use it with the routes from [Handling Submissions](handling-submissions.md).

## Constraints

Constraints are the first choice: they're one keyword, they're always
checked on submit, and most of them also become HTML attributes, so the
browser catches many mistakes before the form is even sent.

| Constraint | Checks | Browser gets |
|---|---|---|
| `min_length=3`, `max_length=20` | Length of a string or list | `minlength`, `maxlength` |
| `pattern=r"^[a-z0-9_]+$"` | A regular expression | `pattern` |
| `ge=13`, `le=120` | At least / at most | `min`, `max` |
| `gt=0`, `lt=100` | Strictly greater / less than | (checked on submit only) |
| `multiple_of=5` | Divisible by | (checked on submit only) |

The messages are Pydantic's, with the range ones shortened: `age=9` shows
"Must be 13 or greater".

## Required checkboxes

To make the user tick a box, such as "I accept the terms", type it
`Literal[True]`. Ticking passes and leaving it unticked fails. An unticked box
submits nothing, so the error would be "Field required"; `unchecked_message`
replaces that with your own wording, as `accept_terms` does above. It also works
on a `bool` with no default.

## Field validators

`@field_validator` is a classmethod that gets the value and returns it,
possibly changed, or raises `ValueError` with the message to show.

**Cleaning up a value** is a `mode="before"` validator, so it runs before the
constraints: `lowercase_username` turns `" ADA "` into `"ada"`, which then
passes the lowercase-only `pattern`.

**Comparing with another field** uses `info.data`, which holds the fields
declared above this one that already passed. `passwords_match` puts its
error on the confirmation field, right where the user needs to fix it.

## Model validators

`@model_validator(mode="after")` runs once every field has passed, with the
whole form as `self`. Use it for rules that aren't about any single field.
Its error is a **form-wide error**: it appears at the top of the form, in the
error summary, as "Form: The end date must be after the start date", and in
`result.errors` under the `"_errors"` key:

```python
{"_errors": "The end date must be after the start date"}
```

A model validator only runs when every field is valid, so a user sees field
errors first, then form-wide ones.

!!! tip "Field or form?"
    If the error has an obvious field to blame, use a field validator so the
    message sits next to that field. Use a model validator when it doesn't.

## Where errors show up

After a failed submit, `result.render_with_errors()` shows:

- the user's values, still filled in;
- each field's message under the field, with the field marked invalid for
  screen readers (`aria-invalid`) and linked to the message;
- a summary at the top listing every error, including form-wide ones.

`result.errors` holds the same messages, shaped like the form:
`{"age": "Must be 13 or greater"}`, and for sub-forms and lists, nested the
same way as the data; see [Nested Forms and Lists](nested-forms.md).

??? note "Rule-based validation and live validation"

    Pydantic validation covers almost every form. The library also has a
    rule-based layer (`FormValidator`, with ready-made rules such as
    `EmailRule` and `PhoneRule`) for rules you want to share between the
    submit route and live checks while the user types, or switch on and
    off per route. See [Rule-Based Validation](../advanced/rule-validation.md)
    and [Live Validation](../advanced/live-validation.md).

Next: [Nested Forms and Lists](nested-forms.md).
