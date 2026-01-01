"""JSON/OpenAPI schema generation utilities."""

from __future__ import annotations

import types
from datetime import date, datetime
from typing import Annotated, Any, Dict, Optional, Type, Union, get_args, get_origin

from annotated_types import Ge, Gt, Le, Lt, MaxLen, MinLen, MultipleOf
from pydantic import AnyUrl, BaseModel, EmailStr
from pydantic.fields import FieldInfo


def _issubclass_safe(candidate: Any, parent: type) -> bool:
    """Return True if candidate is a subclass of parent without raising."""

    try:
        return isinstance(candidate, type) and issubclass(candidate, parent)
    except TypeError:
        return False


class JSONSchemaGenerator:
    """Generate JSON Schema definitions from Pydantic form models."""

    def generate_schema(self, form_model) -> Dict[str, Any]:
        model_cls = self.ensure_model_class(form_model)
        properties: Dict[str, Dict[str, Any]] = {}
        required_fields = []

        for field_name, field_info in model_cls.model_fields.items():
            field_schema = self.generate_field_schema(field_info.annotation, field_info, field_name)
            properties[field_name] = field_schema
            if field_info.is_required():
                required_fields.append(field_name)

        return {"type": "object", "properties": properties, "required": required_fields}

    def generate_field_schema(
        self, field_type: Any, field_info: Optional[FieldInfo] = None, field_name: Optional[str] = None
    ) -> Dict[str, Any]:
        resolved_type = self.normalize_annotation(field_type)
        schema_type, format_hint = self._map_type_to_schema(resolved_type)

        schema: Dict[str, Any] = {"type": schema_type}
        if format_hint:
            schema["format"] = format_hint

        if field_name:
            self._apply_name_based_hints(field_name, schema)

        if field_info:
            self._apply_field_metadata(schema, field_info)

        return schema

    @staticmethod
    def ensure_model_class(form_model) -> Type[BaseModel]:
        """Normalize user input to a BaseModel subclass and validate it."""

        if form_model is None:
            raise TypeError("form_model cannot be None")

        if isinstance(form_model, BaseModel):
            model_cls = form_model.__class__
        elif isinstance(form_model, type):
            model_cls = form_model
        else:
            raise TypeError("form_model must be a BaseModel subclass or instance")

        if not issubclass(model_cls, BaseModel):
            raise TypeError("form_model must inherit from pydantic.BaseModel")
        if not hasattr(model_cls, "model_fields"):
            raise ValueError("form_model is missing model_fields metadata")

        return model_cls

    @staticmethod
    def normalize_annotation(annotation: Any) -> Any:
        """Resolve Optional/Annotated annotations down to their core type."""

        if annotation is None:
            return str

        origin = get_origin(annotation)
        if origin in (types.UnionType, Union):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]  # noqa: E721
            return JSONSchemaGenerator.normalize_annotation(args[0]) if args else str

        if origin is Annotated:
            base = get_args(annotation)
            if base:
                return JSONSchemaGenerator.normalize_annotation(base[0])

        return annotation

    def _map_type_to_schema(self, resolved_type: Any) -> tuple[str, Optional[str]]:
        """Map a Python type to JSON Schema type/format."""

        if _issubclass_safe(resolved_type, bool):
            return "boolean", None
        if _issubclass_safe(resolved_type, int) and not _issubclass_safe(resolved_type, bool):
            return "integer", None
        if _issubclass_safe(resolved_type, float):
            return "number", None
        if resolved_type is datetime:
            return "string", "date-time"
        if resolved_type is date:
            return "string", "date"
        if _issubclass_safe(resolved_type, EmailStr):
            return "string", "email"
        if _issubclass_safe(resolved_type, AnyUrl):
            return "string", "uri"

        return "string", None

    def _apply_name_based_hints(self, field_name: str, schema: Dict[str, Any]) -> None:
        """Infer formats from conventional field names when not already set."""

        if schema.get("type") != "string" or "format" in schema:
            return

        lowered = field_name.lower()
        if "email" in lowered:
            schema["format"] = "email"
        elif any(token in lowered for token in ("url", "uri", "website")):
            schema["format"] = "uri"

    def _apply_field_metadata(self, schema: Dict[str, Any], field_info: FieldInfo) -> None:
        """Augment schema with description and validation constraints."""

        if getattr(field_info, "description", None):
            schema.setdefault("description", field_info.description)

        metadata = getattr(field_info, "metadata", None) or []
        schema_type = schema.get("type")

        for meta in metadata:
            if schema_type == "string":
                if isinstance(meta, MinLen) and meta.min_length is not None:
                    schema["minLength"] = meta.min_length
                elif isinstance(meta, MaxLen) and meta.max_length is not None:
                    schema["maxLength"] = meta.max_length
            if schema_type in {"integer", "number"}:
                if isinstance(meta, Ge) and meta.ge is not None:
                    schema["minimum"] = meta.ge
                elif isinstance(meta, Gt) and meta.gt is not None:
                    schema["exclusiveMinimum"] = meta.gt
                elif isinstance(meta, Le) and meta.le is not None:
                    schema["maximum"] = meta.le
                elif isinstance(meta, Lt) and meta.lt is not None:
                    schema["exclusiveMaximum"] = meta.lt
                elif isinstance(meta, MultipleOf) and meta.multiple_of is not None:
                    schema["multipleOf"] = meta.multiple_of

        if schema_type == "boolean" and getattr(field_info, "default", None) is not None:
            schema["default"] = field_info.default


class OpenAPISchemaGenerator:
    def generate_request_schema(self, form_model) -> Dict[str, Any]:
        schema = JSONSchemaGenerator().generate_schema(form_model)
        return {"content": {"application/json": {"schema": schema}}}

    def generate_response_schema(self, form_model) -> Dict[str, Any]:
        return {
            "200": {
                "description": "Success",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean"},
                                "data": JSONSchemaGenerator().generate_schema(form_model),
                            },
                        }
                    }
                },
            },
            "422": {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "errors": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                }
                            },
                        }
                    }
                },
            },
        }

    def generate_complete_spec(self, form_model, endpoint_path: str, method: str = "POST") -> Dict[str, Any]:
        return {
            "paths": {
                endpoint_path: {
                    method.lower(): {
                        "requestBody": self.generate_request_schema(form_model),
                        "responses": self.generate_response_schema(form_model),
                    }
                }
            }
        }


__all__ = ["JSONSchemaGenerator", "OpenAPISchemaGenerator"]
