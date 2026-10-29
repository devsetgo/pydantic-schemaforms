from flask import Flask, request
from models import CheckoutForm

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
FORM_OPTIONS = {'submit_url': '/checkout', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/checkout')
def show_checkout():
    return render_form_html(CheckoutForm, **FORM_OPTIONS)


@app.post('/checkout')
def checkout():
    result = CheckoutForm.validate(request.form, **FORM_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    billing = result.instance.billing_address()
    return html(t'<p>Billing {billing.street}, {billing.city}.</p>')
