import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ApplicationForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
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


def load_draft(request: Request) -> dict | None:
    return DRAFTS.get(request.cookies.get('draft_id', ''))


@app.get('/apply', response_class=HTMLResponse)
async def show_application(request: Request):
    return await render_form_html_async(ApplicationForm, draft=load_draft(request), **FORM)


@app.post('/apply', response_class=HTMLResponse)
async def apply(request: Request):
    draft_id = request.cookies.get('draft_id') or secrets.token_urlsafe(16)
    result = ApplicationForm.validate_step(await request.form(), draft=load_draft(request), **FORM)
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
    response = HTMLResponse(await result.render_async())
    response.set_cookie('draft_id', draft_id, httponly=True, samesite='lax')
    return response
