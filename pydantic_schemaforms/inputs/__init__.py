"""Lazy-loading facade for pydantic-schemaforms input components."""

from importlib import import_module
from typing import Dict

# Organized exports by category
TEXT_INPUTS = [
    "TextInput",
    "PasswordInput",
    "EmailInput",
    "SearchInput",
    "TextArea",
    "URLInput",
    "TelInput",
    "SSNInput",
    "PhoneInput",
    "CreditCardInput",
    "CurrencyInput",
]

NUMERIC_INPUTS = [
    "NumberInput",
    "RangeInput",
    "PercentageInput",
    "DecimalInput",
    "IntegerInput",
    "AgeInput",
    "QuantityInput",
    "ScoreInput",
    "RatingInput",
    "SliderInput",
    "TemperatureInput",
]

SELECTION_INPUTS = [
    "SelectInput",
    "MultiSelectInput",
    "CheckboxInput",
    "CheckboxGroup",
    "RadioInput",
    "RadioGroup",
    "ToggleSwitch",
    "ComboBoxInput",
]

DATETIME_INPUTS = [
    "DateInput",
    "TimeInput",
    "DatetimeInput",
    "MonthInput",
    "WeekInput",
    "DateRangeInput",
    "TimeRangeInput",
    "BirthdateInput",
]

SPECIALIZED_INPUTS = [
    "FileInput",
    "ImageInput",
    "ColorInput",
    "HiddenInput",
    "ButtonInput",
    "SubmitInput",
    "ResetInput",
    "CSRFInput",
    "HoneypotInput",
    "CaptchaInput",
    "RatingStarsInput",
    "TagsInput",
]

BASE_CLASSES = ["BaseInput", "FormInput", "NumericInput", "FileInputBase", "SelectInputBase"]

UTILITIES = ["build_label", "build_error_message", "build_help_text"]

# All available inputs
ALL_INPUTS = TEXT_INPUTS + NUMERIC_INPUTS + SELECTION_INPUTS + DATETIME_INPUTS + SPECIALIZED_INPUTS

__all__ = ALL_INPUTS + BASE_CLASSES + UTILITIES

_MODULE_MAP: Dict[str, str] = {}

# Wire categories to their modules without importing them eagerly
for _name in BASE_CLASSES + UTILITIES:
    _MODULE_MAP[_name] = "pydantic_schemaforms.inputs.base"
for _name in DATETIME_INPUTS:
    _MODULE_MAP[_name] = "pydantic_schemaforms.inputs.datetime_inputs"
for _name in NUMERIC_INPUTS:
    _MODULE_MAP[_name] = "pydantic_schemaforms.inputs.numeric_inputs"
for _name in SELECTION_INPUTS:
    _MODULE_MAP[_name] = "pydantic_schemaforms.inputs.selection_inputs"
for _name in SPECIALIZED_INPUTS:
    _MODULE_MAP[_name] = "pydantic_schemaforms.inputs.specialized_inputs"
for _name in TEXT_INPUTS:
    _MODULE_MAP[_name] = "pydantic_schemaforms.inputs.text_inputs"


def __getattr__(name: str):
    """Lazily import concrete input classes on first access."""

    if name not in _MODULE_MAP:
        raise AttributeError(
            f"module 'pydantic_schemaforms.inputs' has no attribute '{name}'"
        )

    module = import_module(_MODULE_MAP[name])
    attr = getattr(module, name)
    globals()[name] = attr
    return attr


def __dir__():  # pragma: no cover - aids interactive discovery
    return sorted(set(list(globals().keys()) + __all__))
