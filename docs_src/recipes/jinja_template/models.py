from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel


class SignupForm(FormModel):
    name: str = Field(title='Full name', min_length=2, ui_autofocus=True)
    email: EmailStr = Field(title='Email')
