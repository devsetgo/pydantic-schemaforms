from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ApplicationForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {
    'submit_url': '/apply',
    'layout': 'wizard',
    'wizard_options': {'next_label': 'Continue'},
    'include_framework_assets': True,
    'asset_mode': 'cdn',
}


@app.get('/apply', response_class=HTMLResponse)
async def show_application():
    return await render_form_html_async(ApplicationForm, **FORM_OPTIONS)


@app.post('/apply', response_class=HTMLResponse)
async def apply(request: Request):
    result = ApplicationForm.validate(await request.form(), **FORM_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    name = result.data['applicant']['full_name']
    role = result.data['position']['role']
    return html(t'<p>Thanks, {name}. We received your application for {role}.</p>')
