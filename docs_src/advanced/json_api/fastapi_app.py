from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ContactForm

from pydantic_schemaforms import html, render_form_html_async

ContactSchema = ContactForm.as_api_model()  # same fields and rules, no ui_* settings
app = FastAPI()


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return await render_form_html_async(ContactForm, submit_url='/contact')


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), submit_url='/contact')
    if not result.is_valid:
        return await result.render_with_errors_async()
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')


@app.post('/api/contact', response_model=ContactSchema)
async def api_contact(contact: ContactSchema):
    return contact
