# Validation Rules

The classes behind [Rule-Based Validation](../advanced/rule-validation.md)
and [Live Validation](../advanced/live-validation.md). Everything here is
imported from the top-level package:

```python
from pydantic_schemaforms import FormValidator, PhoneRule, NumericRangeRule
```

Rules run alongside the model's own validation, never instead of it. The
built-in rules other than `RequiredRule` pass an empty value, so an optional
field is only checked when it's filled in. A `CustomRule` function is called
for empty values too.

## Rule classes

Every rule takes `message=` to replace its default text.

| Rule | Checks | Arguments |
|---|---|---|
| `RequiredRule()` | The value is present and not blank | `message` |
| `MinLengthRule(min_length)` | At least `min_length` characters | `min_length`, `message` |
| `MaxLengthRule(max_length)` | At most `max_length` characters | `max_length`, `message` |
| `RegexRule(pattern)` | Matches the regular expression | `pattern`, `message`, `flags` |
| `EmailRule()` | Looks like an email address (format only) | `message` |
| `EmailDeliverabilityRule()` | The email's domain exists and accepts mail (a real DNS lookup; server only; needs the `email` extra) | `message`, `timeout` (seconds) |
| `PhoneRule()` | Looks like a phone number: 10 to 15 digits, with optional `+`, spaces, dashes, dots and parentheses | `message` |
| `NumericRangeRule(min_value, max_value)` | A number within the range; either end can be `None` | `min_value`, `max_value`, `message` |
| `DateRangeRule(min_date, max_date)` | A date within the range; dates or `"YYYY-MM-DD"` strings | `min_date`, `max_date`, `message` |
| `CustomRule(func)` | `func(value)` returns `True`, or `(is_valid, message)` | `validator_func`, `message` |

Without `message=`, `EmailDeliverabilityRule` reports the lookup's own reason,
such as "The domain name example.invalid does not exist."

A rule on its own: `PhoneRule().validate("abc")` returns
`(False, "Please enter a valid phone number")`.

## `FormValidator`

A set of rules for a whole form.

| Method | Does |
|---|---|
| `FormValidator()` (or `create_validator()`) | Creates an empty set |
| `.field(name)` | The `FieldValidator` for that field, created on first use |
| `.add_cross_field_rule(func)` | Adds a check of the whole data. `func(data)` returns `(is_valid, {field: message})`. |
| `.validate(data)` | Runs every rule. Returns `(is_valid, {field: [messages]})`. |

## `FieldValidator`

The rules of one field. Every method returns the validator, so they chain:

```python
rules.field("username").required().min_length(3).max_length(20)
```

| Method | Adds |
|---|---|
| `.add_rule(rule)` | Any rule instance |
| `.required(message=None)` | `RequiredRule` |
| `.min_length(n, message=None)` / `.max_length(n, message=None)` | `MinLengthRule` / `MaxLengthRule` |
| `.email(message=None, check_deliverability=False, dns_timeout=None)` | `EmailRule`, plus `EmailDeliverabilityRule` when asked |
| `.email_deliverability(message=None, dns_timeout=None)` | `EmailDeliverabilityRule` |
| `.phone(message=None)` | `PhoneRule` |
| `.numeric_range(min_val=None, max_val=None, message=None)` | `NumericRangeRule` |
| `.date_range(min_date=None, max_date=None, message=None)` | `DateRangeRule` |
| `.regex(pattern, message=None)` | `RegexRule` |
| `.custom(func, message=None)` | `CustomRule` |
| `.validate(value)` | Runs the rules: `(is_valid, [messages])` |

`FieldValidator("email")` also works on its own, and a `ValidationSchema`
collects several (`.add_field(validator)`) for a `LiveValidator`
(`.build_live_validator()`).

## `CrossFieldRules`

Ready-made functions for `add_cross_field_rule()`:

| Function | Checks |
|---|---|
| `CrossFieldRules.password_confirmation(password_field="password", confirm_field="confirm_password", message=...)` | The two fields match; the message goes on the confirmation |
| `CrossFieldRules.date_range_validation(start_field, end_field, message=...)` | The end date is after the start date; the message goes on the end date |

## Single-value checks

| Function | Returns |
|---|---|
| `create_email_validator(check_deliverability=False, dns_timeout=None)` | A function that checks one email and returns a `ValidationResponse` |
| `create_password_strength_validator(min_length=8)` | A function that checks a password's length and mix of characters, with `warnings` and `suggestions` |

`ValidationResponse` has `field_name`, `is_valid`, `errors`, `warnings`,
`suggestions`, `value` and `formatted_value`, plus `to_dict()` and `to_json()`.

## `DeliverableEmailStr`

An `EmailStr` type that also does the DNS check as part of Pydantic
validation, so a model field is enough:

```python
from pydantic_schemaforms import DeliverableEmailStr, Field, FormModel


class SignupForm(FormModel):
    email: DeliverableEmailStr = Field(title="Email")
```

`validate()`, `as_api_model()` and `LiveValidator.for_model()` all apply it.

## `LiveValidator`

Checks fields on the server as the user types; the
[Live Validation](../advanced/live-validation.md) page shows the whole setup.

| Member | Does |
|---|---|
| `LiveValidator.for_model(*models, debounce_ms=600, config=None)` | A validator that checks each field of the given models against their own types and constraints |
| `.register_field_validator(validator)` | Adds a `FieldValidator`'s rules for its field |
| `.register_schema(schema)` | Adds every field of a `ValidationSchema` |
| `.register_model_validator(Model)` | Adds every field of another model, for several forms on one validator |
| `.validate_field(name, value)` | Checks one value: a `ValidationResponse` |
| `.render_field_with_live_validation(...)` | Renders one input wired to the validation endpoint |
| `.render_htmx_script()` | The script tag that loads HTMX for the page |

`HTMXValidationConfig` sets when checks run and how results look:
`validate_on_blur` (default `True`), `validate_on_change` (`True`),
`validate_on_input` (`False`), `debounce_ms` (300), the CSS classes
(`success_class`, `error_class`, `warning_class`, `loading_class`) and
whether to show success, warnings and suggestions.
`validation_response_headers()` returns the response headers an endpoint
should send with a check's result.
