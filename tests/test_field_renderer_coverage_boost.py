"""Targeted branch coverage tests for rendering/field_renderer.py."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from pydantic_schemaforms.rendering.context import RenderContext
from pydantic_schemaforms.rendering.field_renderer import FieldRenderer


class _DummyRenderer:
    def __init__(self, config=None, framework="bootstrap", theme=None):
        self.config = config or {}
        self.framework = framework
        self.theme = theme

    def _render_layout_field(self, *args, **kwargs):
        return "<div>layout</div>"


class _CaptureInput:
    last_kwargs = None

    def render_with_label(self, **kwargs):
        _CaptureInput.last_kwargs = kwargs
        return "<input data-captured='true' />"


class _NoneInput:
    def render_with_label(self, **kwargs):
        return None


def _context(schema_defs=None):
    return RenderContext(form_data={}, schema_defs=schema_defs or {})


def test_render_field_uses_schema_and_ui_option_attributes_with_config_wrapper(monkeypatch):
    renderer = _DummyRenderer(
        config={
            "input_class": "base-input",
            "field_wrapper_class": "field-wrap",
        }
    )
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        "pydantic_schemaforms.rendering.field_renderer.get_input_component",
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name="username",
        field_schema={
            "type": "string",
            "title": "User Name",
            "description": "desc",
            "minLength": 2,
            "maxLength": 20,
            "minimum": 1,
            "maximum": 99,
            "pattern": "^[a-z]+$",
            "ui": {
                "autofocus": True,
                "disabled": True,
                "readonly": True,
                "placeholder": "Your name",
                "class": "ui-class",
                "style": "color: red",
                "icon": "user",
                "options": {
                    "class": "opt-class",
                    "style": "font-weight: bold",
                    "data-x": "1",
                    "choices": ["ignored"],
                    "obj": {"a": 1},
                    "list": [1, 2],
                },
            },
        },
        value="alice",
        required_fields=["username"],
        context=_context(),
    )

    assert "field-wrap" in html
    captured = _CaptureInput.last_kwargs
    assert captured is not None
    assert captured["name"] == "username"
    assert captured["required"] is True
    assert captured["minlength"] == 2
    assert captured["maxlength"] == 20
    assert captured["min"] == 1
    assert captured["max"] == 99
    assert captured["pattern"] == "^[a-z]+$"
    assert captured["placeholder"] == "Your name"
    assert captured["autofocus"] is True
    assert captured["disabled"] is True
    assert captured["readonly"] is True
    assert "base-input" in captured["class"]
    assert "ui-class" in captured["class"]
    assert "opt-class" in captured["class"]
    assert "color: red" in captured["style"]
    assert "font-weight: bold" in captured["style"]
    assert captured["data-x"] == "1"


def test_render_field_uses_theme_wrapper_class(monkeypatch):
    class _Theme:
        @staticmethod
        def input_class(_ui):
            return "theme-input"

        @staticmethod
        def field_wrapper_class():
            return "theme-field-wrap"

    renderer = _DummyRenderer(config={"field_wrapper_class": "config-wrap"}, theme=_Theme())
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        "pydantic_schemaforms.rendering.field_renderer.get_input_component",
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name="title",
        field_schema={"type": "string"},
        value="x",
        context=_context(),
    )

    assert "theme-field-wrap" in html
    assert "config-wrap" not in html


def test_render_field_selection_paths_multiselect_and_no_options(monkeypatch):
    renderer = _DummyRenderer(config={"select_class": "sel-class"})
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        "pydantic_schemaforms.rendering.field_renderer.get_input_component",
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name="tags",
        field_schema={
            "type": "array",
            "items": {"enum": ["a", "b", "c"]},
            "ui": {"element": "multiselect"},
        },
        value=["b"],
        context=_context(),
    )

    assert "captured" in html
    captured = _CaptureInput.last_kwargs
    assert captured["multiple"] is True
    assert "value" not in captured
    assert len(captured["options"]) == 3
    assert any(opt["value"] == "b" and opt["selected"] for opt in captured["options"])

    no_options_html = field_renderer.render_field(
        field_name="empty_select",
        field_schema={"type": "string", "ui": {"element": "select"}},
        value=None,
        context=_context(),
    )
    assert "Warning: No options provided" in no_options_html


def test_render_field_handles_none_from_component(monkeypatch):
    renderer = _DummyRenderer()
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        "pydantic_schemaforms.rendering.field_renderer.get_input_component",
        lambda _ui_element: _NoneInput,
    )

    html = field_renderer.render_field(
        field_name="nickname",
        field_schema={"type": "string"},
        value="nick",
        context=_context(),
    )

    assert "input returned None" in html


def test_extract_apply_and_normalize_option_helpers():
    field_renderer = FieldRenderer(_DummyRenderer())

    options_dict, options_list = field_renderer._extract_ui_options(
        {"options": [{"value": 1}]},
        {},
    )
    assert options_dict == {}
    assert options_list == [{"value": 1}]

    options_dict, options_list = field_renderer._extract_ui_options(
        {"ui_options": {"choices": ["x", "y"]}},
        {},
    )
    assert options_dict == {"choices": ["x", "y"]}
    assert options_list == ["x", "y"]

    options_dict, options_list = field_renderer._extract_ui_options(
        {},
        {"ui_options": {"options": ["m", "n"]}},
    )
    assert options_dict == {"options": ["m", "n"]}
    assert options_list == ["m", "n"]

    attrs = field_renderer._apply_ui_option_attributes(
        {"class": "base", "style": "color: red"},
        {
            "class": "extra",
            "style": "font-size: 12px",
            "size": 5,
            "choices": [1],
            "obj": {"a": 1},
        },
    )
    assert attrs["class"] == "base extra"
    assert "color: red" in attrs["style"] and "font-size: 12px" in attrs["style"]
    assert attrs["size"] == 5

    normalized = field_renderer._normalize_options(
        [
            {"id": "a", "label": "Alpha"},
            ("b", "Beta"),
            "c",
        ],
        current_value=["b", "c"],
    )
    assert normalized[0]["value"] == "a"
    assert normalized[0]["label"] == "Alpha"
    assert normalized[1]["selected"] is True
    assert normalized[2]["selected"] is True

    assert field_renderer._is_option_selected(None, "x") is False
    assert field_renderer._is_option_selected("x", None) is False
    assert field_renderer._is_option_selected("2", {1, 2}) is True
    assert field_renderer._is_option_selected("2", "2") is True


def test_render_model_list_field_errors_and_model_class_paths():
    field_renderer = FieldRenderer(_DummyRenderer())

    no_ref = field_renderer._render_model_list_field(
        field_name="items",
        field_schema={"type": "array", "items": {}},
        value=None,
        error=None,
        required_fields=[],
        ui_info={},
        context=_context(),
        all_errors={},
    )
    assert "model_class not specified" in no_ref

    unresolved_ref = field_renderer._render_model_list_field(
        field_name="items",
        field_schema={"type": "array", "items": {"$ref": "#/defs/Missing"}},
        value=None,
        error=None,
        required_fields=[],
        ui_info={},
        context=_context(schema_defs={}),
        all_errors={},
    )
    assert "Could not resolve model reference" in unresolved_ref

    class _FakeItem:
        def __init__(self, payload):
            self.payload = payload

        def model_dump(self):
            return self.payload

    class _FakeModelListRenderer:
        def __init__(self, framework):
            self.framework = framework

        def render_model_list(self, **kwargs):
            assert kwargs["is_required"] is True
            assert kwargs["nested_errors"] == {"0.name": "required"}
            assert kwargs["values"][0] == {"name": "a"}
            assert kwargs["values"][1] == {"name": "b"}
            assert kwargs["values"][2] == {"name": "c"}
            return "<div>model-list-rendered</div>"

    with patch("pydantic_schemaforms.model_list.ModelListRenderer", _FakeModelListRenderer):
        html = field_renderer._render_model_list_field(
            field_name="items",
            field_schema={"type": "array", "title": "Items"},
            value=[_FakeItem({"name": "a"}), {"name": "b"}, _FakeItem({"name": "c"})],
            error="E",
            required_fields=["items"],
            ui_info={"model_class": SimpleNamespace, "help_text": "help", "min_items": 1, "max_items": 4},
            context=_context(),
            all_errors={"items[0].name": "required", "other": "x"},
        )
    assert "model-list-rendered" in html

def test_render_model_list_field_single_model_dump_value_path():
    field_renderer = FieldRenderer(_DummyRenderer())

    class _SingleItem:
        @staticmethod
        def model_dump():
            return {"name": "single"}

    class _FakeModelListRenderer:
        def __init__(self, framework):
            self.framework = framework

        def render_model_list(self, **kwargs):
            assert kwargs["values"] == [{"name": "single"}]
            return "<div>single-model</div>"

    with patch("pydantic_schemaforms.model_list.ModelListRenderer", _FakeModelListRenderer):
        html = field_renderer._render_model_list_field(
            field_name="items",
            field_schema={"type": "array"},
            value=_SingleItem(),
            error=None,
            required_fields=[],
            ui_info={"model_class": SimpleNamespace},
            context=_context(),
            all_errors={},
        )

    assert "single-model" in html


def test_render_model_list_field_schema_fallback_and_container_theming(monkeypatch):
    class _Theme:
        @staticmethod
        def render_model_list_container(**kwargs):
            return f"<section data-field='{kwargs['field_name']}'>theme</section>"

    field_renderer = FieldRenderer(_DummyRenderer(theme=_Theme()))

    calls = []

    def _fake_item(field_name, schema_def, index, item_data, context, ui_info):
        calls.append((field_name, index, dict(item_data)))
        return f"<article data-index='{index}'>item</article>"

    monkeypatch.setattr(field_renderer, "_render_schema_list_item", _fake_item)

    themed = field_renderer.render_model_list_from_schema(
        field_name="items",
        field_schema={"title": "Items", "minItems": 2, "maxItems": 5},
        schema_def={"properties": {"name": {"type": "string"}}},
        values=[],
        error=None,
        ui_info={"help_text": "help", "add_button_label": "Add"},
        required_fields=["items"],
        context=_context(),
    )
    assert "data-field='items'" in themed
    assert calls == [("items", 0, {}), ("items", 1, {}), ("items", 0, {})]

    class _ThemeEmpty:
        @staticmethod
        def render_model_list_container(**kwargs):
            return ""

    field_renderer_empty = FieldRenderer(_DummyRenderer(theme=_ThemeEmpty()))
    monkeypatch.setattr(field_renderer_empty, "_render_schema_list_item", _fake_item)

    fallback = field_renderer_empty.render_model_list_from_schema(
        field_name="things",
        field_schema={"title": "Things", "minItems": 0, "description": "desc"},
        schema_def={"properties": {}},
        values=[],
        error="oops",
        ui_info={},
        required_fields=[],
        context=_context(),
    )
    assert "model-list-container" in fallback


def test_extract_nested_errors_and_schema_list_item_rendering(monkeypatch):
    field_renderer = FieldRenderer(_DummyRenderer())

    extracted = field_renderer.extract_nested_errors_for_field(
        "addresses",
        {
            "addresses[0].street": "required",
            "addresses[0]": "ignored",
            "other[0].x": "not used",
        },
    )
    assert extracted == {"0.street": "required"}

    monkeypatch.setattr(field_renderer, "render_field", lambda name, *_args, **_kwargs: f"<input name='{name}' />")

    html_collapsible = field_renderer._render_schema_list_item(
        field_name="addresses[]",
        schema_def={
            "properties": {
                "_internal": {"type": "string"},
                "street": {"type": "string"},
                "phones": {"type": "array", "input_type": "model_list"},
                "zip": {"type": "string"},
                "city": {"type": "string"},
                "country": {"type": "string"},
            }
        },
        index=1,
        item_data={"street": "Main"},
        context=_context(),
        ui_info={"collapsible_items": True, "items_expanded": False},
    )
    assert "_item_1_content" in html_collapsible
    assert "bi-chevron-right" in html_collapsible
    assert "col-lg-4 col-md-6" in html_collapsible
    assert "col-12" in html_collapsible

    html_non_collapsible = field_renderer._render_schema_list_item(
        field_name="tasks",
        schema_def={"properties": {"name": {"type": "string"}, "due": {"type": "string"}}},
        index=0,
        item_data={"name": "A"},
        context=_context(),
        ui_info={"collapsible_items": False, "item_title_template": "Task #{index}"},
    )
    assert "bi-card-list" in html_non_collapsible
    assert "data-bs-toggle=\"collapse\"" not in html_non_collapsible
    assert "col-12" in html_non_collapsible

    html_medium_columns = field_renderer._render_schema_list_item(
        field_name="contacts",
        schema_def={
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
            }
        },
        index=0,
        item_data={"name": "A"},
        context=_context(),
        ui_info={"collapsible_items": False},
    )
    assert "col-md-6" in html_medium_columns


def test_render_field_radio_enum_branch_and_helpers(monkeypatch):
    renderer = _DummyRenderer(config={"select_class": "select-base"})
    field_renderer = FieldRenderer(renderer)

    monkeypatch.setattr(
        "pydantic_schemaforms.rendering.field_renderer.get_input_component",
        lambda _ui_element: _CaptureInput,
    )

    html = field_renderer.render_field(
        field_name="status",
        field_schema={
            "type": "string",
            "enum": ["open", "closed"],
            "ui": {"element": "radio"},
        },
        value="closed",
        context=_context(),
    )

    assert "captured" in html
    captured = _CaptureInput.last_kwargs
    assert captured["group_name"] == "status"
    assert captured["legend"] == "Status"
    assert any(opt["value"] == "closed" and opt["selected"] for opt in captured["options"])

    attrs = {"x": 1}
    assert field_renderer._apply_ui_option_attributes(attrs, {}) == {"x": 1}

    normalized = field_renderer._normalize_options([{"id": "abc"}], current_value="abc")
    assert normalized[0]["value"] == "abc"
    assert normalized[0]["label"] == "abc"
    assert normalized[0]["selected"] is True

    assert field_renderer._infer_ui_element({"type": "string", "maxLength": 500}) == "textarea"
    assert field_renderer._infer_ui_element({"type": "string", "title": "Email Address"}) == "email"
    assert field_renderer._infer_ui_element({"type": "string", "title": "Password"}) == "password"
    assert field_renderer._infer_ui_element({"type": "number"}) == "number"
    assert field_renderer._infer_ui_element({"type": "boolean"}) == "checkbox"
    assert field_renderer._infer_ui_element({"type": "object"}) == "text"
    assert field_renderer._get_input_class("checkbox") == ""


def test_render_model_list_field_non_type_model_and_schema_path(monkeypatch):
    field_renderer = FieldRenderer(_DummyRenderer())

    non_type_model = field_renderer._render_model_list_field(
        field_name="items",
        field_schema={"type": "array", "items": {}},
        value=None,
        error=None,
        required_fields=[],
        ui_info={"model_class": "not-a-type"},
        context=_context(),
        all_errors={},
    )
    assert "model_class not specified" in non_type_model

    schema_defs = {"Thing": {"properties": {"name": {"type": "string"}}}}

    monkeypatch.setattr(
        field_renderer,
        "render_model_list_from_schema",
        lambda **kwargs: f"schema-list:{kwargs['field_name']}:{len(kwargs['values'])}",
    )

    schema_result = field_renderer._render_model_list_field(
        field_name="things",
        field_schema={"type": "array", "items": {"$ref": "#/defs/Thing"}},
        value={"name": "single"},
        error=None,
        required_fields=[],
        ui_info={},
        context=_context(schema_defs=schema_defs),
        all_errors={},
    )
    assert schema_result == "schema-list:things:1"


def test_render_model_list_from_schema_values_path(monkeypatch):
    field_renderer = FieldRenderer(_DummyRenderer())
    call_indexes = []

    def _fake_item(field_name, schema_def, index, item_data, context, ui_info):
        call_indexes.append(index)
        return f"<item idx='{index}' />"

    monkeypatch.setattr(field_renderer, "_render_schema_list_item", _fake_item)

    html = field_renderer.render_model_list_from_schema(
        field_name="rows",
        field_schema={"title": "Rows", "maxItems": 7},
        schema_def={"properties": {"name": {"type": "string"}}},
        values=[{"name": "a"}, {"name": "b"}],
        error=None,
        ui_info={},
        required_fields=[],
        context=_context(),
    )

    assert "model-list-container" in html
    assert call_indexes == [0, 1, 0]
