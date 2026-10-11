"""The example app must demonstrate every layout, input type, widget option,
and kind of validation (CLAUDE.md, "Examples must cover every layout, input,
and validation").

Input options are read from each input class's own render()/__init__
signature, so adding an option to a widget fails this file until an example
uses it.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import examples.main
from examples import (
    datatable_import_example,
    date_time_formats_example,
    menu_order_example,
    nested_forms_example,
    shared_models,
)
from pydantic_schemaforms import FormModel, validation
from pydantic_schemaforms.inputs.registry import get_input_component_map
from pydantic_schemaforms.rendering.layout_engine import LAYOUTS, WIZARD_OPTIONS

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / 'examples'
# Static cheatsheet text, not a rendered form; it must not count as coverage.
CHEATSHEET = 'input_type_reference.py'

# render()/__init__ parameters that are not widget options: the field
# plumbing every input receives, and values the library fills in itself.
NOT_OPTIONS = {
    'self', 'name', 'id', 'value', 'label', 'help_text', 'error', 'required',
    'placeholder', 'options', 'framework', 'icon', 'group_name', 'legend',
    'token', 'secret_key', 'current_rating',
}  # fmt: skip

# Security inputs are demonstrated on /showcase through their own flows
# (CSRF via csrf_mode=, CAPTCHA verified in the route), not as gallery widgets.
SECURITY_ELEMENTS = {'csrf', 'captcha', 'honeypot'}


def _example_source() -> str:
    return '\n'.join(
        path.read_text() for path in EXAMPLES_DIR.glob('*.py') if path.name != CHEATSHEET
    )


def _example_models() -> list[type[FormModel]]:
    modules = (
        shared_models,
        menu_order_example,
        datatable_import_example,
        date_time_formats_example,
        nested_forms_example,
    )
    models = {
        obj
        for module in modules
        for obj in vars(module).values()
        if isinstance(obj, type) and issubclass(obj, FormModel)
    }
    return sorted(models, key=lambda m: m.__name__)


def _field_schemas(model: type[FormModel]) -> list[dict[str, Any]]:
    try:
        schema = model.model_json_schema()
    except Exception:  # noqa: BLE001 - abstract/composite models without a schema
        return []
    nodes = [schema, *(schema.get('$defs') or {}).values()]
    return [prop for node in nodes for prop in (node.get('properties') or {}).values()]


def _used_options() -> dict[str, set[str]]:
    """{input class name: option keys some example field passes it}."""
    component_map = get_input_component_map()
    used: dict[str, set[str]] = {}
    for model in _example_models():
        for prop in _field_schemas(model):
            element = prop.get('ui_element') or prop.get('input_type')
            cls = component_map.get(element)
            if cls is None:
                continue
            ui_options = prop.get('ui_options') or {}
            keys = set(ui_options) if isinstance(ui_options, dict) else set()
            used.setdefault(cls.__name__, set()).update(keys)
    return used


def _declared_options(cls: type) -> set[str]:
    names: set[str] = set()
    for method_name in ('__init__', 'render'):
        method = getattr(cls, method_name, None)
        try:
            parameters = inspect.signature(method).parameters.values()
        except TypeError, ValueError:
            continue
        names |= {
            p.name
            for p in parameters
            if p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL) and p.name not in NOT_OPTIONS
        }
    return names


def test_every_registered_input_name_and_alias_is_used_by_an_example() -> None:
    source = _example_source()
    used = set(re.findall(r"(?:ui_element|input_type)\s*=\s*['\"]([\w-]+)['\"]", source))
    missing = sorted(set(get_input_component_map()) - used - SECURITY_ELEMENTS)
    assert not missing, f'No example form uses these ui_elements: {missing}'


def test_security_inputs_are_demonstrated() -> None:
    source = _example_source()
    for element in ('captcha', 'honeypot'):
        assert re.search(rf"(?:ui_element|input_type)\s*=\s*['\"]{element}['\"]", source), element
    assert 'csrf_mode=' in source


@pytest.mark.parametrize(
    'cls',
    sorted(set(get_input_component_map().values()), key=lambda c: c.__name__),
    ids=lambda cls: cls.__name__,
)
def test_every_widget_option_is_used_by_an_example(cls: type) -> None:
    missing = _declared_options(cls) - _used_options().get(cls.__name__, set())
    assert not missing, (
        f'{cls.__name__} options never passed by an example form via ui_options: '
        f'{sorted(missing)}. Add a field to the widget gallery (examples/shared_models.py).'
    )


def test_every_layout_and_wizard_option_is_demonstrated() -> None:
    client = TestClient(examples.main.app)
    home = client.get('/').text
    for layout in sorted(LAYOUTS):
        response = client.get('/layouts', params={'layout': layout})
        assert response.status_code == 200, layout
        # Reachable is not enough: a reader has to be able to find it.
        assert f'/layouts?layout={layout}' in home, f'home page has no link to layout={layout}'
        assert f'layout={layout}' in response.text, f'/layouts has no switcher link to {layout}'
    wizard = client.get(
        '/layouts',
        params={'layout': 'wizard', 'linear': 'false', 'progress': 'false', 'labels': 'true'},
    ).text
    assert 'data-linear="false"' in wizard
    assert 'class="wizard-progress"' not in wizard
    assert '>Continue</button>' in wizard
    source = _example_source()
    for option in WIZARD_OPTIONS:
        assert f"'{option}'" in source, f'wizard_options key {option!r} is never used'
    for field_option in ('ui_step_title', 'ui_collapsible', 'ui_collapsed'):
        assert field_option in source, field_option


def test_every_validation_kind_is_demonstrated() -> None:
    source = _example_source()
    for constraint in (
        'min_length',
        'max_length',
        'ge',
        'le',
        'gt',
        'lt',
        'pattern',
        'multiple_of',
    ):
        assert re.search(rf'\b{constraint}=', source), f'no example uses Field({constraint}=...)'
    for construct in (
        '@field_validator',
        '@model_validator',
        'add_cross_field_rule',
        'LiveValidator',
    ):
        assert construct in source, construct
    rule_classes = {
        name
        for name, obj in vars(validation).items()
        if isinstance(obj, type)
        and issubclass(obj, validation.ValidationRule)
        and obj is not validation.ValidationRule
        and name in validation.__all__
    }
    missing = sorted(name for name in rule_classes if f'{name}(' not in source)
    assert not missing, f'No example uses these validation rules: {missing}'


@pytest.fixture(scope='module')
def example_client() -> TestClient:
    return TestClient(examples.main.app, raise_server_exceptions=False)


def _routes(method: str) -> list[str]:
    paths = examples.main.app.openapi()['paths']
    return sorted(path for path, ops in paths.items() if method in ops and '{' not in path)


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_every_example_page_renders(example_client: TestClient, style: str) -> None:
    failures = []
    for path in _routes('get'):
        response = example_client.get(path, params={'style': style})
        if response.status_code >= 500 or '<!-- Error' in response.text:
            failures.append((path, response.status_code))
    assert not failures


def test_every_example_post_handles_a_bad_submission(example_client: TestClient) -> None:
    failures = []
    for path in _routes('post'):
        response = example_client.post(path, data={'unexpected': 'value'})
        if response.status_code >= 500:
            failures.append((path, response.status_code))
    assert not failures
