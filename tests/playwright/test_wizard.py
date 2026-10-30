"""
Playwright end-to-end tests for layout="wizard".

tests/test_nested_model_forms.py covers the server-rendered markup (steps,
active step on re-render, no-JS fallback); these cover what only a real
browser can prove -- Next refusing to leave a step with an HTML5-invalid
input, Back never validating, the submit button appearing only on the last
step, and one POST carrying every step's values.

Requires: playwright install chromium
Run:      pytest tests/playwright/test_wizard.py -v
"""

import json
import socket
import threading
import time

import pytest
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from playwright.sync_api import Page, expect

from pydantic_schemaforms import Field, FormModel, render_form_html

TIMEOUT = 3_000  # ms — generous for CI latency


class Contact(FormModel):
    email: str = Field(title='Email', ui_element='email')


class Address(FormModel):
    city: str = Field(title='City', min_length=2)


class SignupForm(FormModel):
    nickname: str = Field(title='Nickname')
    contact: Contact = Field(title='Contact')
    address: Address = Field(title='Address')


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get('/', response_class=HTMLResponse)
    async def form_page(
        linear: bool = True, framework: str = 'bootstrap', layout: str = 'wizard'
    ) -> HTMLResponse:
        form_html = render_form_html(
            SignupForm,
            layout=layout,
            framework=framework,
            submit_url='/submit',
            wizard_options={'linear': linear},
        )
        return HTMLResponse(f'<!DOCTYPE html><html><body>{form_html}</body></html>')

    @app.post('/submit', response_class=HTMLResponse)
    async def submit(request: Request) -> HTMLResponse:
        result = SignupForm.validate(await request.form(), submit_url='/submit')
        payload = json.dumps({'valid': result.is_valid, 'data': result.data})
        return HTMLResponse(f'<pre id="result">{payload}</pre>')

    return app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def wizard_server_url():
    """Start a standalone FastAPI server rendering SignupForm as a wizard."""
    port = _free_port()
    config = uvicorn.Config(_build_app(), host='127.0.0.1', port=port, log_level='warning')
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError('Test server did not start within 10 seconds')
        time.sleep(0.05)

    yield f'http://127.0.0.1:{port}'

    server.should_exit = True
    thread.join(timeout=5)


def _step(page: Page, index: int):
    return page.locator(f'[data-wizard-step="{index}"]')


class TestWizardNavigation:
    def test_only_the_first_step_is_visible_and_submit_is_hidden(
        self, page: Page, wizard_server_url: str
    ) -> None:
        page.goto(wizard_server_url)
        expect(_step(page, 0)).to_be_visible(timeout=TIMEOUT)
        expect(_step(page, 1)).to_be_hidden()
        expect(_step(page, 2)).to_be_hidden()
        expect(page.locator('[data-wizard-back]')).to_be_hidden()
        expect(page.locator('button[type="submit"]')).to_be_hidden()

    def test_next_is_blocked_by_an_invalid_field_in_the_current_step(
        self, page: Page, wizard_server_url: str
    ) -> None:
        page.goto(wizard_server_url)
        page.locator('[data-wizard-next]').click()
        expect(_step(page, 0)).to_be_visible(timeout=TIMEOUT)
        expect(_step(page, 1)).to_be_hidden()

        page.locator('[name="nickname"]').fill('mk')
        page.locator('[data-wizard-next]').click()
        expect(_step(page, 1)).to_be_visible(timeout=TIMEOUT)

        page.locator('[name="contact.email"]').fill('not-an-email')
        page.locator('[data-wizard-next]').click()
        expect(_step(page, 1)).to_be_visible(timeout=TIMEOUT)

    def test_back_never_validates(self, page: Page, wizard_server_url: str) -> None:
        page.goto(wizard_server_url)
        page.locator('[name="nickname"]').fill('mk')
        page.locator('[data-wizard-next]').click()
        page.locator('[name="contact.email"]').fill('not-an-email')
        page.locator('[data-wizard-back]').click()
        expect(_step(page, 0)).to_be_visible(timeout=TIMEOUT)

    def test_linear_header_cannot_skip_an_invalid_step(
        self, page: Page, wizard_server_url: str
    ) -> None:
        page.goto(wizard_server_url)
        page.locator('[data-wizard-goto="2"]').click()
        expect(_step(page, 0)).to_be_visible(timeout=TIMEOUT)
        expect(_step(page, 2)).to_be_hidden()

    def test_non_linear_header_jumps_to_any_step(self, page: Page, wizard_server_url: str) -> None:
        page.goto(f'{wizard_server_url}/?linear=false')
        page.locator('[data-wizard-goto="2"]').click()
        expect(_step(page, 2)).to_be_visible(timeout=TIMEOUT)
        expect(_step(page, 0)).to_be_hidden()

    def test_enter_before_the_last_step_advances_instead_of_submitting(
        self, page: Page, wizard_server_url: str
    ) -> None:
        page.goto(wizard_server_url)
        page.locator('[name="nickname"]').fill('mk')
        page.locator('[name="nickname"]').press('Enter')
        expect(_step(page, 1)).to_be_visible(timeout=TIMEOUT)
        assert page.url.rstrip('/') == wizard_server_url

    def test_a_submit_button_inside_a_step_still_submits(
        self, page: Page, wizard_server_url: str
    ) -> None:
        # Stands in for a composite's own submit button, such as
        # DataTableLayout's "Load CSV", which must not be turned into Next.
        page.goto(wizard_server_url)
        page.evaluate(
            """() => {
                const button = document.createElement('button');
                button.type = 'submit';
                button.id = 'in-step-submit';
                document.querySelector('[data-wizard-step="0"]').appendChild(button);
            }"""
        )
        page.locator('#in-step-submit').click()
        expect(page.locator('#result')).to_be_attached(timeout=TIMEOUT)

    def test_one_post_submits_every_step(self, page: Page, wizard_server_url: str) -> None:
        page.goto(wizard_server_url)
        page.locator('[name="nickname"]').fill('mk')
        page.locator('[data-wizard-next]').click()
        page.locator('[name="contact.email"]').fill('a@b.co')
        page.locator('[data-wizard-next]').click()
        page.locator('[name="address.city"]').fill('Xy')
        expect(page.locator('[data-wizard-next]')).to_be_hidden(timeout=TIMEOUT)
        page.locator('button[type="submit"]').click()

        result = json.loads(page.locator('#result').inner_text(timeout=TIMEOUT))
        assert result == {
            'valid': True,
            'data': {
                'nickname': 'mk',
                'contact': {'email': 'a@b.co'},
                'address': {'city': 'Xy'},
            },
        }


class TestMaterialForms:
    """Material forms submit to the server, like every other style."""

    def test_wizard_runs_under_material(self, page: Page, wizard_server_url: str) -> None:
        errors: list[str] = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'{wizard_server_url}/?framework=material')
        page.locator('[name="nickname"]').fill('mk')
        page.locator('[data-wizard-next]').click()
        expect(_step(page, 1)).to_be_visible(timeout=TIMEOUT)
        assert errors == []

    def test_required_fields_in_hidden_tabs_do_not_block_submit(
        self, page: Page, wizard_server_url: str
    ) -> None:
        page.goto(f'{wizard_server_url}/?framework=material&layout=tabbed')
        page.locator('[name="nickname"]').fill('mk')
        page.locator('button[type="submit"]').click()

        result = json.loads(page.locator('#result').inner_text(timeout=TIMEOUT))
        assert result['valid'] is False

    def test_an_empty_required_field_reaches_the_server(
        self, page: Page, wizard_server_url: str
    ) -> None:
        page.goto(f'{wizard_server_url}/?framework=material&layout=tabbed')
        page.locator('button[type="submit"]').click()
        result = json.loads(page.locator('#result').inner_text(timeout=TIMEOUT))
        assert result['valid'] is False
