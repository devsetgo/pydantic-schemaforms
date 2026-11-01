<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/pydantic-schemaforms/references/complex-forms.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
# Complex forms reference

A bigger form is several `FormModel`s nested as fields of a parent `FormModel`. There are no
wrapper or layout classes: a sub-form is an ordinary typed field, and how the groups are shown is
one `layout=` argument.

## Sub-forms and repeating sub-forms

```python
from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)


class Pet(FormModel):
    name: str = Field(title='Name')
    age: int = Field(0, title='Age', ge=0)


class ProfileForm(FormModel):
    nickname: str = Field(title='Nickname')
    address: Address = Field(title='Home address')
    pets: list[Pet] = Field(
        default_factory=list,
        title='Pets',
        max_length=5,
        ui_add_button_label='Add a pet',
        ui_item_title_template='{name}',
    )
```

- **`address: Address`** renders the `Address` fields as a titled section, inputs named
  `address.street`, `address.city`. Its own rules apply as usual, and it can nest further.
- **`pets: list[Pet]`** renders one card per item with Add and Remove buttons. `min_length` and
  `max_length` on the list count items, are checked on submit, and are enforced by the buttons.
  With `min_length=n`, an empty list starts with `n` blank items.
- **Never hand-write add/remove JavaScript**; a `list[FormModel]` field already does it.

| Option on a sub-form field | Effect |
|---|---|
| `title="..."` | Section heading, and the tab, column, panel or step title in grouped layouts |
| `ui_help_text="..."` | Help text under the heading |
| `ui_collapsible=True` | Under `layout="vertical"`, a collapsible section |
| `ui_collapsed=True` | Starts collapsed; opens by itself when it contains an error |
| `ui_order=n` | Position among the groups (lower first) |
| `ui_step_title="..."` | Step title under `layout="wizard"` only |

| Option on a `list[FormModel]` field | Effect |
|---|---|
| `ui_add_button_label="Add a pet"` | Text of the Add button |
| `ui_item_title_template="{name}"` | Each card's title, filled from the item's fields; `{index}` is the 1-based position |
| `ui_collapsible_items=False` | Plain cards instead of collapsible ones |
| `ui_items_expanded=False` | Cards start collapsed |

These are `Field()` arguments, not `ui_options` keys.

## Optional sub-forms

A sub-form typed `Address | None` can be left empty. Its inputs aren't required in the browser,
and when every one of them comes back blank or still at its default, `validate()` returns `None`
for it. Once the user fills in part of it, the whole sub-form is validated. A common use is a
billing address that's only needed when it differs:

```python
from typing import Literal, Self

from pydantic import EmailStr, model_validator

from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)
    postal_code: str = Field(title='Postal code', pattern=r'^[A-Za-z0-9 -]{3,10}$')
    country: Literal['US', 'CA', 'GB', 'FR', 'DE'] = Field('US', title='Country')


class CheckoutForm(FormModel):
    email: EmailStr = Field(title='Email for the receipt')
    shipping: Address = Field(title='Shipping address')
    billing_same_as_shipping: bool = Field(True, title='Bill to the shipping address')
    billing: Address | None = Field(None, title='Billing address', ui_collapsed=True)

    @model_validator(mode='after')
    def billing_given(self) -> Self:
        if not self.billing_same_as_shipping and self.billing is None:
            raise ValueError('Enter a billing address, or bill to the shipping address')
        return self

    def billing_address(self) -> Address:
        return self.shipping if self.billing_same_as_shipping else self.billing
```

## Layouts

Pass `layout=` to `render_form_html()` **and** to `validate()`, so a failed submit comes back in
the same layout.

| `layout=` | Result |
|---|---|
| `"vertical"` (default) | The form's own fields, then each sub-form as a titled section |
| `"tabbed"` | One tab for the form's own fields, then one tab per sub-form |
| `"accordion"` | The same groups as collapsible panels, the first open |
| `"side-by-side"` | The same groups as columns in one row |
| `"wizard"` | The same groups as steps with Back and Next |

- The grouped layouts arrange **sub-forms**. On a form with only plain fields they raise
  `ValueError`: split the fields into nested models, one per section.
- The first group holds the parent's own plain fields, titled by
  `model_config = {"title": "..."}` or "General". Each sub-form (or list of sub-forms) is one
  group, in declaration order unless `ui_order` says otherwise.
- After a failed submit, the first tab, panel or step with an error opens.
- Use `tabbed` or `accordion` for long forms with distinct sections (account, profile,
  preferences), `side-by-side` for a few short groups, `wizard` for a flow filled in order
  (signup, onboarding, checkout, applications).

```python
from pydantic_schemaforms import Field, FormModel


class Contact(FormModel):
    email: str = Field(title='Email', ui_element='email')
    phone: str = Field('', title='Phone', ui_element='tel')


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City')


class Preferences(FormModel):
    newsletter: bool = Field(False, title='Send me the newsletter')
    language: str = Field(
        'en', title='Language', ui_element='select', ui_options={'choices': ['en', 'fr', 'de']}
    )


class AccountForm(FormModel):
    model_config = {'title': 'About you'}

    name: str = Field(title='Full name')
    contact: Contact = Field(title='Contact details')
    address: Address = Field(title='Address')
    preferences: Preferences = Field(title='Preferences', ui_order=1)
```

## Groups and widths without nesting

For a heading over some fields, or two fields on a row, keep the model flat instead of adding a
sub-form: `Field(ui_group="Address", ui_cols=6)`. `ui_group` gathers fields with the same title
into a section (or a tab, panel, column or step under a grouped layout), and `result.data` stays
flat. `ui_cols` (1-12) makes consecutive fields share a row, under every style.
`ui_group_collapsible=True`, `ui_group_collapsed=True` and `ui_group_show_when={...}` apply to the
whole group and go on any one of its fields. Neither option applies inside `model_list` items.

## Wizard

```python
from models import AccountForm

from pydantic_schemaforms import render_form_html

form_html = render_form_html(
    AccountForm,
    layout='wizard',
    wizard_options={'next_label': 'Continue', 'linear': True},
    submit_url='/account',
)
```

- **One `<form>`, one POST.** The routes are the same as for any layout. Never build a route per
  step or keep step state in the session.
- **Next checks the current step** with the browser's own validation; the server checks
  everything on submit. The submit button is on the last step. Without JavaScript, all steps show
  stacked.
- `wizard_options`: `linear` (default `True`; `False` lets the progress header jump to any step),
  `show_progress` (`True`), `back_label` (`"Back"`), `next_label` (`"Next"`). An unknown key
  raises `ValueError`. Pass it to `validate()` too.

## Nested data and errors

`result.data` is nested exactly like the model:

```python
{
    'nickname': 'mk',
    'address': {'street': '1 Main', 'city': 'Paris'},
    'pets': [{'name': 'Rex', 'age': 3}],
}
```

`result.errors` is nested the same way, so an error sits at the same path as its value:

```python
{
    'address': {'city': 'String should have at least 2 characters'},
    'pets': {1: {'age': 'Must be 0 or greater'}},
}
```

- A list's errors are keyed by item index; only failing items appear.
- A message about a whole list or sub-form (such as too many items) is a string at its key, or
  under `"_errors"` there when its children also have errors. Form-wide messages are under the
  top-level `"_errors"`.
- A node can be a string or a dict, so read defensively:
  `result.errors.get("address", {}).get("city")` only works when `address` has child errors.
- `result.error_list()` gives a flat `[{"loc": ["pets", 1, "age"], "msg": "..."}]` list for logs
  and API responses.
- Pre-fill nested forms with nested data:
  `form_data={"address": {"city": "Paris"}, "pets": [{"name": "Rex"}]}`.
- Inputs are named `address.city` and `pets[0].name` in the HTML. The library builds and decodes
  those names; **never construct or parse them in app code**, and never decode the form yourself
  before `validate()`.
