from datetime import date
from typing import Literal

from pydantic import EmailStr

from pydantic_schemaforms import Field, FormModel


class Applicant(FormModel):
    full_name: str = Field(title='Full name', min_length=2)
    email: EmailStr = Field(title='Email')
    phone: str = Field('', title='Phone', ui_element='tel')


class Position(FormModel):
    role: Literal['Engineer', 'Designer', 'Product manager'] = Field(title='Role')
    start_date: date = Field(title='Earliest start date')
    remote: bool = Field(False, title='I want to work remotely')


class Job(FormModel):
    employer: str = Field(title='Employer')
    job_title: str = Field(title='Job title')
    years: int = Field(1, title='Years', ge=0, le=50)


class Motivation(FormModel):
    cover_letter: str = Field(
        title='Why do you want to join?', min_length=50, ui_element='textarea'
    )
    consent: bool = Field(title='You may keep my application on file for 12 months')


class ApplicationForm(FormModel):
    applicant: Applicant = Field(title='About you')
    position: Position = Field(title='Position')
    experience: list[Job] = Field(
        default_factory=list,
        title='Experience',
        max_length=10,
        ui_add_button_label='Add a job',
        ui_item_title_template='{employer}',
    )
    motivation: Motivation = Field(title='Motivation')
