from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, html, render_form_html_async


class SignupForm(FormModel):
    name: str = Field(title='Full name', min_length=2)
    email: str = Field(title='Email', ui_element='email')


app = FastAPI()
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/signup', response_class=HTMLResponse)
async def show_signup():
    return await render_form_html_async(SignupForm, submit_url='/signup', **RENDER_OPTIONS)


@app.post('/signup', response_class=HTMLResponse)
async def submit_signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup', **RENDER_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()

    name = result.data['name']
    return html(t'<p>Thanks for signing up, {name}!</p>')
