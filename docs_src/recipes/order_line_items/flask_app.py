from flask import Flask, request
from models import OrderForm

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
FORM_OPTIONS = {'submit_url': '/orders/new', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/orders/new')
def new_order():
    return render_form_html(OrderForm, **FORM_OPTIONS)


@app.post('/orders/new')
def create_order():
    result = OrderForm.validate(request.form, **FORM_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    order = result.instance
    lines = len(order.items)
    total = sum(item.total for item in order.items)
    return html(t'<p>Order for {order.customer}: {lines} lines, {total:.2f} in total.</p>')
