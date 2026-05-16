"""Fixtures for Playwright HTMX live-validation tests."""

import socket
import threading
import time

import pytest
import uvicorn

from tests.playwright._server import app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def live_server_url():
    """Start the FastAPI test server and yield its base URL."""
    port = _free_port()
    config = uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning')
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
