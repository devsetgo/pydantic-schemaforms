from flask import Flask, request

from pydantic_schemaforms import Field, FormModel, render_form_html


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


app = Flask(__name__)
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/contact')
def show_contact():
    return render_form_html(ContactForm, submit_url='/contact', **RENDER_OPTIONS)


@app.post('/contact')
def submit_contact():
    result = ContactForm.validate(request.form, submit_url='/contact', **RENDER_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    return ContactForm.render_display(result.data, **RENDER_OPTIONS)
