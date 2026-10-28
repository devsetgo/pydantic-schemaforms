from flask import Flask

from pydantic_schemaforms import Field, FormModel, render_form_html


class SignupForm(FormModel):
    name: str = Field(title='Full name')
    email: str = Field(title='Email', ui_element='email')


app = Flask(__name__)


@app.get('/signup')
def show_signup():
    return render_form_html(
        SignupForm,
        submit_url='/signup',
        include_framework_assets=True,
        asset_mode='cdn',
    )
