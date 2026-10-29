from datetime import date

from pydantic import ValidationInfo, field_validator, model_validator

from pydantic_schemaforms import Field, FormModel


class RegistrationForm(FormModel):
    username: str = Field(title='Username', min_length=3, max_length=20, pattern=r'^[a-z0-9_]+$')
    password: str = Field(title='Password', ui_element='password', min_length=8)
    confirm_password: str = Field(title='Confirm password', ui_element='password')
    age: int = Field(title='Age', ge=13, le=120)
    start_date: date = Field(title='Start date')
    end_date: date = Field(title='End date')

    @field_validator('username', mode='before')
    @classmethod
    def lowercase_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get('password'):
            raise ValueError('Passwords do not match')
        return value

    @model_validator(mode='after')
    def end_after_start(self) -> 'RegistrationForm':
        if self.end_date < self.start_date:
            raise ValueError('The end date must be after the start date')
        return self
