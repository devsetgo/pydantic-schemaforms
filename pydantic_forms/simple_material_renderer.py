"""
Simple Material Design 3 Form Renderer
=====================================

A clean, working Material Design 3 renderer for pydantic-forms.
This renderer creates self-contained forms with embedded Material Design styling.
"""

from html import escape
from typing import Any, Dict, List, Optional

from .enhanced_renderer import EnhancedFormRenderer
from .icon_mapping import map_icon_for_framework
from .rendering.context import RenderContext
from .rendering.themes import MaterialEmbeddedTheme


class SimpleMaterialRenderer(EnhancedFormRenderer):
    """
    Simple Material Design 3 form renderer that actually works.
    Creates self-contained forms with embedded Material Design styling.
    """

    def __init__(self):
        """Initialize Simple Material Design renderer."""
        super().__init__(framework="material", theme=MaterialEmbeddedTheme())

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

        # Start field container
        field_parts = ['<div class="md-field">']

        # Create field wrapper that may contain icon + input
        if has_icon:
            field_parts.append('<div class="md-field-with-icon">')
            # Add icon outside the input on the left
            field_parts.append(f'<span class="md-icon material-icons">{icon}</span>')

        # Create input wrapper for proper label positioning
        field_parts.append('<div class="md-input-wrapper">')

        # Add the input/select/textarea
        if input_type == "textarea":
            field_parts.append(
                self._render_textarea_input(field_name, value, error, ui_info, has_icon)
            )
        elif input_type == "select":
            field_parts.append(
                self._render_select_input(field_name, value, error, ui_info, field_schema, has_icon)
            )
        else:
            field_parts.append(
                self._render_text_input(field_name, input_type, value, error, ui_info, has_icon)
            )

        # Add floating label
        field_parts.append(
            f'<label class="md-floating-label" for="{field_name}">{escape(label)}{required_text}</label>'
        )

        # Close input wrapper
        field_parts.append("</div>")

        # Close field wrapper if has icon
        if has_icon:
            field_parts.append("</div>")

        # Add help text
        if help_text:
            field_parts.append(f'<div class="md-help-text">{escape(help_text)}</div>')

        # Add error text
        if error:
            field_parts.append(f'<div class="md-error-text">{escape(error)}</div>')

        # Close field container
        field_parts.append("</div>")
        return "\n".join(field_parts)

    def _render_text_input(
        self,
        field_name: str,
        input_type: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        has_icon: bool = False,
    ) -> str:
        """Render a Material Design text input."""
        error_class = " error" if error else ""
        value_attr = f' value="{escape(str(value))}"' if value else ""
        placeholder_attr = ' placeholder=" "'  # Single space for floating label to work

        # Handle input attributes
        attrs = []
        if ui_info.get("min_value") is not None:
            attrs.append(f'min="{ui_info["min_value"]}"')
        if ui_info.get("max_value") is not None:
            attrs.append(f'max="{ui_info["max_value"]}"')
        if ui_info.get("min_length") is not None:
            attrs.append(f'minlength="{ui_info["min_length"]}"')
        if ui_info.get("max_length") is not None:
            attrs.append(f'maxlength="{ui_info["max_length"]}"')

        attrs_str = " " + " ".join(attrs) if attrs else ""

        return f'<input type="{input_type}" name="{field_name}" id="{field_name}" class="md-input{error_class}"{value_attr}{placeholder_attr}{attrs_str}>'

    def _render_textarea_input(
        self,
        field_name: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        has_icon: bool = False,
    ) -> str:
        """Render a Material Design textarea."""
        error_class = " error" if error else ""
        placeholder_attr = ' placeholder=" "'  # Single space for floating label to work
        value_content = escape(str(value)) if value else ""

        return f'<textarea name="{field_name}" id="{field_name}" class="md-textarea{error_class}"{placeholder_attr}>{value_content}</textarea>'

    def _render_select_input(
        self,
        field_name: str,
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        field_schema: Dict[str, Any],
        has_icon: bool = False,
    ) -> str:
        """Render a Material Design select field."""
        error_class = " error" if error else ""
        options_html = []

        # Get options from UI info or enum
        options = ui_info.get("options", [])
        if not options and "enum" in field_schema:
            options = [{"value": v, "label": v} for v in field_schema["enum"]]

        # Add empty option
        options_html.append('<option value=""></option>')

        # Add options
        for option in options:
            if isinstance(option, dict):
                opt_value = option.get("value", "")
                opt_label = option.get("label", opt_value)
            else:
                opt_value = opt_label = str(option)

            selected = " selected" if str(value) == str(opt_value) else ""
            options_html.append(
                f'<option value="{escape(str(opt_value))}">{selected}>{escape(str(opt_label))}</option>'
            )

        return f'<select name="{field_name}" id="{field_name}" class="md-select{error_class}">{"".join(options_html)}</select>'

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
        checked = " checked" if value else ""
        required_text = " *" if is_required else ""

        field_parts = ['<div class="md-field">']
        field_parts.append('<div class="md-checkbox-container">')
        field_parts.append(
            f'<input type="checkbox" name="{field_name}" id="{field_name}" class="md-checkbox"{checked} value="true">'
        )
        field_parts.append(
            f'<label for="{field_name}" class="md-checkbox-label">{escape(label)}{required_text}</label>'
        )
        field_parts.append("</div>")

        # Add help text
        if help_text:
            field_parts.append(f'<div class="md-help-text">{escape(help_text)}</div>')

        # Add error text
        if error:
            field_parts.append(f'<div class="md-error-text">{escape(error)}</div>')

        field_parts.append("</div>")
        return "\n".join(field_parts)

    def _render_submit_button(self) -> str:
        """Render a Material Design submit button."""
        return """
        <div class="md-field">
            <button type="submit" class="md-button md-button-filled">Submit</button>
        </div>"""

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

        return f"""
        <div class="md-field">
            <div class="md-model-list-container">
                {field_html}
            </div>
        </div>
        """

    def _model_list_framework(self) -> str:
        """Material renderer still leverages Bootstrap model list assets."""

        return "bootstrap"




# Alias for backward compatibility
MaterialDesign3Renderer = SimpleMaterialRenderer
