from __future__ import annotations

from typing import Annotated, Optional

import pytest
from pydantic import BaseModel

from pydantic_schemaforms.integration.schema import JSONSchemaGenerator
from pydantic_schemaforms.inputs.base import (
    BaseInput,
    SelectInputBase,
    build_label,
    render_template,
    t,
)
from pydantic_schemaforms.inputs.selection_inputs import (
    CheckboxGroup,
    ComboBoxInput,
    RadioGroup,
    SelectInput,
)
from pydantic_schemaforms.rendering import form_style as form_style_module
from pydantic_schemaforms.rendering.form_style import FormStyle, get_form_style, register_form_style
from pydantic_schemaforms.rendering.schema_parser import _extract_ui_info, _field_info_to_schema, _infer_field_type
from pydantic_schemaforms.rendering.themes import MaterialEmbeddedTheme, RendererTheme
from pydantic_schemaforms.schema_form import Field, FormModel
from pydantic_schemaforms.simple_material_renderer import SimpleMaterialRenderer


class _DummyBaseInput(BaseInput):
    def get_input_type(self) -> str:
        return "text"

    def render(self, **kwargs) -> str:
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = "text"
        return f"<input {self._build_attributes_string(attrs)} />"


class _DummySelectInput(SelectInputBase):
    def get_input_type(self) -> str:
        return "select"

    def render(self, options, **kwargs) -> str:
        attrs = self.validate_attributes(**kwargs)
        return f"<select {self._build_attributes_string(attrs)}>{len(options)}</select>"


class _ModelForSchema(BaseModel):
    email_address: str


def test_inputs_base_helpers_cover_fallback_and_attribute_branches() -> None:
    # t() fallback and render_template() string/Template-object behavior
    assert t("abc") == "abc"

    class _TemplateObj:
        strings = ["<b>", "</b>"]
        values = ["x"]

    assert render_template(_TemplateObj()) == "<b>x</b>"
    assert render_template("already") == "already"

    inp = _DummyBaseInput()
    attrs = inp.validate_attributes(
        name="n",
        id=None,
        required=False,
        hidden=True,
        role="button",
        **{"data-x": ["a", None, "b"], "x-unknown": '<unsafe"'},
    )
    # bool False => omitted, bool True => attribute name
    built = inp._build_attributes_string(attrs)
    assert 'name="n"' in built
    assert "hidden" in built
    assert 'required="False"' in built
    assert "data-x=\"a b\"" in built
    assert "x-unknown=\"&lt;unsafe&quot;\"" in built

    # Cover fontawesome and bootstrap icon formatting paths
    fa = build_label("my_field", icon="user", framework="fontawesome")
    assert "fas fa-user" in fa
    bs = build_label("my_field", icon="bi bi-check", framework="bootstrap")
    assert "bi bi-check" in bs


def test_select_input_base_renders_for_all_framework_branches() -> None:
    comp = _DummySelectInput()
    options = [{"value": "a", "label": "A"}]

    bootstrap = comp.render_with_label(
        label="L",
        help_text="H",
        error="E",
        icon="person",
        framework="bootstrap",
        options=options,
        name="field",
        id="field",
    )
    assert "input-group" in bootstrap

    material = comp.render_with_label(
        label="L",
        help_text="H",
        error="E",
        icon="person",
        framework="material",
        options=options,
        name="field",
        id="field",
    )
    assert "md-field" in material

    plain = comp.render_with_label(
        label="L",
        help_text="H",
        error="E",
        icon="person",
        framework="plain",
        options=options,
        name="field",
        id="field",
    )
    assert "input-with-icon" in plain


def test_selection_inputs_fallback_template_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    def _explode(*_args, **_kwargs):
        raise ValueError("boom")

    monkeypatch.setattr("string.Template.substitute", _explode)

    select_html = SelectInput().render(options=[{"value": "1", "label": "One"}], name="s")
    assert "<select" in select_html

    checkbox_html = CheckboxGroup().render(
        options=[{"value": "x", "label": "X"}],
        group_name="grp",
    )
    assert "<fieldset" in checkbox_html

    radio_html = RadioGroup().render(
        options=[{"value": "x", "label": "X"}],
        group_name="grp",
    )
    assert "<fieldset" in radio_html

    combo_html = ComboBoxInput().render(options=["a", "b"], name="combo")
    assert "datalist" in combo_html


def test_json_schema_generator_error_and_mapping_branches() -> None:
    gen = JSONSchemaGenerator()

    with pytest.raises(TypeError, match="cannot be None"):
        gen.ensure_model_class(None)

    with pytest.raises(TypeError, match="BaseModel subclass or instance"):
        gen.ensure_model_class("bad")

    class _NotModel:
        pass

    with pytest.raises(TypeError, match="inherit"):
        gen.ensure_model_class(_NotModel)

    assert gen.normalize_annotation(None) is str
    assert gen.normalize_annotation(Optional[int]) is int
    assert gen.normalize_annotation(Annotated[str, "meta"]) is str

    assert gen.generate_field_schema(str, field_name="user_email")["format"] == "email"
    assert gen.generate_field_schema(str, field_name="home_uri")["format"] == "uri"


class _SchemaFieldModel(FormModel):
    count: int = Field(..., description="counter", ui_element="text")


def test_schema_parser_private_helpers_branches() -> None:
    field_info = _SchemaFieldModel.model_fields["count"]
    schema = _field_info_to_schema("count", field_info)
    assert schema["description"] == "counter"
    assert schema["ui"]["element"] == "text"

    assert _extract_ui_info(field_info)["element"] == "text"

    # infer type branches
    class _F(FormModel):
        a: float = Field(...)
        b: bool = Field(...)

    assert _infer_field_type(_F.model_fields["a"]) == "number"
    assert _infer_field_type(_F.model_fields["b"]) == "boolean"


def test_renderer_theme_fallback_and_wrapper_timing(monkeypatch: pytest.MonkeyPatch) -> None:
    theme = RendererTheme(submit_label="Go")

    # Exercise _load_form_style fallback branch (KeyError => default)
    calls = {"n": 0}

    def _fake_get_form_style(*_args, **_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyError("missing")
        return get_form_style("default", "default")

    monkeypatch.setattr("pydantic_schemaforms.rendering.themes.get_form_style", _fake_get_form_style)
    # Fallback call should not raise
    theme._load_form_style("missing", "x")

    wrapped = theme.render_form_wrapper(
        form_attrs={"method": "POST", "action": "/x", "disabled": True},
        csrf_token="",
        form_content="<input>",
        submit_markup="<button>Go</button>",
        render_time=0.5,
    )
    assert "Rendered in 0.500s" in wrapped


def test_material_embedded_theme_and_simple_material_renderer_branches() -> None:
    theme = MaterialEmbeddedTheme()
    transformed = theme.transform_form_attributes({"class": "x", "novalidate": True})
    assert transformed["class"].startswith("md-form")
    assert "novalidate" not in transformed

    # No help/error branch and optional model-list blocks
    container = theme.render_model_list_container(
        field_name="items",
        label="Items",
        is_required=False,
        min_items=0,
        max_items=1,
        items_html="",
        help_text=None,
        error=None,
        add_button_label="Add",
    )
    assert "md-model-list-wrapper" in container
    assert "md-help-text" not in container

    renderer = SimpleMaterialRenderer()
    assert renderer._attr(None) == ""
    assert renderer._render_help_block(None) == ""
    assert renderer._render_error_block(None) == ""
    assert renderer._model_list_framework() == "bootstrap"

    # enum fallback for select options and scalar option normalization
    options = renderer._build_select_options({}, {"enum": ["A", "B"]})
    assert options == [["A", "A"], ["B", "B"]]

    options2 = renderer._build_select_options({"options": ["X", {"value": "Y", "label": "Why"}]}, {})
    assert options2 == [["X", "X"], ["Y", "Why"]]


def test_form_style_registry_keyerror_branch() -> None:
    temp_style = FormStyle(framework="tmp-framework", variant="v1")
    register_form_style(temp_style)
    assert get_form_style("tmp-framework:v1").framework == "tmp-framework"

    registry = form_style_module._FORM_STYLE_REGISTRY
    backup = dict(registry)
    try:
        registry.clear()
        with pytest.raises(KeyError):
            get_form_style("unknown", "none")
    finally:
        registry.clear()
        registry.update(backup)
