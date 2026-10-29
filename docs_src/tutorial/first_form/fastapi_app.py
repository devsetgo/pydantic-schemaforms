from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, render_form_html_async


class SignupForm(FormModel):
    name: str = Field(title='Full name')
    email: str = Field(title='Email', ui_element='email')


app = FastAPI()


@app.get('/signup', response_class=HTMLResponse)
async def show_signup():
    return await render_form_html_async(
        SignupForm,
        submit_url='/signup',
        include_framework_assets=True,
        asset_mode='cdn',
    )
