"""Vue Formulate integration helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Union


class VueFormulateIntegration:
    """Generate configuration for Vue Formulate."""

    def generate_form_config(self, form_model) -> List[Dict[str, Any]]:
        config: List[Dict[str, Any]] = []

        for field_name, field_info in form_model.model_fields.items():
            field_type = field_info.annotation
            if hasattr(field_type, "__origin__") and field_type.__origin__ == Union:
                non_none_types = [t for t in field_type.__args__ if t is not type(None)]
                if non_none_types:
                    field_type = non_none_types[0]

            field_config = {"name": field_name, "label": field_name.replace("_", " ").title()}
            lowered = field_name.lower()

            if "email" in lowered:
                field_config["type"] = "email"
            elif "password" in lowered:
                field_config["type"] = "password"
            elif field_type is bool:
                field_config["type"] = "checkbox"
            elif field_type in (int, float):
                field_config["type"] = "number"
            else:
                field_config["type"] = "text"

            config.append(field_config)

        return config

    def generate_validation_rules(self, form_model) -> Dict[str, List[str]]:
        rules: Dict[str, List[str]] = {}

        for field_name, field_info in form_model.model_fields.items():
            field_rules: List[str] = []
            if field_info.is_required():
                field_rules.append("required")
            if "email" in field_name.lower():
                field_rules.append("email")
            if field_rules:
                rules[field_name] = field_rules

        return rules


__all__ = ["VueFormulateIntegration"]
