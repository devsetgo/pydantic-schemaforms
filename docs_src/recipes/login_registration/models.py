from pydantic import EmailStr, ValidationInfo, field_validator

from pydantic_schemaforms import Field, FormModel


class LoginForm(FormModel):
    username: str = Field(title='Username', ui_autofocus=True)
    password: str = Field(title='Password', ui_element='password')
    remember_me: bool = Field(False, title='Keep me signed in')


class RegistrationForm(FormModel):
    username: str = Field(
        title='Username',
        min_length=3,
        max_length=30,
        pattern=r'^[a-z0-9_]+$',
        description='Lowercase letters, numbers and underscores.',
    )
    email: EmailStr = Field(title='Email')
    password: str = Field(title='Password', ui_element='password', min_length=12)
    confirm_password: str = Field(title='Confirm password', ui_element='password')
    accept_terms: bool = Field(False, title='I accept the terms of service', validate_default=True)

    @field_validator('username', mode='before')
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value

    @field_validator('accept_terms')
    @classmethod
    def terms_accepted(cls, value: bool) -> bool:
        if not value:
            raise ValueError('You must accept the terms to create an account')
        return value
