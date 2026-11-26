"""Content-Security-Policy compatibility of rendered output.

A strict ``script-src`` never runs inline event-handler attributes, nonce or not,
so the library's markup must wire its behavior up from its own scripts.
"""

from __future__ import annotations

import ast
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path

import pytest

from examples.shared_models import LayoutDemonstrationForm, WidgetGalleryForm
from pydantic_schemaforms import (
    Field,
    FormModel,
    FormValidator,
    LiveValidator,
    ModalLayout,
    SafeHTML,
)
from pydantic_schemaforms.csp import app_style_scope, csp_nonces, script_tag, style_attr
from pydantic_schemaforms.rendering.layout_engine import LAYOUTS

FRAMEWORKS = ('bootstrap', 'material', 'none')
_HANDLER_ATTR = re.compile(r'<[a-zA-Z][^>]*\son[a-z]+\s*=', re.IGNORECASE)


def _handlers(markup: str) -> list[str]:
    return [match.group(0)[:120] for match in _HANDLER_ATTR.finditer(markup)]


@pytest.mark.parametrize('framework', FRAMEWORKS)
@pytest.mark.parametrize('layout', sorted(LAYOUTS))
def test_layouts_render_no_inline_event_handlers(framework: str, layout: str) -> None:
    markup = LayoutDemonstrationForm.render_form(
        framework=framework, submit_url='/x', layout=layout
    )
    assert _handlers(markup) == []


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_every_widget_renders_no_inline_event_handlers(framework: str) -> None:
    markup = WidgetGalleryForm.render_form(
        framework=framework, submit_url='/x', include_framework_assets=True
    )
    assert _handlers(markup) == []


def test_modal_layout_renders_no_inline_event_handlers() -> None:
    assert _handlers(ModalLayout('m1', 'Title', 'Body').render()) == []


_PACKAGE = Path(__file__).resolve().parent.parent / 'pydantic_schemaforms'
_TAG_LITERAL = re.compile(r'<(script|style)\b', re.IGNORECASE)
_STYLE_ATTR_LITERAL = re.compile(r'\bstyle\s*=\s*["\'$]|setAttribute\(\s*["\']style', re.IGNORECASE)


def _docstring_nodes(tree: ast.AST) -> set[int]:
    owners = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, owners) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                found.add(id(first.value))
    return found


def _tag_literals(path: Path, pattern: re.Pattern[str] = _TAG_LITERAL) -> list[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    docstrings = _docstring_nodes(tree)
    hits = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and pattern.search(node.value)
        ):
            hits.append(f'{path.relative_to(_PACKAGE.parent)}:{node.lineno}')
    return hits


def test_only_the_csp_helpers_write_script_and_style_tags() -> None:
    """Every <script>/<style> goes through pydantic_schemaforms.csp, so each gets the nonce."""
    offenders = [
        hit
        for path in sorted(_PACKAGE.rglob('*.py'))
        if 'vendor' not in path.parts and path.name != 'csp.py'
        for hit in _tag_literals(path)
    ]
    assert offenders == [], 'Build these tags with csp.script_tag/style_tag:\n' + '\n'.join(
        offenders
    )


NONCE = 'abc123DEF456'
NONCES = {'script_nonce': NONCE, 'style_nonce': NONCE}


class _TagCounter(HTMLParser):
    """Real start tags only: script and style content is raw text, so a '<script'
    inside JavaScript (as in vendored DataTables) is not counted."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ('script', 'style'):
            self.tags.append((tag, dict(attrs).get('nonce')))


def _tags(markup: str) -> list[tuple[str, str | None]]:
    counter = _TagCounter()
    counter.feed(markup)
    return counter.tags


def _assert_all_nonced(markup: str, nonce: str = NONCE) -> None:
    tags = _tags(markup)
    assert tags, 'expected the render to emit at least one <script> or <style>'
    assert [tag for tag in tags if tag[1] != nonce] == []


@pytest.mark.parametrize('framework', FRAMEWORKS)
@pytest.mark.parametrize('layout', sorted(LAYOUTS))
def test_every_layout_tag_carries_the_nonce(framework: str, layout: str) -> None:
    _assert_all_nonced(
        LayoutDemonstrationForm.render_form(
            framework=framework, submit_url='/x', layout=layout, **NONCES
        )
    )


@pytest.mark.parametrize('framework', FRAMEWORKS)
@pytest.mark.parametrize('asset_mode', ['vendored', 'cdn'])
def test_every_widget_and_asset_tag_carries_the_nonce(framework: str, asset_mode: str) -> None:
    markup = WidgetGalleryForm.render_form(
        framework=framework,
        submit_url='/x',
        include_framework_assets=True,
        asset_mode=asset_mode,
        **NONCES,
    )
    _assert_all_nonced(markup)


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_display_tags_carry_the_nonce(framework: str) -> None:
    _assert_all_nonced(WidgetGalleryForm.render_display({}, framework=framework, **NONCES))


@pytest.mark.asyncio
async def test_async_render_and_datatable_tags_carry_the_nonce() -> None:
    from examples.datatable_import_example import EmployeeImport, EmployeeImportForm

    markup = await EmployeeImportForm.render_form_async(
        data={'employees': EmployeeImport.as_layout_value(rows=[], table_id='t')},
        submit_url='/x',
        include_framework_assets=True,
        **NONCES,
    )
    _assert_all_nonced(markup)


def test_script_and_style_nonces_are_independent() -> None:
    markup = LayoutDemonstrationForm.render_form(
        submit_url='/x', layout='tabbed', script_nonce='scriptN0nce', style_nonce='styleN0nce'
    )
    tags = _tags(markup)
    assert {nonce for tag, nonce in tags if tag == 'script'} == {'scriptN0nce'}
    assert {nonce for tag, nonce in tags if tag == 'style'} == {'styleN0nce'}


def test_render_with_errors_keeps_the_nonce_given_to_validate() -> None:
    result = WidgetGalleryForm.validate({}, submit_url='/x', framework='material', **NONCES)
    assert not result.is_valid
    _assert_all_nonced(result.render_with_errors())


def test_wizard_step_render_keeps_the_nonce_given_to_validate_step() -> None:
    from examples.job_application_example import JobApplicationForm, _apply_options

    result = JobApplicationForm.validate_step(
        {}, draft=None, **_apply_options('bootstrap', None), **NONCES
    )
    _assert_all_nonced(result.render())


def test_no_nonce_renders_exactly_as_before() -> None:
    plain = LayoutDemonstrationForm.render_form(submit_url='/x', layout='vertical')
    assert (
        LayoutDemonstrationForm.render_form(
            submit_url='/x', layout='vertical', script_nonce=None, style_nonce=None
        )
        == plain
    )
    assert 'nonce=' not in plain


def test_standalone_scripts_take_a_nonce() -> None:
    validator = FormValidator()
    validator.field('name').required()
    _assert_all_nonced(validator.generate_client_validation_script(**NONCES))
    _assert_all_nonced(LiveValidator().render_htmx_script(script_nonce=NONCE))
    with csp_nonces(**NONCES):
        _assert_all_nonced(ModalLayout('m1', 'Title', 'Body').render())


def test_a_nested_block_without_a_nonce_keeps_the_outer_one() -> None:
    with csp_nonces(script_nonce='outerN0nce'):
        with csp_nonces():
            assert 'nonce="outerN0nce"' in script_tag('1')
    assert 'nonce=' not in script_tag('1')


def test_app_written_scripts_in_content_blocks_get_no_nonce() -> None:
    class Page(FormModel):
        note: None = Field(
            ui_element='content',
            ui_content=SafeHTML('<p>Hi</p><script>evil()</script>'),
        )

    tags = _tags(Page.render_form(submit_url='/x', **NONCES))
    assert ('script', None) in tags


@pytest.mark.parametrize(
    'bad', ['x" onload="alert(1)', 'has space', '', 'abc<def', 'a=b', 'tooo===', 42]
)
def test_a_malformed_nonce_is_rejected(bad: object) -> None:
    with pytest.raises(ValueError, match='script_nonce'):
        LayoutDemonstrationForm.render_form(submit_url='/x', script_nonce=bad)
    with pytest.raises(ValueError, match='style_nonce'):
        WidgetGalleryForm.render_display({}, style_nonce=bad)
    with pytest.raises(ValueError, match='script_nonce'):
        WidgetGalleryForm.validate({}, submit_url='/x', script_nonce=bad)
    with pytest.raises(ValueError, match='style_nonce'):
        WidgetGalleryForm.validate_step({}, submit_url='/x', style_nonce=bad)


@pytest.mark.parametrize('good', ['abc123DEF456', 'r4nd0m+/base64==', 'url_safe-token_', 'A='])
def test_base64_and_base64url_nonces_are_accepted(good: str) -> None:
    assert f'nonce="{good}"' in LayoutDemonstrationForm.render_form(
        submit_url='/x', script_nonce=good
    )


def test_no_style_attribute_is_written_in_package_source() -> None:
    """A strict style-src blocks every style="" attribute, even an empty one: the library's
    own styling lives in its stylesheets, and an app's ui_style goes through csp.style_attr."""
    offenders = [
        hit
        for path in sorted(_PACKAGE.rglob('*.py'))
        if 'vendor' not in path.parts and path.name != 'csp.py'
        for hit in _tag_literals(path, _STYLE_ATTR_LITERAL)
    ]
    assert offenders == [], 'Use a class, the hidden attribute or csp.style_attr:\n' + '\n'.join(
        offenders
    )


class _StyleAttrs(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.values += [value or '' for name, value in attrs if name == 'style']


def _style_attrs(markup: str) -> set[str]:
    parser = _StyleAttrs()
    parser.feed(markup)
    return set(parser.values)


# The gallery's ui_style demo: an app's own inline style, passed through as given.
_APP_STYLES = {'font-weight: 600'}


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_rendered_output_has_no_library_style_attributes(framework: str) -> None:
    renders = [
        WidgetGalleryForm.render_form(
            framework=framework, submit_url='/x', include_framework_assets=True
        ),
        WidgetGalleryForm.render_display({}, framework=framework),
        WidgetGalleryForm.validate({}, submit_url='/x', framework=framework).render_with_errors(),
        *(
            LayoutDemonstrationForm.render_form(framework=framework, submit_url='/x', layout=layout)
            for layout in sorted(LAYOUTS)
        ),
    ]
    for markup in renders:
        assert _style_attrs(markup) <= _APP_STYLES


def test_legacy_layouts_write_no_style_attribute_unless_given_one() -> None:
    assert _style_attrs(ModalLayout('m1', 'Title', 'Body').render()) == set()


@pytest.mark.asyncio
async def test_a_request_wide_block_reaches_sync_async_and_rerenders() -> None:
    from pydantic_schemaforms import csp_nonces as exported

    with exported(**NONCES):
        _assert_all_nonced(LayoutDemonstrationForm.render_form(submit_url='/x', layout='tabbed'))
        _assert_all_nonced(
            await LayoutDemonstrationForm.render_form_async(submit_url='/x', layout='accordion')
        )
        result = WidgetGalleryForm.validate({}, submit_url='/x')
        _assert_all_nonced(await result.render_with_errors_async())
        _assert_all_nonced(WidgetGalleryForm.render_display({}))


def _gallery_with_app_style(**options: object) -> str:
    return WidgetGalleryForm.render_form(framework='material', submit_url='/x', **options)


def test_an_app_style_becomes_a_nonced_rule_under_a_style_nonce() -> None:
    markup = _gallery_with_app_style(**NONCES)
    assert _style_attrs(markup) == set()
    key = re.search(r'data-schemaforms-style="([0-9a-f]{12})"', markup)
    assert key
    block = re.search(
        r'<style data-schemaforms-app-styles nonce="abc123DEF456">(.*?)</style>', markup, re.S
    )
    assert (
        block
        and f'[data-schemaforms-style="{key.group(1)}"] {{ font-weight: 600 !important; }}'
        in (block.group(1))
    )
    assert markup.count('data-schemaforms-app-styles') == 1


def test_an_app_style_stays_an_attribute_without_a_style_nonce() -> None:
    markup = _gallery_with_app_style(script_nonce=NONCE)
    assert _style_attrs(markup) == _APP_STYLES
    assert 'data-schemaforms-style' not in markup


@pytest.mark.parametrize('bad', ['color: red} body {color: blue', 'x: url(<a>)', '{'])
def test_an_app_style_that_could_leave_its_rule_is_rejected(bad: str) -> None:
    with pytest.raises(ValueError, match='ui_style'):
        Field('', ui_style=bad)
    with csp_nonces(style_nonce=NONCE), pytest.raises(ValueError, match='inline style'):
        with app_style_scope():
            style_attr(bad)
    assert style_attr(bad) == f' style="{escape(bad)}"'
