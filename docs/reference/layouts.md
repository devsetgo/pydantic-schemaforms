# Layouts

The values of `layout=` and their options. The [Layouts chapter](../tutorial/layouts.md)
of the tutorial introduces them with a complete example.

## `layout=`

Pass `layout=` to `render_form_html()` (or `render_form_html_async()`,
`FormModel.render_form()`) and to `FormModel.validate()`, so
`render_with_errors()` comes back the same way.

| Value | What you get |
|---|---|
| `"vertical"` (default) | The form's own fields first, then each sub-form as a titled section |
| `"tabbed"` | One tab for the form's own fields, then one tab per sub-form |
| `"side-by-side"` | The same groups as columns in one row |
| `"accordion"` | The same groups as collapsible panels, the first one open |
| `"wizard"` | The same groups as steps, one at a time, with Back and Next |

An unknown value raises `ValueError`.

## Groups

Fields sharing a `ui_group` title also form a group, so a flat model can use these
layouts too; see [Group fields without nesting](../tutorial/layouts.md#group-fields-without-nesting).

The grouped layouts (`tabbed`, `side-by-side`, `accordion`, `wizard`) arrange
**groups**:

- The first group holds the form's own fields (those that aren't sub-forms).
  Its title is the model's title, `model_config = {"title": "About you"}`, or
  "General" when the model has none. It is left out when there are no such
  fields.
- Then one group per sub-form field: a field typed as a `FormModel`, a `list`
  of one, or a composite such as a [data table](../advanced/data-tables.md).

A form without any sub-form field has nothing to group, so a grouped layout
raises a `ValueError` asking you to split it into nested models.

After a failed submit, the first tab, panel or step with an error is the one
that opens, and the error summary at the top of the form stays visible.

## Sub-form field options

Set these on the sub-form field:

| Option | Effect |
|---|---|
| `title="..."` | Section heading, tab label, column heading, panel title or step title |
| `ui_step_title="..."` | Step title under `layout="wizard"` only, instead of `title` |
| `ui_help_text="..."` | Help text under the section heading |
| `ui_order=n` | Position among the groups (lower first); groups otherwise follow declaration order |
| `ui_collapsible=True` | Under `vertical`, render the section as a collapsible panel |
| `ui_collapsed=True` | Start the collapsible section closed; it opens when it contains an error |

## `wizard_options=`

Pass to `render_form_html()` and `validate()` together with `layout="wizard"`:

| Key | Default | Effect |
|---|---|---|
| `linear` | `True` | Clicking a later step in the progress header checks the steps in between. `False` lets the header jump to any step. |
| `show_progress` | `True` | `False` hides the progress header. |
| `back_label` | `"Back"` | Text of the Back button |
| `next_label` | `"Next"` | Text of the Next button |

An unknown key raises `ValueError`.

How the wizard behaves:

- **One form, one POST.** Every step is in the same `<form>` and only hidden in
  the browser. No state is kept between steps.
- **Next checks the current step** with the browser's own validation
  (`required`, `minlength`, `min`/`max`, `pattern`, `type="email"`, ...) and
  stays put if something fails. Back never checks. Enter in a field moves to
  the next step instead of submitting.
- **The submit button is on the last step.** The server validates everything,
  including rules the browser can't check.
- **After a failed submit**, the first step with an error opens and every step
  with an error is marked in the progress header.
- **Without JavaScript**, every step is shown, stacked under its title, with
  the submit button at the end.

## Repeating sub-form options

A `list` of a `FormModel` renders as cards with Add and Remove buttons. Set
these on the list field:

| Option | Effect |
|---|---|
| `min_length=n` / `max_length=n` | Fewest and most items, checked in the browser and on the server. With `min_length`, an empty list starts with that many blank items. |
| `ui_add_button_label="..."` | Text of the Add button |
| `ui_item_title_template="..."` | Each card's title, filled from the item's fields (`"{name}"`); `{index}` is the 1-based position |
| `ui_collapsible_items=False` | Plain cards instead of collapsible ones |
| `ui_items_expanded=False` | Start the cards collapsed |

## Other layout tools

- [Layout Primitives](../advanced/layout-primitives.md): grids, cards and tabs
  for arranging HTML you've already rendered.
- [Plugin Hooks and Custom Composites](../advanced/plugin-hooks.md): register
  a renderer for a control of your own.
