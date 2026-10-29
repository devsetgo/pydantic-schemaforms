from flask import Flask, request

from pydantic_schemaforms import Field, FormModel, html, render_form_html


class SignupForm(FormModel):
    name: str = Field(title='Full name', min_length=2)
    email: str = Field(title='Email', ui_element='email')


app = Flask(__name__)
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/signup')
def show_signup():
    return render_form_html(SignupForm, submit_url='/signup', **RENDER_OPTIONS)


@app.post('/signup')
def submit_signup():
    result = SignupForm.validate(request.form, submit_url='/signup', **RENDER_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()

    name = result.data['name']
    return html(t'<p>Thanks for signing up, {name}!</p>')
