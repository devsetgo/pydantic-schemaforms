from pydantic_schemaforms import Field, FormModel


class Contact(FormModel):
    email: str = Field(title='Email', ui_element='email')
    phone: str = Field('', title='Phone', ui_element='tel')


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City')


class Preferences(FormModel):
    newsletter: bool = Field(False, title='Send me the newsletter')
    language: str = Field(
        'en', title='Language', ui_element='select', ui_options={'choices': ['en', 'fr', 'de']}
    )


class AccountForm(FormModel):
    model_config = {'title': 'About you'}

    name: str = Field(title='Full name')
    contact: Contact = Field(title='Contact details')
    address: Address = Field(title='Address')
    preferences: Preferences = Field(title='Preferences', ui_order=1)
