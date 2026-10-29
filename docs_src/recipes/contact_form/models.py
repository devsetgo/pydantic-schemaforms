from typing import Literal

from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel


class ContactForm(FormModel):
    name: str = Field(title='Your name', min_length=2, ui_autofocus=True)
    email: EmailStr = Field(title='Email')
    topic: Literal['Question', 'Feedback', 'Bug report'] = Field('Question', title='Topic')
    message: str = Field(title='Message', min_length=10, max_length=2000, ui_element='textarea')
    website: str = Field('', ui_element='honeypot')  # hidden; only bots fill it in
