from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, render_form_html_async


class ContactForm(FormModel):
    name: str = Field(title='Full name')
    contact: str = Field(
        'email',
        title='Contact me by',
        ui_element='radio',
        ui_options={
            'choices': [{'value': 'email', 'label': 'Email'}, {'value': 'phone', 'label': 'Phone'}]
        },
    )
    phone: str = Field(
        '',
        title='Phone number',
        ui_show_when={'field': 'contact', 'equals': 'phone', 'required': True},
    )


app = FastAPI()
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return await render_form_html_async(ContactForm, submit_url='/contact', **RENDER_OPTIONS)


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), submit_url='/contact', **RENDER_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    return ContactForm.render_display(result.data, **RENDER_OPTIONS)
