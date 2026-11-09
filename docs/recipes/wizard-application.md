# Multi-Step Application (Wizard)

A job application in four steps: about you, the position, past jobs and a
cover letter. It is one form and one POST; the wizard only shows it a step at
a time.

```python title="models.py"
--8<-- "docs_src/recipes/wizard_application/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/wizard_application/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/wizard_application/flask_app.py"
    ```

## How it works

- **Each sub-form is a step**, titled by its field's `title`, in the order the
  fields are declared. The repeating `experience` list is a step of its own.
- **`layout="wizard"` is passed to `validate()` too**, so a failed submit
  comes back as a wizard, opened at the first step with an error.
- **Next checks the current step** in the browser before moving on, and the
  server checks everything on submit.
- **`wizard_options`** renames the Next button here; it can also rename Back,
  hide the progress header or let users jump between steps. See
  [Layouts](../tutorial/layouts.md#wizard).
- **`"review_step": True`** adds a last step that shows every answer, grouped
  by step, with an Edit button for each. The submit button is on that step.
- **The consent box has no default**, so it's required: the form can't be
  sent without it.

Since no state is kept between steps, there is nothing to store in a session,
and the browser's back button and a page reload behave like on any form.

For fuller wizards, each showing different features, see
[Wizard Examples](wizard-examples.md). Its job application goes further than
this recipe: a sign-in page, each step saved on the server, a resume upload,
and an edit page that marks what changed.
