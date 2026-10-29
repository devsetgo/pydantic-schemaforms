from flask import Flask, request
from models import SignupForm, rules

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)


@app.get('/signup')
def show_signup():
    return render_form_html(SignupForm, submit_url='/signup')


@app.post('/signup')
def submit_signup():
    result = SignupForm.validate(request.form, submit_url='/signup')
    rules_ok, rule_errors = rules.validate(result.original_data)
    if not (result.is_valid and rules_ok):
        return result.render_with_errors(errors={**rule_errors, **result.errors})
    username = result.data['username']
    return html(t'<p>Welcome, {username}!</p>')
