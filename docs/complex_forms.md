# Composing complex forms

A complex form is several `FormModel`s nested inside a parent `FormModel`.
There are no wrapper or layout classes to learn: a sub-form is an ordinary
typed field, and how the sub-forms are presented (stacked sections, tabs,
columns, or accordion panels) is one `layout=` choice when you render.

```python
from pydantic_schemaforms import Field, FormModel, render_form_html


class Contact(FormModel):
    email: str = Field(title='Email', ui_element='email')
    phone: str = Field('', title='Phone', ui_element='tel')


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)


class Pet(FormModel):
    name: str = Field(title='Pet name')
    age: int = Field(0, title='Age', ge=0)


class ProfileForm(FormModel):
    nickname: str = Field(title='Nickname')  # a plain field
    contact: Contact = Field(title='Contact details')  # a sub-form
    address: Address = Field(title='Home address', ui_collapsible=True)  # a collapsible sub-form
    pets: list[Pet] = Field(
        default_factory=list, title='Pets', min_length=1
    )  # a repeating sub-form


html = render_form_html(ProfileForm, layout='tabbed', submit_url='/profile')
# tabs: General | Contact details | Home address | Pets
```

Every level is just a `FormModel` field, so nesting goes as deep as you need:
a sub-form can contain a list of sub-forms whose items contain sub-forms.

## Presentation: `layout=`

The model's structure never changes to get a different look. Pass `layout=` to
`render_form_html()`, `FormModel.render_form()`, or `FormModel.validate()` (so
`render_with_errors()` re-renders the same way).

| `layout=` | What you get |
|---|---|
| `"vertical"` (default) | Plain fields first, each sub-form as a titled section below them |
| `"tabbed"` | A "General" tab for the parent's plain fields, then one tab per sub-form |
| `"side-by-side"` | The same groups as columns in one row |
| `"accordion"` | The same groups as collapsible panels, first one open |
| `"wizard"` | The same groups as steps, one at a time, with Back/Next (see "Step wizard" below) |

The grouped layouts need sub-forms to group. Asking for `layout="tabbed"` on a
form with no sub-form fields raises a `ValueError` telling you to split it
into nested models.

### Order

Tabs, sections, columns, and panels follow field declaration order. To change
the order without moving code, give fields a `ui_order` (lower first):

```python
class ProfileForm(FormModel):
    contact: Contact = Field(title='Contact details', ui_order=2)
    address: Address = Field(title='Home address', ui_order=1)
```

The "General" group holding the parent's own plain fields always comes first.
Its heading is the model's title (`model_config = {"title": "About you"}`), or
"General" when the model has none. If you want a different first tab, move
those plain fields into their own sub-form.

### Per-sub-form options

Set these on the sub-form field itself:

| Option | Effect |
|---|---|
| `title="..."` | Section heading, tab label, column heading, panel title, or step title |
| `ui_step_title="..."` | Step title under `layout="wizard"` only, overriding `title=` |
| `ui_help_text="..."` | Help text shown under the section heading |
| `ui_collapsible=True` | Render the section as a collapsible `<details>` (vertical layout) |
| `ui_collapsed=True` | Start collapsed; it opens automatically when it contains an error |
| `ui_order=n` | Position among the groups |

### Step wizard

`layout="wizard"` shows the same groups one at a time: a progress header naming
each step, then Back/Next buttons, with the form's submit button on the last
step only.

```python
class SignupForm(FormModel):
    nickname: str = Field(title='Nickname')  # step 1 ("General")
    contact: Contact = Field(title='Contact details', ui_step_title='How to reach you')
    address: Address = Field(title='Home address')


html = render_form_html(SignupForm, layout='wizard', submit_url='/signup')
```

- **One form, one POST.** Every step is rendered into the same `<form>` and only
  hidden in the browser, so the route is the same as for any other layout:
  `SignupForm.validate(await request.form(), submit_url="/signup", layout="wizard")`.
  No session state is kept between steps.
- **Next checks the current step.** Next runs the browser's own validation
  (`required`, `minlength`, `min`/`max`, `pattern`, `type="email"`, ...) on the
  current step's inputs and stays put if one fails. Back never validates.
  Enter in a field moves to the next step instead of submitting early. Pydantic
  still validates everything on submit, including rules the browser can't check.
- **Errors.** After a failed submit, `render_with_errors()` opens the first step
  with an error and marks every step with an error in the progress header. The
  error summary at the top of the form stays visible on every step.
- **No JavaScript.** All steps show stacked, each under its title, with the
  normal submit button at the end.

Options go in `wizard_options=` (also accepted by `validate()` for
`render_with_errors()`):

| Key | Default | Effect |
|---|---|---|
| `linear` | `True` | Clicking a later step in the header validates the steps in between. `False` lets the header jump to any step. |
| `show_progress` | `True` | `False` hides the progress header. |
| `back_label` / `next_label` | `"Back"` / `"Next"` | Button text |

An unknown key raises `ValueError`.

A `list[SubModel]` field is rendered as a repeating sub-form with add/remove
buttons automatically; `ui_element="model_list"` is optional. See the
"Repeating sub-forms" recipe in `docs/recipes.md` for its own options.

## JSON in, JSON out

Your route hands the raw request form to `validate()`. The result's `data` is
nested exactly like the model, and `errors` is nested exactly like `data`.

```python
@app.post('/profile')
async def profile_post(request: Request):
    result = ProfileForm.validate(await request.form(), submit_url='/profile', layout='tabbed')
    if result.is_valid:
        save(result.data)  # or result.instance, the validated ProfileForm
        return RedirectResponse('/done', status_code=303)
    return HTMLResponse(result.render_with_errors())
```

Flask is the same: `ProfileForm.validate(request.form, submit_url="/profile")`.

`validate()` accepts:

- the request form object (Starlette/FastAPI `FormData`, Werkzeug/Flask `MultiDict`), keeping repeated values such as multi-selects and checkbox groups as lists;
- a list of `(name, value)` pairs;
- a nested dict, for example a JSON API body (`ProfileForm.validate(await request.json())`).

### `result.data`

```python
{
    'nickname': 'mk',
    'contact': {'email': 'a@b.c', 'phone': ''},
    'address': {'street': '1 Main', 'city': 'Xy'},
    'pets': [{'name': 'Rex', 'age': 3}, {'name': 'Tux', 'age': 1}],
}
```

Values keep their Python types (`date`, `Decimal`, `SecretStr`, ...). Keys
that are not fields of the model, such as a CSRF token, are dropped at every
level. `result.instance` is the validated model instance itself.

### `result.errors`

```python
{
    'address': {'city': 'String should have at least 2 characters'},
    'pets': {1: {'age': 'Must be 0 or greater'}},
}
```

The rules:

- Look up an error at the same path as its value: `result.errors["address"]["city"]`, `result.errors["pets"][1]["age"]`.
- A list's errors are a dict keyed by item index. Only failing items appear. JSON serialises the keys as strings (`"1"`).
- A message about a whole list or sub-form (for example `min_length=1` on `pets`) is a plain string when there are no item errors (`{"pets": "List should have at least 1 item after validation, not 0"}`), and sits under the reserved key `"_errors"` when there are (`{"pets": {"_errors": "...", 0: {...}}}`).
- Form-wide messages, such as those raised by a `@model_validator`, are under the top-level `"_errors"` key. Use the same key for your own form-level message: `render_form_html(..., errors={"_errors": "Session expired"})`.

For a flat list instead, `result.error_list()` returns
`[{"loc": ["pets", 1, "age"], "msg": "Must be 0 or greater"}, ...]`, which is
handy for API responses and logging.

On `render_with_errors()`, every message is shown next to its input, the
first tab or panel that contains an error is the one opened, and the summary
at the top reads like "Pet #2 — Age: Must be 0 or greater".

### Wire format (internal)

HTML inputs need a string `name`, so the library names nested inputs
`contact.email` and `pets[0].name`, and decodes them back for you. You should
never need to build or parse these names. If you are testing a route with a
raw POST, these are the names to send.

## Upgrading

Version 26.4.1 removed the older ways of combining forms. Using any of them
raises `FormLayoutRemovedError` whose message contains these steps.

| Removed | Replacement |
|---|---|
| `TabbedLayout`, `VerticalLayout`, `HorizontalLayout` wrapper classes | Nested `FormModel` fields plus `layout="tabbed"` / `"vertical"` / `"side-by-side"` |
| `ListLayout(Item, ...)` | `items: list[Item] = Field(default_factory=list, title="Items")` |
| `SectionDesign(section_title=..., ...)` | `Field(title=..., ui_help_text=..., ui_collapsible=True)` on the sub-form field |
| `FormDesign(...)` | Arguments to `render_form_html(...)` / `render_form_page(...)` and your page template |
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
