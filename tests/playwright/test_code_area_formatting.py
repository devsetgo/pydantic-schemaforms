"""
Playwright end-to-end tests for TextArea's code/data formatting + highlighting mode.

Static tests in tests/test_inputs.py cover the HTML/script the code-mode
TextArea renders; these behavioral checks cover what only a real browser can
prove -- the Format button actually transforming the value, invalid input
showing an error state without throwing, Tab inserting spaces, and the
highlight overlay actually tokenizing text. Self-contained server fixture so
this file doesn't share state with tests/playwright/test_htmx_live_validation.py.

Requires: playwright install chromium
Run:      pytest tests/playwright/test_code_area_formatting.py -v
"""

import re
import socket
import threading
import time

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from playwright.sync_api import Page, expect

from pydantic_schemaforms.inputs.text_inputs import TextArea

TIMEOUT = 3_000  # ms — generous for CI latency

_LANGUAGES = ('json', 'yaml', 'toml', 'bash', 'python')


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get('/', response_class=HTMLResponse)
    async def form_page() -> HTMLResponse:
        fields = []
        for language in _LANGUAGES:
            field_html = TextArea().render(name=language, id=language, value='', language=language)
            fields.append(f'<form id="form-{language}">{field_html}</form>')
        body = '\n'.join(fields)
        return HTMLResponse(content=f'<!DOCTYPE html><html><body>{body}</body></html>')

    return app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def code_area_server_url():
    """Start a standalone FastAPI server rendering one code-mode TextArea per language."""
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


class TestFormatButton:
    def test_json_format_button_reserializes_value(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        field = page.locator('#json')
        field.fill('{"b":2,"a":1}')
        page.locator('#json_code_format_btn').click()
        expect(field).to_have_value('{\n  "b": 2,\n  "a": 1\n}', timeout=TIMEOUT)

    def test_yaml_format_button_reserializes_value(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        field = page.locator('#yaml')
        field.fill('a: 1\nb: 2\n')
        page.locator('#yaml_code_format_btn').click()
        expect(field).to_have_value('a: 1\nb: 2\n', timeout=TIMEOUT)

    def test_toml_format_button_reserializes_value(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        field = page.locator('#toml')
        field.fill('a = 1\n')
        page.locator('#toml_code_format_btn').click()
        expect(field).to_have_value('a = 1\n', timeout=TIMEOUT)

    def test_python_format_button_cleans_whitespace_only(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        field = page.locator('#python')
        field.fill('def f():   \n\tx = 1\n\n\n\ny = 2')
        page.locator('#python_code_format_btn').click()
        expect(field).to_have_value('def f():\n  x = 1\n\ny = 2\n', timeout=TIMEOUT)

    def test_invalid_json_shows_error_without_throwing(
        self, page: Page, code_area_server_url: str
    ) -> None:
        errors: list[str] = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))

        page.goto(code_area_server_url)
        field = page.locator('#json')
        field.fill('{not valid json')
        page.locator('#json_code_format_btn').click()

        expect(field).to_have_class(re.compile(r'code-invalid'), timeout=TIMEOUT)
        expect(page.locator('#json_code_error')).not_to_be_empty(timeout=TIMEOUT)
        assert errors == []

    def test_editing_after_error_clears_invalid_state(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        field = page.locator('#json')
        field.fill('{bad')
        page.locator('#json_code_format_btn').click()
        expect(field).to_have_class(re.compile(r'code-invalid'), timeout=TIMEOUT)

        field.press('End')
        field.press_sequentially('x')
        expect(field).not_to_have_class(re.compile(r'code-invalid'), timeout=TIMEOUT)


class TestTabIndent:
    def test_tab_inserts_spaces_instead_of_moving_focus(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        field = page.locator('#python')
        field.fill('x = 1')
        field.press('Home')
        field.press('Tab')
        expect(field).to_have_value('  x = 1', timeout=TIMEOUT)
        expect(field).to_be_focused()


class TestHighlightOverlay:
    def test_highlight_layer_tokenizes_json_input(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        field = page.locator('#json')
        field.fill('{"a": 1}')
        expect(page.locator('#json_code_layer_inner .token').first).to_be_attached(timeout=TIMEOUT)

    def test_highlight_enabled_field_has_overlay_element(
        self, page: Page, code_area_server_url: str
    ) -> None:
        page.goto(code_area_server_url)
        expect(page.locator('#json_code_layer_inner')).to_be_attached()
        # sanity: a field with no matching id never gets a highlight layer
        assert page.locator('#does-not-exist_code_layer_inner').count() == 0

    def test_highlight_layer_does_not_cover_the_format_button(
        self, page: Page, code_area_server_url: str
    ) -> None:
        """Regression test: the highlight <pre> is `position: absolute; inset: 0`
        relative to its nearest positioned ancestor. If that ancestor also
        contained the toolbar, the dark overlay would paint over the Format
        button (positioned elements paint above static-flow siblings
        regardless of z-index), making it invisible/unclickable even though
        it's still present and clickable in the accessibility tree."""
        page.goto(code_area_server_url)
        btn_box = page.locator('#json_code_format_btn').bounding_box()
        layer_box = page.locator('#json_code_layer').bounding_box()
        assert btn_box is not None
        assert layer_box is not None
        assert btn_box['y'] + btn_box['height'] <= layer_box['y'] + 1  # 1px rounding slack
