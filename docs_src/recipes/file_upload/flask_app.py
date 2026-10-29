from pathlib import Path

from flask import Flask, request
from models import ALLOWED_TYPES, MAX_BYTES, UploadForm
from werkzeug.datastructures import CombinedMultiDict, FileStorage

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_BYTES + 64 * 1024  # Flask refuses bigger requests
FORM_OPTIONS = {'submit_url': '/upload', 'include_framework_assets': True, 'asset_mode': 'cdn'}


def check_upload(upload: object) -> tuple[str | None, bytes]:
    if not isinstance(upload, FileStorage) or not upload.filename:
        return 'Choose a file to upload', b''
    if Path(upload.filename).suffix.lower() not in ALLOWED_TYPES:
        return 'Upload a PDF or Word document', b''
    content = upload.stream.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        return 'The file is larger than 5 MB', b''
    return None, content


@app.get('/upload')
def show_upload():
    return render_form_html(UploadForm, **FORM_OPTIONS)


@app.post('/upload')
def upload():
    result = UploadForm.validate(CombinedMultiDict([request.form, request.files]), **FORM_OPTIONS)
    file_error, content = check_upload(request.files.get('document'))
    if not result.is_valid or file_error:
        errors = {**result.errors, **({'document': file_error} if file_error else {})}
        return render_form_html(
            UploadForm,
            form_data={'title': request.form.get('title')},
            errors=errors,
            **FORM_OPTIONS,
        )
    size = len(content)
    return html(t'<p>Stored "{result.data["title"]}" ({size} bytes).</p>')
