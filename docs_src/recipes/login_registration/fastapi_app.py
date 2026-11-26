from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from models import LoginForm, RegistrationForm, SignInCodeForm

from pydantic_schemaforms import render_form_html_async

app = FastAPI()
ASSETS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


def authenticate(username: str, password: str) -> bool:
    return False  # look the user up and verify the password hash


def code_matches(code: str) -> bool:
    return False  # check the code against the user's authenticator secret


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
    return RedirectResponse('/login/code', status_code=303)


@app.get('/login/code', response_class=HTMLResponse)
async def show_code():
    return await render_form_html_async(SignInCodeForm, submit_url='/login/code', **ASSETS)


@app.post('/login/code', response_class=HTMLResponse)
async def check_code(request: Request):
    result = SignInCodeForm.validate(await request.form(), submit_url='/login/code', **ASSETS)
    if not result.is_valid:
        return await result.render_with_errors_async()
    if not code_matches(result.data['code']):
        return await render_form_html_async(
            SignInCodeForm,
            errors={'code': 'That code is wrong or has expired'},
            submit_url='/login/code',
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
