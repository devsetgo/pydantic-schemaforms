from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import ContactForm, live_validator
from page import feedback, page

from pydantic_schemaforms import html, render_form_html_async, validation_response_headers

app = FastAPI()


@app.get('/contact', response_class=HTMLResponse)
async def show_contact():
    return page(await render_form_html_async(ContactForm, submit_url='/contact'))


@app.post('/contact', response_class=HTMLResponse)
async def submit_contact(request: Request):
    result = ContactForm.validate(await request.form(), submit_url='/contact')
    if not result.is_valid:
        return page(await result.render_with_errors_async())
    name = result.data['name']
    return html(t'<p>Thanks, {name}!</p>')


@app.post('/validate/{field_name}', response_class=HTMLResponse)
async def validate_field(field_name: str, request: Request):
    value = str((await request.form()).get(field_name, ''))
    result = live_validator.validate_field(field_name, value)
    return HTMLResponse(
        feedback(result.errors),
        headers=validation_response_headers(field_name, result.is_valid),
    )
