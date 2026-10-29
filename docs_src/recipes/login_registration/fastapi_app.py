from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from models import LoginForm, RegistrationForm

from pydantic_schemaforms import render_form_html_async

app = FastAPI()
ASSETS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


def authenticate(username: str, password: str) -> bool:
    return False  # look the user up and verify the password hash


def username_taken(username: str) -> bool:
    return username == 'admin'


def create_user(data: dict) -> None: ...  # hash the password, then store the user


@app.get('/login', response_class=HTMLResponse)
async def show_login():
    return await render_form_html_async(LoginForm, submit_url='/login', **ASSETS)


@app.post('/login', response_class=HTMLResponse)
async def login(request: Request):
    result = LoginForm.validate(await request.form(), submit_url='/login', **ASSETS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    if not authenticate(result.data['username'], result.data['password']):
        return await render_form_html_async(
            LoginForm,
            form_data={'username': result.data['username']},
            errors={'_errors': 'Wrong username or password'},
            submit_url='/login',
            **ASSETS,
        )
    return RedirectResponse('/', status_code=303)


@app.get('/register', response_class=HTMLResponse)
async def show_register():
    return await render_form_html_async(RegistrationForm, submit_url='/register', **ASSETS)


@app.post('/register', response_class=HTMLResponse)
async def register(request: Request):
    form = await request.form()
    result = RegistrationForm.validate(form, submit_url='/register', **ASSETS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    if username_taken(result.data['username']):
        return await render_form_html_async(
            RegistrationForm,
            form_data=dict(form),
            errors={'username': 'That username is taken'},
            submit_url='/register',
            **ASSETS,
        )
    create_user(result.data)
    return RedirectResponse('/login', status_code=303)
