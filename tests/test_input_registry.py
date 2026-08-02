"""Tests guarding the ui_element -> input-class registry against collisions.

`get_input_component_map()` walks every BaseInput subclass and indexes it by
its `ui_element` (and aliases). Subclasses that inherit `ui_element` from a
parent instead of declaring their own collide in that map, so the *wrong*
widget class silently wins the base name (e.g. ui_element="hidden" resolving
to HoneypotInput, which discards the value it's given). This file locks in
the fix and prevents new subclasses from reintroducing the same bug.
"""

from __future__ import annotations

from collections import defaultdict

from pydantic_schemaforms.inputs.datetime_inputs import BirthdateInput, DateInput
from pydantic_schemaforms.inputs.numeric_inputs import (
    AgeInput,
    DecimalInput,
    IntegerInput,
    NumberInput,
    PercentageInput,
    QuantityInput,
    RangeInput,
    RatingInput,
    ScoreInput,
    SliderInput,
    TemperatureInput,
)
from pydantic_schemaforms.inputs.registry import (
    _declared_aliases,
    _iter_input_classes,
    get_input_component_map,
    register_input_class,
    reset_input_registry,
)
from pydantic_schemaforms.inputs.selection_inputs import CheckboxGroup
from pydantic_schemaforms.inputs.specialized_inputs import (
    CaptchaInput,
    HiddenInput,
    HoneypotInput,
    RatingStarsInput,
    TagsInput,
)


def test_no_ui_element_collisions() -> None:
    """Every registered ui_element/alias must map to exactly one input class."""
    owners: dict[str, set[str]] = defaultdict(set)
    for cls in _iter_input_classes():
        for alias in _declared_aliases(cls):
            owners[alias].add(cls.__name__)

    collisions = {alias: names for alias, names in owners.items() if len(names) > 1}
    assert collisions == {}, f'ui_element values claimed by multiple classes: {collisions}'


def test_base_ui_elements_resolve_to_base_classes() -> None:
    mapping = get_input_component_map()
    assert mapping['date'] is DateInput
    assert mapping['number'] is NumberInput
    assert mapping['range'] is RangeInput
    assert mapping['hidden'] is HiddenInput


def test_specialized_numeric_and_date_elements_are_individually_addressable() -> None:
    mapping = get_input_component_map()
    assert mapping['birthdate'] is BirthdateInput
    assert mapping['honeypot'] is HoneypotInput
    assert mapping['percentage'] is PercentageInput
    assert mapping['decimal'] is DecimalInput
    assert mapping['integer'] is IntegerInput
    assert mapping['age'] is AgeInput
    assert mapping['quantity'] is QuantityInput
    assert mapping['score'] is ScoreInput
    assert mapping['rating'] is RatingInput
    assert mapping['rating_stars'] is RatingInput
    assert mapping['slider'] is SliderInput
    assert mapping['temperature'] is TemperatureInput


def test_tier2_widgets_are_individually_addressable() -> None:
    """Widgets fixed/wired up as part of the Tier-2 modernization pass."""
    mapping = get_input_component_map()
    assert mapping['checkbox_group'] is CheckboxGroup
    assert mapping['star_rating'] is RatingStarsInput
    assert mapping['tags'] is TagsInput
    assert mapping['captcha'] is CaptchaInput
    # 'rating'/'rating_stars' must still point at the range-slider RatingInput,
    # not the new clickable-star widget -- they are deliberately different widgets.
    assert mapping['rating_stars'] is not RatingStarsInput


def test_register_input_class_is_used_by_actual_rendering() -> None:
    """Regression guard: registering a custom BaseInput subclass at runtime must
    actually be picked up by the real render path (not just get_input_component_map()
    in isolation) -- this is the library's documented escape hatch for a genuinely
    custom widget (docs/inputs.md's "Unknown elements" section), and it silently did
    nothing end-to-end because pydantic_schemaforms/rendering/frameworks.py cached a
    snapshot of the registry at import time, which is always before any app code gets
    a chance to register anything (pydantic_schemaforms/__init__.py eagerly imports
    frameworks.py transitively)."""
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    from pydantic_schemaforms.inputs.base import FormInput
    from pydantic_schemaforms.schema_form import Field, FormModel
    from pydantic_schemaforms.tstring import html

    class _CustomProbeInput(FormInput):
        ui_element = '_test_custom_probe_widget'

        def get_input_type(self) -> str:
            return 'text'

        def render(self, **kwargs: object) -> str:
            return html(t'<div class="custom-probe-widget"></div>')

    try:
        register_input_class(_CustomProbeInput, aliases=['_test_custom_probe_widget'])

        class _ProbeForm(FormModel):
            field: str = Field(..., ui_element='_test_custom_probe_widget')

        renderer = EnhancedFormRenderer(framework='bootstrap')
        html_out = renderer.render_form_from_model(_ProbeForm, data={'field': 'x'}, submit_url='/x')
        assert 'custom-probe-widget' in html_out
    finally:
        reset_input_registry()
