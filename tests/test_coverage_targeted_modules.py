from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import BaseModel

from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.inputs.base import SelectInputBase, render_template
from pydantic_schemaforms.inputs.numeric_inputs import (
    AgeInput,
    DecimalInput,
    PercentageInput,
    QuantityInput,
    RatingInput,
    ScoreInput,
    SliderInput,
    TemperatureInput,
)
from pydantic_schemaforms.inputs.selection_inputs import (
    CheckboxGroup,
    ComboBoxInput,
    RadioGroup,
    ToggleSwitch,
)
import pydantic_schemaforms.inputs.specialized_inputs as specialized_inputs
from pydantic_schemaforms.inputs.text_inputs import CreditCardInput, CurrencyInput, SSNInput
from pydantic_schemaforms.live_validation import HTMXValidationConfig, LiveValidator
from pydantic_schemaforms.schema_form import Field, FormModel


class _SimpleForm(FormModel):
    name: str = Field(...)


def test_enhanced_renderer_humanize_indexed_and_plural_fields() -> None:
    renderer = EnhancedFormRenderer()

    assert renderer._humanize_error_field("pets[7].name") == "Pet #8 — Name"
    assert renderer._humanize_error_field("companies[1].tax_id") == "Company #2 — Tax Id"
    assert renderer._humanize_error_field("form") == "Form"


def test_base_render_template_handles_template_like_objects() -> None:
    @dataclass
    class _TemplateLike:
        strings: tuple[str, ...]
        values: tuple[str, ...]

    template = _TemplateLike(strings=("<b>", "</b>"), values=("ok",))
    assert render_template(template) == "<b>ok</b>"
    assert render_template("plain") == "plain"


class _DummySelectInput(SelectInputBase):
    ui_element = "dummy"

    def get_input_type(self) -> str:
        return "select"

    def render(self, options=None, **kwargs):  # pragma: no cover - simple helper
        return '<select name="x"></select>'


def test_select_input_base_render_with_label_plain_framework_branch() -> None:
    widget = _DummySelectInput()
    html = widget.render_with_label(
        label="My Label",
        help_text="Help me",
        error="Boom",
        framework="none",
        options=[{"value": "a", "label": "A"}],
        id="f1",
    )

    assert 'class="field"' in html
    assert "My Label" in html
    assert "Help me" in html
    assert "Boom" in html


def test_numeric_specialized_renderers_cover_branches() -> None:
    assert "%" in PercentageInput().render(name="p", value="20")
    assert 'step="0.001"' in DecimalInput().render(name="d", decimal_places=3)
    assert 'max="150"' in AgeInput().render(name="age")
    assert 'min="1"' in QuantityInput().render(name="qty")
    assert 'step="0.1"' in ScoreInput().render(name="score", min_score=0.0, max_score=10.0)

    rating_html = RatingInput().render(name="rating", max_rating=7, value="4")
    assert "star-rating" in rating_html
    assert "☆☆☆" in rating_html

    slider_html = SliderInput().render(name="slider", min="10", max="20", show_labels=True)
    assert "slider-labels" in slider_html
    assert "slider-min" in slider_html

    temp_html = TemperatureInput().render(name="temp", unit="fahrenheit")
    assert "68°F" in temp_html
    assert "-459.67" in temp_html


def test_text_specialized_renderers_cover_patterns() -> None:
    ssn_html = SSNInput().render(name="ssn")
    cc_html = CreditCardInput().render(name="cc")
    currency_html = CurrencyInput().render(name="amount", currency_symbol="$")

    assert "123-45-6789" in ssn_html
    assert "\\d{3}-\\d{2}-\\d{4}" in ssn_html
    assert "1234 5678 9012 3456" in cc_html
    assert "cc-number" in cc_html
    assert "$0.00" in currency_html


def test_selection_toggle_and_combobox_and_radio_fallback(monkeypatch) -> None:
    toggle_html = ToggleSwitch().render(name="enabled", label="Enabled")
    assert "toggle-switch-wrapper" in toggle_html
    assert "toggle-switch-text" in toggle_html

    combo = ComboBoxInput()
    combo_html = combo.render(name="city", options=[{"value": "LA", "label": "Los Angeles"}])
    assert "datalist" in combo_html
    assert "Los Angeles" in combo_html

    def _raise(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("pydantic_schemaforms.inputs.selection_inputs.Template.substitute", _raise)
    fallback_html = RadioGroup().render(
        group_name="g1",
        options=[{"value": "v1", "label": "Value 1", "checked": True}],
        legend="Legend",
    )
    assert "radio-group" in fallback_html
    assert "Legend" in fallback_html

    checkbox_fallback = CheckboxGroup().render(
        group_name="g2",
        options=[{"value": "v1", "label": "Value 1", "disabled": True}],
        legend="Legend 2",
    )
    assert "checkbox-group" in checkbox_fallback
    assert "Legend 2" in checkbox_fallback


def test_specialized_widget_renderers_cover_extended_blocks(monkeypatch) -> None:
    class _ConcreteFormInput:
        def render(self, **kwargs):
            attrs = " ".join(f'{k}="{v}"' for k, v in kwargs.items())
            return f"<input {attrs} />"

    monkeypatch.setattr(specialized_inputs, "FormInput", _ConcreteFormInput)

    captcha_html = specialized_inputs.CaptchaInput().render(name="captcha_code")
    assert "What is" in captcha_html
    assert "captcha_code_answer" in captcha_html

    stars_html = specialized_inputs.RatingStarsInput().render(
        name="rating",
        max_stars=7,
        current_rating=4,
    )
    assert "star-rating-input" in stars_html
    assert "rating-star" in stars_html
    assert "data-rating=\"7\"" in stars_html

    tags_html = specialized_inputs.TagsInput().render(
        name="tags",
        placeholder="Add tags",
        separator=";",
        value="alpha;beta",
    )
    assert "tags-input" in tags_html
    assert "alpha;beta" in tags_html
    assert "removeTag" in tags_html


class _ProfileModel(BaseModel):
    age: int | None = None


class _FakeFieldValidator:
    field_name = "email"

    def validate(self, value):
        return (False, ["Email invalid"]) if "@" not in str(value) else (True, [])

    def to_rule_descriptors(self):
        return [{"type": "email"}]


class _FakeSchema:
    def validators(self):
        return [_FakeFieldValidator()]


def test_live_validator_model_schema_and_render_paths() -> None:
    validator = LiveValidator()
    validator.register_schema(_FakeSchema())
    assert "email" in validator.validators
    assert validator.field_configs["email"]["rules"][0]["type"] == "email"

    validator.register_model_validator(_ProfileModel)
    ok = validator.validate_field("age", 33)
    bad = validator.validate_field("age", "not-int")
    missing = validator.validate_field("unknown", "x")

    assert ok.is_valid is True
    assert bad.is_valid is False
    assert missing.is_valid is True
    assert "No validator registered" in missing.warnings[0]

    flask_code = validator.generate_validation_endpoint_code("flask")
    fastapi_code = validator.generate_validation_endpoint_code("fastapi")
    assert "@app.route('/validate/<field_name>'" in flask_code
    assert "@app.post('/validate/{field_name}')" in fastapi_code

    with pytest.raises(ValueError):
        validator.generate_validation_endpoint_code("django")


def test_live_validator_trigger_variants_and_htmx_script() -> None:
    blur_validator = LiveValidator(HTMXValidationConfig(validate_on_blur=True))
    blur_html = blur_validator.render_field_with_live_validation("username", label="User")
    assert 'hx-trigger="blur"' in blur_html

    input_validator = LiveValidator(
        HTMXValidationConfig(validate_on_blur=False, validate_on_input=True, debounce_ms=150)
    )
    input_html = input_validator.render_field_with_live_validation("email")
    assert 'hx-trigger="input delay:150ms"' in input_html

    change_validator = LiveValidator(
        HTMXValidationConfig(validate_on_blur=False, validate_on_input=False, validate_on_change=True)
    )
    change_html = change_validator.render_field_with_live_validation("city", readonly="readonly")
    assert 'hx-trigger="change"' in change_html
    assert 'readonly="readonly"' in change_html

    script = change_validator.render_htmx_script()
    assert "validationConfig" in script
    assert '"validate_on_change": true' in script.lower()