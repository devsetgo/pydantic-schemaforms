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
