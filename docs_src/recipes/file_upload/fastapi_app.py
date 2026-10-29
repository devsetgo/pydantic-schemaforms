from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ALLOWED_TYPES, MAX_BYTES, UploadForm
from starlette.datastructures import UploadFile

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/upload', 'include_framework_assets': True, 'asset_mode': 'cdn'}


def check_upload(upload: object) -> tuple[str | None, bytes]:
    if not isinstance(upload, UploadFile) or not upload.filename:
        return 'Choose a file to upload', b''
    if Path(upload.filename).suffix.lower() not in ALLOWED_TYPES:
        return 'Upload a PDF or Word document', b''
    content = upload.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        return 'The file is larger than 5 MB', b''
    return None, content


@app.get('/upload', response_class=HTMLResponse)
async def show_upload():
    return await render_form_html_async(UploadForm, **FORM_OPTIONS)


@app.post('/upload', response_class=HTMLResponse)
async def upload(request: Request):
    form = await request.form()
    result = UploadForm.validate(form, **FORM_OPTIONS)
    file_error, content = check_upload(form.get('document'))
    if not result.is_valid or file_error:
        errors = {**result.errors, **({'document': file_error} if file_error else {})}
        return await render_form_html_async(
            UploadForm, form_data={'title': form.get('title')}, errors=errors, **FORM_OPTIONS
        )
    size = len(content)
    return html(t'<p>Stored "{result.data["title"]}" ({size} bytes).</p>')
