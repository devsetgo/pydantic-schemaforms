from datetime import date
from enum import Enum
from typing import Literal

from pydantic_schemaforms import Field, FormModel


class Plan(str, Enum):
    free = 'free'
    team = 'team'
    enterprise = 'enterprise'


class SignupForm(FormModel):
    name: str = Field(title='Full name', min_length=2, ui_autofocus=True)
    email: str = Field(title='Email', ui_element='email', ui_placeholder='you@example.com')
    birthday: date | None = Field(None, title='Birthday')
    plan: Plan = Field(Plan.free, title='Plan', description='You can change plans at any time.')
    team_size: int = Field(1, title='Team size', ge=1, le=500)
    contact: Literal['email', 'phone'] = Field('email', title='Contact me by', ui_element='radio')
    bio: str = Field('', title='About you', ui_element='textarea')
    newsletter: bool = Field(False, title='Send me the newsletter')
