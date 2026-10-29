# Login and Registration

A login form and a registration form, with the checks that only your app can
make (is the password right? is the username free?) shown in the form like
any other error.

```python title="models.py"
--8<-- "docs_src/recipes/login_registration/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/login_registration/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/login_registration/flask_app.py"
    ```

## How it works

- **The confirmation must match.** `passwords_match` reads the password from
  `info.data` and puts its error under the confirmation field.
- **The terms box must be ticked.** `validate_default=True` makes Pydantic run
  `terms_accepted` even when the box is left unticked (and so not submitted),
  so the user sees your message instead of nothing.
- **The username is cleaned up first.** `mode="before"` lowercases and trims
  it before `pattern` checks it.
- **Errors from your own checks** go through `render_form_html()`'s
  `errors=`: `{"username": "..."}` shows under that field, and `"_errors"`
  shows a message for the whole form in the summary at the top. Pass
  `form_data=` so the user's input stays filled in. The login form only puts
  back the username, never the password.
- **After success, redirect** (303) so reloading the page doesn't send the
  form again.

!!! warning "Before going live"

    Store password hashes, never passwords (use a library such as `argon2-cffi`
    or `bcrypt`). Protect both forms with a CSRF token once users are logged
    in; see [CSRF Protection](../tutorial/csrf.md).
