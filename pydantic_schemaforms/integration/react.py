"""React JSON Schema form helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .schema import JSONSchemaGenerator


class ReactJSONSchemaIntegration:
    """Generate JSON schema artifacts for React JSON Schema Forms."""

    def __init__(self) -> None:
        self._schema_generator = JSONSchemaGenerator()

    def generate_schema(self, form_model):
        return self._schema_generator.generate_schema(form_model)

    def generate_ui_schema(self, form_model):
        ui_schema: Dict[str, Dict[str, Any]] = {}
        model_cls = JSONSchemaGenerator.ensure_model_class(form_model)

        for field_name, field_info in model_cls.model_fields.items():
            field_schema = self._schema_generator.generate_field_schema(
                field_info.annotation, field_info, field_name
            )
            widget_entry = self._build_ui_entry(field_name, field_schema, field_info)
            if widget_entry:
                ui_schema[field_name] = widget_entry

        return ui_schema

    def _build_ui_entry(
        self, field_name: str, field_schema: Dict[str, Any], field_info
    ) -> Optional[Dict[str, Any]]:
        raw_extra = getattr(field_info, "json_schema_extra", None)
        extra = raw_extra if isinstance(raw_extra, dict) else {}
        widget = extra.get("ui_widget") or extra.get("ui_element")
        format_hint = field_schema.get("format")
        lowered = field_name.lower()

        if not widget:
            if format_hint in {"email", "date", "date-time"}:
                widget = "datetime" if format_hint == "date-time" else format_hint
            elif "password" in lowered:
                widget = "password"
            elif lowered in {"bio", "description", "comment", "notes"}:
                widget = "textarea"

        if not widget:
            return None

        ui_entry: Dict[str, Any] = {"ui:widget": widget}

        options = extra.get("ui_options")
        if isinstance(options, dict) and options:
            ui_entry["ui:options"] = options

        if extra.get("ui_autofocus"):
            ui_entry["ui:autofocus"] = True
        if extra.get("ui_placeholder"):
            ui_entry["ui:placeholder"] = extra["ui_placeholder"]
        if extra.get("ui_help_text"):
            ui_entry["ui:help"] = extra["ui_help_text"]
        if extra.get("ui_disabled"):
            ui_entry["ui:disabled"] = True
        if extra.get("ui_readonly"):
            ui_entry["ui:readonly"] = True

        return ui_entry

    def generate_form_data(self, form_model, data):  # pragma: no cover - passthrough
        return data

    def generate_complete_config(self, form_model, initial_data: Optional[Dict[str, Any]] = None):
        return {
            "schema": self.generate_schema(form_model),
            "uiSchema": self.generate_ui_schema(form_model),
            "formData": initial_data or {},
        }


__all__ = ["ReactJSONSchemaIntegration"]
