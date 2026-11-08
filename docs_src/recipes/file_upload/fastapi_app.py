from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import UploadForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/upload', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/upload', response_class=HTMLResponse)
async def show_upload():
    return await render_form_html_async(UploadForm, **FORM_OPTIONS)


@app.post('/upload', response_class=HTMLResponse)
async def upload(request: Request):
    result = UploadForm.validate(await request.form(), **FORM_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    size = len(result.data['document'].read())
    return html(t'<p>Stored "{result.data["title"]}" ({size} bytes).</p>')
