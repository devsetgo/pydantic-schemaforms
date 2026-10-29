import json

from flask import Flask, request
from models import ServiceSettings

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
FORM_OPTIONS = {'submit_url': '/settings', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/settings')
def show_settings():
    return render_form_html(ServiceSettings, **FORM_OPTIONS)


@app.post('/settings')
def save_settings():
    result = ServiceSettings.validate(request.form, **FORM_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    replicas = json.loads(result.data['config']).get('replicas', 1)
    return html(t'<p>Saved {result.data["name"]} with {replicas} replicas.</p>')
