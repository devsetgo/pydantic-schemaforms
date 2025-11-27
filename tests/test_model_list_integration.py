"""Integration-style tests for ModelListRenderer theme hooks."""

from pydantic_forms.model_list import ModelListRenderer
from pydantic_forms.schema_form import FormModel


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
