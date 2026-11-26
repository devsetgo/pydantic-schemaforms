from pydantic_schemaforms import Field, FormModel


class ContactForm(FormModel):
    name: str = Field(title='Full name', min_length=2, ui_style='font-weight: 600')
    topic: str = Field(
        'question',
        title='Topic',
        ui_element='radio',
        ui_options={'choices': ['question', 'other']},
    )
    other_topic: str = Field(
        '',
        title='What about?',
        ui_show_when={'field': 'topic', 'equals': 'other', 'required': True},
    )
    message: str = Field(title='Message', min_length=10, ui_element='textarea')
