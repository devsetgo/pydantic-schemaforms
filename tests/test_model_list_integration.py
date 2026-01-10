"""Integration-style tests for ModelListRenderer theme hooks."""

import pytest
from pydantic import ValidationError

from examples.shared_models import TaskItem, TaskListForm
from pydantic_schemaforms.model_list import ModelListRenderer
from pydantic_schemaforms.schema_form import FormModel


class _PetModel(FormModel):
    name: str
    age: int


def test_bootstrap_model_list_renders_theme_wrappers() -> None:
    renderer = ModelListRenderer(framework="bootstrap")

    html = renderer.render_model_list(
        field_name="pets",
        label="Pets",
        model_class=_PetModel,
        values=[{"name": "Rex", "age": 5}],
        min_items=0,
        max_items=3,
    )

    assert 'class="model-list-container"' in html
    assert 'border rounded p-3' in html  # bootstrap theme chrome
    assert 'Add Pets' in html
    assert 'remove-item-btn' in html


def test_material_model_list_renders_theme_wrappers() -> None:
    renderer = ModelListRenderer(framework="material")

    html = renderer.render_model_list(
        field_name="pets",
        label="Pets",
        model_class=_PetModel,
        values=[{"name": "Miso", "age": 2}],
        min_items=0,
        max_items=3,
    )

    assert 'mdc-card--outlined' in html  # material theme item wrapper
    assert 'mdc-card__primary-action' in html  # material item wrapper
    assert 'Add Pets' in html
    assert 'mdc-icon-button remove-item-btn' in html


def test_model_list_renders_hidden_template_item_for_optional_lists() -> None:
    """Optional (min_items=0) lists must support adding after becoming empty.

    This is done by rendering a hidden <template> list-item that JS can clone
    even after the last visible item is deleted.
    """

    bootstrap = ModelListRenderer(framework="bootstrap").render_model_list(
        field_name="pets",
        label="Pets",
        model_class=_PetModel,
        values=[],
        min_items=0,
        max_items=3,
    )
    assert "model-list-item-template" in bootstrap

    material = ModelListRenderer(framework="material").render_model_list(
        field_name="pets",
        label="Pets",
        model_class=_PetModel,
        values=[],
        min_items=0,
        max_items=3,
    )
    assert "model-list-item-template" in material
    assert "model-list-item" in material


def _task(name: str, priority: str = "medium", due: str = "2024-12-01") -> dict:
    return {
        "task_name": name,
        "priority": priority,
        "due_date": due,
        "completed": False,
    }


def test_task_list_renders_add_and_remove_controls() -> None:
    renderer = ModelListRenderer(framework="bootstrap")
    html = renderer.render_model_list(
        field_name="tasks",
        label="Task List",
        model_class=TaskItem,
        values=[_task("One"), _task("Two")],
        min_items=1,
        max_items=10,
    )

    # Ensure add and remove affordances exist for list items
    assert "Add Task" in html
    assert html.count("remove-item-btn") >= 2


def test_task_list_enforces_min_and_max_items() -> None:
    # Min length: empty task list should fail validation
    with pytest.raises(ValidationError) as excinfo_min:
        TaskListForm.model_validate({"project_name": "Demo", "tasks": []})

    msg = str(excinfo_min.value)
    assert "tasks" in msg and "1" in msg  # context hints about min length

    # Max length: more than 10 items should fail validation
    too_many_tasks = {"project_name": "Demo", "tasks": [_task(f"Task {i}") for i in range(12)]}
    with pytest.raises(ValidationError) as excinfo_max:
        TaskListForm.model_validate(too_many_tasks)

    msg = str(excinfo_max.value)
    assert "tasks" in msg and "10" in msg  # context hints about max length
