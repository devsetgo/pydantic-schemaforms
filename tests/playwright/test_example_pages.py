"""
Every example page must load in a real browser without a JavaScript error.

Inline scripts are built inside Python strings, where a stray Python-style
`# comment` is a syntax error that silently disables the whole script (this
happened to the Material theme script and to the file-input preview). Only a
browser catches that, so this loads every example GET route under Bootstrap
and Material.

Requires: playwright install chromium
Run:      pytest tests/playwright/test_example_pages.py -v
"""

import re
import socket
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import Page, expect

import examples.main

TIMEOUT = 3_000  # ms — generous for CI latency


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def examples_server_url():
    """Start the example app (examples/main.py) on a free port."""
    port = _free_port()
    config = uvicorn.Config(examples.main.app, host='127.0.0.1', port=port, log_level='warning')
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


def _html_pages() -> list[str]:
    paths = examples.main.app.openapi()['paths']
    return sorted(
        path
        for path, ops in paths.items()
        if 'get' in ops
        and '{' not in path
        and not path.startswith(('/api/', '/vendor/'))
        and not path.endswith(('.csv', '.js', '.css'))
    )


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('path', _html_pages())
def test_example_page_has_no_javascript_errors(
    page: Page, examples_server_url: str, path: str, style: str
) -> None:
    errors: list[str] = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(f'{examples_server_url}{path}?style={style}', wait_until='domcontentloaded')
    page.wait_for_timeout(200)
    assert errors == [], f'{path} ({style}): {errors}'


def test_file_input_preview_lists_the_chosen_file(page: Page, examples_server_url: str) -> None:
    page.goto(f'{examples_server_url}/gallery')
    page.get_by_role('tab', name='Files & Specialized').click()
    page.set_input_files(
        '[name="files_specialized.file_input"]',
        files=[{'name': '<b>report</b>.txt', 'mimeType': 'text/plain', 'buffer': b'hello'}],
    )
    preview = page.locator('[id="files_specialized.file_input_preview"]')
    # The name is shown as text, never parsed as markup.
    expect(preview).to_contain_text('<b>report</b>.txt', timeout=TIMEOUT)
    expect(preview.locator('b')).to_have_count(0)


def test_material_placeholder_select_keeps_its_label_floated(
    page: Page, examples_server_url: str
) -> None:
    page.goto(f'{examples_server_url}/gallery?style=material')
    page.locator('.tab-button', has_text='Selection Inputs').click()
    label = page.locator('label[for="selection_inputs.select_placeholder"]')
    # Unfloated is translateY(0); the CSS floats a select's label above it.
    expect(label).not_to_have_attribute('style', re.compile(r'translateY\(0\)'), timeout=TIMEOUT)
