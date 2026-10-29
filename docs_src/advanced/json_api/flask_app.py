from flask import Flask, request
from models import ContactForm

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)


@app.get('/contact')
def show_contact():
    return render_form_html(ContactForm, submit_url='/contact')


@app.post('/contact')
def submit_contact():
    result = ContactForm.validate(request.form, submit_url='/contact')
    if not result.is_valid:
        return result.render_with_errors()
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')


@app.post('/api/contact')
def api_contact():
    result = ContactForm.validate(request.get_json(silent=True) or {})
    if not result.is_valid:
        return {'errors': result.errors}, 422
    return result.data
