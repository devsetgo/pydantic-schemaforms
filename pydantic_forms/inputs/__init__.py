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
from .base import (
    BaseInput,
    FormInput,
    NumericInput,
    FileInputBase,
    SelectInputBase,
    build_label,
    build_error_message,
    build_help_text
)

# Text inputs
from .text_inputs import (
    TextInput,
    PasswordInput,
    EmailInput,
    SearchInput,
    TextArea,
    URLInput,
    TelInput,
    SSNInput,
    PhoneInput,
    CreditCardInput,
    CurrencyInput
)

# Numeric inputs
from .numeric_inputs import (
    NumberInput,
    RangeInput,
    PercentageInput,
    DecimalInput,
    IntegerInput,
    AgeInput,
    QuantityInput,
    ScoreInput,
    RatingInput,
    SliderInput,
    TemperatureInput
)

# Selection inputs
from .selection_inputs import (
    SelectInput,
    MultiSelectInput,
    CheckboxInput,
    CheckboxGroup,
    RadioInput,
    RadioGroup,
    ToggleSwitch,
    ComboBoxInput
)

# DateTime inputs
from .datetime_inputs import (
    DateInput,
    TimeInput,
    DatetimeInput,
    MonthInput,
    WeekInput,
    DateRangeInput,
    TimeRangeInput,
    BirthdateInput
)

# Specialized inputs
from .specialized_inputs import (
    FileInput,
    ImageInput,
    ColorInput,
    HiddenInput,
    ButtonInput,
    SubmitInput,
    ResetInput,
    CSRFInput,
    HoneypotInput,
    CaptchaInput,
    RatingStarsInput,
    TagsInput
)

# Organized exports by category
TEXT_INPUTS = [
    'TextInput', 'PasswordInput', 'EmailInput', 'SearchInput', 'TextArea', 
    'URLInput', 'TelInput', 'SSNInput', 'PhoneInput', 'CreditCardInput', 'CurrencyInput'
]

NUMERIC_INPUTS = [
    'NumberInput', 'RangeInput', 'PercentageInput', 'DecimalInput', 'IntegerInput',
    'AgeInput', 'QuantityInput', 'ScoreInput', 'RatingInput', 'SliderInput', 'TemperatureInput'
]

SELECTION_INPUTS = [
    'SelectInput', 'MultiSelectInput', 'CheckboxInput', 'CheckboxGroup', 
    'RadioInput', 'RadioGroup', 'ToggleSwitch', 'ComboBoxInput'
]

DATETIME_INPUTS = [
    'DateInput', 'TimeInput', 'DatetimeInput', 'MonthInput', 'WeekInput',
    'DateRangeInput', 'TimeRangeInput', 'BirthdateInput'
]

SPECIALIZED_INPUTS = [
    'FileInput', 'ImageInput', 'ColorInput', 'HiddenInput', 'ButtonInput',
    'SubmitInput', 'ResetInput', 'CSRFInput', 'HoneypotInput', 'CaptchaInput',
    'RatingStarsInput', 'TagsInput'
]

BASE_CLASSES = [
    'BaseInput', 'FormInput', 'NumericInput', 'FileInputBase', 'SelectInputBase'
]

UTILITIES = [
    'build_label', 'build_error_message', 'build_help_text'
]

# All available inputs
ALL_INPUTS = (
    TEXT_INPUTS + NUMERIC_INPUTS + SELECTION_INPUTS + 
    DATETIME_INPUTS + SPECIALIZED_INPUTS
)

__all__ = ALL_INPUTS + BASE_CLASSES + UTILITIES