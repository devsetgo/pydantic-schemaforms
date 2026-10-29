from pydantic_schemaforms import Field, FormModel


class Address(FormModel):
    street: str = Field(title='Street')
    city: str = Field(title='City')


class PersonForm(FormModel):
    name: str = Field(title='Full name', ui_autofocus=True)
    address: Address = Field(title='Address')


schema = PersonForm.get_pydantic_json_schema()
# {"$defs": {"Address": {...}}, "properties": {"address": {"$ref": "#/$defs/Address"}, ...}}

openapi_schema = PersonForm.get_pydantic_json_schema(ref_template='#/components/schemas/{model}')
