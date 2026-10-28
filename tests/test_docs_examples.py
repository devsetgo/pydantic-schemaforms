"""Every code example in the docs is a real file under docs_src/, included into
the pages with pymdownx.snippets. This imports each one and exercises it, so an
example in the docs can't silently stop working.

- A file with an ``app`` (FastAPI or Flask) has each GET route requested and
  each POST route sent an empty submission; both must render without a server
  error.
- Any other file must at least render every FormModel it defines.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType

import pytest

from pydantic_schemaforms import FormModel, render_form_html

DOCS_SRC = Path(__file__).resolve().parent.parent / 'docs_src'
EXAMPLES = sorted(DOCS_SRC.rglob('*.py'))


def _load(path: Path) -> ModuleType:
    # Each example directory is self-contained (an app file may import its
    # sibling models.py), so it goes on sys.path and any same-named sibling
    # cached from another directory is dropped first.
    for name in [m for m in sys.modules if m in {p.stem for p in path.parent.glob('*.py')}]:
        del sys.modules[name]
    sys.path.insert(0, str(path.parent))
    try:
        module_name = 'docs_src_' + '_'.join(path.relative_to(DOCS_SRC).with_suffix('').parts)
        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(path.parent))


def _get_post_paths(app) -> tuple[list[str], list[str]]:
    gets: list[str] = []
    posts: list[str] = []
    if hasattr(app, 'url_map'):  # Flask
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static' or rule.arguments:
                continue
            if 'GET' in rule.methods:
                gets.append(rule.rule)
            if 'POST' in rule.methods:
                posts.append(rule.rule)
    else:  # FastAPI / Starlette
        for route in app.routes:
            path = getattr(route, 'path', '')
            if '{' in path or path.startswith(('/docs', '/redoc', '/openapi')):
                continue
            methods = getattr(route, 'methods', set()) or set()
            if 'GET' in methods:
                gets.append(path)
            if 'POST' in methods:
                posts.append(path)
    return gets, posts


def _client(app):
    if hasattr(app, 'test_client'):
        return app.test_client()
    from fastapi.testclient import TestClient

    return TestClient(app)


def _status(response) -> int:
    return getattr(response, 'status_code', None) or response.status_code


def test_docs_src_has_examples() -> None:
    assert EXAMPLES, 'docs_src/ has no examples'


@pytest.mark.parametrize('path', EXAMPLES, ids=lambda p: str(p.relative_to(DOCS_SRC)))
def test_docs_example_runs(path: Path) -> None:
    module = _load(path)
    app = getattr(module, 'app', None)
    if app is None:
        forms = [
            obj
            for obj in vars(module).values()
            if inspect.isclass(obj)
            and issubclass(obj, FormModel)
            and obj is not FormModel
            and obj.__module__ == module.__name__
        ]
        for form in forms:
            try:
                html_out = render_form_html(form, submit_url='/x')
            except NotImplementedError:
                continue  # composites such as DataTableLayout render as a field
            assert '<form' in html_out, form.__name__
        return

    client = _client(app)
    gets, posts = _get_post_paths(app)
    assert gets or posts, f'{path.name}: no routes found'
    for url in gets:
        response = client.get(url)
        assert _status(response) < 500, f'GET {url} -> {_status(response)}'
    for url in posts:
        response = client.post(url, data={})
        assert _status(response) < 500, f'POST {url} -> {_status(response)}'
