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
| `save_steps` | `False` | `True` makes each step its own page and POST, saved on the server. See [Saving each step](#saving-each-step). |
| `review_step` | `False` | `True` adds a final review step. A dict sets `title` (default `"Review"`) and `edit_label` (default `"Edit"`); any other key, or a non-text value, raises `ValueError`. See [Review step](#review-step). |

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

### Saving each step

With `wizard_options={"save_steps": True}`, only the current step's inputs are
rendered, with the progress header. Back, Next and the header's links are
submit buttons, so it works without JavaScript. The form's own submit button is
on the last step. Steps not reached yet are shown disabled in the header.

- **`draft=`** on `render_form_html()`, `render_form_html_async()` and
  `Model.render_form()` is the `result.draft` you saved. `None` starts at step
  1. It raises `TypeError` without `save_steps`.
- **`Model.validate_step(data, *, draft=None, **render_options)`** takes the
  request form, the saved draft and the same render options, and returns a
  `WizardStepResult`. It raises `ValueError` unless `layout="wizard"` and
  `save_steps` are set, or if `draft` was not produced by `result.draft`.
- **Next needs a valid step.** Back never blocks: it keeps the step if valid
  and drops invalid input on the step being left. A header jump back behaves
  like Back; forward goes only to steps already reached, and with `linear` it
  checks the current step first.
- **The final submit validates the whole model**, so `@model_validator` and
  cross-step checks run. An error in an earlier step reopens that step; a
  form-wide error stays on the last step.
- **`ui_show_when`** rules controlled by a field on another step render from
  the draft's data.

See [Rendering API](rendering-api.md#wizardstepresult) for the result and the
[Save and Continue recipe](../recipes/save-and-continue.md) for a full route.

### Review step

`wizard_options={"review_step": True}` adds a step after the last real one that
shows everything entered, read-only, in a section per step titled with the
step's title. Values are shown as `render_display()` shows them: option labels,
Yes/No for checkboxes, masked passwords, only the last four digits of card and
social security numbers, file names, and a `model_list` as a table. Fields
hidden by a `ui_show_when` rule are left out.

- **Edit** on a section goes back to that step. It is always allowed, also
  with `linear`.
- **The submit button is on the review step only.** Next on the last real step
  goes to the review.
- **One-POST wizard:** the browser fills the review from the live inputs each
  time it is reached, as plain text. Added or removed `model_list` items show
  up. The review adds no inputs, so the POST is unchanged. Without JavaScript
  the review shows the values the page was rendered with.
- **With `save_steps`:** the server renders the review from the saved draft,
  with no script. Edit buttons are submit buttons that jump back to the step.
  Submit on the review is the final submit: an error in a step reopens that
  step, and a form-wide `@model_validator` error shows on the review.
- **After a failed submit**, the wizard opens on the first step with an error,
  never on the review.

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
