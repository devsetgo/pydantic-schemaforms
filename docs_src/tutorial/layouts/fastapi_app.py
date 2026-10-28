from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import AccountForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'layout': 'tabbed', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/account', response_class=HTMLResponse)
async def show_account():
    return await render_form_html_async(AccountForm, submit_url='/account', **FORM_OPTIONS)


@app.post('/account', response_class=HTMLResponse)
async def save_account(request: Request):
    result = AccountForm.validate(await request.form(), submit_url='/account', **FORM_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    name = result.data['name']
    return html(t'<p>Saved {name}.</p>')
