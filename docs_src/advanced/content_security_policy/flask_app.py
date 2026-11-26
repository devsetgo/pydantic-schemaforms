import secrets
from contextlib import ExitStack

from flask import Flask, g, request
from models import ContactForm

from pydantic_schemaforms import csp_nonces, html

POLICY = "default-src 'self'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'"
app = Flask(__name__)


@app.before_request
def open_nonce_block():
    g.csp_nonce = secrets.token_urlsafe(16)  # also for tags in your own templates
    g.csp_block = ExitStack()
    g.csp_block.enter_context(csp_nonces(script_nonce=g.csp_nonce, style_nonce=g.csp_nonce))


@app.after_request
def add_policy(response):
    response.headers['Content-Security-Policy'] = POLICY.format(nonce=g.csp_nonce)
    return response


@app.teardown_request
def close_nonce_block(_error):
    g.pop('csp_block').close()


@app.get('/contact')
def show_contact():
    return ContactForm.render_form(submit_url='/contact')


@app.post('/contact')
def submit_contact():
    result = ContactForm.validate(request.form, submit_url='/contact')
    if not result.is_valid:
        return result.render_with_errors()
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')
