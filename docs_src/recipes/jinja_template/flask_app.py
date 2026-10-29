from pathlib import Path

from flask import Flask, render_template, request
from models import SignupForm

from pydantic_schemaforms import render_form_html

app = Flask(__name__, template_folder=Path(__file__).parent / 'templates')


@app.get('/signup')
def show_signup():
    form_html = render_form_html(SignupForm, submit_url='/signup')
    return render_template('signup.html', form_html=form_html)


@app.post('/signup')
def signup():
    result = SignupForm.validate(request.form, submit_url='/signup')
    if not result.is_valid:
        return render_template('signup.html', form_html=result.render_with_errors()), 422
    form_html = render_form_html(SignupForm, submit_url='/signup')
    return render_template('signup.html', form_html=form_html, name=result.data['name'])
