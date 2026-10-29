from pydantic_schemaforms import Field, FormModel, render_form_html


class SignupForm(FormModel):
    name: str = Field(title='Full name')
    email: str = Field(title='Email', ui_element='email')


bootstrap_html = render_form_html(SignupForm, submit_url='/signup')
material_html = render_form_html(SignupForm, framework='material', submit_url='/signup')
plain_html = render_form_html(SignupForm, framework='none', submit_url='/signup')
