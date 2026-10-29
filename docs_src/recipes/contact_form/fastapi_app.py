from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ContactForm

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()
FORM_OPTIONS = {'submit_url': '/contact', 'include_framework_assets': True, 'asset_mode': 'cdn'}


def send_message(data: dict) -> None: ...  # email it, store it, open a ticket


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return await render_form_html_async(ContactForm, **FORM_OPTIONS)


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), **FORM_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    if not result.data['website']:
        send_message(result.data)
    name = result.data['name']
    return html(t'<p>Thanks, {name}. We will get back to you soon.</p>')
