from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models import SignupForm

from pydantic_schemaforms import render_form_html_async

app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')


@app.get('/signup', response_class=HTMLResponse)
async def show_signup(request: Request):
    form_html = await render_form_html_async(SignupForm, submit_url='/signup')
    return templates.TemplateResponse(request, 'signup.html', {'form_html': form_html})


@app.post('/signup', response_class=HTMLResponse)
async def signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup')
    if not result.is_valid:
        form_html = await result.render_with_errors_async()
        return templates.TemplateResponse(
            request, 'signup.html', {'form_html': form_html}, status_code=422
        )
    form_html = await render_form_html_async(SignupForm, submit_url='/signup')
    context = {'form_html': form_html, 'name': result.data['name']}
    return templates.TemplateResponse(request, 'signup.html', context)
