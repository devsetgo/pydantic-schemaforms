from flask import Flask, request
from models import ApplicationForm

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
FORM_OPTIONS = {
    'submit_url': '/apply',
    'layout': 'wizard',
    'wizard_options': {'next_label': 'Continue'},
    'include_framework_assets': True,
    'asset_mode': 'cdn',
}


@app.get('/apply')
def show_application():
    return render_form_html(ApplicationForm, **FORM_OPTIONS)


@app.post('/apply')
def apply():
    result = ApplicationForm.validate(request.form, **FORM_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    name = result.data['applicant']['full_name']
    role = result.data['position']['role']
    return html(t'<p>Thanks, {name}. We received your application for {role}.</p>')
