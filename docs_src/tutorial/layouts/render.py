from models import AccountForm

from pydantic_schemaforms import render_form_html

form_html = render_form_html(AccountForm, layout='tabbed', submit_url='/account')
