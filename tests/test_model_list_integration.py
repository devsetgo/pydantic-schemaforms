"""Integration-style tests for model_list rendering and validation."""

import pytest
from pydantic import ValidationError

from examples.shared_models import TaskListForm
from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.field_renderer import FieldRenderer


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
