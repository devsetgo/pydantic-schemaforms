import pytest

from pydantic_schemaforms.inputs.base import BaseInput
from pydantic_schemaforms.inputs.registry import (
    get_input_component_map,
    register_input_class,
    reset_input_registry,
)
from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.layout_engine import LayoutEngine


class _FancyInput(BaseInput):
    ui_element = 'fancy'
    ui_element_aliases = ('fn',)

    def get_input_type(self) -> str:  # pragma: no cover - simple return
        return 'text'

    def render(self, **kwargs):  # pragma: no cover - simple return
        return '<input>'


class _DummyRenderer:
    framework = 'bootstrap'


@pytest.fixture(autouse=True)
def _reset_registries():
    yield
    reset_input_registry()
    LayoutEngine.reset_layout_renderers()


def test_register_input_class_populates_component_map():
    register_input_class(_FancyInput)
    mapping = get_input_component_map()

    assert mapping['fancy'] is _FancyInput
    assert mapping['fn'] is _FancyInput


def test_layout_engine_custom_renderer_is_invoked():
    calls = {}

    def handler(field_name, field_schema, value, ui_info, context, engine):
        calls['field'] = field_name
        calls['value'] = value
        return '<div>custom-layout</div>'

    LayoutEngine.register_layout_renderer('custom_layout', handler)

    engine = LayoutEngine(renderer=_DummyRenderer())
    ui_info = {'layout_handler': 'custom_layout'}
    output = engine._build_layout_body(
        'my_layout',
        {'ui': ui_info},
        {'steps': [1, 2]},
        ui_info,
        RenderContext(form_data={}, schema_defs={}),
    )

    assert 'custom-layout' in output
    assert calls['field'] == 'my_layout'
    assert calls['value'] == {'steps': [1, 2]}


def test_reset_layout_renderers_preserves_builtin_registrations():
    """Module-level registration (e.g. DataTableLayout's/model_list's own
    renderer) only runs once per process -- reset_layout_renderers() is
    called between many tests across the suite, so a builtin renderer must
    survive it or it's gone for the rest of the run. Only ad hoc/app-level
    renderers (registered without builtin=True) should actually get
    cleared."""

    def one_off_handler(field_name, field_schema, value, ui_info, context, engine):
        return '<div>one-off</div>'

    def library_handler(field_name, field_schema, value, ui_info, context, engine):
        return '<div>library-owned</div>'

    LayoutEngine.register_layout_renderer('one_off', one_off_handler)
    LayoutEngine.register_layout_renderer('library_owned', library_handler, builtin=True)
    try:
        LayoutEngine.reset_layout_renderers()

        assert LayoutEngine.get_renderer_for_element('one_off') is None
        assert LayoutEngine.get_renderer_for_element('library_owned') is library_handler
    finally:
        # builtin registrations survive reset_layout_renderers() by design,
        # so this test must clean up after itself explicitly.
        LayoutEngine._custom_renderers.pop('library_owned', None)
        LayoutEngine._builtin_renderer_names.discard('library_owned')


def test_layout_renderer_decorator_registers_as_builtin_by_default():
    @LayoutEngine.layout_renderer('decorator_registered')
    def handler(field_name, field_schema, value, ui_info, context, engine):
        return '<div>decorated</div>'

    try:
        LayoutEngine.reset_layout_renderers()

        assert LayoutEngine.get_renderer_for_element('decorator_registered') is handler
    finally:
        LayoutEngine._custom_renderers.pop('decorator_registered', None)
        LayoutEngine._builtin_renderer_names.discard('decorator_registered')


def test_requires_multipart_predicate_is_consulted_with_the_fields_value():
    # A layout field's own schema only ever says ui_element == 'layout' --
    # it can't reveal that its *rendered output* contains a nested file
    # input (like DataTableLayout's does when csv_upload is on). Without a
    # way to ask "does *this* value need multipart", a form embedding one
    # would silently miss enctype="multipart/form-data" and a browser would
    # submit the file's name only, never its contents.
    def handler(field_name, field_schema, value, ui_info, context, engine):
        return '<div>with-upload</div>'

    def needs_multipart(value):
        return bool((value or {}).get('has_file'))

    LayoutEngine.register_layout_renderer(
        'with_upload', handler, builtin=True, requires_multipart=needs_multipart
    )
    try:
        assert LayoutEngine.layout_field_needs_multipart('with_upload', {'has_file': True}) is True
        assert (
            LayoutEngine.layout_field_needs_multipart('with_upload', {'has_file': False}) is False
        )
        assert LayoutEngine.layout_field_needs_multipart('with_upload', None) is False
        assert LayoutEngine.layout_field_needs_multipart('no_such_handler', {}) is False
        assert LayoutEngine.layout_field_needs_multipart(None, {}) is False
    finally:
        LayoutEngine._custom_renderers.pop('with_upload', None)
        LayoutEngine._builtin_renderer_names.discard('with_upload')
        LayoutEngine._multipart_predicates.pop('with_upload', None)


def test_requires_multipart_predicate_cleared_on_reset_when_not_builtin():
    def handler(field_name, field_schema, value, ui_info, context, engine):
        return '<div>one-off</div>'

    LayoutEngine.register_layout_renderer(
        'one_off_upload', handler, requires_multipart=lambda value: True
    )
    LayoutEngine.reset_layout_renderers()

    assert LayoutEngine.layout_field_needs_multipart('one_off_upload', {}) is False
