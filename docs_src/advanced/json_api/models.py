from pydantic_schemaforms import Field, FormModel


class ContactForm(FormModel):
    name: str = Field(title='Full name', min_length=2, examples=['Ada Lovelace'], ui_autofocus=True)
    email: str = Field(title='Email', examples=['ada@example.com'], ui_element='email')
    message: str = Field(title='Message', min_length=10, ui_element='textarea')
