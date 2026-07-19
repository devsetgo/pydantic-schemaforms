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
)
from pydantic_schemaforms.inputs.specialized_inputs import HiddenInput, HoneypotInput


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
