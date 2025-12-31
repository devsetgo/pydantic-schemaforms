"""Helpers for turning pydantic model schemas into render plans."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic.fields import FieldInfo

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

    if hasattr(model_cls, "ensure_dynamic_fields") and model_cls.ensure_dynamic_fields():
        reset_schema_metadata_cache()

    return _compute_schema_metadata(model_cls)


def reset_schema_metadata_cache() -> None:
    """Clear the cached schema metadata (used in tests or hot reload)."""

    _compute_schema_metadata.cache_clear()


@lru_cache(maxsize=128)
def _compute_schema_metadata(model_cls: Type[FormModel]) -> SchemaMetadata:
    schema = model_cls.model_json_schema()
    properties = schema.setdefault("properties", {})
    required_fields = schema.get("required", []) or []

    _inject_dynamic_fields(model_cls, properties, required_fields)
    schema["required"] = required_fields

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

    schema_defs = schema.get("$defs", {}) or {}

    return SchemaMetadata(
        schema=schema,
        fields=fields,
        required_fields=required_fields,
        layout_fields=layout_fields,
        non_layout_fields=non_layout_fields,
        schema_defs=schema_defs,
    )


def _inject_dynamic_fields(
    model_cls: Type[FormModel],
    properties: Dict[str, Dict[str, Any]],
    required_fields: List[str],
) -> None:
    """Add FieldInfo attributes declared post-class-definition into the schema."""

    for attr_name, attr_value in model_cls.__dict__.items():
        if not isinstance(attr_value, FieldInfo):
            continue
        if attr_name in properties:
            continue

        properties[attr_name] = _field_info_to_schema(attr_name, attr_value)
        if attr_value.is_required():
            required_fields.append(attr_name)


def _field_info_to_schema(field_name: str, field_info: FieldInfo) -> Dict[str, Any]:
    """Convert a FieldInfo instance into the schema structure expected by renderers."""

    schema: Dict[str, Any] = {
        "type": _infer_field_type(field_info),
        "title": field_name.replace("_", " ").title(),
    }

    if field_info.description:
        schema["description"] = field_info.description

    ui_info = _extract_ui_info(field_info)
    if ui_info:
        schema["ui"] = ui_info

    return schema


def _extract_ui_info(field_info: FieldInfo) -> Dict[str, Any]:
    extra = field_info.json_schema_extra or {}
    ui_info: Dict[str, Any] = {}
    for key, value in extra.items():
        if key.startswith("ui_"):
            ui_info[key[3:]] = value
    return ui_info


def _infer_field_type(field_info: FieldInfo) -> str:
    annotation = getattr(field_info, "annotation", None)
    if annotation in (int,):
        return "integer"
    if annotation in (float,):
        return "number"
    if annotation is bool:
        return "boolean"
    return "string"
