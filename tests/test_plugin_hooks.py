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
    ui_element = "fancy"
    ui_element_aliases = ("fn",)

    def get_input_type(self) -> str:  # pragma: no cover - simple return
        return "text"

    def render(self, **kwargs):  # pragma: no cover - simple return
        return "<input>"


class _DummyRenderer:
    framework = "bootstrap"


@pytest.fixture(autouse=True)
def _reset_registries():
    yield
    reset_input_registry()
    LayoutEngine.reset_layout_renderers()


def test_register_input_class_populates_component_map():
    register_input_class(_FancyInput)
    mapping = get_input_component_map()

    assert mapping["fancy"] is _FancyInput
    assert mapping["fn"] is _FancyInput


def test_layout_engine_custom_renderer_is_invoked():
    calls = {}

    def handler(field_name, field_schema, value, ui_info, context, engine):
        calls["field"] = field_name
        calls["value"] = value
        return "<div>custom-layout</div>"

    LayoutEngine.register_layout_renderer("custom_layout", handler)

    engine = LayoutEngine(renderer=_DummyRenderer())
    ui_info = {"layout_handler": "custom_layout"}
    output = engine._build_layout_body(
        "my_layout",
        {"ui": ui_info},
        {"steps": [1, 2]},
        ui_info,
        RenderContext(form_data={}, schema_defs={}),
    )

    assert "custom-layout" in output
    assert calls["field"] == "my_layout"
    assert calls["value"] == {"steps": [1, 2]}
