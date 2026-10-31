---
name: schemaforms-upgrade
description: Upgrade app code to the installed pydantic-schemaforms version. Use when code imports or calls removed APIs (FormBuilder, AutoFormBuilder, create_login_form, render_form_page, handle_form, form_validator, TabbedLayout, ListLayout, SectionDesign, FormDesign, validate flatten=, ReactJSONSchemaFormAdapter), when an ImportError or FormLayoutRemovedError names a replacement, or when forms, errors or data shapes broke after upgrading pydantic-schemaforms.
---
<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/schemaforms-upgrade/SKILL.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->

# Upgrade pydantic-schemaforms code

Bring an app's form code up to the installed version. Every removed API raises an error naming
its replacement; this skill has the full mapping and the order to do it in.

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

1. **Find the installed version**: `python -c "import importlib.metadata as m; print(m.version('pydantic-schemaforms'))"`.
2. **Find every use of a removed API.** Search the app (not the virtual environment) for the names
   in the tables below, for example:
   `grep -rnE "FormBuilder|create_(login|registration|contact)_form|create_form_from_model|render_form_page|handle_form|FormIntegration|form_validator|TabbedLayout|ListLayout|SectionDesign|FormDesign|FormLayoutBase|flatten=|parse_nested_form_data|pydantic_schemaforms\.(layouts|integration|form_layouts)|ReactJSONSchemaFormAdapter|VueFormulateAdapter|\"general\"" --include=*.py --include=*.html .`
3. **Upgrade one form at a time**: the model, then its routes, then everything that reads its data
   or errors (templates, saving code, tests). Data shapes change with nested forms, so check every
   consumer of `result.data`.
4. **Run the app's tests after each form.** Add a test that renders the form and posts an invalid
   submission if there isn't one.
5. **Report** what changed per form, and anything that behaves differently (for example data now
   nested under a sub-form's name).

## 26.4.4: Material Design 3

`framework="material"` was rebuilt on Material Design 3. Forms keep working with no code change;
only customizations of the Material style need attention. Search the app for `MaterialEmbeddedTheme`,
`materialize`, and CSS or tests that target Material markup.

| Changed | Replace with |
|---|---|
| CSS or tests written against the old Material markup | The new markup; the form keeps its `md-form` class. Color overrides use `--md-sys-color-*` tokens on `form.md-form` |
| `MaterialEmbeddedTheme` | `MaterialTheme` |
| Materialize, and `framework_css_tag()`/`framework_js_tag()` for `"material"` | Nothing: both now return nothing for `"material"`, and the page needs no Materialize |

## 26.4.3: one way to build a form

The builder API, the React and Vue adapters and `@form_validator` are removed. Importing a removed
name raises `ImportError: pydantic_schemaforms.<name> was removed. <what to do instead>`.

| Removed | Replacement |
|---|---|
| `FormBuilder`, `AutoFormBuilder`, `create_form_from_model`, `FormDefinition`, `FormSection`, `ModernFormRenderer` | A `FormModel` class rendered with `render_form_html()`. For fields known only at runtime, `create_model(name, __base__=FormModel, **fields)`. |
| `create_login_form`, `create_registration_form`, `create_contact_form` | Declare the `FormModel` (see the example below, or the `schemaforms-create` skill's catalogue) |
| `render_form_page` | `render_form_html()` inside the app's own page template |
| `FormIntegration`, `handle_form`, `handle_form_async` | `result = Model.validate(request_form, submit_url=...)`, then `result.is_valid`, `result.data`, `result.render_with_errors()` |
| `@form_validator` (it never ran) | `@model_validator(mode="after")` on the model (message under `"_errors"`), or `FormValidator.add_cross_field_rule()` |
| `ReactJSONSchemaFormAdapter`, `VueFormulateAdapter`, `map_ui_element_to_framework`, `convert_validation_rules` | `Model.get_pydantic_json_schema()` for a JSON Schema, `Model.as_api_model()` for a plain Pydantic model |
| `DataTableLayout` inputs named `rows[i].col`, `csv_file`, `datatable_action` | Named under the embedding field: `employees.rows[i].col`, `employees.csv_file`. Only code that reads these keys directly or posts them in tests changes; `handle_import_post()` finds them itself. With two tables on the same row model, pass `field="employees"`. |

Before and after for a builder-made form:

```python
# before
form = create_registration_form(framework='bootstrap')
html_out = form.render(data=submitted, errors=errors)


# after
class RegistrationForm(FormModel):
    username: str = Field(title='Username', min_length=3)
    email: EmailStr = Field(title='Email')
    password: str = Field(title='Password', ui_element='password', min_length=12)
    confirm_password: str = Field(title='Confirm password', ui_element='password')

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value


html_out = render_form_html(RegistrationForm, submit_url='/register')
```

## Upgrading to nested forms

Version 26.4.1 removed the older ways of combining forms. Code using them fails with
`FormLayoutRemovedError` (a `TypeError`) at class definition or call time.

| Removed | Replace with |
|---|---|
| `TabbedLayout`, `VerticalLayout`, `HorizontalLayout` wrapper classes (`form = X` attributes, `_get_layouts()` overrides) | One nested `FormModel` field per wrapped form, plus `layout="tabbed"` / `"vertical"` / `"side-by-side"` on render and validate |
| A parent field like `tabs: MyTabs = Field(default_factory=MyTabs, input_type="layout")` | Delete it; the sub-form fields go directly on the parent |
| `ListLayout(Item, min_items=..., max_items=..., add_button_text=...)` | `items: list[Item] = Field(default_factory=list, min_length=..., max_length=..., ui_add_button_label=...)` |
| `SectionDesign(section_title=..., section_description=..., collapsible=...)` | `Field(title=..., ui_help_text=..., ui_collapsible=True)` on the sub-form field |
| `FormDesign(...)` | Arguments to `render_form_html(...)` and the app's own page template |
| `parse_nested_form_data(...)` / `dict(await request.form())` before validating | `Model.validate(await request.form(), ...)` |
| `validate(..., flatten=True)` | Removed. `result.data` is always nested |
| Error keys like `result.errors["pets[0].name"]` or `result.errors["city"]` for a sub-form field | `result.errors["pets"][0]["name"]`, `result.errors["address"]["city"]` |
| `errors={"general": ...}` | `errors={"_errors": ...}` |
| `layout="tabbed"` on a flat form (fields grouped by name keywords) | Split the fields into sub-forms; each sub-form is a tab |
| Several `input_type="layout"` fields that auto-rendered as tabs | Nested sub-form fields plus explicit `layout="tabbed"` |
| `from pydantic_schemaforms.layouts import ...` | `from pydantic_schemaforms import ...` (top-level `VerticalLayout`/`HorizontalLayout` are now the plain flex layout primitives) |

Before:

```python
class ContactTab(VerticalLayout):
    form = Contact


class AddressTab(VerticalLayout):
    form = Address


class ProfileTabs(TabbedLayout):
    contact = ContactTab()
    address = AddressTab()


class ProfileForm(FormModel):
    tabs: ProfileTabs = Field(default_factory=ProfileTabs, input_type='layout')


data = parse_nested_form_data(dict(await request.form()))
result = ProfileForm.validate(data, submit_url='/profile')
city_error = result.errors.get('city')
email = result.data['email']
```

After:

```python
class ProfileForm(FormModel):
    contact: Contact = Field(title='Contact')
    address: Address = Field(title='Address')


html_out = await render_form_html_async(ProfileForm, layout='tabbed', submit_url='/profile')
result = ProfileForm.validate(await request.form(), submit_url='/profile', layout='tabbed')
city_error = result.errors.get('address', {}).get('city')
email = result.data['contact']['email']
```

**Data changes shape:** each sub-form's values arrive under its field name
(`result.data["contact"]["email"]`, not `result.data["email"]`). Update everything that reads
`result.data`, saves it, or pre-fills `form_data`, and pre-fill with the same nested shape:
`form_data={"contact": {"email": ...}}`. Saved records may need a migration or a mapping layer.

## Behaviour changes worth checking after any upgrade

- A fresh form now starts from the field defaults; code that passed defaults in `form_data` by
  hand can drop them.
- Inputs are inferred from more types (`date`, `Enum`, `Literal`, `EmailStr`, `AnyUrl`,
  `Optional`). Hand-built `ui_options={"choices": [...]}` for an `Enum` field can be removed.
- Validator messages are shown without Pydantic's "Value error, " prefix; update tests that
  assert the old text.
- A checkbox that defaults to `True` now validates as `False` when unticked.
- An optional sub-form left blank validates to `None` instead of failing.
