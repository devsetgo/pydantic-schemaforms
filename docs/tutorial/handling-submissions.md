# Handling Submissions

Add a POST route that validates what was submitted. If anything is wrong, the
form comes back with the user's values kept and an error under each field
that failed. If everything is valid, you get the data as a plain dictionary.

=== "FastAPI"

    ```python hl_lines="21-28"
    --8<-- "docs_src/tutorial/submissions/fastapi_app.py"
    ```

=== "Flask"

    ```python hl_lines="20-27"
    --8<-- "docs_src/tutorial/submissions/flask_app.py"
    ```

Try submitting the form with a one-letter name: it comes back with "String
should have at least 2 characters" under the name, and your email still filled
in.

## `validate()`

`SignupForm.validate()` takes the **raw request form**, `await request.form()`
in FastAPI or `request.form` in Flask, exactly as the framework gives it to
you. There is nothing to convert first.

It returns a `ValidationResult`:

| Attribute | What it holds |
|---|---|
| `result.is_valid` | `True` when every field passed |
| `result.data` | The validated values as a dictionary, shaped like the model: `{"name": "Ada", "email": "ada@example.com"}` |
| `result.errors` | The error messages, keyed the same way: `{"name": "String should have at least 2 characters"}` |
| `result.render_with_errors()` | The form again, with the submitted values and the error messages |

`submit_url` and any render options passed to `validate()` are remembered, so
`render_with_errors()` needs no arguments. Use
`render_with_errors_async()` in async routes.

## Showing submitted values safely

Anything the user typed is untrusted, even after it passes validation:
`validate()` checks types and constraints, not whether a value is safe to put
in HTML. Build HTML around submitted values with the library's `html()`
function and a **t-string** (`t"..."`, new in Python 3.14):

```python
name = result.data["name"]
return html(t"<p>Thanks for signing up, {name}!</p>")
```

`html()` escapes every `{value}` in the t-string, so a name like
`<script>alert(1)</script>` is shown as text, not run. An f-string or
`.format()` would insert it as live HTML. This is the same mechanism the
library uses for every piece of HTML it generates.

Next: [Fields and Inputs](fields.md).
