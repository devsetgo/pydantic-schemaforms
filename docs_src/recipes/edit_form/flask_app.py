from flask import Flask, abort, redirect, request
from models import PRODUCTS, ProductForm

from pydantic_schemaforms import render_form_html

app = Flask(__name__)
ASSETS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


def load_product(product_id: int) -> dict:
    if product_id not in PRODUCTS:
        abort(404)
    return PRODUCTS[product_id]


@app.get('/products/<int:product_id>/edit')
def edit_product(product_id: int):
    row = load_product(product_id)
    return render_form_html(
        ProductForm,
        form_data={name: row[name] for name in ProductForm.model_fields},
        submit_url=f'/products/{product_id}/edit',
        **ASSETS,
    )


@app.post('/products/<int:product_id>/edit')
def save_product(product_id: int):
    row = load_product(product_id)
    result = ProductForm.validate(request.form, submit_url=f'/products/{product_id}/edit', **ASSETS)
    if not result.is_valid:
        return result.render_with_errors()
    row.update(result.data)
    return redirect(f'/products/{product_id}/edit', code=303)
