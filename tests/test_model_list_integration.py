"""Integration-style tests for model_list rendering and validation."""

import pytest
from pydantic import ValidationError

from examples.shared_models import TaskListForm
from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.field_renderer import FieldRenderer
from pydantic_schemaforms.rendering.layout_engine import LayoutEngine


def _task(name: str, priority: str = 'medium', due: str = '2024-12-01') -> dict:
    return {
        'task_name': name,
        'priority': priority,
        'due_date': due,
        'completed': False,
    }


def test_task_list_form_renders_add_and_remove_controls_bootstrap() -> None:
    html = render_form_html(
        TaskListForm,
        submit_url='/tasks',
        framework='bootstrap',
        form_data={
            'project_name': 'Demo',
            'tasks': [_task('One'), _task('Two')],
        },
    )
    assert 'add-item-btn' in html
    assert html.count('remove-item-btn') >= 2


def test_task_list_form_renders_add_and_remove_controls_material() -> None:
    html = render_form_html(
        TaskListForm,
        submit_url='/tasks',
        framework='material',
        form_data={
            'project_name': 'Demo',
            'tasks': [_task('One'), _task('Two')],
        },
    )
    assert 'add-item-btn' in html
    assert html.count('remove-item-btn') >= 2


def test_task_list_form_renders_hidden_template_item_when_empty() -> None:
    """Optional (min_items=0) lists must support adding after becoming empty.

    This is done by rendering a hidden <template> list-item that JS can clone
    even after the last visible item is deleted.
    """

    html = render_form_html(
        TaskListForm,
        submit_url='/tasks',
        framework='bootstrap',
        form_data={'project_name': 'Demo', 'tasks': []},
    )
    assert 'model-list-item-template' in html


def test_schema_model_list_renders_hidden_template_item_for_optional_lists() -> None:
    """Schema-based model_list rendering must include the hidden template too."""

    class _DummyRenderer:
        framework = 'bootstrap'
        config = {}
        theme = None

    renderer = FieldRenderer(_DummyRenderer())
    context = RenderContext(form_data={}, schema_defs={})

    schema_def = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'title': 'Name'},
        },
    }

    html = renderer.render_model_list_from_schema(
        field_name='pets',
        field_schema={'type': 'array', 'title': 'Pets', 'minItems': 0, 'maxItems': 5},
        schema_def=schema_def,
        values=[],
        error=None,
        ui_info={'item_title_template': '🐾 {name}'},
        required_fields=[],
        context=context,
    )

    assert 'model-list-item-template' in html


def test_model_list_is_registered_as_a_builtin_layout_engine_renderer() -> None:
    """model_list now dispatches through LayoutEngine's registry (the same
    mechanism DataTableLayout uses), not a hardcoded ui_element check in
    FieldRenderer -- and it's registered builtin=True so it survives
    LayoutEngine.reset_layout_renderers() (called by several test fixtures
    across the suite), since this module-level registration only ever runs
    once per process."""
    LayoutEngine.reset_layout_renderers()

    assert LayoutEngine.get_renderer_for_element('model_list') is not None
    assert 'model_list' in LayoutEngine._builtin_renderer_names


def test_render_field_dispatches_model_list_through_the_registry(monkeypatch) -> None:
    """A real assertion that FieldRenderer.render_field's generic dispatch
    actually reaches the registered 'model_list' renderer (rather than a
    hardcoded branch), by swapping in a fake registered renderer and
    confirming it -- not the real one -- produces the output."""

    class _DummyRenderer:
        framework = 'bootstrap'
        config = {}
        theme = None

    dummy = _DummyRenderer()
    field_renderer = FieldRenderer(dummy)
    dummy._field_renderer = field_renderer
    dummy._layout_engine = LayoutEngine(dummy)

    calls = {}

    def fake_renderer(field_name, field_schema, value, ui_info, context, engine):
        calls['field_name'] = field_name
        calls['error'] = context.error
        calls['required_fields'] = context.required_fields
        return '<div>fake-model-list-output</div>'

    monkeypatch.setitem(LayoutEngine._custom_renderers, 'model_list', fake_renderer)

    result = field_renderer.render_field(
        field_name='tasks',
        field_schema={'type': 'array', 'ui': {'element': 'model_list'}},
        value=[],
        error='some error',
        required_fields=['tasks'],
        context=RenderContext(form_data={}, schema_defs={}),
    )

    assert result == '<div>fake-model-list-output</div>'
    assert calls['field_name'] == 'tasks'
    assert calls['error'] == 'some error'
    assert calls['required_fields'] == ('tasks',)


def test_task_list_enforces_min_and_max_items() -> None:
    # Min length: empty task list should fail validation
    with pytest.raises(ValidationError) as excinfo_min:
        TaskListForm.model_validate({'project_name': 'Demo', 'tasks': []})

    msg = str(excinfo_min.value)
    assert 'tasks' in msg and '1' in msg  # context hints about min length

    # Max length: more than 10 items should fail validation
    too_many_tasks = {'project_name': 'Demo', 'tasks': [_task(f'Task {i}') for i in range(12)]}
    with pytest.raises(ValidationError) as excinfo_max:
        TaskListForm.model_validate(too_many_tasks)

    msg = str(excinfo_max.value)
    assert 'tasks' in msg and '10' in msg  # context hints about max length
