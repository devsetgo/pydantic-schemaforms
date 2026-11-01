# Layouts

Once a form has sub-forms, the same model can be shown as stacked sections,
tabs, columns, collapsible panels or a step-by-step wizard. The model doesn't
change: you pick the presentation with one `layout=` argument.

```python
--8<-- "docs_src/tutorial/layouts/models.py"
```

Pass the layout both when rendering and when validating, so a failed submit
comes back in the same layout:

=== "FastAPI"

    ```python hl_lines="8"
    --8<-- "docs_src/tutorial/layouts/fastapi_app.py"
    ```

=== "Flask"

    ```python hl_lines="7"
    --8<-- "docs_src/tutorial/layouts/flask_app.py"
    ```

## The layouts

| `layout=` | What you get |
|---|---|
| `"vertical"` (default) | The form's own fields first, then each sub-form as a titled section |
| `"tabbed"` | One tab for the form's own fields, then one tab per sub-form |
| `"accordion"` | The same groups as collapsible panels, the first one open |
| `"side-by-side"` | The same groups as columns in one row |
| `"wizard"` | The same groups as steps, one at a time, with Back and Next |

Each sub-form, and each repeating sub-form, is one group. The grouped
layouts need at least one sub-form; on a flat form they raise a `ValueError`
telling you to split it into nested models.

After a failed submit, the first tab, panel or step that contains an error is
the one that opens, and the error summary at the top stays visible.

## Group titles and order

- A sub-form's group is titled by its field's `title` ("Contact details").
- The first group holds the form's own fields (here, the name). Its title is
  the model's title, `model_config = {"title": "About you"}`, or "General"
  when the model has none.
- Groups follow the order the fields are declared in. `ui_order` changes it
  without moving code: `ui_order=1` puts Preferences right after the first group.

## Group fields without nesting

Sub-forms are right when the data is really nested. For "these four fields under a
heading" or "first and last name on one row", keep the model flat:

```python
--8<-- "docs_src/tutorial/layouts/field_groups.py"
```

`result.data` stays flat, with no `address` key: groups only affect how the form looks.

- **`ui_group`** gathers fields with the same title into one section, placed where
  its first field is declared. Under `layout="tabbed"`, `"accordion"`, `"side-by-side"`
  or `"wizard"`, each group becomes its own tab, panel, column or step, alongside any
  sub-forms.
- **`ui_cols`** is a width out of 12. Consecutive fields share a row until they pass 12,
  and a field with no `ui_cols` starts a new row. Below 768px wide, every field is full
  width. It works the same under all three styles.
- **`ui_group_collapsible=True`** lets the user fold the group away, and
  **`ui_group_collapsed=True`** starts it closed; a group with an error always opens.
  These apply in `layout="vertical"`, since a tab or panel already folds.
- **`ui_group_show_when`** hides the whole group, heading included, using the same rules
  as `ui_show_when`. Its fields need defaults. Under `"tabbed"`, `"accordion"` and
  `"wizard"`, the tab, panel or step stays in place, empty.

The `ui_group_*` options go on any one field of the group. `render_display()` shows groups
as titled sections too, without the column widths. Inside a `model_list` item, `ui_group`
and `ui_cols` have no effect, since each item already arranges its own fields;
`ui_group_show_when` still hides each of the group's fields.

## Wizard

`layout="wizard"` shows one group at a time with a progress header and Back
and Next buttons; the submit button is on the last step.

```python
--8<-- "docs_src/tutorial/layouts/wizard.py"
```

- **One form, one POST.** All steps are in the same `<form>`, so the routes
  are exactly the ones above with `layout="wizard"`. No state is kept between
  steps.
- **Next checks the current step** with the browser's own validation
  (`required`, `min`, `pattern`, ...) and stays put if something is wrong.
  Pydantic still validates everything on submit.
- **Without JavaScript**, every step is shown, stacked, with a normal submit button.

`wizard_options` sets the button labels, hides the progress header, or lets
the header jump to any step (`"linear": False`). `ui_step_title` on a
sub-form field gives its step a different title from its `title`. All the
options are in the [Layouts reference](../reference/layouts.md).

??? note "Layouts for content that isn't a form field"

    The library also has layout building blocks, such as a grid, tabs and
    cards, for arranging HTML you've already rendered. They're for page
    composition, not for forms; see
    [Layout Primitives](../advanced/layout-primitives.md).

Next: [Styling](styling.md).
