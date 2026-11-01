from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, render_form_html_async


class Address(FormModel):
    city: str = Field(title='City', min_length=2)


class OrderForm(FormModel):
    name: str = Field(title='Full name', min_length=2)
    size: str = Field(
        title='Size',
        ui_element='select',
        ui_options={
            'choices': [{'value': 's', 'label': 'Small'}, {'value': 'l', 'label': 'Large'}]
        },
    )
    gift: bool = Field(False, title='Gift wrap')
    address: Address = Field(title='Delivery address')


app = FastAPI()
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/order', response_class=HTMLResponse)
async def show_order():
    return await render_form_html_async(OrderForm, submit_url='/order', **RENDER_OPTIONS)


@app.post('/order', response_class=HTMLResponse)
async def submit_order(request: Request):
    result = OrderForm.validate(await request.form(), submit_url='/order', **RENDER_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()

    return OrderForm.render_display(result.data, edit_urls={'address': '/order'}, **RENDER_OPTIONS)
