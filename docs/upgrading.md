# Upgrading

Breaking changes that need more than a one-line fix, with the steps to
upgrade. Every release's changes are in the [Release Notes](release-notes.md).

## Next release: one way to build a form

The builder API, the React and Vue adapters and `@form_validator` are
removed. Importing a removed name raises an `ImportError` that names its
replacement.

| Removed | Replacement |
|---|---|
| `FormBuilder`, `AutoFormBuilder`, `create_form_from_model` | A `FormModel` class. For fields known only at runtime, `create_model(..., __base__=FormModel)`; see [Forms Built at Runtime](advanced/runtime-forms.md). |
| `create_login_form`, `create_registration_form`, `create_contact_form` | The [Login and Registration](recipes/login-registration.md) and [Contact Form](recipes/contact-form.md) recipes |
| `render_form_page`, `FormIntegration`, `handle_form`, `handle_form_async` | `render_form_html()`, `FormModel.validate()` and `result.render_with_errors()`; see [Handling Submissions](tutorial/handling-submissions.md) |
| `@form_validator` (it never ran) | Pydantic's `@model_validator(mode="after")`, whose message lands in the form-wide `"_errors"`, or `FormValidator.add_cross_field_rule()` |
| `ReactJSONSchemaFormAdapter`, `VueFormulateAdapter` | `FormModel.get_pydantic_json_schema()` or `as_api_model()`; see [JSON API and JSON Schema](advanced/json-api.md) |
| `DataTableLayout` inputs named `rows[i].col`, `csv_file` | The same names under the embedding field: `employees.rows[i].col`, `employees.csv_file`. Only code that reads these keys directly changes. |

## To 26.4.1: nested forms

Version 26.4.1 removed the older ways of combining forms. Using any of them
raises `FormLayoutRemovedError` whose message contains these steps.

| Removed | Replacement |
|---|---|
| `TabbedLayout`, `VerticalLayout`, `HorizontalLayout` wrapper classes | Nested `FormModel` fields plus `layout="tabbed"` / `"vertical"` / `"side-by-side"` |
| `ListLayout(Item, ...)` | `items: list[Item] = Field(default_factory=list, title="Items")` |
| `SectionDesign(section_title=..., ...)` | `Field(title=..., ui_help_text=..., ui_collapsible=True)` on the sub-form field |
| `FormDesign(...)` | Arguments to `render_form_html(...)` and your page template |
| `parse_nested_form_data(...)` in routes | Pass the request form straight to `validate()` |
| `validate(..., flatten=True)` | Removed; `result.data` is always nested |
| Error keys like `"pets[0].name"` | `result.errors["pets"][0]["name"]` |
| `errors={"general": ...}` | `errors={"_errors": ...}` |
| `layout="tabbed"` on a flat form (keyword-guessed tabs) | Split the form into sub-forms; each becomes a tab |
| Several `input_type="layout"` fields auto-tabbing | `layout="tabbed"` on the parent |

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


data = parse_nested_form_data(await request.form())
result = ProfileForm.validate(data, submit_url='/profile')
city_error = result.errors.get('city')
```

After:

```python
class ProfileForm(FormModel):
    contact: Contact = Field(title='Contact')
    address: Address = Field(title='Address')


html = render_form_html(ProfileForm, layout='tabbed', submit_url='/profile')
result = ProfileForm.validate(await request.form(), submit_url='/profile', layout='tabbed')
city_error = result.errors.get('address', {}).get('city')
```

Submitted data and saved records change shape too: the contact fields now
arrive under `data["contact"]` instead of at the top level.
