"""
Every example page must load in a real browser without a JavaScript error,
and pass axe-core with no serious or critical accessibility violation.

Inline scripts are built inside Python strings, where a stray Python-style
`# comment` is a syntax error that silently disables the whole script (this
happened to the Material theme script and to the file-input preview). Only a
browser catches that, so this loads every example GET route under Bootstrap
and Material.

axe-core is vendored for tests only (tests/playwright/vendor/axe.min.js,
MPL-2.0, not shipped in the package). To update it, download axe.min.js from
the axe-core npm tarball and update _AXE_VERSION and _AXE_SHA256 below.

Requires: playwright install chromium
Run:      pytest tests/playwright/test_example_pages.py -v
"""

import hashlib
import re
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import Page, expect

import examples.main

TIMEOUT = 3_000  # ms — generous for CI latency

_AXE_PATH = Path(__file__).parent / 'vendor' / 'axe.min.js'
_AXE_VERSION = '4.14.0'
_AXE_SHA256 = '20c09fe157a8a34a30e241aaa1fcdade657734f08ab379ecfbeb7d45cc46e878'
_BLOCKING_IMPACTS = ('serious', 'critical')
# Named explicitly so docs/accessibility.md's claim can't drift with axe's
# defaults (which leave out WCAG 2.2). axe maps these rules to Section 508
# and EN 301 549 as well.
_AXE_RULE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']


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


def _axe_source() -> str:
    data = _AXE_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == _AXE_SHA256, 'vendored axe.min.js changed'
    assert data.startswith(f'/*! axe v{_AXE_VERSION}'.encode())
    return data.decode()


def _blocking_violations(page: Page) -> list[str]:
    page.add_script_tag(content=_axe_source())
    results = page.evaluate(
        "tags => axe.run(document, {runOnly: {type: 'tag', values: tags}, "
        "resultTypes: ['violations']})",
        _AXE_RULE_TAGS,
    )
    return [
        f'[{violation["impact"]}] {violation["id"]}: {violation["help"]} -> '
        + ', '.join(str(node['target']) for node in violation['nodes'][:5])
        for violation in results['violations']
        if violation['impact'] in _BLOCKING_IMPACTS
    ]


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('path', _html_pages())
def test_example_page_has_no_serious_accessibility_violations(
    page: Page, examples_server_url: str, path: str, style: str
) -> None:
    page.goto(f'{examples_server_url}{path}?style={style}', wait_until='load')
    violations = _blocking_violations(page)
    assert violations == [], f'{path} ({style}):\n' + '\n'.join(violations)


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_validation_errors_have_no_serious_accessibility_violations(
    page: Page, examples_server_url: str, style: str
) -> None:
    # The error state (messages, aria-invalid, the error summary) only exists
    # after a failed submit. form.submit() skips the browser's own constraint
    # checks so the server's errors are what gets rendered.
    page.goto(f'{examples_server_url}/validation?style={style}', wait_until='load')
    with page.expect_navigation(wait_until='load'):
        page.evaluate("document.querySelector('form').submit()")
    expect(page.locator('[aria-invalid="true"]').first).to_be_attached(timeout=TIMEOUT)
    violations = _blocking_violations(page)
    assert violations == [], f'/validation errors ({style}):\n' + '\n'.join(violations)


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


_GROUP_CONTROLS = {
    'tabbed': '[role="tab"][aria-controls^="tab-"]',
    'accordion': 'button[aria-controls^="accordion-"]',
}


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('layout', ['tabbed', 'accordion'])
def test_grouped_forms_on_one_page_switch_independently(
    page: Page, examples_server_url: str, layout: str, style: str
) -> None:
    page.goto(f'{examples_server_url}/layouts/two-forms?style={style}&layout={layout}')
    first, second = page.locator('form').nth(0), page.locator('form').nth(1)

    def panel(form, index: int):
        control = form.locator(_GROUP_CONTROLS[layout]).nth(index)
        return page.locator(f'[id="{control.get_attribute("aria-controls")}"]')

    second.locator(_GROUP_CONTROLS[layout]).nth(1).click()

    expect(panel(second, 1)).to_be_visible(timeout=TIMEOUT)
    expect(panel(first, 0)).to_be_visible(timeout=TIMEOUT)
    expect(panel(first, 1)).to_be_hidden(timeout=TIMEOUT)
