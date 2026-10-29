from flask import Flask, request
from models import AccountForm

from pydantic_schemaforms import html, render_form_html

app = Flask(__name__)
FORM_OPTIONS = {'layout': 'tabbed', 'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/account')
def show_account():
    return render_form_html(AccountForm, submit_url='/account', **FORM_OPTIONS)


@app.post('/account')
def save_account():
    result = AccountForm.validate(request.form, submit_url='/account', **FORM_OPTIONS)
    if not result.is_valid:
        return result.render_with_errors()
    name = result.data['name']
    return html(t'<p>Saved {name}.</p>')
