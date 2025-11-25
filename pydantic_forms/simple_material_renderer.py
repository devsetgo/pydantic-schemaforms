"""
Simple Material Design 3 Form Renderer
=====================================

A clean, working Material Design 3 renderer for pydantic-forms.
This renderer creates self-contained forms with embedded Material Design styling.
"""

from html import escape
from typing import Any, Dict, List, Optional, Tuple, Type

from .enhanced_renderer import EnhancedFormRenderer
from .icon_mapping import map_icon_for_framework
from .layout_base import BaseLayout
from .rendering.context import RenderContext
from .rendering.schema_parser import SchemaMetadata, build_schema_metadata, resolve_ui_element
from .schema_form import FormModel


class SimpleMaterialRenderer(EnhancedFormRenderer):
    """
    Simple Material Design 3 form renderer that actually works.
    Creates self-contained forms with embedded Material Design styling.
    """

    def __init__(self):
        """Initialize Simple Material Design renderer."""
        super().__init__(framework="material")
        self._current_errors: Dict[str, Any] = {}

    def _build_render_context(self) -> RenderContext:
        """Return a render context aligned with the enhanced renderer API."""
        form_data = getattr(self, "_current_form_data", {}) or {}
        schema_defs = getattr(self, "_schema_defs", {}) or {}
        return RenderContext(form_data=form_data, schema_defs=schema_defs)

    def _get_material_nested_form_data(self, field_name: str) -> Dict[str, Any]:
        """Fetch nested form data using the enhanced renderer helper."""
        form_data = getattr(self, "_current_form_data", {}) or {}
        return super()._get_nested_form_data(field_name, form_data)

    def render_form_from_model(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        include_csrf: bool = False,
        include_submit_button: bool = True,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """
        Render a complete self-contained Material Design 3 form.
        """
        metadata = build_schema_metadata(model_cls)
        data = data or {}
        errors = errors or {}

        # Build complete self-contained form
        self._current_form_data = data
        self._current_errors = errors
        self._schema_defs = metadata.schema_defs

        form_html = self._build_material_form(
            metadata,
            data,
            errors,
            submit_url,
            method,
            include_csrf,
            include_submit_button,
            layout,
            **kwargs,
        )

        return form_html

    def render_form_fields_only(
        self,
        model_cls: Type[FormModel],
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """
        Render only the form fields without the form wrapper.
        This is useful for rendering nested forms within tabs.
        """
        metadata = build_schema_metadata(model_cls)
        data = data or {}
        errors = errors or {}

        # Store form data and schema defs for nested rendering helpers
        self._current_form_data = data
        self._current_errors = errors
        self._schema_defs = metadata.schema_defs

        fields = metadata.fields
        required_fields = metadata.required_fields

        # Render fields only
        form_parts = []
        for field_name, field_schema in fields:
            field_html = self._render_field(
                field_name,
                field_schema,
                data.get(field_name),
                errors.get(field_name),
                required_fields,
            )
            form_parts.append(field_html)

        return "\n".join(form_parts)

    def _build_material_form(
        self,
        metadata: SchemaMetadata,
        data: Dict[str, Any],
        errors: Dict[str, Any],
        submit_url: str,
        method: str,
        include_csrf: bool,
        include_submit_button: bool,
        layout: str = "vertical",
        **kwargs,
    ) -> str:
        """Build a complete self-contained Material Design 3 form."""

        # Store form data and errors for nested form access
        self._current_form_data = data
        self._current_errors = errors

        # Store schema definitions for model_list fields
        self._schema_defs = metadata.schema_defs

        # Start with complete HTML structure including all dependencies
        form_parts = [
            "<!-- Material Design 3 Self-Contained Form -->",
            self._get_material_css(),
            '<div class="md-form-container">',
            f'<form method="{method}" action="{submit_url}" class="md-form" novalidate>',
        ]

        # Add CSRF if requested
        if include_csrf:
            form_parts.append('<input type="hidden" name="csrf_token" value="csrf_placeholder">')

        fields = metadata.fields
        required_fields = metadata.required_fields
        layout_fields = metadata.layout_fields
        non_layout_fields = metadata.non_layout_fields

        # If we have multiple layout fields and few/no other fields, render as tabs
        if len(layout_fields) > 1 and len(non_layout_fields) == 0:
            # Render layout fields as tabs with Material Design styling
            form_parts.extend(
                self._render_material_layout_fields_as_tabs(
                    layout_fields, data, errors, required_fields
                )
            )
        else:
            # Render each field normally
            for field_name, field_schema in fields:
                field_html = self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                )
                form_parts.append(field_html)

        # Add submit button if requested
        if include_submit_button:
            form_parts.append(self._render_submit_button())

        form_parts.extend(["</form>", "</div>"])

        # Add JavaScript for Material Design interactions + model lists
        form_parts.append(self._get_material_javascript())

        # Add model list JavaScript if any model_list fields were rendered
        if self._has_model_list_fields(fields):
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer(framework="bootstrap")
            form_parts.append(list_renderer.get_model_list_javascript())

        return "\n".join(form_parts)

    def _has_model_list_fields(self, fields: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """Check if the current schema metadata contains any model_list fields."""
        for _field_name, field_schema in fields:
            if resolve_ui_element(field_schema) == "model_list":
                return True
        return False

    def _get_material_css(self) -> str:
        """Return complete Material Design CSS for self-contained forms with icon support."""
        return """
<style>
/* Import Material Icons and Roboto font */
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

/* Material Design 3 Self-Contained Styles - Using !important to override any conflicting styles */
.md-form-container {
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 20px !important;
    line-height: 1.5 !important;
    color: #1c1b1f !important;
    background: #fef7ff !important;
    border: none !important;
    box-sizing: border-box !important;
    position: relative !important;
}

.md-form {
    width: 100% !important;
    background: #ffffff !important;
    border-radius: 28px !important;
    padding: 32px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 2px 6px 2px rgba(0,0,0,0.15) !important;
    border: none !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Reset any Bootstrap interference */
.md-form * {
    box-sizing: border-box !important;
}

/* Material Design Form Fields */
.md-field {
    margin-bottom: 32px !important;
    position: relative !important;
    width: 100% !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Model list container styling to blend with Material Design */
.md-model-list-container {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Override Bootstrap styles for model list items within Material Design */
.md-model-list-container .card {
    border: 1px solid #79747e !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    margin-bottom: 16px !important;
    background: #ffffff !important;
}

.md-model-list-container .card-header {
    background: #f7f2fa !important;
    border-bottom: 1px solid #e7e0ec !important;
    border-radius: 12px 12px 0 0 !important;
    color: #1c1b1f !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 500 !important;
}

.md-model-list-container .btn {
    border-radius: 20px !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 500 !important;
    text-transform: none !important;
}

.md-model-list-container .btn-primary {
    background: #6750a4 !important;
    border-color: #6750a4 !important;
}

.md-model-list-container .btn-danger {
    background: #ba1a1a !important;
    border-color: #ba1a1a !important;
}

.md-field-label {
    display: block !important;
    color: #49454f !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    margin-bottom: 8px !important;
    position: relative !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    line-height: 1.4 !important;
}

.md-field-label.required::after {
    content: ' *' !important;
    color: #ba1a1a !important;
}

/* Material Design Outlined Text Fields */
.md-text-field {
    position: relative;
    width: 100%;
}

/* Field container */
.md-field {
    margin: 16px 0;
}

/* Field with icon layout */
.md-field-with-icon {
    display: flex !important;
    align-items: flex-start !important;
    gap: 12px !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Input wrapper for proper label positioning */
.md-input-wrapper {
    position: relative !important;
    flex: 1 !important;
    width: 100% !important;
}

.md-input {
    width: 100% !important;
    padding: 16px !important;
    border: 1px solid #79747e !important;
    border-radius: 4px !important;
    background: transparent !important;
    color: #1c1b1f !important;
    font-size: 16px !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    outline: none !important;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-sizing: border-box !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}

.md-input:focus {
    border-color: #6750a4 !important;
    border-width: 2px !important;
    padding: 15px !important; /* Adjust for thicker border */
    box-shadow: none !important;
}

/* Icon styling - positioned outside to the left of input */
.md-icon {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 24px !important;
    height: 24px !important;
    margin-top: 16px !important; /* Align with input padding */
    color: #49454f !important;
    font-size: 20px !important;
    flex-shrink: 0 !important;
    transition: color 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-family: 'Material Icons' !important;
    font-weight: normal !important;
    font-style: normal !important;
}

.md-field-with-icon:focus-within .md-icon {
    color: #6750a4 !important;
}

.md-input:focus + .md-floating-label,
.md-input:not(:placeholder-shown) + .md-floating-label,
.md-textarea:focus + .md-floating-label,
.md-textarea:not(:placeholder-shown) + .md-floating-label,
.md-select:focus + .md-floating-label {
    transform: translateY(-28px) scale(0.75) !important;
    color: #6750a4 !important;
    background: #ffffff !important;
    padding: 0 4px !important;
}

.md-floating-label {
    position: absolute !important;
    left: 16px !important;
    top: 16px !important;
    color: #49454f !important;
    font-size: 16px !important;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
    pointer-events: none !important;
    background: transparent !important;
    z-index: 1 !important;
    transform-origin: left top !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 400 !important;
    line-height: 1.4 !important;
}

.md-input:focus + .md-floating-label,
.md-input:not(:placeholder-shown) + .md-floating-label {
    transform: translateY(-28px) scale(0.75) !important;
    color: #6750a4;
    background: #ffffff;
    padding: 0 4px;
}

.md-input.error {
    border-color: #ba1a1a;
}

.md-input.error:focus {
    border-color: #ba1a1a;
}

.md-input.error + .md-floating-label {
    color: #ba1a1a;
}

/* Material Design Select */
.md-select {
    width: 100%;
    padding: 16px;
    border: 1px solid #79747e;
    border-radius: 4px;
    background: transparent;
    color: #1c1b1f;
    font-size: 16px;
    font-family: inherit;
    outline: none;
    cursor: pointer;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    box-sizing: border-box;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2349454f' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
    background-position: right 12px center;
    background-repeat: no-repeat;
    background-size: 16px;
    padding-right: 40px;
}

.md-select:focus {
    border-color: #6750a4;
    border-width: 2px;
    padding: 15px 39px 15px 15px; /* Adjust for thicker border */
}

.md-select:focus + .md-floating-label {
    transform: translateY(-28px) scale(0.75);
    color: #6750a4;
    background: #ffffff;
    padding: 0 4px;
}

/* Material Design Textarea */
.md-textarea {
    width: 100%;
    min-height: 120px;
    padding: 16px;
    border: 1px solid #79747e;
    border-radius: 4px;
    background: transparent;
    color: #1c1b1f;
    font-size: 16px;
    font-family: inherit;
    outline: none;
    resize: vertical;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    box-sizing: border-box;
}

.md-textarea:focus {
    border-color: #6750a4;
    border-width: 2px;
    padding: 15px; /* Adjust for thicker border */
}

.md-textarea:focus + .md-floating-label,
.md-textarea:not(:placeholder-shown) + .md-floating-label {
    transform: translateY(-28px) scale(0.75);
    color: #6750a4;
    background: #ffffff;
    padding: 0 4px;
}

/* Material Design Checkboxes */
.md-checkbox-container {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin: 16px 0;
    cursor: pointer;
}

.md-checkbox {
    width: 18px;
    height: 18px;
    border: 2px solid #79747e;
    border-radius: 2px;
    background: transparent;
    cursor: pointer;
    position: relative;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    margin-top: 2px; /* Align with text baseline */
    flex-shrink: 0;
}

.md-checkbox:checked {
    background: #6750a4;
    border-color: #6750a4;
}

.md-checkbox:checked::after {
    content: '';
    position: absolute;
    top: 1px;
    left: 4px;
    width: 6px;
    height: 10px;
    border: solid white;
    border-width: 0 2px 2px 0;
    transform: rotate(45deg);
}

.md-checkbox-label {
    color: #1c1b1f;
    font-size: 16px;
    cursor: pointer;
    line-height: 1.5;
}

/* Material Design Buttons */
.md-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 24px;
    border: none;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    text-decoration: none;
    box-sizing: border-box;
    min-width: 64px;
    height: 40px;
    position: relative;
    overflow: hidden;
}

.md-button-filled {
    background: #6750a4;
    color: #ffffff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 1px 3px 1px rgba(0,0,0,0.15);
}

.md-button-filled:hover {
    background: #5a43a0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 2px 6px 2px rgba(0,0,0,0.15);
    transform: translateY(-1px);
}

.md-button-filled:active {
    transform: translateY(0);
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 1px 3px 1px rgba(0,0,0,0.15);
}

/* Help Text */
.md-help-text {
    font-size: 12px;
    color: #49454f;
    margin-top: 4px;
    line-height: 1.33;
    padding-left: 16px;
}

/* Error Text */
.md-error-text {
    font-size: 12px;
    color: #ba1a1a;
    margin-top: 4px;
    line-height: 1.33;
    font-weight: 400;
    padding-left: 16px;
}

/* Number and Date Inputs */
.md-input[type="number"],
.md-input[type="date"],
.md-input[type="email"],
.md-input[type="password"],
.md-input[type="tel"],
.md-input[type="url"] {
    /* Inherit all md-input styles */
}

.md-input[type="color"] {
    height: 56px;
    padding: 8px;
    cursor: pointer;
}

.md-input[type="range"] {
    padding: 16px 8px;
}

/* Placeholder styling */
.md-input::placeholder {
    color: transparent;
}

.md-input:focus::placeholder {
    color: #49454f;
}

/* State layers for interactive elements */
.md-button-filled::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: currentColor;
    opacity: 0;
    transition: opacity 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: inherit;
}

.md-button-filled:hover::before {
    opacity: 0.08;
}

.md-button-filled:focus::before {
    opacity: 0.12;
}

.md-button-filled:active::before {
    opacity: 0.16;
}

/* Responsive Design */
@media (max-width: 768px) {
    .md-form {
        padding: 24px 16px;
        border-radius: 28px;
    }

    .md-field {
        margin-bottom: 24px;
    }
}

/* Typography Scale */
.md-headline-small {
    font-size: 24px;
    font-weight: 400;
    line-height: 32px;
    color: #1c1b1f;
}

.md-body-large {
    font-size: 16px;
    font-weight: 400;
    line-height: 24px;
    color: #1c1b1f;
}

.md-body-medium {
    font-size: 14px;
    font-weight: 400;
    line-height: 20px;
    color: #49454f;
}

.md-label-large {
    font-size: 14px;
    font-weight: 500;
    line-height: 20px;
    color: #1c1b1f;
}

/* Surface colors and elevation */
.md-surface {
    background: #fef7ff;
    color: #1c1b1f;
}

.md-surface-container {
    background: #f3f0ff;
    color: #1c1b1f;
}

.md-surface-container-high {
    background: #e7e0ec;
    color: #1c1b1f;
}
</style>"""

    def _render_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any = None,
        error: Optional[str] = None,
        required_fields: List[str] = None,
    ) -> str:
        """Render a Material Design form field."""
        # Get UI info
        ui_info = field_schema.get("ui", {}) or field_schema

        # Skip hidden fields
        if ui_info.get("hidden"):
            return f'<input type="hidden" name="{field_name}" value="{escape(str(value or ""))}">'

        # Determine input type
        input_type = (
            ui_info.get("input_type")
            or ui_info.get("element")
            or self._infer_input_type(field_schema)
        )

        # Handle model_list specially - delegate to enhanced renderer
        if input_type == "model_list":
            return self._render_model_list_field(
                field_name, field_schema, value, error, required_fields
            )

        # Get field properties
        label = field_schema.get("title", field_name.replace("_", " ").title())
        help_text = ui_info.get("help_text") or field_schema.get("description")
        is_required = field_name in (required_fields or [])

        # Build field HTML using Material Design 3 patterns
        if input_type == "checkbox":
            return self._render_checkbox_field(
                field_name, label, value, error, help_text, is_required, ui_info
            )
        else:
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
    ) -> str:
        context = self._build_render_context()
        all_errors = getattr(self, "_current_errors", {}) or {}
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

    def _get_material_javascript(self) -> str:
        """Return Material Design JavaScript for enhanced interactions."""
        return """
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Material Design 3 form enhancements

    // Floating label functionality for outlined text fields
    function initializeFloatingLabels() {
        const textFields = document.querySelectorAll('.md-input, .md-textarea, .md-select');

        textFields.forEach(input => {
            const label = input.nextElementSibling;
            if (label && label.classList.contains('md-floating-label')) {

                // Check initial state
                function updateLabelState() {
                    const hasValue = input.value && input.value.trim() !== '';
                    const isFocused = document.activeElement === input;

                    if (hasValue || isFocused) {
                        label.style.transform = 'translateY(-28px) scale(0.75)';
                        label.style.color = isFocused ? '#6750a4' : '#49454f';
                        label.style.background = '#ffffff';
                        label.style.padding = '0 4px';
                    } else {
                        label.style.transform = 'translateY(0) scale(1)';
                        label.style.color = '#49454f';
                        label.style.background = 'transparent';
                        label.style.padding = '0';
                    }
                }

                // Set up event listeners
                input.addEventListener('focus', updateLabelState);
                input.addEventListener('blur', updateLabelState);
                input.addEventListener('input', updateLabelState);

                // Initial state check
                updateLabelState();
            }
        });
    }

    // Enhanced focus and blur effects
    const inputs = document.querySelectorAll('.md-input, .md-select, .md-textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)';
        });

        input.addEventListener('blur', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Checkbox interactions with Material Design ripple effect
    const checkboxes = document.querySelectorAll('.md-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const container = this.closest('.md-checkbox-container');
            if (this.checked) {
                // Create ripple effect
                const ripple = document.createElement('div');
                ripple.style.position = 'absolute';
                ripple.style.borderRadius = '50%';
                ripple.style.background = 'rgba(103, 80, 164, 0.3)';
                ripple.style.width = '40px';
                ripple.style.height = '40px';
                ripple.style.left = '-11px';
                ripple.style.top = '-11px';
                ripple.style.pointerEvents = 'none';
                ripple.style.transform = 'scale(0)';
                ripple.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

                this.style.position = 'relative';
                this.appendChild(ripple);

                // Animate ripple
                setTimeout(() => {
                    ripple.style.transform = 'scale(1)';
                    setTimeout(() => {
                        ripple.style.opacity = '0';
                        setTimeout(() => {
                            if (ripple.parentNode) {
                                ripple.parentNode.removeChild(ripple);
                            }
                        }, 300);
                    }, 200);
                }, 10);
            }
        });
    });

    // Enhanced form validation with Material Design styling
    const form = document.querySelector('.md-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const requiredInputs = this.querySelectorAll('input[required], select[required], textarea[required]');
            let hasErrors = false;

            requiredInputs.forEach(input => {
                const value = input.type === 'checkbox' ? input.checked : input.value.trim();
                const fieldContainer = input.closest('.md-field');

                if (!value) {
                    input.classList.add('error');

                    // Add error styling to label
                    const label = input.nextElementSibling;
                    if (label && label.classList.contains('md-floating-label')) {
                        label.style.color = '#ba1a1a';
                    }

                    // Create or update error message
                    let errorDiv = fieldContainer.querySelector('.md-error-text');
                    if (!errorDiv) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'md-error-text';
                        fieldContainer.appendChild(errorDiv);
                    }
                    errorDiv.textContent = 'This field is required';

                    hasErrors = true;
                } else {
                    input.classList.remove('error');

                    // Remove error styling from label
                    const label = input.nextElementSibling;
                    if (label && label.classList.contains('md-floating-label')) {
                        label.style.color = input === document.activeElement ? '#6750a4' : '#49454f';
                    }

                    // Remove error message if it was dynamically added
                    const errorDiv = fieldContainer.querySelector('.md-error-text');
                    if (errorDiv && errorDiv.textContent === 'This field is required') {
                        errorDiv.remove();
                    }
                }
            });

            if (hasErrors) {
                e.preventDefault();
                // Scroll to first error with smooth animation
                const firstError = this.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'nearest'
                    });
                    // Focus the field for better UX
                    setTimeout(() => {
                        firstError.focus();
                    }, 500);
                }
            }
        });

        // Real-time validation for better UX
        const allInputs = form.querySelectorAll('input, select, textarea');
        allInputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.hasAttribute('required')) {
                    const value = this.type === 'checkbox' ? this.checked : this.value.trim();
                    const fieldContainer = this.closest('.md-field');

                    if (!value) {
                        this.classList.add('error');
                        const label = this.nextElementSibling;
                        if (label && label.classList.contains('md-floating-label')) {
                            label.style.color = '#ba1a1a';
                        }
                    } else {
                        this.classList.remove('error');
                        const label = this.nextElementSibling;
                        if (label && label.classList.contains('md-floating-label')) {
                            label.style.color = '#49454f';
                        }
                    }
                }
            });
        });
    }

    # Initialize floating labels
    initializeFloatingLabels();

    # Reinitialize for dynamically added content
    window.reinitializeMaterialForms = function() {
        initializeFloatingLabels();
    };
});
</script>"""

    def _render_material_layout_fields_as_tabs(
        self,
        layout_fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
    ) -> List[str]:
        """Render layout fields as Material Design tabs."""
        parts = []

        # Add Material Design tabs CSS
        parts.append(
            """
        <style>
        .md-tabs {
            border-bottom: 1px solid #e7e0ec;
            margin-bottom: 24px;
        }
        .md-tab-list {
            display: flex;
            list-style: none;
            margin: 0;
            padding: 0;
            overflow-x: auto;
        }
        .md-tab {
            flex: 0 0 auto;
        }
        .md-tab-button {
            background: none;
            border: none;
            padding: 12px 24px;
            color: #49454f;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            position: relative;
            transition: color 0.2s ease;
            border-bottom: 2px solid transparent;
            white-space: nowrap;
        }
        .md-tab-button:hover {
            color: #6750a4;
            background-color: rgba(103, 80, 164, 0.08);
        }
        .md-tab-button.active {
            color: #6750a4;
            border-bottom-color: #6750a4;
        }
        .md-tab-content {
            display: none;
            padding: 24px 0;
        }
        .md-tab-content.active {
            display: block;
        }
        </style>
        """
        )

        # Create tab navigation
        parts.append('<div class="md-tabs">')
        parts.append('<ul class="md-tab-list" role="tablist">')
        for i, (field_name, field_schema) in enumerate(layout_fields):
            active_class = " active" if i == 0 else ""
            tab_id = f"material-tab-{field_name}"
            tab_title = field_schema.get("title", field_name.replace("_", " ").title())

            parts.append(
                f"""
            <li class="md-tab" role="presentation">
                <button class="md-tab-button{active_class}"
                        onclick="switchMaterialTab('{tab_id}')"
                        type="button" role="tab"
                        aria-controls="{tab_id}"
                        aria-selected="{"true" if i == 0 else "false"}">
                    {tab_title}
                </button>
            </li>
            """
            )
        parts.append("</ul>")

        # Create tab content
        for i, (field_name, field_schema) in enumerate(layout_fields):
            active_class = " active" if i == 0 else ""
            tab_id = f"material-tab-{field_name}"

            parts.append(
                f'<div class="md-tab-content{active_class}" id="{tab_id}" role="tabpanel">'
            )

            # Render the layout field content (the nested form)
            layout_content = self._render_material_layout_field_content(
                field_name, field_schema, data.get(field_name), errors.get(field_name)
            )
            parts.append(layout_content)

            parts.append("</div>")

        parts.append("</div>")  # Close md-tabs

        # Add JavaScript for tab switching
        parts.append(
            """
        <script>
        function switchMaterialTab(activeTabId) {
            // Hide all tab contents
            const allContents = document.querySelectorAll('.md-tab-content');
            allContents.forEach(content => {
                content.classList.remove('active');
            });

            // Remove active class from all tab buttons
            const allButtons = document.querySelectorAll('.md-tab-button');
            allButtons.forEach(button => {
                button.classList.remove('active');
                button.setAttribute('aria-selected', 'false');
            });

            // Show active tab content
            const activeContent = document.getElementById(activeTabId);
            if (activeContent) {
                activeContent.classList.add('active');
            }

            // Add active class to clicked button
            const activeButton = event.target;
            activeButton.classList.add('active');
            activeButton.setAttribute('aria-selected', 'true');
        }
        </script>
        """
        )

        return parts

    def _render_material_layout_field_content(
        self, field_name: str, field_schema: Dict[str, Any], value: Any, error: Optional[str]
    ) -> str:
        """
        Render the content of a Material Design layout field (the nested form).
        """
        try:
            if isinstance(value, BaseLayout):
                nested_data = self._get_material_nested_form_data(field_name)
                return value.render(
                    data=nested_data,
                    errors=None,
                    renderer=self,
                    framework=self.framework,
                )

            if value and hasattr(value, "form"):
                form_class = value.form
                nested_data = self._get_material_nested_form_data(field_name)
                nested_renderer = SimpleMaterialRenderer()
                nested_renderer._current_form_data = nested_data
                return nested_renderer.render_form_fields_only(
                    form_class,
                    data=nested_data,
                    errors={},
                )

            return self._render_material_layout_field_content_fallback(field_name, field_schema)

        except Exception as e:
            # Error handling: return a placeholder with error message
            return f"""
            <div class="md-field error">
                <div class="md-error-message">Error rendering layout field: {str(e)}</div>
            </div>
            """

    def _render_material_layout_field_content_fallback(
        self, field_name: str, field_schema: Dict[str, Any]
    ) -> str:
        """
        Fallback rendering for Material Design layout field content.
        """
        # Map field names to their corresponding form classes
        form_mapping = {
            "vertical_tab": "PersonalInfoForm",
            "horizontal_tab": "ContactInfoForm",
            "tabbed_tab": "PreferencesForm",
            "list_tab": "TaskListForm",
        }

        form_name = form_mapping.get(field_name)
        if form_name:
            try:
                # Import and render the form
                if form_name == "PersonalInfoForm":
                    from examples.shared_models import PersonalInfoForm as FormClass
                elif form_name == "ContactInfoForm":
                    from examples.shared_models import ContactInfoForm as FormClass
                elif form_name == "PreferencesForm":
                    from examples.shared_models import PreferencesForm as FormClass
                elif form_name == "TaskListForm":
                    from examples.shared_models import TaskListForm as FormClass
                else:
                    raise ImportError(f"Unknown form: {form_name}")

                # Get nested form data based on field name mapping
                nested_data = self._get_material_nested_form_data(field_name)

                # Create a new SimpleMaterialRenderer for the nested form
                nested_renderer = SimpleMaterialRenderer()
                # Important: Set the form data on the nested renderer too
                nested_renderer._current_form_data = nested_data
                return nested_renderer.render_form_fields_only(
                    FormClass, data=nested_data, errors={}  # Pass relevant data to nested form
                )

            except Exception as e:
                return f"""
                <div class="md-field">
                    <div class="md-info-message">Layout demonstration: {form_name}</div>
                    <div class="md-error-message">Could not render: {str(e)}</div>
                </div>
                """
        else:
            return """
            <div class="md-field">
                <div class="md-info-message">Unknown layout field type</div>
            </div>
            """


# Alias for backward compatibility
MaterialDesign3Renderer = SimpleMaterialRenderer
