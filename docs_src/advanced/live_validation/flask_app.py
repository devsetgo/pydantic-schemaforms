from flask import Flask, request
from models import ContactForm, live_validator
from page import feedback, page

from pydantic_schemaforms import html, render_form_html, validation_response_headers

app = Flask(__name__)


@app.get('/contact')
def show_contact():
    return page(render_form_html(ContactForm, submit_url='/contact'))


@app.post('/contact')
def submit_contact():
    result = ContactForm.validate(request.form, submit_url='/contact')
    if not result.is_valid:
        return page(result.render_with_errors())
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')


@app.post('/validate/<field_name>')
def validate_field(field_name: str):
    value = request.form.get(field_name, '')
    result = live_validator.validate_field(field_name, value)
    return feedback(result.errors), validation_response_headers(field_name, result.is_valid)
