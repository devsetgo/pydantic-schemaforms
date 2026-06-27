"""Backward-compat shim — use json_schema_form_adapter instead."""

from .json_schema_form_adapter import ReactJSONSchemaFormAdapter as ReactJSONSchemaIntegration

__all__ = ['ReactJSONSchemaIntegration']
