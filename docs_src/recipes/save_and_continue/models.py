from datetime import date

from pydantic_schemaforms import Field, FormModel, UploadedFile


class AboutYou(FormModel):
    full_name: str = Field(title='Full name', min_length=2)
    zip_code: str = Field(title='ZIP code', pattern=r'^\d{5}$')


class Resume(FormModel):
    resume: UploadedFile = Field(
        title='Resume (PDF or text, up to 200 KB)',
        ui_max_size=200 * 1024,
        ui_options={'accept': '.pdf,.txt'},
    )


class Availability(FormModel):
    city: str = Field(title='City', min_length=2)
    start_date: date = Field(title='Earliest start date')


class ApplicationForm(FormModel):
    about_you: AboutYou = Field(title='About you')
    resume: Resume = Field(title='Resume')
    availability: Availability = Field(title='Availability')
