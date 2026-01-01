"""Smoke tests for the Layout Demonstration page (Bootstrap/Material).

These tests ensure initial tab content renders server-side without JS execution
and that the first tab is marked active so content is visible on page load.
"""

from pathlib import Path

import examples.fastapi_example as fastapi_example
from examples.fastapi_example import app
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient


def _patch_templates_to_repo_root() -> None:
    """Ensure templates resolve when running tests from repo root."""

    base_dir = Path(fastapi_example.__file__).resolve().parent
    fastapi_example.templates = Jinja2Templates(directory=base_dir / "templates")


def _client() -> TestClient:
    _patch_templates_to_repo_root()
    return TestClient(app)


def test_layout_demo_bootstrap_initial_tab_renders():
    client = _client()
    resp = client.get("/layouts?style=bootstrap")
    assert resp.status_code == 200

    body = resp.text
    # Bootstrap tab pane should render first tab as show active
    assert "tab-pane fade show active" in body
    # Personal info content should be present immediately
    assert "Alex" in body  # demo data
    assert "Personal Info" in body


def test_layout_demo_material_initial_tab_renders():
    client = _client()
    resp = client.get("/layouts?style=material")
    assert resp.status_code == 200

    body = resp.text
    # Material tabs use shared tab-panel with active class and display:block on first
    assert "tab-panel active" in body or "tab-panel  active" in body
    # Tab buttons should have generic tab-button class for JS-less toggling
    assert "tab-button" in body
    assert "Alex" in body
    assert "Personal Info" in body


def test_layout_demo_tab_buttons_present():
    client = _client()
    resp = client.get("/layouts?style=bootstrap")
    assert resp.status_code == 200
    body = resp.text
    # Tab buttons should include all four sections
    for label in ["Personal Info", "Contact Info", "Preferences", "Task List"]:
        assert label in body
