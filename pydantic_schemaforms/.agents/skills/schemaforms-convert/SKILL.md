---
name: schemaforms-convert
description: Convert existing code into pydantic-schemaforms forms - a Pydantic model, dataclass, JSON Schema, sample JSON payload, WTForms/Flask-WTF form, Django form or ModelForm, or a hand-written HTML form - into a FormModel with routes, keeping every field and validation rule. Also covers building a FormModel at runtime from data with create_model. Use when migrating forms to pydantic-schemaforms or turning a model or schema into a form.
---
<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/schemaforms-convert/SKILL.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->

# Convert to pydantic-schemaforms

Turn an existing model, schema or form into a `FormModel` and routes, without losing a field or a
validation rule. The output works the same as before, with the library rendering the form.

## Rules for any code that uses pydantic-schemaforms

These apply to every task. Read them before writing code.

1. **Treat the library as a dependency.** Never edit, copy or vendor its source into the app, and
   never import from its submodules (`pydantic_schemaforms.inputs`, `.rendering`, `.templates`,
   `.tstring`, `.validation`, `.live_validation`, ...). Everything app code needs is exported from
   the top level: `from pydantic_schemaforms import FormModel, Field, html, ...`. If a name won't
   import from there, re-check its spelling before looking anywhere else.
2. **A form is a `FormModel`.** It's a Pydantic `BaseModel` subclass, so the model is the form, its
   validation and its data. Ordinary Pydantic is expected: `@field_validator`,
   `@model_validator`, `EmailStr`, `Enum`, `Literal`, `Optional`, `create_model()`.
3. **Use what's built in before writing code.** Formatted inputs (phone, currency, tags, ratings,
   date formats, file upload), repeating sub-forms, layouts, wizards and CSV-import tables are all
   `Field(...)` settings or nested models, not HTML or JavaScript you write.
4. **Constraints validate; `ui_options` only decorates.** `min_length`, `max_length`, `pattern`,
   `ge`, `le`, `gt`, `lt` and `multiple_of` go on `Field()`: they're checked on submit, and most
   also become HTML attributes so the browser checks them first. The same value in `ui_options` is never checked on the server.
5. **Build HTML around user data with `html(t'...')`.** A value that passed `validate()` can still
   contain `<script>`. `html()` takes a Python 3.14 t-string and escapes every interpolated
   value; an f-string or `.format()` doesn't. Output the library rendered (`render_form_html()`,
   `render_with_errors()`) is already safe and can be placed as is.
6. **Mistakes fail silently, so check names.** An unknown `ui_element` renders a plain text box, an
   unknown `ui_options` key becomes an HTML attribute, and a misspelled `framework` falls back
   to another style. None of them raise. The frameworks are `"bootstrap"`, `"material"` and
   `"none"`.
7. **`EmailStr` needs the `email` extra** (`pydantic-schemaforms[email]`) just to define the
   model. Add it to the app's dependencies whenever a form has an email field typed `EmailStr`.

## Steps

1. **Inventory the source.** List every field with its type, required/optional, default, choices,
   limits, help text, label and custom validation. Also note where the form is rendered and
   handled (routes, templates, CSRF).
2. **Map each field** with the tables below, in this order of precedence: an explicit hint in the
   source (a widget, a format), then the type, then the field's name, then the plain type.
3. **Carry every rule over** as a `Field()` constraint, a type, or a validator. Never drop one and
   never move one into `ui_options`.
4. **Keep the structure.** Groups or fieldsets become nested `FormModel`s (and a `layout=` if
   they were tabs or steps); repeated groups become `list[ItemForm]`.
5. **Replace the handling code**: render with `render_form_html()`, validate with
   `Model.validate(request_form, ...)`, re-render with `result.render_with_errors()`. Remove the
   old form object, template field loops and error plumbing.
6. **Show a mapping table** in your reply: source field → new field, type, input and rules, plus
   anything that couldn't be carried over exactly.
7. **Test** that the page renders, an invalid POST keeps the values and shows each error under the
   right field, and a valid POST produces the same data as before.

Don't invent fields that aren't in the source. When the source is ambiguous (a sample payload),
keep its structure and say what you assumed.

## From a Pydantic model or dataclass

Don't duplicate an existing Pydantic model: inherit from it, `FormModel` first, and redeclare only
the fields that need form settings.

```python
from pydantic import BaseModel
from pydantic import Field as PydanticField

from pydantic_schemaforms import Field, FormModel, render_form_html


# The app's existing model, used elsewhere (an API, the database layer). Leave it as it is.
class User(BaseModel):
    name: str = PydanticField(min_length=2, title='Name')
    email: str
    bio: str = ''


# FormModel first, then the existing model: every field and constraint is inherited.
# Redeclare only the fields that need form settings.
class UserForm(FormModel, User):
    email: str = Field(title='Email', ui_element='email')
    bio: str = Field('', title='About you', max_length=500, ui_element='textarea')


form_html = render_form_html(UserForm, submit_url='/users/new')
```

A standard-library dataclass has no constraints to inherit: write a `FormModel` with the same
fields, adding constraints the code checks elsewhere.

## From WTForms / Flask-WTF

```python
from datetime import date
from typing import Literal

from pydantic import EmailStr, ValidationInfo, field_validator

from pydantic_schemaforms import Field, FormModel


# Converted from:
#   class SignupForm(FlaskForm):
#       username = StringField('Username', [DataRequired(), Length(min=3, max=25)])
#       email = EmailField('Email', [DataRequired(), Email()])
#       password = PasswordField('Password', [DataRequired(), Length(min=12)])
#       confirm = PasswordField('Repeat password', [EqualTo('password')])
#       plan = SelectField('Plan', choices=[('free', 'Free'), ('pro', 'Pro')])
#       birthday = DateField('Birthday', [Optional()])
#       newsletter = BooleanField('Send me the newsletter')
class SignupForm(FormModel):
    username: str = Field(title='Username', min_length=3, max_length=25)
    email: EmailStr = Field(title='Email')
    password: str = Field(title='Password', ui_element='password', min_length=12)
    confirm: str = Field(title='Repeat password', ui_element='password')
    plan: Literal['free', 'pro'] = Field('free', title='Plan')
    birthday: date | None = Field(None, title='Birthday')
    newsletter: bool = Field(False, title='Send me the newsletter')

    @field_validator('confirm')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value
```

| WTForms | FormModel |
|---|---|
| `StringField` | `str` |
| `TextAreaField` | `str`, `ui_element="textarea"` |
| `PasswordField` | `str`, `ui_element="password"` |
| `EmailField` / `Email()` | `EmailStr` |
| `URLField` / `URL()` | `AnyUrl` |
| `IntegerField`, `DecimalField`, `FloatField` | `int`, `Decimal`, `float` |
| `BooleanField` | `bool` with a `False` default; with `DataRequired()`, `Literal[True]` |
| `SelectField(choices=...)` | `Literal[...]` or an `Enum`; `ui_options={"choices": [{"value": ..., "label": ...}]}` when labels differ from values |
| `RadioField` | the same, `ui_element="radio"` |
| `SelectMultipleField` | `list[Literal[...]]` |
| `DateField`, `DateTimeLocalField`, `TimeField` | `date`, `datetime`, `time` |
| `FileField` / `MultipleFileField` | `Any`, `ui_element="file"`; check the file in the route |
| `HiddenField` | the type, `ui_hidden=True` |
| `FormField(Sub)` | a nested `FormModel` |
| `FieldList(FormField(Item))` | `list[ItemForm]`; `min_entries` → `min_length` |
| `DataRequired()` / `InputRequired()` | no default |
| `Optional()` | `X \| None = None` |
| `Length(min, max)` | `min_length`, `max_length` |
| `NumberRange(min, max)` | `ge`, `le` |
| `Regexp(p)` | `pattern=p` |
| `AnyOf([...])` | `Literal[...]` |
| `EqualTo("password")` | a `@field_validator` comparing with `info.data` |
| `validate_<field>()` | `@field_validator("<field>")` |
| label, `description` | `title`, `description` |

Route changes: `form.validate_on_submit()` → `result = Model.validate(request.form, ...)` and
`result.is_valid`; `form.data` → `result.data`; `form.errors` → `result.errors` (nested);
template field loops → `{{ form_html | safe }}`. Flask-WTF's CSRF → `csrf_mode="required-provider"`
with the token in the session (see the `pydantic-schemaforms` skill's security reference).

## From Django forms

| Django | FormModel |
|---|---|
| `CharField(max_length=n)` | `str`, `max_length=n` |
| `CharField(widget=Textarea)` | `str`, `ui_element="textarea"` |
| `EmailField`, `URLField` | `EmailStr`, `AnyUrl` |
| `IntegerField(min_value, max_value)` | `int`, `ge`, `le` |
| `DecimalField(max_digits, decimal_places)` | `Decimal`, `max_digits`, `decimal_places` |
| `BooleanField(required=False)` | `bool = False` |
| `BooleanField()` (required, so it must be ticked) | `Literal[True]`; `unchecked_message=` for its error |
| `ChoiceField(choices=...)` / `TypedChoiceField` | `Literal[...]` or an `Enum` |
| `MultipleChoiceField` | `list[Literal[...]]` |
| `ModelChoiceField(queryset)` | choices built at runtime: `ui_options={"choices": [...]}` from the query, or `create_model()` |
| `DateField`, `DateTimeField`, `TimeField` | `date`, `datetime`, `time` |
| `FileField`, `ImageField` | `Any`, `ui_element="file"` |
| `required=False` | a default (`None` with `X \| None`) |
| `label`, `help_text`, `initial` | `title`, `description`, the default |
| `clean_<field>()` | `@field_validator("<field>")` |
| `clean()` | `@model_validator(mode="after")` (message goes to `"_errors"`) |
| formsets | `list[ItemForm]` |

A `ModelForm` maps the model's fields the same way, through their form field types. Django's
CSRF middleware still applies; render its token into the page or use `csrf_mode` with Django's
token as `csrf_token_provider`.

## From JSON Schema or a sample JSON payload

| JSON Schema | FormModel |
|---|---|
| `"type": "string"` | `str`; `minLength`/`maxLength`/`pattern` → `min_length`/`max_length`/`pattern` |
| `"format": "email"`, `"uri"`, `"date"`, `"date-time"`, `"time"` | `EmailStr`, `AnyUrl`, `date`, `datetime`, `time` |
| `"type": "integer"` / `"number"` | `int` / `float`; `minimum`/`maximum` → `ge`/`le`; `exclusiveMinimum` → `gt`; `multipleOf` → `multiple_of` |
| `"type": "boolean"` | `bool`; with `"const": true`, `Literal[True]` |
| `"enum": [...]` | `Literal[...]` or an `Enum` |
| `"type": "array"` of enum | `list[Literal[...]]` |
| `"type": "array"` of objects | `list[ItemForm]`; `minItems`/`maxItems` → `min_length`/`max_length` |
| `"type": "object"` / `$ref` | a nested `FormModel` |
| not in `required` | a default, or `X \| None = None` |
| `title`, `description`, `default`, `examples` | the same `Field()` arguments |

From a sample payload, infer types from the values (an ISO date string is a `date`, a list of
objects is a repeating sub-form) and mark every field required unless told otherwise.

## Fields known only at runtime

When the fields come from data (a database table of questions, a config file), build the model
with Pydantic's `create_model` and `__base__=FormModel`. It renders, validates and re-renders like
a declared class:

```python
from pydantic import create_model

from pydantic_schemaforms import Field, FormModel, render_form_html

# Loaded from a database or a config file at runtime
FIELDS = [
    {'name': 'name', 'title': 'Your name', 'ui_element': 'text', 'required': True},
    {'name': 'email', 'title': 'Email', 'ui_element': 'email', 'required': True},
    {'name': 'rating', 'title': 'Rating', 'ui_element': 'rating', 'required': False},
    {'name': 'comments', 'title': 'Comments', 'ui_element': 'textarea', 'required': False},
]


def build_form(fields: list[dict]) -> type[FormModel]:
    return create_model(
        'FeedbackForm',
        __base__=FormModel,
        **{
            spec['name']: (
                str,
                Field(
                    ... if spec['required'] else '',
                    title=spec['title'],
                    ui_element=spec['ui_element'],
                ),
            )
            for spec in fields
        },
    )


FeedbackForm = build_form(FIELDS)
form_html = render_form_html(FeedbackForm, submit_url='/feedback')
```

Build it once (at startup, or cached per definition), not on every request.

## Keeping an API in step

If the same data also has a JSON API, don't keep a second model: `ApiModel = Form.as_api_model()`
gives a plain Pydantic model with the same fields and rules and no form settings, for request
bodies and `response_model`.
