from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Optional

import pytest
from pydantic import BaseModel

from pydantic_schemaforms.assets import runtime as runtime_assets
from pydantic_schemaforms.enhanced_renderer import (
    EnhancedFormRenderer,
    SchemaFormValidationError,
    render_form_html,
    render_form_html_async,
)
from pydantic_schemaforms.form_field import (
    CheckboxField,
    DateField,
    EmailField,
    FormField,
    NumberField,
    SelectField,
    TextAreaField,
    TextField,
    create_field_with_validation,
)
from pydantic_schemaforms.form_layouts import FormDesign, ListLayout, TabbedLayout, VerticalLayout
from pydantic_schemaforms.modern_renderer import (
    FormDefinition,
    FormField as LegacyFormField,
    FormSection,
    ModernFormRenderer,
)
from pydantic_schemaforms.rendering.themes import RendererTheme
from pydantic_schemaforms.schema_form import Field, FormModel


class _SimpleForm(FormModel):
    name: str = Field(..., title='Name')


def test_runtime_asset_helpers_cover_modes_and_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime_assets, '_vendor_manifest', lambda: {'assets': 'invalid'})
    assert runtime_assets.vendored_asset_version('htmx') is None

    monkeypatch.setattr(runtime_assets, '_vendor_manifest', lambda: {'assets': []})
    assert runtime_assets.vendored_asset_version('missing') is None

    def _missing(_path: str) -> str:
        raise FileNotFoundError('missing')

    monkeypatch.setattr(runtime_assets, 'read_asset_text', _missing)
    assert runtime_assets._vendored_text_or_empty('missing.css') == ''

    monkeypatch.setattr(runtime_assets, 'read_asset_text', lambda _path: 'console.log(1)')
    assert runtime_assets.htmx_script_tag(asset_mode='none') == ''
    assert runtime_assets.imask_script_tag(asset_mode='none') == ''
    assert 'unpkg.com' in runtime_assets.imask_script_tag(asset_mode='cdn')
    assert '<script>' in runtime_assets.imask_script_tag(asset_mode='vendored')

    monkeypatch.setattr(runtime_assets, '_vendored_text_or_empty', lambda _path: '/*css*/')
    css_material = runtime_assets.framework_css_tag(framework='material', asset_mode='vendored')
    css_cdn = runtime_assets.framework_css_tag(framework='material', asset_mode='cdn')
    assert '<style>' in css_material
    assert 'cdn.jsdelivr.net' in css_cdn

    monkeypatch.setattr(runtime_assets, '_vendored_text_or_empty', lambda _path: '//js')
    js_material = runtime_assets.framework_js_tag(framework='material', asset_mode='vendored')
    js_cdn = runtime_assets.framework_js_tag(framework='material', asset_mode='cdn')
    assert '<script>' in js_material
    assert 'cdn.jsdelivr.net' in js_cdn
    assert runtime_assets.framework_css_tag(framework='unknown', asset_mode='vendored') == ''
    assert runtime_assets.framework_js_tag(framework='unknown', asset_mode='vendored') == ''


def test_form_field_convenience_helpers_and_optional_validation() -> None:
    FormField.validate_input_type(Optional[str], 'text', 'title')
    inferred = FormField.get_default_input_type(Optional[str])
    assert isinstance(inferred, str)
    assert FormField.format_icon('user', framework='bootstrap')

    auto_field = create_field_with_validation(str, title='Auto')
    assert auto_field.json_schema_extra.get('input_type') == 'text'

    text_field = TextField(title='Text')
    email_field = EmailField()
    number_field = NumberField(min_value=1, max_value=10)
    select_field = SelectField(options=['A', 'B'])
    checkbox_field = CheckboxField()
    date_field = DateField()
    textarea_field = TextAreaField(rows=7)

    assert text_field.json_schema_extra.get('input_type') == 'text'
    assert email_field.json_schema_extra.get('placeholder') == 'example@example.com'
    assert email_field.json_schema_extra.get('icon') == 'envelope'
    assert number_field.json_schema_extra.get('input_type') == 'number'
    assert select_field.json_schema_extra.get('options') == ['A', 'B']
    assert checkbox_field.json_schema_extra.get('input_type') == 'checkbox'
    assert date_field.json_schema_extra.get('icon') == 'calendar'
    assert textarea_field.json_schema_extra.get('rows') == 7


def test_modern_renderer_legacy_field_and_model_definition_paths() -> None:
    def _false_validator(_value: object) -> bool:
        return False

    def _error_validator(_value: object) -> bool:
        raise ValueError('bad value')

    legacy = LegacyFormField(
        'city',
        required=True,
        validators=[_false_validator, _error_validator],
        options=[{'value': 'nyc', 'label': 'NYC'}],
        attributes={'maxlength': 30},
        **{'class': 'x', 'style': 'y', 'order': 9, 'meta': 'v', 'ignored_list': [1], 'ignored_dict': {'k': 'v'}},
    )

    assert not legacy.validate('')
    legacy.required = False
    assert not legacy.validate('ok')
    assert any('failed validation' in msg for msg in legacy.errors)
    assert any('bad value' in msg for msg in legacy.errors)

    _annotation, schema_field = legacy.as_model_field(order=1, section='Section A')
    assert schema_field.json_schema_extra.get('ui_section') == 'Section A'
    assert schema_field.json_schema_extra.get('ui_order') == 1

    form_def = FormDefinition(
        title='My Form!',
        sections=[FormSection('Main', [LegacyFormField('name', required=True)])],
        honeypot_protection=True,
    )
    model_cls_1 = form_def.to_form_model_class()
    model_cls_2 = form_def.to_form_model_class()
    assert model_cls_1 is model_cls_2
    assert 'honeypot_trap' in model_cls_1.model_fields

    with pytest.raises(ValueError, match='at least one field'):
        FormDefinition(title='Empty').to_form_model_class()


def test_modern_renderer_aliases_extract_and_theme_clone_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = ModernFormRenderer()
    form_def = FormDefinition(sections=[FormSection('Main', [LegacyFormField('name', required=True)])])

    async def _fake_render_form_async(*_args, **_kwargs) -> str:
        return 'ok'

    monkeypatch.setattr(renderer, 'render_form_async', _fake_render_form_async)
    assert asyncio.run(renderer.render_async(form_def)) == 'ok'
    assert asyncio.run(renderer.async_render(form_def)) == 'ok'

    fake_metadata = SimpleNamespace(
        fields=[('choice', {'title': 'Choice', 'description': 'desc', 'ui': {'options': 'x', 'ui_section': 'sec'}})],
        required_fields={'choice'},
    )
    monkeypatch.setattr('pydantic_schemaforms.modern_renderer.build_schema_metadata', lambda _model: fake_metadata)
    monkeypatch.setattr('pydantic_schemaforms.modern_renderer.resolve_ui_element', lambda _schema: None)
    extracted = renderer.extract_form_fields(_SimpleForm)
    assert extracted[0].field_type == 'text'
    assert extracted[0].options == []

    class _NeedsArgTheme(RendererTheme):
        def __init__(self, submit_label: str) -> None:
            super().__init__(submit_label=submit_label)

    renderer_with_custom_theme = ModernFormRenderer(theme=_NeedsArgTheme('Send'))
    cloned = renderer_with_custom_theme._clone_theme()
    assert isinstance(cloned, RendererTheme)
    assert cloned.submit_label == 'Send'

    switched = renderer._ensure_renderer('material')
    assert switched is not renderer
    assert isinstance(switched, ModernFormRenderer)


def test_enhanced_renderer_branches_and_wrappers(monkeypatch: pytest.MonkeyPatch) -> None:
    error = SchemaFormValidationError([{'name': 'field', 'message': 'problem'}])
    assert 'Schema form validation error' in str(error)

    renderer = EnhancedFormRenderer()
    captured: dict[str, object] = {}

    class _FieldInfo:
        def __init__(self, *, default_factory=None, required: bool = False, default=None):
            self.default_factory = default_factory
            self._required = required
            self.default = default

        def is_required(self) -> bool:
            return self._required

    class _FakeModel:
        __name__ = 'FakeModel'
        model_fields = {
            'layout_factory': _FieldInfo(default_factory=lambda: {'seed': 1}),
            'layout_default': _FieldInfo(required=False, default={'d': 2}),
        }

    fake_metadata = SimpleNamespace(
        schema_defs={},
        fields=[('layout_factory', {}), ('layout_default', {})],
        required_fields=[],
        layout_fields=[('layout_factory', {}), ('layout_missing', {}), ('layout_default', {})],
        non_layout_fields=[],
    )
    monkeypatch.setattr('pydantic_schemaforms.enhanced_renderer.build_schema_metadata', lambda _model: fake_metadata)
    monkeypatch.setattr(renderer, '_render_layout_fields_as_tabs', lambda *_args: ['layout-tabs'])
    monkeypatch.setattr(renderer._theme, 'render_form_wrapper', lambda **kwargs: kwargs['form_content'])
    monkeypatch.setattr('pydantic_schemaforms.enhanced_renderer.logger.debug', lambda msg: captured.update({'log': msg}))

    html = renderer.render_form_from_model(
        _FakeModel,
        data={},
        errors={'errors': [{'name': 'layout_default', 'message': 'bad'}]},
        submit_url='/submit',
        enable_logging=True,
    )
    assert 'layout-tabs' in html
    assert 'rendered in' in str(captured.get('log', '')).lower()

    assert renderer._humanize_error_field('[]') == '[]'
    assert renderer._humanize_error_field('[0].name').startswith('Item #1')
    assert renderer._singularize_label('cat') == 'cat'
    assert renderer._render_error_summary({'nested': None}) == ''

    fields_meta = SimpleNamespace(
        schema_defs={},
        fields=[('name', {})],
        required_fields=[],
        layout_fields=[],
        non_layout_fields=[('name', {})],
    )
    monkeypatch.setattr('pydantic_schemaforms.enhanced_renderer.build_schema_metadata', lambda _model: fields_meta)
    monkeypatch.setattr(renderer, '_render_tabbed_layout', lambda *_args: ['tabbed-out'])
    monkeypatch.setattr(renderer, '_render_side_by_side_layout', lambda *_args: ['sbs-out'])
    monkeypatch.setattr(renderer._theme, 'render_form_wrapper', lambda **kwargs: kwargs['form_content'])
    assert 'tabbed-out' in renderer.render_form_from_model(_FakeModel, layout='tabbed', submit_url='/submit')
    assert 'sbs-out' in renderer.render_form_from_model(_FakeModel, layout='side-by-side', submit_url='/submit')

    monkeypatch.setattr(renderer, '_render_field', lambda *args, **kwargs: 'FIELD')
    fields_only = renderer.render_form_fields_only(
        _FakeModel,
        errors={'errors': [{'name': 'name', 'message': 'bad'}]},
    )
    assert fields_only == 'FIELD'

    renderer_wrappers = EnhancedFormRenderer()
    monkeypatch.setattr(renderer_wrappers._layout_engine, 'render_tabbed_layout', lambda *_args: ['X'])
    monkeypatch.setattr(renderer_wrappers._layout_engine, 'render_layout_field_content', lambda *_args: 'Y')
    monkeypatch.setattr(renderer_wrappers._layout_engine, 'render_side_by_side_layout', lambda *_args: ['Z'])
    assert renderer_wrappers._render_tabbed_layout([], {}, {}, [], SimpleNamespace()) == ['X']
    assert renderer_wrappers._render_layout_field_content('n', {}, None, None, {}, SimpleNamespace()) == 'Y'
    assert renderer_wrappers._render_side_by_side_layout([], {}, {}, [], SimpleNamespace()) == ['Z']
    assert renderer_wrappers._get_nested_form_data('name', {'name': {'x': 1}}) == {'x': 1}

    with pytest.raises(ValueError, match='submit_url cannot be empty'):
        render_form_html(_SimpleForm, submit_url='   ')

    converted = render_form_html(
        _SimpleForm,
        submit_url='/submit',
        errors=SchemaFormValidationError([{'name': 'name', 'message': 'oops'}]),
        include_html_markers=False,
    )
    assert 'oops' in converted

    async_html = asyncio.run(
        render_form_html_async(
            _SimpleForm,
            submit_url='/submit',
            self_contained=True,
            include_html_markers=False,
        )
    )
    assert '<form' in async_html


def test_render_form_html_async_falls_back_to_get_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _run() -> str:
        current_loop = asyncio.get_running_loop()
        monkeypatch.setattr('pydantic_schemaforms.enhanced_renderer.asyncio.get_running_loop', lambda: (_ for _ in ()).throw(RuntimeError('no running loop')))
        monkeypatch.setattr('pydantic_schemaforms.enhanced_renderer.asyncio.get_event_loop', lambda: current_loop)
        return await render_form_html_async(_SimpleForm, submit_url='/submit', include_html_markers=False)

    html = asyncio.run(_run())
    assert '<form' in html


@pytest.mark.filterwarnings('ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning')
def test_form_layouts_branches_for_tabbed_and_list_layout() -> None:
    tabbed = TabbedLayout()
    assert tabbed._render_complete_page('x') == 'x'

    designed_tabbed = TabbedLayout(form_config=FormDesign(form_name='Demo', ui_theme='bootstrap'))
    page = designed_tabbed._render_complete_page('<div>Inner</div>')
    assert '<!DOCTYPE html>' in page
    assert 'Demo' in page

    class _ListItemForm(FormModel):
        qty: int = Field(..., title='Quantity')

    class _StubRenderer:
        def render_form_from_model(self, *_args, **_kwargs) -> str:
            return '<label for="qty">Qty</label><input id="qty" name="qty" />'

    list_layout = ListLayout(
        form_model=_ListItemForm,
        min_items=2,
        max_items=1,
        section_design=SimpleNamespace(
            render_header=lambda _framework: '<h3>Items</h3>',
            collapsible=False,
            collapsed=False,
            css_class='custom-list',
        ),
        collapsible_items=True,
    )

    summary = list_layout._create_item_summary({'qty': 0}, index=0)
    assert summary.endswith('#1')

    js = list_layout._render_javascript('list_x', 'material')
    assert 'toggleCollapse' in js
    assert 'Maximum 1 items allowed' in js

    assert 'newCollapseId' in list_layout._render_collapsible_update_js('list_x', 'material')
    assert 'newCollapseId' in list_layout._render_collapsible_reindex_js('list_x', 'material')

    validation = list_layout.validate({'item_0_qty': 'not-int'})
    assert not validation.is_valid
    assert 'item_0' in validation.errors

    rendered = list_layout.render(data=[{'qty': 'bad'}], renderer=_StubRenderer(), framework='bootstrap')
    assert 'list-items-container' in rendered
    assert 'custom-list' in rendered

    rendered_from_items_key = list_layout.render(data={'items': [{'qty': 'bad'}]}, renderer=_StubRenderer())
    assert 'list-items-container' in rendered_from_items_key


@pytest.mark.filterwarnings('ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning')
def test_form_layouts_vertical_horizontal_header_and_exception_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    section = SimpleNamespace(
        render_header=lambda _framework: '<h3>Header</h3>',
        collapsible=False,
        collapsed=False,
        css_class='s',
    )

    vertical = VerticalLayout(form_config=section)
    monkeypatch.setattr(vertical, '_render_form_instances', lambda **_kwargs: ['<div>Body</div>'])
    vertical_html = vertical.render()
    assert '<h3>Header</h3>' in vertical_html

    class _RaiseNoErrors:
        @classmethod
        def __call__(cls, **_kwargs):
            raise Exception('boom')

        @classmethod
        def __init_subclass__(cls):
            return None

    class _BadForm:
        def __init__(self, **_kwargs):
            raise Exception('boom')

    monkeypatch.setattr(vertical, '_get_forms', lambda: [_BadForm])
    result_v = vertical.validate({'a': 1})
    assert result_v.errors.get('_form') == 'boom'

    from pydantic_schemaforms.form_layouts import HorizontalLayout

    horizontal = HorizontalLayout(form_config=section)
    monkeypatch.setattr(horizontal, '_render_form_instances', lambda **_kwargs: ['<div>Col</div>'])
    horizontal_html = horizontal.render()
    assert horizontal_html.startswith('<h3>Header</h3>')

    monkeypatch.setattr(horizontal, '_get_forms', lambda: [_BadForm])
    result_h = horizontal.validate({'a': 1})
    assert result_h.errors.get('_form') == 'boom'


@pytest.mark.filterwarnings('ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning')
def test_form_layouts_render_form_instances_fallback_when_renderer_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    class _StubForm:
        @classmethod
        def render_form(cls, **kwargs):
            assert kwargs.get('include_submit_button') is False
            return '<div>fallback-render</div>'

    vertical = VerticalLayout()
    monkeypatch.setattr(vertical, '_get_forms', lambda: [_StubForm])
    monkeypatch.setattr(vertical, '_get_renderer_for_framework', lambda _fw: None)
    rendered = vertical._render_form_instances(data={}, errors={}, framework='bootstrap')
    assert rendered == ['<div>fallback-render</div>']


@pytest.mark.filterwarnings('ignore:pydantic_schemaforms.form_layouts will be removed in a future release:DeprecationWarning')
def test_form_layout_core_schema_serializer_handles_exceptions_and_non_layout_values() -> None:
    class _ExplodingVertical(VerticalLayout):
        def _get_layouts(self):
            raise RuntimeError('boom')

    class _Wrapper(BaseModel):
        payload: _ExplodingVertical

    model_layout = _Wrapper(payload=_ExplodingVertical())
    payload_layout = model_layout.model_dump()['payload']
    assert payload_layout['layout'] is True
    assert payload_layout['type'] == '_ExplodingVertical'

    payload_dict = _Wrapper(payload={'raw': 'dict'}).model_dump()['payload']
    assert payload_dict == {'raw': 'dict'}

    payload_scalar = _Wrapper(payload=7).model_dump()['payload']
    assert payload_scalar == {'value': '7'}
