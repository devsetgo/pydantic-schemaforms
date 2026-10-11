"""Helpers for turning pydantic model schemas into render plans."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from pydantic.fields import FieldInfo

from pydantic_schemaforms.schema_form import FormModel


@dataclass(frozen=True)
class SchemaMetadata:
    """Sorted schema information for downstream renderers."""

    schema: dict[str, Any]
    fields: list[tuple[str, dict[str, Any]]]
    required_fields: list[str]
    layout_fields: list[tuple[str, dict[str, Any]]]
    non_layout_fields: list[tuple[str, dict[str, Any]]]
    schema_defs: dict[str, Any]
    group_fields: tuple[tuple[str, dict[str, Any]], ...] = ()


# ui_element values whose field renders a whole sub-form, and so becomes its
# own group (section / tab / column / accordion panel) under a grouped layout.
GROUP_ELEMENTS = frozenset({'nested_model', 'model_list', 'layout'})


def extract_ui_info(field_schema: dict[str, Any]) -> dict[str, Any]:
    """Normalize a field schema's UI metadata into a single dict.

    Dynamically registered fields (see `_field_info_to_schema`) nest UI
    metadata under a 'ui' key with the 'ui_' prefix already stripped.
    Fields declared via normal type annotations go through Pydantic's
    `model_json_schema()`, which merges `json_schema_extra` straight into
    the property dict — so keys like `ui_placeholder` appear flat, with
    the prefix intact, alongside unprefixed keys like `input_type` (from
    FormField/legacy callers) that callers expect to read as-is.

    The old `field_schema.get('ui', {}) or field_schema` fallback returned
    the flat schema verbatim when there was no nested 'ui' dict, so
    unprefixed keys (input_type, title, options, model_class, ...) worked,
    but prefixed ones (ui_placeholder, ui_autofocus, ui_help_text, ...)
    were never stripped and so never matched lookups like
    `ui_info.get('placeholder')`. This keeps the flat schema intact,
    additionally exposes stripped-prefix aliases for `ui_*` keys, and lets
    an explicit nested 'ui' dict (if present) take precedence over both.
    """

    ui_info: dict[str, Any] = dict(field_schema)
    for key, value in field_schema.items():
        if key.startswith('ui_'):
            ui_info.setdefault(key[3:], value)
    ui_info.update(field_schema.get('ui') or {})
    return ui_info


def _ref_name(ref: Any) -> str | None:
    return ref.split('/')[-1] if isinstance(ref, str) and ref else None


def resolve_nested_model_ref(field_schema: dict[str, Any]) -> str | None:
    """The ``$defs`` name when a property is one nested model (or an Optional of one)."""

    direct = _ref_name(field_schema.get('$ref'))
    if direct:
        return direct
    for option in field_schema.get('anyOf') or []:
        if isinstance(option, dict) and option.get('$ref'):
            return _ref_name(option['$ref'])
    return None


def resolve_list_item_ref(field_schema: dict[str, Any]) -> str | None:
    """The ``$defs`` name of a ``list[Model]`` property's item model."""

    candidates = [field_schema, *(field_schema.get('anyOf') or [])]
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get('type') == 'array':
            items = candidate.get('items')
            if isinstance(items, dict):
                return _ref_name(items.get('$ref'))
    return None


def resolve_ui_element(field_schema: dict[str, Any]) -> str | None:
    """Return the UI element for a schema field: the declared one, else an
    inferred composite (``nested_model`` for a sub-model, ``model_list`` for a
    list of sub-models), else ``None``."""

    ui_info = extract_ui_info(field_schema)
    declared = (
        ui_info.get('element')
        or ui_info.get('ui_element')
        or ui_info.get('widget')
        or ui_info.get('input_type')
    )
    if declared:
        return declared
    if resolve_nested_model_ref(field_schema):
        return 'nested_model'
    if resolve_list_item_ref(field_schema):
        return 'model_list'
    return None


def ordered_properties(schema: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """A schema's properties in render order: declaration order, then ``ui_order``."""

    properties = list((schema.get('properties') or {}).items())
    properties.sort(key=lambda item: extract_ui_info(item[1]).get('order', 999))
    return properties


def build_schema_metadata(model_cls: type[FormModel]) -> SchemaMetadata:
    """Collect (cached) schema data along with sorted fields and layout groupings."""

    if hasattr(model_cls, 'ensure_dynamic_fields') and model_cls.ensure_dynamic_fields():
        reset_schema_metadata_cache()

    return _compute_schema_metadata(model_cls)


def reset_schema_metadata_cache() -> None:
    """Clear the cached schema metadata (used in tests or hot reload)."""

    _compute_schema_metadata.cache_clear()


@lru_cache(maxsize=128)
def _compute_schema_metadata(model_cls: type[FormModel]) -> SchemaMetadata:
    schema = model_cls.model_json_schema()
    properties = schema.setdefault('properties', {})
    required_fields = schema.get('required', []) or []

    _inject_dynamic_fields(model_cls, properties, required_fields)
    schema['required'] = required_fields

    fields = ordered_properties(schema)

    layout_fields: list[tuple[str, dict[str, Any]]] = []
    non_layout_fields: list[tuple[str, dict[str, Any]]] = []

    for field_name, field_schema in fields:
        ui_element = resolve_ui_element(field_schema)
        if ui_element == 'layout':
            layout_fields.append((field_name, field_schema))
        else:
            non_layout_fields.append((field_name, field_schema))

    schema_defs = schema.get('$defs', {}) or {}
    group_fields = tuple(
        (field_name, field_schema)
        for field_name, field_schema in fields
        if resolve_ui_element(field_schema) in GROUP_ELEMENTS
    )

    return SchemaMetadata(
        schema=schema,
        fields=fields,
        required_fields=required_fields,
        layout_fields=layout_fields,
        non_layout_fields=non_layout_fields,
        schema_defs=schema_defs,
        group_fields=group_fields,
    )


def _inject_dynamic_fields(
    model_cls: type[FormModel],
    properties: dict[str, dict[str, Any]],
    required_fields: list[str],
) -> None:
    """Add FieldInfo attributes declared post-class-definition into the schema."""

    # Registered runtime fields are tracked explicitly on FormModel and may
    # not exist as class attributes.
    runtime_fields = dict(getattr(model_cls, '__runtime_fields__', {}))
    for field_name, (_annotation, field_info) in runtime_fields.items():
        if field_name in properties:
            continue
        properties[field_name] = _field_info_to_schema(field_name, field_info)
        if field_info.is_required() and field_name not in required_fields:
            required_fields.append(field_name)

    for attr_name, attr_value in model_cls.__dict__.items():
        if not isinstance(attr_value, FieldInfo):
            continue
        if attr_name in properties:
            continue

        properties[attr_name] = _field_info_to_schema(attr_name, attr_value)
        if attr_value.is_required() and attr_name not in required_fields:
            required_fields.append(attr_name)


def _field_info_to_schema(field_name: str, field_info: FieldInfo) -> dict[str, Any]:
    """Convert a FieldInfo instance into the schema structure expected by renderers."""

    schema: dict[str, Any] = {
        'type': _infer_field_type(field_info),
        'title': field_name.replace('_', ' ').title(),
    }

    if field_info.description:
        schema['description'] = field_info.description

    ui_info = _extract_ui_info(field_info)
    if ui_info:
        schema['ui'] = ui_info

    return schema


def _extract_ui_info(field_info: FieldInfo) -> dict[str, Any]:
    extra = field_info.json_schema_extra or {}
    ui_info: dict[str, Any] = {}
    for key, value in extra.items():
        if key.startswith('ui_'):
            ui_info[key[3:]] = value
    return ui_info


def _infer_field_type(field_info: FieldInfo) -> str:
    annotation = getattr(field_info, 'annotation', None)
    if annotation in (int,):
        return 'integer'
    if annotation in (float,):
        return 'number'
    if annotation is bool:
        return 'boolean'
    return 'string'
