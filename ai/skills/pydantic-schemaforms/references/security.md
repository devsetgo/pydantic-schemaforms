# Security reference

## HTML built around submitted data

The library escapes everything it renders. HTML that app code writes around submitted values
must be escaped too, even after `validate()` succeeded: a valid `str` can be
`<script>alert(1)</script>`.

```python
from pydantic_schemaforms import SafeHTML, html

name = result.data['name']
page = html(t'<p>Thanks, {name}!</p>')  # name is escaped

form = SafeHTML(form_html)  # library output: trusted, not escaped again
page = html(t'<main>{form}</main>')
```

- `html()` takes a t-string (`t"..."`, Python 3.14) and returns a `SafeHTML` (a `str`).
- Never build HTML from user data with an f-string, `.format()` or `+`.
- Wrap only HTML you trust in `SafeHTML(...)`: library output, or your own constant markup.
- In Jinja templates, `{{ form_html | safe }}` for the library's output only; everything else stays
  auto-escaped.

## CSRF

Forms that change something on a site with cookie logins need a CSRF token. The library renders
the hidden field; the app creates the token, keeps it in the session and checks it.

<!-- INCLUDE-CODE: docs_src/tutorial/csrf/fastapi_app.py -->

- `csrf_mode="required-provider"` with `csrf_token_provider=` (the token or a function returning
  it) renders a hidden `csrf_token` field and refuses to render without a token.
  `csrf_field_name=` renames the field.
- Check the token **before** validating, with `hmac.compare_digest`, and answer 403 (or re-render
  with `errors={"_errors": "..."}`) when it doesn't match.
- Pass the same options to `validate()`, so a re-rendered form gets a new token.
- Never declare the token as a model field. `validate()` drops unknown keys.
- `csrf_mode="field-only"` is for debugging and raises `ValueError` unless `debug=True`. Don't
  generate it for real routes.
- Keep the session secret out of code; serve the site over HTTPS.

## Spam protection

- **Honeypot:** `website: str = Field('', ui_element='honeypot')` renders an input people can't
  see. When it comes back filled in, answer as if the submission worked and drop it.
- **Captcha:** a self-hosted arithmetic question. Declare only the answer field; the signed token
  is added for you. Check it in the route before validating:

```python
from pydantic_schemaforms import Field, FormModel, verify_captcha


class SignupForm(FormModel):
    captcha_answer: str = Field('', ui_element='captcha', ui_options={'secret_key': CAPTCHA_SECRET})


# in the POST route:
form = await request.form()
if not verify_captcha(
    token=form.get('captcha_answer_token'),
    answer=form.get('captcha_answer'),
    secret_key=CAPTCHA_SECRET,
):
    ...  # re-render with errors={"captcha_answer": "Wrong answer"}; a new question is generated
```

Load `CAPTCHA_SECRET` from the app's configuration, never a literal in code.

## File uploads

<!-- INCLUDE-CODE: docs_src/recipes/file_upload/fastapi_app.py -->

- Type the file field `Any`; `validate()` passes the upload object through. In FastAPI it's
  `starlette.datastructures.UploadFile` (not `fastapi.UploadFile`, so `isinstance` against the
  FastAPI class fails). In Flask, validate `CombinedMultiDict([request.form, request.files])`;
  the file is a `FileStorage`, and set `app.config["MAX_CONTENT_LENGTH"]`.
- Check that a file was chosen (`upload.filename`), its extension and its size, reading at most
  one byte more than the limit. `accept` in `ui_options` only filters the file picker.
- Store files outside the web root under names you generate; never show a file name in HTML
  without `html(t'...')`.

## Accessibility

Every built-in input is tested with axe-core against WCAG 2.0–2.2 A and AA: each control has a
label, help and errors are linked with `aria-describedby`, and invalid fields get
`aria-invalid="true"`. Keep it that way:

- Give every field a meaningful `title`; it's the label.
- Don't remove or rewrite the `id`/`aria-*` attributes in rendered HTML.
- The page around the form is the app's job: `<html lang>`, one `<h1>`, `<main>`, contrast.
- Don't call the app WCAG, ADA or Section 508 compliant: the library is tested, not certified.
