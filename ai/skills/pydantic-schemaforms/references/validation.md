# Validation reference

Validation comes from the model first: the field types, `Field()` constraints and Pydantic
validators. The rule classes and live HTMX checks below are extras for when the model isn't
enough. All names are imported from the top-level package.

## Constraints and validators on the model

<!-- INCLUDE-CODE: docs_src/tutorial/validation/models.py -->

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
- A required checkbox ("I accept the terms") with a custom message: give it a `False` default,
  `validate_default=True`, and a `@field_validator` that raises when it's `False`. An unticked
  box sends nothing, so without `validate_default` the validator never runs.

## Rule-based validation

`FormValidator` holds a set of rules that run on the submitted data alongside the model. Use it
for a ready-made check that isn't a Pydantic type (`PhoneRule`), rules switched per route, or the
same rules behind live validation and the submit route.

<!-- INCLUDE-CODE: docs_src/advanced/rule_validation/models.py -->

Run the rules on `result.original_data` (the decoded submission, nested like the model) and
merge both sets of errors into one re-render:

<!-- INCLUDE-CODE: docs_src/advanced/rule_validation/fastapi_app.py -->

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

## Live validation (HTMX)

Checks fields on the server while the user types, without reloading the page. It's an addition
to submit-time validation, never a replacement: the POST route still calls `validate()`.

<!-- INCLUDE-CODE: docs_src/advanced/live_validation/models.py -->

<!-- INCLUDE-CODE: docs_src/advanced/live_validation/page.py -->

<!-- INCLUDE-CODE: docs_src/advanced/live_validation/fastapi_app.py -->

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

## Two error shapes

| From | `.errors` is |
|---|---|
| `Model.validate()` → `ValidationResult` | a nested tree shaped like the data: `{"email": "...", "address": {"city": "..."}, "_errors": "..."}` |
| `LiveValidator.validate_field()` / `FieldValidator.validate()` → `ValidationResponse` or tuple | a `list[str]` of messages for one field |
| `FormValidator.validate()` | `{field: [messages]}` |

Don't index one shape as if it were another. `render_with_errors(errors=...)` and
`render_form_html(errors=...)` accept the tree and the `{field: [messages]}` form.
