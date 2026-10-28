from models import AccountForm

from pydantic_schemaforms import render_form_html

form_html = render_form_html(
    AccountForm,
    layout='wizard',
    wizard_options={'next_label': 'Continue', 'linear': True},
    submit_url='/account',
)
