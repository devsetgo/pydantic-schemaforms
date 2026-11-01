"""Screenshots of the Material pages, for a person (or an agent) to look at.

Not pixel-compared. They land in tests/playwright/screenshots/ and are uploaded
as a CI artifact; a green run says nothing about how the pages look.
"""

from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import Page, expect

import examples.main

OUTPUT = Path(__file__).parent / 'screenshots'
PAGES = {
    'gallery': '/gallery?style=material',
    'gallery-filled': '/gallery?style=material&variant=filled',
    'tabbed': '/layouts?style=material&layout=tabbed',
    'tabbed-filled': '/layouts?style=material&layout=tabbed&variant=filled',
    'accordion': '/layouts?style=material&layout=accordion',
    'side-by-side': '/layouts?style=material&layout=side-by-side',
    'wizard': '/layouts?style=material&layout=wizard',
    'model-list': '/pets?style=material&demo=true',
    'data-table': '/employees/import?style=material',
    'validation': '/validation?style=material',
    'review': '/layouts/review?style=material',
    'field-groups': '/layouts/field-groups?style=material',
    'review-gallery': '/gallery/review?style=material',
}


@pytest.fixture(scope='module')
def server_url():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(examples.main.app, host='127.0.0.1', port=port, log_level='warning')
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    yield f'http://127.0.0.1:{port}'
    server.should_exit = True
    thread.join(timeout=5)


@pytest.mark.parametrize('theme', ['light', 'dark'])
@pytest.mark.parametrize('name', sorted(PAGES))
def test_screenshot(page: Page, server_url: str, name: str, theme: str) -> None:
    OUTPUT.mkdir(exist_ok=True)
    page.add_init_script(f"localStorage.setItem('sf-theme', '{theme}')")
    page.goto(f'{server_url}{PAGES[name]}')
    form = page.locator('.md-form').first
    expect(form).to_be_visible(timeout=15_000)
    page.screenshot(path=OUTPUT / f'{name}-{theme}.png', full_page=True)
