"""Route/style smoke matrix for the FastAPI example app.

Verifies GET and POST behavior across all form routes and supported styles.
"""

from pathlib import Path
import re

import examples.fastapi_example as fastapi_example
from examples.fastapi_example import app
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
import pytest


FORM_ROUTES = ["login", "register", "showcase", "pets", "organization", "layouts"]
STYLES = ["bootstrap", "material"]

INPUT_RE = re.compile(r"<input\b[^>]*>", re.I)
TEXTAREA_RE = re.compile(r"<textarea\b([^>]*)>(.*?)</textarea>", re.I | re.S)
SELECT_RE = re.compile(r"<select\b([^>]*)>(.*?)</select>", re.I | re.S)
OPTION_RE = re.compile(r"<option\b([^>]*)>(.*?)</option>", re.I | re.S)
ATTR_RE = re.compile(r"([\w:-]+)\s*=\s*([\"\'])(.*?)\2", re.S)


def _patch_templates_to_repo_root() -> None:
    base_dir = Path(fastapi_example.__file__).resolve().parent
    fastapi_example.templates = Jinja2Templates(directory=base_dir / "templates")
    fastapi_example.templates.env.filters["safe_json"] = fastapi_example.safe_json_filter


@pytest.fixture
def client() -> TestClient:
    _patch_templates_to_repo_root()
    return TestClient(app)


def _parse_attrs(tag: str) -> dict[str, str]:
    return {key.lower(): value for key, _, value in ATTR_RE.findall(tag)}


def _has_attr(tag: str, name: str) -> bool:
    return re.search(rf"\b{name}\b", tag, re.I) is not None


def _extract_form_payload(html: str) -> dict[str, str] | None:
    form_match = re.search(r"<form\b[^>]*>(.*?)</form>", html, re.I | re.S)
    if not form_match:
        return None

    form_html = form_match.group(1)
    payload: dict[str, str] = {}

    for tag in INPUT_RE.findall(form_html):
        attrs = _parse_attrs(tag)
        name = attrs.get("name")
        if not name:
            continue
        input_type = attrs.get("type", "text").lower()
        if input_type in {"submit", "button", "reset", "image", "file"}:
            continue
        if input_type in {"checkbox", "radio"}:
            if _has_attr(tag, "checked"):
                payload[name] = attrs.get("value", "on")
            continue
        payload[name] = attrs.get("value", "")

    for head, inner in TEXTAREA_RE.findall(form_html):
        attrs = _parse_attrs(head)
        name = attrs.get("name")
        if name:
            payload[name] = inner.strip()

    for head, inner in SELECT_RE.findall(form_html):
        attrs = _parse_attrs(head)
        name = attrs.get("name")
        if not name:
            continue

        selected_value: str | None = None
        first_non_empty: str | None = None
        first_any: str | None = None

        for option_head, option_text in OPTION_RE.findall(inner):
            option_attrs = _parse_attrs(option_head)
            value = option_attrs.get("value", re.sub(r"<[^>]+>", "", option_text).strip())

            if first_any is None:
                first_any = value
            if first_non_empty is None and value != "":
                first_non_empty = value
            if _has_attr(option_head, "selected"):
                selected_value = value

        if selected_value is not None:
            payload[name] = selected_value
        elif name not in payload:
            payload[name] = first_non_empty if first_non_empty is not None else (first_any or "")

    return payload


def _assert_style_marker(style: str, body: str) -> None:
    lower = body.lower()
    if style == "bootstrap":
        assert "btn btn-primary" in body or "bootstrap" in lower
    elif style == "material":
        markers = ["md3-", "material", "outlined-text-field", "filled-text-field"]
        assert any(marker in lower for marker in markers)


@pytest.mark.parametrize("route", FORM_ROUTES)
@pytest.mark.parametrize("style", STYLES)
def test_fastapi_form_routes_get_post_matrix(client: TestClient, route: str, style: str):
    get_response = client.get(f"/{route}?style={style}&demo=true")
    assert get_response.status_code == 200

    get_body = get_response.text
    assert "<form" in get_body.lower()
    assert "Internal Server Error" not in get_body
    assert "Traceback (most recent call last)" not in get_body
    _assert_style_marker(style, get_body)

    payload = _extract_form_payload(get_body)
    assert payload is not None

    post_response = client.post(f"/{route}?style={style}", data=payload)
    assert post_response.status_code == 200

    post_body = post_response.text
    assert "Internal Server Error" not in post_body
    assert "Traceback (most recent call last)" not in post_body
    assert "Exception:" not in post_body

    is_success = any(
        token in post_body.lower()
        for token in ["successful", "submitted successfully", "registration successful", "login successful"]
    )
    is_rerender = "<form" in post_body.lower()
    assert is_success or is_rerender


def test_fastapi_self_contained_get(client: TestClient):
    response = client.get("/self-contained?demo=true")
    assert response.status_code == 200
    body = response.text
    assert "Self-Contained Form Demo" in body
    assert "<form" in body.lower()
    assert "Internal Server Error" not in body


def test_fastapi_self_contained_honors_plain_html_style(client: TestClient):
    response = client.get("/self-contained?style=none&demo=true")
    assert response.status_code == 200
    body = response.text
    assert "Selected Style:</strong> <code>none</code>" in body
    assert "generated by <code>EnhancedFormRenderer</code>" in body
