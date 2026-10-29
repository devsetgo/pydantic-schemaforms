"""Helpers for turning pydantic model schemas into render plans."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, get_args

from pydantic import BaseModel
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


def _is_enum_def(definition: Any) -> bool:
    return isinstance(definition, dict) and 'enum' in definition and 'properties' not in definition


def normalize_field_schema(
    field_schema: dict[str, Any], schema_defs: dict[str, Any]
) -> dict[str, Any]:
    """Flatten the two shapes Pydantic gives common field types, so input
    inference sees the real type:

    - ``Optional[T]`` arrives as ``anyOf: [T, {"type": "null"}]``; a scalar
      ``T`` is unwrapped and marked ``nullable`` (so a select can offer an
      empty choice). Optional sub-models are left alone, since the
      nested-form code already resolves them through ``anyOf``.
    - An ``Enum`` arrives as a ``$ref`` to ``$defs``; its values are inlined
      as ``enum`` so it renders as a select. The definition's own title (the
      Enum class name) is not copied, so the label still comes from the field.
    """

    options = field_schema.get('anyOf')
    if isinstance(options, list):
        non_null = [o for o in options if not (isinstance(o, dict) and o.get('type') == 'null')]
        member = non_null[0] if len(non_null) == 1 and len(non_null) < len(options) else None
        member_ref = _ref_name(member.get('$ref')) if isinstance(member, dict) else None
        if isinstance(member, dict) and (
            member_ref is None or _is_enum_def(schema_defs.get(member_ref))
        ):
            rest = {key: value for key, value in field_schema.items() if key != 'anyOf'}
            field_schema = {**member, **rest, 'nullable': True}

    ref = _ref_name(field_schema.get('$ref'))
    definition = schema_defs.get(ref) if ref else None
    if isinstance(definition, dict) and _is_enum_def(definition):
        inlined = {k: v for k, v in definition.items() if k not in ('title', 'description')}
        rest = {key: value for key, value in field_schema.items() if key != '$ref'}
        field_schema = {**inlined, **rest}
    return field_schema


def _normalize_properties(properties: dict[str, Any], schema_defs: dict[str, Any]) -> None:
    for name, field_schema in properties.items():
        if isinstance(field_schema, dict):
            properties[name] = normalize_field_schema(field_schema, schema_defs)


def _models_by_name(model_cls: type[BaseModel]) -> dict[str, type[BaseModel]]:
    """Every model reachable from ``model_cls`` (sub-models, list items),
    keyed by name the way Pydantic keys ``$defs``."""

    found: dict[str, type[BaseModel]] = {}
    pending: list[Any] = [model_cls]
    while pending:
        candidate = pending.pop()
        if isinstance(candidate, type) and issubclass(candidate, BaseModel):
            if candidate.__name__ in found:
                continue
            found[candidate.__name__] = candidate
            pending.extend(info.annotation for info in candidate.model_fields.values())
        else:
            pending.extend(get_args(candidate))
    return found


def _restore_titles(properties: dict[str, Any], model_fields: dict[str, FieldInfo]) -> None:
    # Pydantic drops a $ref field's title when it equals the referenced
    # class's own title (Field(title="Size") on a `Size` enum), which would
    # otherwise leave the label to fall back to the field name.
    for name, info in model_fields.items():
        field_schema = properties.get(info.alias or name)
        if isinstance(field_schema, dict) and info.title and 'title' not in field_schema:
            field_schema['title'] = info.title


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

    schema_defs = schema.get('$defs', {}) or {}
    models = _models_by_name(model_cls)
    _restore_titles(properties, model_cls.model_fields)
    _normalize_properties(properties, schema_defs)
    for def_name, definition in schema_defs.items():
        if isinstance(definition, dict) and isinstance(definition.get('properties'), dict):
            if def_name in models:
                _restore_titles(definition['properties'], models[def_name].model_fields)
            _normalize_properties(definition['properties'], schema_defs)

    fields = ordered_properties(schema)

    layout_fields: list[tuple[str, dict[str, Any]]] = []
    non_layout_fields: list[tuple[str, dict[str, Any]]] = []

    for field_name, field_schema in fields:
        ui_element = resolve_ui_element(field_schema)
        if ui_element == 'layout':
            layout_fields.append((field_name, field_schema))
        else:
            non_layout_fields.append((field_name, field_schema))

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
