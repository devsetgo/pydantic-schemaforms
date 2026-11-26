import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ContactForm

from pydantic_schemaforms import csp_nonces, html

POLICY = "default-src 'self'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'"
app = FastAPI()


@app.middleware('http')
async def content_security_policy(request: Request, call_next):
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce  # for <script>/<style> tags in your own templates
    with csp_nonces(script_nonce=nonce, style_nonce=nonce):
        response = await call_next(request)
    response.headers['Content-Security-Policy'] = POLICY.format(nonce=nonce)
    return response


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return await ContactForm.render_form_async(submit_url='/contact')


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), submit_url='/contact')
    if not result.is_valid:
        return await result.render_with_errors_async()
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')
