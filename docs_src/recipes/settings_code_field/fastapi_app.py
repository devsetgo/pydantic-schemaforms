import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ServiceSettings

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/settings', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/settings', response_class=HTMLResponse)
async def show_settings():
    return await render_form_html_async(ServiceSettings, **FORM_OPTIONS)


@app.post('/settings', response_class=HTMLResponse)
async def save_settings(request: Request):
    result = ServiceSettings.validate(await request.form(), **FORM_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    replicas = json.loads(result.data['config']).get('replicas', 1)
    return html(t'<p>Saved {result.data["name"]} with {replicas} replicas.</p>')
