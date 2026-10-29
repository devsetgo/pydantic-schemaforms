from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from models import PRODUCTS, ProductForm

from pydantic_schemaforms import render_form_html_async

app = FastAPI()
ASSETS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


def load_product(product_id: int) -> dict:
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404)
    return PRODUCTS[product_id]


@app.get('/products/{product_id}/edit', response_class=HTMLResponse)
async def edit_product(product_id: int):
    row = load_product(product_id)
    return await render_form_html_async(
        ProductForm,
        form_data={name: row[name] for name in ProductForm.model_fields},
        submit_url=f'/products/{product_id}/edit',
        **ASSETS,
    )


@app.post('/products/{product_id}/edit', response_class=HTMLResponse)
async def save_product(product_id: int, request: Request):
    row = load_product(product_id)
    result = ProductForm.validate(
        await request.form(), submit_url=f'/products/{product_id}/edit', **ASSETS
    )
    if not result.is_valid:
        return await result.render_with_errors_async()
    row.update(result.data)
    return RedirectResponse(f'/products/{product_id}/edit', status_code=303)
