from flask import Flask, redirect, request
from models import LoginForm, RegistrationForm, SignInCodeForm

from pydantic_schemaforms import render_form_html

app = Flask(__name__)
ASSETS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


def authenticate(username: str, password: str) -> bool:
    return False  # look the user up and verify the password hash


def code_matches(code: str) -> bool:
    return False  # check the code against the user's authenticator secret


def username_taken(username: str) -> bool:
    return username == 'admin'


def create_user(data: dict) -> None: ...  # hash the password, then store the user


@app.get('/login')
def show_login():
    return render_form_html(LoginForm, submit_url='/login', **ASSETS)


@app.post('/login')
def login():
    result = LoginForm.validate(request.form, submit_url='/login', **ASSETS)
    if not result.is_valid:
        return result.render_with_errors()
    if not authenticate(result.data['username'], result.data['password']):
        return render_form_html(
            LoginForm,
            form_data={'username': result.data['username']},
            errors={'_errors': 'Wrong username or password'},
            submit_url='/login',
            **ASSETS,
        )
    return redirect('/login/code', code=303)


@app.get('/login/code')
def show_code():
    return render_form_html(SignInCodeForm, submit_url='/login/code', **ASSETS)


@app.post('/login/code')
def check_code():
    result = SignInCodeForm.validate(request.form, submit_url='/login/code', **ASSETS)
    if not result.is_valid:
        return result.render_with_errors()
    if not code_matches(result.data['code']):
        return render_form_html(
            SignInCodeForm,
            errors={'code': 'That code is wrong or has expired'},
            submit_url='/login/code',
            **ASSETS,
        )
    return redirect('/', code=303)


@app.get('/register')
def show_register():
    return render_form_html(RegistrationForm, submit_url='/register', **ASSETS)


@app.post('/register')
def register():
    result = RegistrationForm.validate(request.form, submit_url='/register', **ASSETS)
    if not result.is_valid:
        return result.render_with_errors()
    if username_taken(result.data['username']):
        return render_form_html(
            RegistrationForm,
            form_data=request.form.to_dict(),
            errors={'username': 'That username is taken'},
            submit_url='/register',
            **ASSETS,
        )
    create_user(result.data)
    return redirect('/login', code=303)
