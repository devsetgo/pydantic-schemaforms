from pydantic_schemaforms import Field, FormModel


class SignupForm(FormModel):
    first_name: str = Field(title='First name', ui_cols=6)
    last_name: str = Field(title='Last name', ui_cols=6)
    street: str = Field(title='Street', ui_group='Address', ui_cols=8)
    unit: str = Field('', title='Unit', ui_group='Address', ui_cols=4)
    city: str = Field(title='City', ui_group='Address')
    notes: str = Field(
        '',
        title='Notes',
        ui_element='textarea',
        ui_group='More',
        ui_group_collapsible=True,
        ui_group_collapsed=True,
    )
