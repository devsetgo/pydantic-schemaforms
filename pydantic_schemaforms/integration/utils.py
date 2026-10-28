"""Shared helper utilities for integration modules."""

from __future__ import annotations

import importlib.util


def map_pydantic_to_json_schema_type(python_type: type) -> str:
    if python_type is str:
        return 'string'
    if python_type is int:
        return 'integer'
    if python_type is float:
        return 'number'
    if python_type is bool:
        return 'boolean'
    if python_type is list:
        return 'array'
    if python_type is dict:
        return 'object'
    return 'string'


def check_framework_availability(framework_name: str) -> bool:
    if framework_name not in {'flask', 'fastapi'}:
        return False
    spec = importlib.util.find_spec(framework_name)
    return spec is not None


__all__ = [
    'map_pydantic_to_json_schema_type',
    'check_framework_availability',
]
