"""
Input type constants and mappings for pydantic-schemaforms.
Provides organized collections of input types and validation mappings.
"""

from datetime import date, datetime, time
from typing import Dict, Set, Type

# Text input types
TEXT_INPUTS = [
    "text",
    "password",
    "email",
    "search",
    "textarea",
    "url",
    "tel",
    "ssn",
    "phone",
    "credit_card",
    "currency",
]

# Numeric input types
NUMERIC_INPUTS = [
    "number",
    "range",
    "percentage",
    "decimal",
    "integer",
    "age",
    "quantity",
    "score",
    "rating",
    "slider",
    "temperature",
]

# Selection input types
SELECTION_INPUTS = [
    "select",
    "multiselect",
    "checkbox",
    "checkbox_group",
    "radio",
    "radio_group",
    "toggle_switch",
    "combobox",
]

# Date/time input types
DATETIME_INPUTS = [
    "date",
    "time",
    "datetime",
    "datetime_local",
    "month",
    "week",
    "date_range",
    "time_range",
    "birthdate",
]

# Specialized input types
SPECIALIZED_INPUTS = [
    "file",
    "image",
    "color",
    "hidden",
    "button",
    "submit",
    "reset",
    "csrf",
    "honeypot",
    "captcha",
    "rating_stars",
    "tags",
]

# All available input types
ALL_INPUT_TYPES = (
    TEXT_INPUTS + NUMERIC_INPUTS + SELECTION_INPUTS + DATETIME_INPUTS + SPECIALIZED_INPUTS
)

# Type mapping for automatic input type detection
PYTHON_TYPE_TO_INPUT_TYPE: Dict[Type, str] = {
    str: "text",
    int: "number",
    float: "number",
    bool: "checkbox",
    list: "select",  # Will need options
    tuple: "select",  # Will need options
}

# Valid input types for each Python type
VALID_INPUT_TYPES_BY_PYTHON_TYPE: Dict[Type, Set[str]] = {
    str: {
        "text",
        "password",
        "email",
        "search",
        "textarea",
        "url",
        "tel",
        "ssn",
        "phone",
        "credit_card",
        "currency",
        "hidden",
        "color",
    },
    int: {
        "number",
        "range",
        "integer",
        "age",
        "quantity",
        "score",
        "rating",
        "slider",
        "temperature",
        "hidden",
    },
    float: {
        "number",
        "range",
        "percentage",
        "decimal",
        "score",
        "rating",
        "slider",
        "temperature",
        "hidden",
    },
    bool: {"checkbox", "toggle_switch", "hidden"},
    list: {"select", "multiselect", "checkbox_group", "radio_group", "tags"},
    tuple: {"select", "multiselect", "checkbox_group", "radio_group"},
}

# Special type mappings
VALID_INPUT_TYPES_BY_PYTHON_TYPE.update(
    {
        date: {"date", "birthdate", "hidden"},
        datetime: {"datetime", "datetime_local", "hidden"},
        time: {"time", "hidden"},
    }
)

# Input type defaults by Python type
DEFAULT_INPUT_TYPE_BY_PYTHON_TYPE: Dict[Type, str] = {
    str: "text",
    int: "number",
    float: "number",
    bool: "checkbox",
    list: "select",
    tuple: "select",
    date: "date",
    datetime: "datetime",
    time: "time",
}


def validate_input_type_for_python_type(python_type: Type, input_type: str) -> bool:
    """
    Validate that an input type is compatible with a Python type.

    Args:
        python_type: The Python type of the field
        input_type: The desired input type

    Returns:
        True if the input type is valid for the Python type
    """
    valid_types = VALID_INPUT_TYPES_BY_PYTHON_TYPE.get(python_type, set())
    return input_type in valid_types


def get_default_input_type(python_type: Type) -> str:
    """
    Get the default input type for a Python type.

    Args:
        python_type: The Python type of the field

    Returns:
        The default input type for the Python type
    """
    return DEFAULT_INPUT_TYPE_BY_PYTHON_TYPE.get(python_type, "text")


def get_valid_input_types(python_type: Type) -> Set[str]:
    """
    Get all valid input types for a Python type.

    Args:
        python_type: The Python type of the field

    Returns:
        Set of valid input types for the Python type
    """
    return VALID_INPUT_TYPES_BY_PYTHON_TYPE.get(python_type, set())


def is_input_type_valid(python_type: Type, input_type: str, field_name: str = "") -> None:
    """
    Validate input type for Python type and raise descriptive error if invalid.

    Args:
        python_type: The Python type of the field
        input_type: The desired input type
        field_name: The field name for error messages

    Raises:
        ValueError: If the input type is not valid for the Python type
    """
    if not validate_input_type_for_python_type(python_type, input_type):
        valid_types = get_valid_input_types(python_type)
        field_info = f" for field '{field_name}'" if field_name else ""
        raise ValueError(
            f"Invalid input type '{input_type}'{field_info}. "
            f"Type {python_type.__name__} supports: {', '.join(sorted(valid_types))}"
        )


# Framework-specific icon mappings
FRAMEWORK_ICON_MAPPINGS = {
    "bootstrap": {"prefix": "bi bi-", "fallback": "bi bi-file-text"},
    "material": {"prefix": "material-icons", "fallback": "description"},
    "fontawesome": {"prefix": "fas fa-", "fallback": "fas fa-file-alt"},
}


def format_icon_class(icon: str, framework: str = "bootstrap") -> str:
    """
    Format an icon class for the specified framework.

    Args:
        icon: The icon name (can include or exclude prefix)
        framework: The UI framework

    Returns:
        Properly formatted icon class
    """
    if not icon:
        return ""

    mapping = FRAMEWORK_ICON_MAPPINGS.get(framework, FRAMEWORK_ICON_MAPPINGS["bootstrap"])

    # If icon already has the prefix, return as-is
    if icon.startswith(mapping["prefix"]):
        return icon

    # Add the prefix
    return f"{mapping['prefix']}{icon}"


__all__ = [
    "TEXT_INPUTS",
    "NUMERIC_INPUTS",
    "SELECTION_INPUTS",
    "DATETIME_INPUTS",
    "SPECIALIZED_INPUTS",
    "ALL_INPUT_TYPES",
    "PYTHON_TYPE_TO_INPUT_TYPE",
    "VALID_INPUT_TYPES_BY_PYTHON_TYPE",
    "DEFAULT_INPUT_TYPE_BY_PYTHON_TYPE",
    "validate_input_type_for_python_type",
    "get_default_input_type",
    "get_valid_input_types",
    "is_input_type_valid",
    "FRAMEWORK_ICON_MAPPINGS",
    "format_icon_class",
]
