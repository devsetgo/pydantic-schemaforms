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
from html.parser import HTMLParser
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


def _library_inputs() -> dict[str, type]:
    # The registry also finds inputs by subclass, so a custom input defined
    # by another test module would show up here depending on test order.
    return {
        name: cls
        for name, cls in get_input_component_map().items()
        if cls.__module__.startswith('pydantic_schemaforms.')
    }


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
        path.read_text(encoding='utf-8')
        for path in EXAMPLES_DIR.glob('*.py')
        if path.name != CHEATSHEET
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
    component_map = _library_inputs()
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
    missing = sorted(set(_library_inputs()) - used - SECURITY_ELEMENTS)
    assert not missing, f'No example form uses these ui_elements: {missing}'


def test_security_inputs_are_demonstrated() -> None:
    source = _example_source()
    for element in ('captcha', 'honeypot'):
        assert re.search(rf"(?:ui_element|input_type)\s*=\s*['\"]{element}['\"]", source), element
    assert 'csrf_mode=' in source


@pytest.mark.parametrize(
    'cls',
    sorted(set(_library_inputs().values()), key=lambda c: c.__name__),
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
    assert '/layouts/field-groups' in home
    for field_option in (
        'ui_step_title',
        'ui_collapsible',
        'ui_collapsed',
        'ui_group',
        'ui_cols',
        'ui_group_collapsible',
        'ui_group_collapsed',
        'ui_group_show_when',
    ):
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


class _FormValues(HTMLParser):
    """Collect what a browser would submit for a page's forms."""

    def __init__(self) -> None:
        super().__init__()
        self.values: list[tuple[str, str]] = []
        self.files: list[str] = []
        self._template_depth = 0
        self._textarea: str | None = None
        self._select: str | None = None
        self._first_option: str | None = None
        self._selected = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # model_list's add-item rows live in <template>, which browsers never submit.
        if tag == 'template':
            self._template_depth += 1
        a = dict(attrs)
        name = a.get('name')
        if self._template_depth or 'disabled' in a:
            return
        if tag == 'input' and name:
            input_type = a.get('type') or 'text'
            if input_type in ('submit', 'button', 'reset', 'image'):
                return
            if input_type == 'file':
                self.files.append(name)
            elif input_type not in ('checkbox', 'radio') or 'checked' in a:
                self.values.append((name, a.get('value') or ''))
        elif tag == 'textarea' and name:
            self._textarea = name
            self.values.append((name, ''))
        elif tag == 'select' and name:
            self._select, self._first_option, self._selected = name, None, False
        elif tag == 'option' and self._select:
            value = a.get('value') or ''
            if self._first_option is None:
                self._first_option = value
            if 'selected' in a:
                self.values.append((self._select, value))
                self._selected = True

    def handle_data(self, data: str) -> None:
        if self._textarea and not self._template_depth:
            name, value = self.values[-1]
            self.values[-1] = (name, value + data)

    def handle_endtag(self, tag: str) -> None:
        if tag == 'template':
            self._template_depth -= 1
        elif self._template_depth:
            return
        elif tag == 'textarea':
            self._textarea = None
        elif tag == 'select' and self._select:
            if not self._selected and self._first_option is not None:
                self.values.append((self._select, self._first_option))
            self._select = None


def _submit_rendered_form(client: TestClient, path: str, style: str = 'bootstrap'):
    parser = _FormValues()
    parser.feed(client.get(path, params={'style': style}).text)
    data: dict[str, list[str]] = {}
    for name, value in parser.values:
        data.setdefault(name, []).append(value)
    # A browser sends an empty part for every file input left blank.
    files = [(name, ('', b'', 'application/octet-stream')) for name in parser.files]
    return client.post(path, params={'style': style}, data=data, files=files or None)


# Pages whose rendered demo values are a complete, valid submission. The rest
# start blank, intentionally invalid (/validation), or need a CAPTCHA answer.
_VALID_DEMO_PAGES = [
    '/date-time-formats',
    '/gallery',
    '/layouts',
    '/login',
    '/organization',
    '/organization-shared',
    '/pets',
    '/register',
    '/self-contained',
]


def test_every_example_post_handles_its_own_rendered_values(example_client: TestClient) -> None:
    failures = []
    get_routes = set(_routes('get'))
    for path in _routes('post'):
        if path in get_routes:
            response = _submit_rendered_form(example_client, path)
            if response.status_code >= 500:
                failures.append((path, response.status_code))
    assert not failures


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
@pytest.mark.parametrize('path', _VALID_DEMO_PAGES)
def test_valid_demo_values_submit_successfully(path: str, style: str) -> None:
    client = TestClient(examples.main.app)
    response = _submit_rendered_form(client, path, style)
    assert response.status_code == 200
    assert 'alert-success' in response.text, path


def _example_form_models() -> list[type[FormModel]]:
    import importlib
    import pkgutil

    import examples

    models: set[type[FormModel]] = set()
    for module_info in pkgutil.iter_modules(examples.__path__):
        module = importlib.import_module(f'examples.{module_info.name}')
        models.update(
            obj
            for obj in vars(module).values()
            if isinstance(obj, type) and issubclass(obj, FormModel) and obj is not FormModel
        )
    return sorted(models, key=lambda m: m.__qualname__)


def test_every_example_option_value_validates_against_its_field() -> None:
    from pydantic import TypeAdapter, ValidationError

    rejected = []
    for model in _example_form_models():
        for name, field in model.model_fields.items():
            extra = field.json_schema_extra if isinstance(field.json_schema_extra, dict) else {}
            adapter = TypeAdapter(field.annotation)
            for option in extra.get('options') or []:
                value = option.get('value') if isinstance(option, dict) else option
                if isinstance(option, dict) and 'options' in option:
                    continue
                try:
                    adapter.validate_python(value)
                except ValidationError:
                    try:
                        adapter.validate_python([value])
                    except ValidationError:
                        rejected.append((model.__qualname__, name, value))
    assert not rejected, f'Options the field itself rejects: {rejected}'


def test_showcase_rerenders_errors_after_a_correct_captcha() -> None:
    client = TestClient(examples.main.app)
    page = client.get('/showcase').text
    question = re.search(r'What is (\d+) ([-+]) (\d+)\?', page)
    assert question
    a, op, b = int(question[1]), question[2], int(question[3])
    csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page)
    token = re.search(r'name="captcha_answer_token"[^>]*value="([^"]+)"', page)
    assert csrf and token
    response = client.post(
        '/showcase',
        data={
            'csrf_token': csrf[1],
            'captcha_answer_token': token[1],
            'captcha_answer': str(a + b if op == '+' else a - b),
        },
    )
    assert response.status_code == 200
    assert 'Submission failed.' in response.text


@pytest.mark.parametrize('style', ['bootstrap', 'material'])
def test_every_example_form_posts_back_in_its_own_style(
    example_client: TestClient, style: str
) -> None:
    """A submit_url without ?style= drops a Material page back to Bootstrap on POST."""
    post_routes = set(_routes('post'))
    lost: dict[str, str] = {}
    for path in _routes('get'):
        response = example_client.get(path, params={'style': style})
        if response.status_code != 200:
            continue
        for action in re.findall(r'<form\b[^>]*\baction="([^"]*)"', response.text):
            action = action.replace('&amp;', '&')
            if action.split('?')[0] in post_routes and f'style={style}' not in action:
                lost[path] = action
    assert not lost


@pytest.mark.parametrize('path', ['/gallery', '/layouts'])
def test_filled_variant_survives_a_failed_submission(example_client: TestClient, path: str) -> None:
    params = {'style': 'material', 'variant': 'filled'}
    page = example_client.get(path, params=params)
    assert 'md-form--filled' in page.text
    assert 'variant=filled' in re.search(r'<form\b[^>]*\baction="([^"]*)"', page.text).group(1)

    failed = example_client.post(path, params=params, data={'unexpected': 'value'})
    assert 'md-form--filled' in failed.text
    assert 'variant=filled' in re.search(r'<form\b[^>]*\baction="([^"]*)"', failed.text).group(1)


@pytest.mark.parametrize(
    ('cookie', 'url', 'is_material'),
    [
        ('material', '/login', True),
        ('bootstrap', '/login?style=material', True),
        ('material', '/login?style=bootstrap', False),
        ('nonsense', '/login', False),
    ],
)
def test_the_style_cookie_applies_only_when_the_url_names_no_style(
    cookie: str, url: str, is_material: bool
) -> None:
    client = TestClient(examples.main.app, cookies={'sf-style': cookie})
    form_tag = re.search(r'<form[^>]*>', client.get(url).text).group(0)
    assert ('md-form' in form_tag) is is_material
