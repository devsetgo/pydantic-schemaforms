from models import SignupForm

from pydantic_schemaforms import render_form_html

saved = {'name': 'Ada Lovelace', 'email': 'ada@example.com', 'plan': 'team', 'team_size': 12}

form_html = render_form_html(SignupForm, form_data=saved, submit_url='/signup')
