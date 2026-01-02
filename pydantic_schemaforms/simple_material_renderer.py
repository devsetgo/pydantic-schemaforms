"""
Simple Material Design 3 Form Renderer
=====================================

A clean, working Material Design 3 renderer for pydantic-schemaforms.
This renderer creates self-contained forms with embedded Material Design styling.
"""

from html import escape
from typing import Any, Dict, List, Optional

from .enhanced_renderer import EnhancedFormRenderer
from .icon_mapping import map_icon_for_framework
from .rendering.context import RenderContext
from .rendering.material_icons import render_material_icon
from .rendering.themes import MaterialEmbeddedTheme
from .templates import FormTemplates, render_template


class SimpleMaterialRenderer(EnhancedFormRenderer):
    """
    Simple Material Design 3 form renderer that actually works.
    Creates self-contained forms with embedded Material Design styling.
    """

    def __init__(self):
        """Initialize Simple Material Design renderer."""
        super().__init__(framework="material", theme=MaterialEmbeddedTheme())

    # --- Template helpers -------------------------------------------------
    def _attr(self, value: Any) -> str:
        """HTML-escape attribute values, treating None as empty."""

        if value is None:
            return ""
        return escape(str(value))

    def _render_help_block(self, help_text: Optional[str]) -> str:
        if not help_text:
            return ""
        return render_template(
            FormTemplates.MATERIAL_HELP_TEXT,
            help_content=escape(str(help_text)),
        )

    def _render_error_block(self, error: Optional[str]) -> str:
        if not error:
            return ""
        return render_template(
            FormTemplates.MATERIAL_ERROR_TEXT,
            error_content=escape(str(error)),
        )

    def _wrap_field_body(
        self,
        *,
        field_body: str,
        help_text: Optional[str],
        error: Optional[str],
    ) -> str:
        """Wrap a field body with shared help/error blocks."""

        return render_template(
            FormTemplates.MATERIAL_FIELD_CONTAINER,
            field_body=field_body,
            help_text=self._render_help_block(help_text),
            error_text=self._render_error_block(error),
        )

    def _wrap_with_icon(self, icon: Optional[str], input_wrapper: str) -> str:
        if not icon:
            return input_wrapper

        # Self-contained Material output must not depend on external icon fonts.
        # Render a small set of icons as inline SVG (falling back to ligatures
        # if the icon name is not recognized).
        icon_markup = render_material_icon(icon, classes="md-icon")
        return render_template(
            FormTemplates.MATERIAL_FIELD_WITH_ICON,
            icon_markup=icon_markup,
            input_wrapper=input_wrapper,
        )

    def _build_text_input_attributes(self, ui_info: Dict[str, Any]) -> str:
        attrs = []
        mapping = {
            "min_value": "min",
            "max_value": "max",
            "min_length": "minlength",
            "max_length": "maxlength",
            "step": "step",
        }
        for source, attr_name in mapping.items():
            if ui_info.get(source) is not None:
                attrs.append(f'{attr_name}="{escape(str(ui_info[source]))}"')

        extra = ui_info.get("attributes")
        if isinstance(extra, dict):
            for attr_name, attr_value in extra.items():
                if attr_value is None:
                    continue
                attrs.append(f'{attr_name}="{escape(str(attr_value))}"')

        return " ".join(attrs)

    def _render_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: Optional[List[str]] = None,
        context: Optional[RenderContext] = None,
        _layout: str = "vertical",
        all_errors: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a Material Design form field."""

        context = context or RenderContext(form_data={}, schema_defs={})
        ui_info = field_schema.get("ui", {}) or field_schema

        if ui_info.get("hidden"):
            return f'<input type="hidden" name="{field_name}" value="{escape(str(value or ""))}">'

        input_type = (
            ui_info.get("input_type")
            or ui_info.get("element")
            or self._infer_input_type(field_schema)
        )

        if input_type == "model_list":
            return self._render_model_list_field(
                field_name,
                field_schema,
                value,
                error,
                required_fields,
                context,
                all_errors,
            )

        label = field_schema.get("title", field_name.replace("_", " ").title())
        help_text = ui_info.get("help_text") or field_schema.get("description")
        is_required = field_name in (required_fields or [])

        if input_type == "checkbox":
            return self._render_checkbox_field(
                field_name,
                label,
                value,
                error,
                help_text,
                is_required,
                ui_info,
            )

        return self._render_outlined_field(
            field_name,
            input_type,
            label,
            value,
            error,
            help_text,
            is_required,
            ui_info,
            field_schema,
        )

    def _render_outlined_field(
        self,
        field_name: str,
        input_type: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
    ) -> str:
        """Render a Material Design 3 outlined field with floating label and optional icon."""
        required_text = " *" if is_required else ""

        # Check for icon in UI info
        icon = ui_info.get("icon")
        # Map icon to Material Design framework
        if icon:
            icon = map_icon_for_framework(icon, "material")
        has_icon = icon is not None

        if input_type == "textarea":
            control_html = self._render_textarea_input(field_name, value, error, ui_info)
        elif input_type == "select":
            control_html = self._render_select_input(field_name, value, error, ui_info, field_schema)
        else:
            control_html = self._render_text_input(field_name, input_type, value, error, ui_info)

        input_wrapper = render_template(
            FormTemplates.MATERIAL_FIELD_INPUT_WRAPPER,
            input_control=control_html,
            field_id=self._attr(field_name),
            label=escape(label),
            required_indicator=required_text,
        )

        field_body = self._wrap_with_icon(icon if has_icon else None, input_wrapper)
        return self._wrap_field_body(
            field_body=field_body,
            help_text=help_text,
            error=error,
        )

    def _render_text_input(
        self,
        field_name: str,
        input_type: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
    ) -> str:
        """Render a Material Design text input."""
        error_class = " error" if error else ""
        attrs = self._build_text_input_attributes(ui_info)
        value_attr = self._attr(value) if value else ""
        return render_template(
            FormTemplates.MATERIAL_TEXT_INPUT,
            input_type=input_type,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            error_class=error_class,
            value=value_attr,
            attributes=attrs,
        )

    def _render_textarea_input(
        self,
        field_name: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
    ) -> str:
        """Render a Material Design textarea."""
        error_class = " error" if error else ""
        value_content = escape(str(value)) if value is not None else ""
        return render_template(
            FormTemplates.MATERIAL_TEXTAREA,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            error_class=error_class,
            value=value_content,
        )

    def _render_select_input(
        self,
        field_name: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
    ) -> str:
        """Render a Material Design select field."""
        error_class = " error" if error else ""
        options = self._build_select_options(ui_info, field_schema)
        rendered_options = [
            render_template(
                FormTemplates.MATERIAL_SELECT_OPTION,
                value="",
                selected="",
                label="",
            )
        ]

        for opt_value, opt_label in options:
            is_selected = str(value) == str(opt_value)
            rendered_options.append(
                render_template(
                    FormTemplates.MATERIAL_SELECT_OPTION,
                    value=self._attr(opt_value),
                    selected=' selected="selected"' if is_selected else "",
                    label=escape(str(opt_label)),
                )
            )

        return render_template(
            FormTemplates.MATERIAL_SELECT,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            error_class=error_class,
            options="".join(rendered_options),
        )

    def _build_select_options(self, ui_info: Dict[str, Any], field_schema: Dict[str, Any]) -> List[List[str]]:
        """Normalize select option definitions."""

        options = ui_info.get("options", [])
        if not options and "enum" in field_schema:
            options = [{"value": v, "label": v} for v in field_schema["enum"]]

        normalized: List[List[str]] = []
        for option in options:
            if isinstance(option, dict):
                opt_value = option.get("value", "")
                opt_label = option.get("label", opt_value)
            else:
                opt_value = opt_label = str(option)
            normalized.append([opt_value, opt_label])

        return normalized

    def _render_checkbox_field(
        self,
        field_name: str,
        label: str,
        value: Any,
        error: Optional[str],
        help_text: Optional[str],
        is_required: bool,
        ui_info: Dict[str, Any],
    ) -> str:
        """Render a Material Design checkbox field."""
        required_text = " *" if is_required else ""

        checked_attr = 'checked="checked"' if value else ""
        return render_template(
            FormTemplates.MATERIAL_CHECKBOX_FIELD,
            name=self._attr(field_name),
            field_id=self._attr(field_name),
            label=escape(label),
            required_indicator=required_text,
            checked=checked_attr,
            help_text=self._render_help_block(help_text),
            error_text=self._render_error_block(error),
        )

    def _render_submit_button(self) -> str:
        """Render a Material Design submit button."""
        return render_template(FormTemplates.MATERIAL_SUBMIT_BUTTON, label="Submit")

    def _infer_input_type(self, field_schema: Dict[str, Any]) -> str:
        """Infer input type from field schema."""
        field_type = field_schema.get("type", "string")
        field_format = field_schema.get("format", "")

        if field_format == "email":
            return "email"
        elif field_format == "date":
            return "date"
        elif field_type == "integer" or field_type == "number":
            return "number"
        elif field_type == "boolean":
            return "checkbox"
        elif field_schema.get("enum"):
            return "select"
        else:
            return "text"

    def _render_model_list_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: List[str] = None,
        context: Optional[RenderContext] = None,
        all_errors: Optional[Dict[str, Any]] = None,
    ) -> str:
        context = context or RenderContext(form_data={}, schema_defs={})
        all_errors = all_errors or {}
        required = required_fields or []

        field_html = self._field_renderer.render_field(
            field_name,
            field_schema,
            value,
            error,
            required,
            context,
            "vertical",
            all_errors,
        )

        return render_template(FormTemplates.MATERIAL_MODEL_LIST_WRAPPER, content=field_html)

    def _model_list_framework(self) -> str:
        """Material renderer still leverages Bootstrap model list assets."""

        return "bootstrap"




# Alias for backward compatibility
MaterialDesign3Renderer = SimpleMaterialRenderer
