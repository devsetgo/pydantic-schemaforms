# Save and Continue (Wizard)

A three-step application that saves each step on the server as it goes: about
you, a resume upload and availability. A user can stop after any step and
come back to the same place. Unlike the
[Multi-Step Application](wizard-application.md), each step is its own page and
its own POST.

```python title="models.py"
--8<-- "docs_src/recipes/save_and_continue/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/save_and_continue/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/save_and_continue/flask_app.py"
    ```

## How it works

- **`"save_steps": True`** in `wizard_options` renders only the current step.
  Back, Next and the progress header are real submit buttons, so it works
  without JavaScript and with CSRF like any form.
- **`validate_step()` replaces `validate()`.** It checks only the step just
  submitted and returns a `WizardStepResult`. Pass it the same render options
  as the form, and `draft=` with what you saved last time.
- **`result.draft` is yours to store.** It is a small JSON-safe dict. Save it
  as it is (session, database, signed cookie) and pass it back as `draft=` on
  the next request, including the GET, so the user resumes where they left
  off. The example keeps it in a dict keyed by a cookie; a real app uses its
  session or database.
- **`"review_step": True`** adds a final step, rendered from the saved draft,
  that shows every answer with an Edit button per step. Submit on it is the
  final submit, so the route needs no other change.
- **`result.render()` shows what comes next**: the next step, or the same step
  with its errors. Save the draft only when `result.is_valid`.
- **On the last step, Submit checks the whole model.** `result.is_complete` is
  then `True` and `result.data` is the validated data. An error in an earlier
  step reopens that step.
- **Back never blocks.** It keeps the step if it is valid and drops invalid
  input on the step being left. The header goes back the same way, and goes
  forward only to steps already reached.
- **A file is uploaded on its own step.** `result.files` holds the
  `UploadedFile`s from that step. Store the content, and set
  `upload.ref` to your own id before reading `result.draft`. The draft keeps
  the file's name, type, size and `ref`, not its content. In later steps and in
  the final `result.data`, the field is a `SavedFile` with those details;
  its `read()` raises, so fetch the content by `ref` from where you stored it.
  Coming back to the step and leaving the input empty keeps the saved file.
- **A later step can be prefilled.** Change `result.data` before
  `result.render()` and before reading `result.draft`, for example to fill a
  field from an answer given on an earlier step.
- **Start from existing values with `form_data=`.** To edit a saved record,
  or to open every step with demo answers, pass the values as `form_data=` on
  the GET and as `data=` to `result.render()`. The steps saved in the draft
  go on top of them.
- **The draft must come from `result.draft`.** Anything else raises
  `ValueError`, and `draft=` without `save_steps` raises `TypeError`.

HTMX per step is not supported yet; each step is a full page load. See
[Layouts](../tutorial/layouts.md#save-each-step) for the short version.
