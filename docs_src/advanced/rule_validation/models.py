from pydantic_schemaforms import Field, FormModel, FormValidator, PhoneRule


class SignupForm(FormModel):
    username: str = Field(title='Username', min_length=3)
    phone: str = Field('', title='Phone', ui_element='tel')
    age: int = Field(title='Age', ge=0)
    parental_consent: bool = Field(False, title='A parent agrees')


def minors_need_consent(data: dict) -> tuple[bool, dict]:
    age = data.get('age')
    if age is not None and int(age) < 18 and not data.get('parental_consent'):
        return False, {'parental_consent': 'A parent must agree for anyone under 18'}
    return True, {}


rules = FormValidator()
rules.field('phone').add_rule(PhoneRule())
rules.add_cross_field_rule(minors_need_consent)
