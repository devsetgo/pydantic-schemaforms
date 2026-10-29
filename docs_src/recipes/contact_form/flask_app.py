from flask import Flask, request
from models import ContactForm

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
FORM_OPTIONS = {'submit_url': '/contact', 'include_framework_assets': True, 'asset_mode': 'cdn'}


def send_message(data: dict) -> None: ...  # email it, store it, open a ticket


@app.get('/contact')
def show_contact():
    return render_form_html(ContactForm, **FORM_OPTIONS)


@app.post('/contact')
def submit_contact():
    result = ContactForm.validate(request.form, **FORM_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    if not result.data['website']:
        send_message(result.data)
    name = result.data['name']
    return html(t'<p>Thanks, {name}. We will get back to you soon.</p>')
