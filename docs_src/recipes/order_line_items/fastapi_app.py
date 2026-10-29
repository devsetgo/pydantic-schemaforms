from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import OrderForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/orders/new', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/orders/new', response_class=HTMLResponse)
async def new_order():
    return await render_form_html_async(OrderForm, **FORM_OPTIONS)


@app.post('/orders/new', response_class=HTMLResponse)
async def create_order(request: Request):
    result = OrderForm.validate(await request.form(), **FORM_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    order = result.instance
    lines = len(order.items)
    total = sum(item.total for item in order.items)
    return html(t'<p>Order for {order.customer}: {lines} lines, {total:.2f} in total.</p>')
