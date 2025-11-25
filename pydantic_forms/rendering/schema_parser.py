"""Helpers for turning pydantic model schemas into render plans."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Type

from ..schema_form import FormModel


@dataclass(frozen=True)
class SchemaMetadata:
    """Sorted schema information for downstream renderers."""

    schema: Dict[str, Any]
    fields: List[Tuple[str, Dict[str, Any]]]
    required_fields: List[str]
    layout_fields: List[Tuple[str, Dict[str, Any]]]
    non_layout_fields: List[Tuple[str, Dict[str, Any]]]
    schema_defs: Dict[str, Any]


def resolve_ui_element(field_schema: Dict[str, Any]) -> Optional[str]:
    """Return the declared UI element name for a schema field."""

    ui_info = field_schema.get("ui", {}) or field_schema
    return (
        ui_info.get("element")
        or ui_info.get("ui_element")
        or ui_info.get("widget")
        or ui_info.get("input_type")
    )


def build_schema_metadata(model_cls: Type[FormModel]) -> SchemaMetadata:
    """Collect (cached) schema data along with sorted fields and layout groupings."""

    return _compute_schema_metadata(model_cls)


def reset_schema_metadata_cache() -> None:
    """Clear the cached schema metadata (used in tests or hot reload)."""

    _compute_schema_metadata.cache_clear()


@lru_cache(maxsize=128)
def _compute_schema_metadata(model_cls: Type[FormModel]) -> SchemaMetadata:
    schema = model_cls.model_json_schema()
    properties = schema.get("properties", {})
    fields: List[Tuple[str, Dict[str, Any]]] = list(properties.items())

    def order_key(item: Tuple[str, Dict[str, Any]]) -> int:
        ui_info = item[1].get("ui", {}) or item[1]
        return ui_info.get("order", 999)

    fields.sort(key=order_key)

    layout_fields: List[Tuple[str, Dict[str, Any]]] = []
    non_layout_fields: List[Tuple[str, Dict[str, Any]]] = []

    for field_name, field_schema in fields:
        ui_element = resolve_ui_element(field_schema)
        if ui_element == "layout":
            layout_fields.append((field_name, field_schema))
        else:
            non_layout_fields.append((field_name, field_schema))

    required_fields = schema.get("required", []) or []
    schema_defs = schema.get("$defs", {}) or {}

    return SchemaMetadata(
        schema=schema,
        fields=fields,
        required_fields=required_fields,
        layout_fields=layout_fields,
        non_layout_fields=non_layout_fields,
        schema_defs=schema_defs,
    )
