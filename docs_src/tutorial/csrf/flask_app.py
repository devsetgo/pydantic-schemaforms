import hmac
import secrets

from flask import Flask, abort, request, session

from pydantic_schemaforms import Field, FormModel, html, render_form_html


class TransferForm(FormModel):
    to_account: str = Field(title='To account')
    amount: int = Field(title='Amount', ge=1)


app = Flask(__name__)
app.secret_key = 'change-me'  # load from your settings


def issue_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return token


def csrf_token_is_valid(submitted: object) -> bool:
    expected = session.get('csrf_token')
    return bool(expected and isinstance(submitted, str)) and hmac.compare_digest(expected, submitted)


def form_options() -> dict:
    return {
        'submit_url': '/transfer',
        'csrf_mode': 'required-provider',
        'csrf_token_provider': issue_csrf_token(),
        'include_framework_assets': True,
        'asset_mode': 'cdn',
    }


@app.get('/transfer')
def show_transfer():
    return render_form_html(TransferForm, **form_options())


@app.post('/transfer')
def submit_transfer():
    if not csrf_token_is_valid(request.form.get('csrf_token')):
        abort(403, 'Invalid or expired form; reload the page.')

    result = TransferForm.validate(request.form, **form_options())
    if not result.is_valid:
        return result.render_with_errors()

    amount = result.data['amount']
    return html(t'<p>Transferred {amount}.</p>')
