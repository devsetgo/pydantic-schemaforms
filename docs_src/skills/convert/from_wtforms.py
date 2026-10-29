from datetime import date
from typing import Literal

from pydantic import EmailStr, ValidationInfo, field_validator

from pydantic_schemaforms import Field, FormModel


# Converted from:
#   class SignupForm(FlaskForm):
#       username = StringField('Username', [DataRequired(), Length(min=3, max=25)])
#       email = EmailField('Email', [DataRequired(), Email()])
#       password = PasswordField('Password', [DataRequired(), Length(min=12)])
#       confirm = PasswordField('Repeat password', [EqualTo('password')])
#       plan = SelectField('Plan', choices=[('free', 'Free'), ('pro', 'Pro')])
#       birthday = DateField('Birthday', [Optional()])
#       newsletter = BooleanField('Send me the newsletter')
class SignupForm(FormModel):
    username: str = Field(title='Username', min_length=3, max_length=25)
    email: EmailStr = Field(title='Email')
    password: str = Field(title='Password', ui_element='password', min_length=12)
    confirm: str = Field(title='Repeat password', ui_element='password')
    plan: Literal['free', 'pro'] = Field('free', title='Plan')
    birthday: date | None = Field(None, title='Birthday')
    newsletter: bool = Field(False, title='Send me the newsletter')

    @field_validator('confirm')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value
