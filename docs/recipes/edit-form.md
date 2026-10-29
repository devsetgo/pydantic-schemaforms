# Edit Form from a Database Row

Show a saved record in a form, let the user change it, and save it back.

```python title="models.py"
--8<-- "docs_src/recipes/edit_form/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/edit_form/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/edit_form/flask_app.py"
    ```

## How it works

- **`form_data=`** fills the form. Pass the row's values as they are: dates,
  Enum members and numbers are shown correctly, so there's nothing to convert.
- **Only the form's fields are passed.** The row also has `id` and
  `created_by`, which the user must not edit. They are left out of
  `form_data`, and since they aren't fields of `ProductForm`, a request that
  sends them anyway can't change them: `validate()` ignores unknown keys.
- **`result.data`** has the same keys as the model, typed (`Status.archived`,
  `date(2026, 3, 1)`, `None` for a cleared date), ready to write back.

If your rows are ORM objects or Pydantic models, build the dictionary the same
way: `{name: getattr(row, name) for name in ProductForm.model_fields}`.
