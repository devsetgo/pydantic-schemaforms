"""
Pydantic Forms Input Components

This module provides all the input components organized by category:
- Text Inputs: TextInput, PasswordInput, EmailInput, TextArea, etc.
- Numeric Inputs: NumberInput, RangeInput, PercentageInput, etc.
- Selection Inputs: SelectInput, RadioGroup, CheckboxInput, etc.
- DateTime Inputs: DateInput, TimeInput, DatetimeInput, etc.
- Specialized Inputs: FileInput, ColorInput, HiddenInput, etc.

All inputs use Python 3.14's native template strings for efficient HTML generation.
"""

# Base classes
from .base import (  # noqa: F401
    BaseInput,
    FileInputBase,
    FormInput,
    NumericInput,
    SelectInputBase,
    build_error_message,
    build_help_text,
    build_label,
)
# DateTime inputs
from .datetime_inputs import (  # noqa: F401
    BirthdateInput,
    DateInput,
    DateRangeInput,
    DatetimeInput,
    MonthInput,
    TimeInput,
    TimeRangeInput,
    WeekInput,
)
# Numeric inputs
from .numeric_inputs import (  # noqa: F401
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
# Selection inputs
from .selection_inputs import (  # noqa: F401
    CheckboxGroup,
    CheckboxInput,
    ComboBoxInput,
    MultiSelectInput,
    RadioGroup,
    RadioInput,
    SelectInput,
    ToggleSwitch,
)
# Specialized inputs
from .specialized_inputs import (  # noqa: F401
    ButtonInput,
    CaptchaInput,
    ColorInput,
    CSRFInput,
    FileInput,
    HiddenInput,
    HoneypotInput,
    ImageInput,
    RatingStarsInput,
    ResetInput,
    SubmitInput,
    TagsInput,
)
# Text inputs
from .text_inputs import (  # noqa: F401
    CreditCardInput,
    CurrencyInput,
    EmailInput,
    PasswordInput,
    PhoneInput,
    SearchInput,
    SSNInput,
    TelInput,
    TextArea,
    TextInput,
    URLInput,
)

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
