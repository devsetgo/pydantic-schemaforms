<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/pydantic-schemaforms/references/security.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
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

```python
import hmac
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from pydantic_schemaforms import Field, FormModel, html, render_form_html_async


class TransferForm(FormModel):
    to_account: str = Field(title='To account')
    amount: int = Field(title='Amount', ge=1)


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='change-me')  # load from your settings


def issue_csrf_token(request: Request) -> str:
    token = secrets.token_urlsafe(32)
    request.session['csrf_token'] = token
    return token


def csrf_token_is_valid(request: Request, submitted: object) -> bool:
    expected = request.session.get('csrf_token')
    return bool(expected and isinstance(submitted, str)) and hmac.compare_digest(
        expected, submitted
    )


def form_options(request: Request) -> dict:
    return {
        'submit_url': '/transfer',
        'csrf_mode': 'required-provider',
        'csrf_token_provider': issue_csrf_token(request),
        'include_framework_assets': True,
        'asset_mode': 'cdn',
    }


@app.get('/transfer', response_class=HTMLResponse)
async def show_transfer(request: Request):
    return await render_form_html_async(TransferForm, **form_options(request))


@app.post('/transfer', response_class=HTMLResponse)
async def submit_transfer(request: Request):
    form = await request.form()
    if not csrf_token_is_valid(request, form.get('csrf_token')):
        raise HTTPException(status_code=403, detail='Invalid or expired form; reload the page.')

    result = TransferForm.validate(form, **form_options(request))
    if not result.is_valid:
        return await result.render_with_errors_async()

    amount = result.data['amount']
    return html(t'<p>Transferred {amount}.</p>')
```

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

```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ALLOWED_TYPES, MAX_BYTES, UploadForm
from starlette.datastructures import UploadFile

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/upload', 'include_framework_assets': True, 'asset_mode': 'cdn'}


def check_upload(upload: object) -> tuple[str | None, bytes]:
    if not isinstance(upload, UploadFile) or not upload.filename:
        return 'Choose a file to upload', b''
    if Path(upload.filename).suffix.lower() not in ALLOWED_TYPES:
        return 'Upload a PDF or Word document', b''
    content = upload.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        return 'The file is larger than 5 MB', b''
    return None, content


@app.get('/upload', response_class=HTMLResponse)
async def show_upload():
    return await render_form_html_async(UploadForm, **FORM_OPTIONS)


@app.post('/upload', response_class=HTMLResponse)
async def upload(request: Request):
    form = await request.form()
    result = UploadForm.validate(form, **FORM_OPTIONS)
    file_error, content = check_upload(form.get('document'))
    if not result.is_valid or file_error:
        errors = {**result.errors, **({'document': file_error} if file_error else {})}
        return await render_form_html_async(
            UploadForm, form_data={'title': form.get('title')}, errors=errors, **FORM_OPTIONS
        )
    size = len(content)
    return html(t'<p>Stored "{result.data["title"]}" ({size} bytes).</p>')
```

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
