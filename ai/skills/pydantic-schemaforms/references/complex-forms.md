# Complex forms reference

A bigger form is several `FormModel`s nested as fields of a parent `FormModel`. There are no
wrapper or layout classes: a sub-form is an ordinary typed field, and how the groups are shown is
one `layout=` argument.

## Sub-forms and repeating sub-forms

<!-- INCLUDE-CODE: docs_src/tutorial/nested/models.py -->

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

<!-- INCLUDE-CODE: docs_src/recipes/address_subform/models.py -->

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

<!-- INCLUDE-CODE: docs_src/tutorial/layouts/models.py -->

## Groups and widths without nesting

For a heading over some fields, or two fields on a row, keep the model flat instead of adding a
sub-form: `Field(ui_group="Address", ui_cols=6)`. `ui_group` gathers fields with the same title
into a section (or a tab, panel, column or step under a grouped layout), and `result.data` stays
flat. `ui_cols` (1-12) makes consecutive fields share a row, under every style.
`ui_group_collapsible=True`, `ui_group_collapsed=True` and `ui_group_show_when={...}` apply to the
whole group and go on any one of its fields. `ui_group` and `ui_cols` don't apply inside
`model_list` items; `ui_group_show_when` there hides each field on its own.

## Wizard

<!-- INCLUDE-CODE: docs_src/tutorial/layouts/wizard.py -->

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
