from flask import Flask, request
from models import MAX_BYTES, UploadForm
from werkzeug.datastructures import CombinedMultiDict

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_BYTES + 64 * 1024  # Flask refuses bigger requests
FORM_OPTIONS = {'submit_url': '/upload', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/upload')
def show_upload():
    return render_form_html(UploadForm, **FORM_OPTIONS)


@app.post('/upload')
def upload():
    result = UploadForm.validate(CombinedMultiDict([request.form, request.files]), **FORM_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    size = len(result.data['document'].read())
    return html(t'<p>Stored "{result.data["title"]}" ({size} bytes).</p>')
