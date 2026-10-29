from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from models import SignupForm, rules

from pydantic_schemaforms import html, render_form_html_async

app = FastAPI()


@app.get('/signup', response_class=HTMLResponse)
async def show_signup():
    return await render_form_html_async(SignupForm, submit_url='/signup')


@app.post('/signup', response_class=HTMLResponse)
async def submit_signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup')
    rules_ok, rule_errors = rules.validate(result.original_data)
    if not (result.is_valid and rules_ok):
        return await result.render_with_errors_async(errors={**rule_errors, **result.errors})
    username = result.data['username']
    return html(t'<p>Welcome, {username}!</p>')
