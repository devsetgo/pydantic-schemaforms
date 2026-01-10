"""Field rendering helpers shared across renderers."""

from __future__ import annotations

from html import escape
from typing import Any, Dict, List, Optional

from ..icon_mapping import map_icon_for_framework
from ..inputs import HiddenInput
from ..rendering.context import RenderContext
from ..rendering.frameworks import get_input_component
from .themes import RendererTheme


class FieldRenderer:
    """Encapsulates the heavy lifting of turning schema fields into HTML."""

    def __init__(self, renderer: Any) -> None:
        self._renderer = renderer

    @property
    def config(self) -> Dict[str, Any]:
        return self._renderer.config

    @property
    def framework(self) -> str:
        return self._renderer.framework

    @property
    def theme(self):
        return getattr(self._renderer, "theme", None)

    def render_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: Optional[List[str]] = None,
        context: Optional[RenderContext] = None,
        layout: str = "vertical",
        all_errors: Optional[Dict[str, str]] = None,
    ) -> str:

        if context is None:
            raise ValueError("RenderContext is required for field rendering")

        ui_info = field_schema.get("ui", {}) or field_schema

        if ui_info.get("hidden"):
            return self._render_hidden_field(field_name, value)

        ui_element = (
            ui_info.get("element")
            or ui_info.get("ui_element")
            or ui_info.get("widget")
            or ui_info.get("input_type")
            or self._infer_ui_element(field_schema)
        )

        if ui_element == "layout":
            return self._renderer._render_layout_field(  # noqa: SLF001
                field_name,
                field_schema,
                value,
                error,
                ui_info,
                context,
            )

        if ui_element == "model_list":
            return self._render_model_list_field(
                field_name,
                field_schema,
                value,
                error,
                required_fields,
                ui_info,
                context,
                all_errors,
            )

        input_component = get_input_component(ui_element)()

        field_attrs = {
            "name": field_name,
            "id": field_name,
            "class": self._get_input_class(ui_element),
        }

        if value is not None and ui_element != "password":
            if ui_element == "checkbox":
                if value is True or value == "true" or value == "1" or value == "on":
                    field_attrs["checked"] = True
                field_attrs["value"] = "1"
            else:
                field_attrs["value"] = value
        elif value is not None and ui_element == "password":
            field_attrs["value"] = value

        resolved_required = required_fields or []
        if field_name in resolved_required:
            field_attrs["required"] = True

        if "minLength" in field_schema:
            field_attrs["minlength"] = field_schema["minLength"]
        if "maxLength" in field_schema:
            field_attrs["maxlength"] = field_schema["maxLength"]
        if "minimum" in field_schema:
            field_attrs["min"] = field_schema["minimum"]
        if "maximum" in field_schema:
            field_attrs["max"] = field_schema["maximum"]
        if "pattern" in field_schema:
            field_attrs["pattern"] = field_schema["pattern"]

        if ui_info.get("autofocus"):
            field_attrs["autofocus"] = True
        if ui_info.get("disabled"):
            field_attrs["disabled"] = True
        if ui_info.get("readonly"):
            field_attrs["readonly"] = True
        if ui_info.get("placeholder"):
            field_attrs["placeholder"] = ui_info["placeholder"]
        if ui_info.get("class"):
            field_attrs["class"] += f" {ui_info['class']}"
        if ui_info.get("style"):
            field_attrs["style"] = ui_info["style"]

        ui_options_dict, ui_options_list = self._extract_ui_options(ui_info, field_schema)
        if ui_options_dict:
            field_attrs = self._apply_ui_option_attributes(field_attrs, ui_options_dict)

        label_text = field_schema.get("title", field_name.replace("_", " ").title())
        help_text = ui_info.get("help_text") or field_schema.get("description")
        icon = ui_info.get("icon")
        if icon:
            icon = map_icon_for_framework(icon, self.framework)

        try:
            if ui_element in ("select", "radio", "multiselect"):
                selection_options = ui_options_list or []
                if not selection_options and "enum" in field_schema:
                    selection_options = field_schema["enum"]
                if (
                    not selection_options
                    and isinstance(field_schema.get("items"), dict)
                    and "enum" in field_schema.get("items", {})
                ):
                    selection_options = field_schema["items"]["enum"]

                formatted_options = self._normalize_options(selection_options, value)

                if not formatted_options:
                    input_html = (
                        f"<!-- Warning: No options provided for {ui_element} field '{field_name}' -->"
                    )
                else:
                    field_attrs.pop("value", None)
                    if ui_element == "radio":
                        field_attrs.setdefault("group_name", field_name)
                        field_attrs.setdefault("legend", label_text)
                    if ui_element == "multiselect":
                        field_attrs["multiple"] = True

                    input_html = input_component.render_with_label(
                        label=label_text,
                        help_text=help_text,
                        error=error,
                        icon=icon,
                        framework=self.framework,
                        options=formatted_options,
                        **field_attrs,
                    )
            else:
                input_html = input_component.render_with_label(
                    label=label_text,
                    help_text=help_text,
                    error=error,
                    icon=icon,
                    framework=self.framework,
                    **field_attrs,
                )

            if input_html is None:
                input_html = f"<!-- Error: {ui_element} input returned None -->"
        except Exception as exc:  # pragma: no cover - defensive fallback
            input_html = f"<!-- Error rendering {ui_element}: {str(exc)} -->"

        wrapper_class = ""
        if self.theme:
            wrapper_class = self.theme.field_wrapper_class() or ""
        if not wrapper_class:
            wrapper_class = self.config.get("field_wrapper_class", "")
        if wrapper_class:
            return f'<div class="{wrapper_class}">{input_html}</div>'
        return input_html

    def _render_model_list_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        required_fields: Optional[List[str]],
        ui_info: Dict[str, Any],
        context: RenderContext,
        all_errors: Optional[Dict[str, str]],
    ) -> str:
        from ..model_list import ModelListRenderer

        list_renderer = ModelListRenderer(framework=self.framework)
        model_class = ui_info.get("model_class")
        if model_class and not isinstance(model_class, type):
            model_class = None
        schema_def: Optional[Dict[str, Any]] = None

        if not model_class:
            items_ref = field_schema.get("items", {}).get("$ref")
            if items_ref:
                model_name = items_ref.split("/")[-1]
                schema_defs = context.schema_defs or {}
                schema_def = schema_defs.get(model_name)
                if not schema_def:
                    return (
                        f"<!-- Error: Could not resolve model reference '{items_ref}' for field '{field_name}' -->"
                    )
            else:
                return (
                    f"<!-- Error: model_class not specified and no items.$ref found for model_list field '{field_name}' -->"
                )

        list_values: List[Dict[str, Any]] = []
        if value:
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, "model_dump"):
                        list_values.append(item.model_dump())
                    elif isinstance(item, dict):
                        list_values.append(item)
            elif hasattr(value, "model_dump"):
                list_values = [value.model_dump()]
            elif isinstance(value, dict):
                list_values = [value]

        nested_errors = self.extract_nested_errors_for_field(field_name, all_errors or {})

        if model_class:
            return list_renderer.render_model_list(
                field_name=field_name,
                label=field_schema.get("title", field_name.replace("_", " ").title()),
                model_class=model_class,
                values=list_values,
                error=error,
                nested_errors=nested_errors,
                help_text=ui_info.get("help_text"),
                is_required=field_name in (required_fields or []),
                min_items=ui_info.get("min_items", 0),
                max_items=ui_info.get("max_items", 10),
            )

        return self.render_model_list_from_schema(
            field_name=field_name,
            field_schema=field_schema,
            schema_def=schema_def or {},
            values=list_values,
            error=error,
            ui_info=ui_info,
            required_fields=required_fields or [],
            context=context,
        )

    def _extract_ui_options(
        self, ui_info: Dict[str, Any], field_schema: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[Any]]:
        raw_options = (
            ui_info.get("options")
            or ui_info.get("ui_options")
            or field_schema.get("ui_options")
            or {}
        )

        options_dict: Dict[str, Any] = raw_options if isinstance(raw_options, dict) else {}
        options_list: List[Any] = []

        if isinstance(raw_options, list):
            options_list = raw_options
        elif isinstance(options_dict, dict):
            if isinstance(options_dict.get("choices"), list):
                options_list = options_dict.get("choices", [])
            elif isinstance(options_dict.get("options"), list):
                options_list = options_dict.get("options", [])

        return options_dict, options_list

    def _apply_ui_option_attributes(
        self, field_attrs: Dict[str, Any], ui_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not ui_options:
            return field_attrs

        option_keys_to_skip = {"choices", "options", "async_options", "fetch_url"}

        for key, option_value in ui_options.items():
            if key in option_keys_to_skip:
                continue
            if isinstance(option_value, (list, dict)):
                continue

            if key == "class" and field_attrs.get("class"):
                field_attrs["class"] = f'{field_attrs["class"]} {option_value}'.strip()
            elif key == "style" and field_attrs.get("style"):
                separator = "; " if not str(field_attrs["style"]).strip().endswith(";") else " "
                field_attrs["style"] = f'{field_attrs["style"]}{separator}{option_value}'
            else:
                field_attrs[key] = option_value

        return field_attrs

    def _normalize_options(self, options: List[Any], current_value: Any) -> List[Dict[str, Any]]:
        if not options:
            return []

        normalized: List[Dict[str, Any]] = []

        for option in options:
            if isinstance(option, dict):
                formatted = option.copy()
                if "value" not in formatted:
                    fallback_value = None
                    for fallback_key in ("id", "key", "label"):
                        if fallback_key in formatted:
                            fallback_value = formatted[fallback_key]
                            break
                    formatted["value"] = fallback_value

                if not formatted.get("label"):
                    formatted["label"] = str(formatted.get("value", ""))

                formatted.setdefault(
                    "selected",
                    self._is_option_selected(formatted.get("value"), current_value),
                )
                normalized.append(formatted)
            elif isinstance(option, (list, tuple)) and option:
                value = option[0]
                label = option[1] if len(option) > 1 else option[0]
                normalized.append(
                    {
                        "value": value,
                        "label": label,
                        "selected": self._is_option_selected(value, current_value),
                    }
                )
            else:
                normalized.append(
                    {
                        "value": option,
                        "label": option,
                        "selected": self._is_option_selected(option, current_value),
                    }
                )

        return normalized

    def _is_option_selected(self, option_value: Any, current_value: Any) -> bool:
        if option_value is None or current_value is None:
            return False

        option_str = str(option_value)

        if isinstance(current_value, (list, tuple, set)):
            return option_str in {str(val) for val in current_value}

        return option_str == str(current_value)

    def _render_hidden_field(self, field_name: str, value: Any) -> str:
        hidden_input = HiddenInput()
        return hidden_input.render(name=field_name, id=field_name, value=value or "")

    def _infer_ui_element(self, field_schema: Dict[str, Any]) -> str:
        field_type = field_schema.get("type", "string")

        if field_type == "string":
            max_length = field_schema.get("maxLength", 0)
            if max_length > 200:
                return "textarea"
            if "email" in field_schema.get("title", "").lower():
                return "email"
            if "password" in field_schema.get("title", "").lower():
                return "password"
            return "text"
        if field_type in ("integer", "number"):
            return "number"
        if field_type == "boolean":
            return "checkbox"
        return "text"

    def _get_input_class(self, ui_element: str) -> str:
        themed_class = ""
        if self.theme:
            themed_class = self.theme.input_class(ui_element)
        if themed_class:
            return themed_class
        if ui_element == "checkbox":
            return self.config.get("checkbox_class", "")
        if ui_element in ("select", "radio", "multiselect"):
            return self.config.get("select_class", "")
        return self.config.get("input_class", "")

    def render_model_list_from_schema(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        schema_def: Dict[str, Any],
        values: List[Dict[str, Any]],
        error: Optional[str],
        ui_info: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> str:
        items_parts: List[str] = []

        for i, item_data in enumerate(values):
            items_parts.append(
                self._render_schema_list_item(
                    field_name,
                    schema_def,
                    i,
                    item_data,
                    context,
                    ui_info,
                )
            )

        min_items = field_schema.get("minItems", 0)
        if not values and min_items > 0:
            for i in range(min_items):
                items_parts.append(
                    self._render_schema_list_item(
                        field_name,
                        schema_def,
                        i,
                        {},
                        context,
                        ui_info,
                    )
                )

        if not values and min_items == 0:
            items_parts.append(
                self._render_schema_list_item(
                    field_name,
                    schema_def,
                    0,
                    {},
                    context,
                    ui_info,
                )
            )

        # Always include a hidden template item so lists can be emptied (minItems=0)
        # and still support adding new items afterwards.
        template_item_html = self._render_schema_list_item(
            field_name,
            schema_def,
            0,
            {},
            context,
            ui_info,
        )
        template_html = f'<template class="model-list-item-template">{template_item_html}</template>'

        items_html = template_html + "".join(items_parts)
        max_items = field_schema.get("maxItems", 10)
        help_text = ui_info.get("help_text") or field_schema.get("description")
        label = field_schema.get("title", field_name.replace("_", " ").title())
        add_button_label = ui_info.get("add_button_label", "Add Item")
        is_required = field_name in (required_fields or [])

        if self.theme:
            themed_html = self.theme.render_model_list_container(
                field_name=field_name,
                label=label,
                is_required=is_required,
                min_items=min_items,
                max_items=max_items,
                items_html=items_html,
                help_text=help_text,
                error=error,
                add_button_label=add_button_label,
            )
            if themed_html:
                return themed_html

        return RendererTheme().render_model_list_container(
            field_name=field_name,
            label=label,
            is_required=is_required,
            min_items=min_items,
            max_items=max_items,
            items_html=items_html,
            help_text=help_text,
            error=error,
            add_button_label=add_button_label,
        )

    def extract_nested_errors_for_field(
        self, field_name: str, all_errors: Dict[str, Any]
    ) -> Dict[str, str]:
        nested_errors: Dict[str, str] = {}
        field_prefix = f"{field_name}["

        for error_path, error_message in (all_errors or {}).items():
            if error_path.startswith(field_prefix):
                nested_part = error_path[len(field_prefix) :]
                if "]." in nested_part:
                    simplified_path = nested_part.replace("].", ".")
                    nested_errors[simplified_path] = error_message

        return nested_errors

    def _render_schema_list_item(
        self,
        field_name: str,
        schema_def: Dict[str, Any],
        index: int,
        item_data: Dict[str, Any],
        context: RenderContext,
        ui_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        ui_info = ui_info or {}
        collapsible = ui_info.get("collapsible_items", True)
        expanded = ui_info.get("items_expanded", True)
        title_template = ui_info.get("item_title_template", "Item #{index}")

        title_vars = {"index": index + 1, **item_data}
        try:
            item_title = title_template.format(**title_vars)
        except (KeyError, ValueError):  # pragma: no cover - best effort rendering
            item_title = f"Item #{index + 1}"

        collapse_class = "" if expanded else "collapse"
        collapse_id = f"{field_name}_item_{index}_content"

        html = f"""
        <div class="model-list-item card border mb-3"
             data-index="{index}"
             data-title-template="{escape(title_template)}"
             data-field-name="{field_name}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">"""

        if collapsible:
            html += f"""
                    <button class="btn btn-link text-decoration-none p-0 text-start"
                            type="button"
                            data-bs-toggle="collapse"
                            data-bs-target="#{collapse_id}"
                            aria-expanded="{str(expanded).lower()}"
                            aria-controls="{collapse_id}">
                        <i class="bi bi-chevron-{'down' if expanded else 'right'} me-2"></i>
                        <i class="bi bi-card-list me-2"></i>
                        {escape(item_title)}
                    </button>"""
        else:
            html += f"""
                    <span>
                        <i class="bi bi-card-list me-2"></i>
                        {escape(item_title)}
                    </span>"""

        html += f"""
                </h6>
                <button type="button"
                        class="btn btn-outline-danger btn-sm remove-item-btn"
                        data-index="{index}"
                        data-field-name="{field_name}"
                        title="Remove this item">
                    <i class="bi bi-trash"></i>
                </button>
            </div>"""

        if collapsible:
            html += f"""
            <div class="collapse {collapse_class} show" id="{collapse_id}">
                <div class="card-body">"""
        else:
            html += """
            <div class="card-body">"""

        html += '<div class="row">'
        properties = schema_def.get("properties", {})
        field_count = len([key for key in properties.keys() if not key.startswith("_")])

        if field_count <= 2:
            col_class = "col-12"
        elif field_count <= 4:
            col_class = "col-md-6"
        else:
            col_class = "col-lg-4 col-md-6"

        for field_key, nested_schema in properties.items():
            if field_key.startswith("_"):
                continue

            field_value = item_data.get(field_key, "")
            input_name = f"{field_name}[{index}].{field_key}"

            html += f"""
                <div class="{col_class}">
                    {self.render_field(
                        input_name,
                        nested_schema,
                        field_value,
                        None,
                        [],
                        context,
                        "vertical",
                        None,
                    )}
                </div>"""

        html += "</div>"

        if collapsible:
            html += """
                </div>
            </div>"""
        else:
            html += """
            </div>"""

        html += """
        </div>"""
        return html
