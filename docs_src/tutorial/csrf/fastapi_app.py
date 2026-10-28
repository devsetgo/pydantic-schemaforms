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
    return bool(expected and isinstance(submitted, str)) and hmac.compare_digest(expected, submitted)


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
