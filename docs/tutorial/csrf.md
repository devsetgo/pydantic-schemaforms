# CSRF Protection

If your site logs users in with a cookie, any other website can make a
visitor's browser post to your forms, and the browser sends the cookie along.
That's cross-site request forgery (CSRF). The defense is a secret token: your
form carries it in a hidden field, and your route refuses any submission that
doesn't send it back.

pydantic-schemaforms renders the hidden field. Your app creates the token,
keeps it in the session and checks it, because only your app knows its
sessions.

=== "FastAPI"

    ```python
    --8<-- "docs_src/tutorial/csrf/fastapi_app.py"
    ```

=== "Flask"

    ```python
    --8<-- "docs_src/tutorial/csrf/flask_app.py"
    ```

## How it works

1. **`issue_csrf_token()`** makes a random token and stores it in the session.
2. **`csrf_mode="required-provider"`** with **`csrf_token_provider=`** renders
   it as a hidden `csrf_token` field. The `required-provider` mode refuses to
   render without a token, so a missing one is caught at once instead of
   silently shipping an unprotected form.
3. **The POST route checks the token first**, with `hmac.compare_digest` so
   the comparison takes the same time whatever the input, and answers 403
   when it doesn't match.
4. **`validate()` gets the same options**, so a re-rendered form carries a new
   token. The token isn't a model field, so it never appears in `result.data`.

## When you need it

You need CSRF protection for forms that change something (create, update,
delete, buy) on a site that identifies users by cookie. You usually don't for
APIs that authenticate with an `Authorization` header instead of cookies, or
for read-only pages.

## Checklist

- Keep the session secret (`secret_key`) out of your code, and long and random.
- Serve the site over HTTPS.
- Never log the token values.
- Use `required-provider`; `csrf_field_name=` changes the hidden field's name
  if your app already uses a different one.

??? note "Other CSRF modes"

    `csrf_mode` also accepts `"off"` (the default: no hidden field) and
    `"field-only"`, which renders the field without requiring a provider. It
    exists for debugging and is only allowed together with `debug=True`.
    `CSRFMode.REQUIRED_PROVIDER` and the other enum values work the same as
    the strings.

That's the end of the tutorial. You can now build, validate, arrange, style
and protect forms. From here:

- the [Recipes](../recipes/index.md) have complete forms to copy;
- the [Advanced User Guide](../advanced/index.md) covers live validation,
  data tables, JSON APIs and more;
- the [Reference](../reference/index.md) lists every input, layout and option.
