from pydantic_schemaforms import Field, FormModel, render_form_html

# A blank three-step wizard: each nested FormModel is one step, in declaration order.
# It is still one <form> and one POST; Next checks the current step in the browser.


class StepOne(FormModel):
    name: str = Field(title='Name')


class StepTwo(FormModel):
    details: str = Field('', title='Details', ui_element='textarea')


class StepThree(FormModel):
    confirm: bool = Field(title='I confirm these details are correct')


class WizardForm(FormModel):
    step_one: StepOne = Field(title='Step one')
    step_two: StepTwo = Field(title='Step two')
    step_three: StepThree = Field(title='Step three', ui_step_title='Confirm')


form_html = render_form_html(
    WizardForm,
    layout='wizard',
    wizard_options={'next_label': 'Continue'},
    submit_url='/form',
)
