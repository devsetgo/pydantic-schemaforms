from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import CheckoutForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/checkout', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/checkout', response_class=HTMLResponse)
async def show_checkout():
    return await render_form_html_async(CheckoutForm, **FORM_OPTIONS)


@app.post('/checkout', response_class=HTMLResponse)
async def checkout(request: Request):
    result = CheckoutForm.validate(await request.form(), **FORM_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    billing = result.instance.billing_address()
    return html(t'<p>Billing {billing.street}, {billing.city}.</p>')
