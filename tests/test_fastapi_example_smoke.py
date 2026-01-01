"""Smoke test for the FastAPI example app (make ex-run).

This keeps runtime light by using TestClient and patching the template directory
so it always resolves correctly from the repo root.
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


def test_homepage_renders():
    _patch_templates_to_repo_root()
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Pydantic Forms" in resp.text or "Forms" in resp.text
