"""Minimal FastAPI app used as the live server for Playwright HTMX tests."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms.assets.runtime import read_asset_text
from pydantic_schemaforms.live_validation import (
    HTMXValidationConfig,
    LiveValidator,
    validation_response_headers,
)
from pydantic_schemaforms.validation import FieldValidator

_email_fv = FieldValidator('email').email()
_name_fv = FieldValidator('name').required().min_length(2, 'Name must be at least 2 characters')

_config = HTMXValidationConfig(validate_on_blur=True, validate_on_input=False)
live_validator = LiveValidator(config=_config)
live_validator.register_field_validator(_email_fv)
live_validator.register_field_validator(_name_fv)

app = FastAPI()


@app.get('/', response_class=HTMLResponse)
async def form_page() -> HTMLResponse:
    htmx_js = read_asset_text('assets/vendor/htmx/htmx.min.js')
    email_html = live_validator.render_field_with_live_validation('email', 'email', label='Email')
    name_html = live_validator.render_field_with_live_validation('name', 'text', label='Name')
    htmx_script = live_validator.render_htmx_script()
    html = f"""<!DOCTYPE html>
<html>
<head><title>HTMX Validation Test</title></head>
<body>
<script>{htmx_js}</script>
<form id="test-form">
{email_html}
{name_html}
</form>
{htmx_script}
</body>
</html>"""
    return HTMLResponse(content=html)


@app.post('/validate/{field_name}', response_class=HTMLResponse)
async def validate_field(field_name: str, request: Request) -> HTMLResponse:
    # HTMX sends the input's own name as the form field key, not "value".
    form = await request.form()
    value = str(form.get(field_name, '') or '')
    result = live_validator.validate_field(field_name, value)
    if result.is_valid:
        feedback = '<span class="valid-feedback d-block">✓ Looks good</span>'
    else:
        errors = '<br>'.join(result.errors)
        feedback = f'<span class="invalid-feedback d-block">{errors}</span>'
    headers = validation_response_headers(field_name, result.is_valid)
    return HTMLResponse(content=feedback, headers=headers)
