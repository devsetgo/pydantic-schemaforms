from typing import Any, Dict, Type

from pydantic import BaseModel


class FormModel(BaseModel):
    """
    Base class for form models. Generates a minimal JSON Schema for standard HTML input rendering.
    """

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        schema = cls.model_json_schema() if hasattr(cls, "model_json_schema") else cls.schema()
        properties = schema.get("properties", {})
        minimal_props = {}
        for field_name, prop in properties.items():
            minimal = {
                "type": prop.get("type", "string"),
                "title": prop.get("title", field_name),
                "description": prop.get("description", ""),
            }
            if minimal["type"] == "string":
                if "minLength" in prop:
                    minimal["minLength"] = prop["minLength"]
                if "maxLength" in prop:
                    minimal["maxLength"] = prop["maxLength"]
            if minimal["type"] in ("number", "integer"):
                if "minimum" in prop:
                    minimal["minimum"] = prop["minimum"]
                if "maximum" in prop:
                    minimal["maximum"] = prop["maximum"]
            if "enum" in prop:
                minimal["enum"] = prop["enum"]
            minimal_props[field_name] = minimal
        return {
            "title": schema.get("title", cls.__name__),
            "type": "object",
            "properties": minimal_props,
            "required": schema.get("required", []),
        }

    @classmethod
    def get_example_form_data(cls: Type["FormModel"]) -> dict:
        example = {}
        for field_name, model_field in cls.model_fields.items():
            typ = getattr(model_field, "annotation", None)
            if typ is str:
                example[field_name] = "example"
            elif typ is int:
                example[field_name] = 123
            elif typ is float:
                example[field_name] = 1.23
            elif typ is bool:
                example[field_name] = True
            else:
                example[field_name] = ""
        return example
