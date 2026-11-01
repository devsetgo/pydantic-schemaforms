from flask import Flask, request

from pydantic_schemaforms import Field, FormModel, render_form_html


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


app = Flask(__name__)
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/order')
def show_order():
    return render_form_html(OrderForm, submit_url='/order', **RENDER_OPTIONS)


@app.post('/order')
def submit_order():
    result = OrderForm.validate(request.form, submit_url='/order', **RENDER_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()

    return OrderForm.render_display(result.data, edit_urls={'address': '/order'}, **RENDER_OPTIONS)
