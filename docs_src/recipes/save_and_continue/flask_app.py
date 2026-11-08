import secrets

from flask import Flask, make_response, request
from models import ApplicationForm
from werkzeug.datastructures import CombinedMultiDict

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
FORM = {
    'submit_url': '/apply',
    'layout': 'wizard',
    'wizard_options': {'save_steps': True, 'review_step': True},
    'include_framework_assets': True,
    'asset_mode': 'cdn',
}

# Stand-ins for a real app's session (or database) and file store.
DRAFTS: dict[str, dict] = {}
FILES: dict[str, bytes] = {}


def load_draft() -> dict | None:
    return DRAFTS.get(request.cookies.get('draft_id', ''))


@app.get('/apply')
def show_application():
    return render_form_html(ApplicationForm, draft=load_draft(), **FORM)


@app.post('/apply')
def apply():
    draft_id = request.cookies.get('draft_id') or secrets.token_urlsafe(16)
    form_data = CombinedMultiDict([request.form, request.files])
    result = ApplicationForm.validate_step(form_data, draft=load_draft(), **FORM)
    if result.is_complete:
        DRAFTS.pop(draft_id, None)
        name = result.data['about_you']['full_name']
        city = result.data['availability']['city']
        return html(t'<p>Thanks, {name}. We will be in touch about {city}.</p>')
    if result.is_valid:
        for upload in result.files:
            upload.ref = secrets.token_hex(8)
            FILES[upload.ref] = upload.read()
        DRAFTS[draft_id] = result.draft
    response = make_response(result.render())
    response.set_cookie('draft_id', draft_id, httponly=True, samesite='lax')
    return response
