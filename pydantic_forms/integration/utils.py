"""Shared helper utilities for integration modules."""

from __future__ import annotations

import importlib.util


def map_pydantic_to_json_schema_type(python_type):
    if python_type is str:
        return "string"
    if python_type is int:
        return "integer"
    if python_type is float:
        return "number"
    if python_type is bool:
        return "boolean"
    if python_type is list:
        return "array"
    if python_type is dict:
        return "object"
    return "string"


def map_ui_element_to_framework(ui_element, framework):
    mapping = {
        "react": {
            "email": "email",
            "password": "password",
            "textarea": "textarea",
            "select": "select",
        },
        "vue": {
            "email": "email",
            "password": "password",
            "textarea": "textarea",
            "select": "select",
        },
    }
    return mapping.get(framework, {}).get(ui_element, ui_element)


def convert_validation_rules(field_info, framework):  # pragma: no cover - passthrough
    if framework == "react":
        return {}
    if framework == "vue":
        return []
    return {}


def check_framework_availability(framework_name: str) -> bool:
    if framework_name not in {"flask", "fastapi"}:
        return False
    spec = importlib.util.find_spec(framework_name)
    return spec is not None


__all__ = [
    "map_pydantic_to_json_schema_type",
    "map_ui_element_to_framework",
    "convert_validation_rules",
    "check_framework_availability",
]
