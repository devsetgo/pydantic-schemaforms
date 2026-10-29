from pydantic import BaseModel
from pydantic import Field as PydanticField

from pydantic_schemaforms import Field, FormModel, render_form_html


# The app's existing model, used elsewhere (an API, the database layer). Leave it as it is.
class User(BaseModel):
    name: str = PydanticField(min_length=2, title='Name')
    email: str
    bio: str = ''


# FormModel first, then the existing model: every field and constraint is inherited.
# Redeclare only the fields that need form settings.
class UserForm(FormModel, User):
    email: str = Field(title='Email', ui_element='email')
    bio: str = Field('', title='About you', max_length=500, ui_element='textarea')


form_html = render_form_html(UserForm, submit_url='/users/new')
