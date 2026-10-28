from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City', min_length=2)


class Pet(FormModel):
    name: str = Field(title='Name')
    age: int = Field(0, title='Age', ge=0)


class ProfileForm(FormModel):
    nickname: str = Field(title='Nickname')
    address: Address = Field(title='Home address')
    pets: list[Pet] = Field(
        default_factory=list,
        title='Pets',
        max_length=5,
        ui_add_button_label='Add a pet',
        ui_item_title_template='{name}',
    )
