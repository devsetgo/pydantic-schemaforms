from pydantic_schemaforms import Field, FormModel, render_form_html

# A blank tabbed form: each nested FormModel becomes one tab.
# Replace the placeholder sections and fields with real ones.


class SectionOne(FormModel):
    first_field: str = Field(title='First field')


class SectionTwo(FormModel):
    second_field: str = Field('', title='Second field')


class SectionThree(FormModel):
    third_field: bool = Field(False, title='Third field')


class TabbedForm(FormModel):
    # Plain fields on the main form become the first tab, titled by model_config.
    model_config = {'title': 'General'}

    name: str = Field(title='Name')
    section_one: SectionOne = Field(title='Section one')
    section_two: SectionTwo = Field(title='Section two')
    section_three: SectionThree = Field(title='Section three')


# The same model works as "accordion", "side-by-side" or "wizard": only layout= changes.
form_html = render_form_html(TabbedForm, layout='tabbed', submit_url='/form')
