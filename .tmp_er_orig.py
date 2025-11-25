"""
Enhanced Form Renderer for Pydantic Models with UI Elements
Supports UI element specifications similar to React JSON Schema Forms
"""

import asyncio
from functools import partial
from html import escape
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from .icon_mapping import map_icon_for_framework
from .inputs import HiddenInput, build_error_message, build_help_text, build_label
from .rendering.context import RenderContext
from .rendering.frameworks import get_framework_config, get_input_component
from .rendering.layout_engine import LayoutEngine, get_nested_form_data
from .schema_form import FormModel


class SchemaFormValidationError(Exception):
    """
    Custom exception for schema form validation errors.
    Accepts a list of error dicts in the format expected by React JSON Schema Forms.
    """

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        super().__init__("Schema form validation error")


class EnhancedFormRenderer:
    """
    Enhanced form renderer that maps Pydantic models with UI elements to HTML forms.
    Supports the same UI element specifications as React JSON Schema Forms.
    """

    def __init__(self, framework: str = "bootstrap"):
        """Initialize renderer with specified framework."""
        self.framework = framework
        self.config = get_framework_config(framework)
        self._layout_engine = LayoutEngine(self)

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
        Render a complete HTML form from a Pydantic model with UI elements.

        Args:
            model_cls: Pydantic model class with UI element specifications
            data: Form data to populate fields with
            errors: Validation errors to display
            submit_url: Form submission URL
            method: HTTP method (POST, GET)
            include_csrf: Whether to include CSRF protection
            include_submit_button: Whether to include submit button
            layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
            **kwargs: Additional form attributes

        Returns:
            Complete HTML form as string
        """
        schema = model_cls.model_json_schema()
        data = data or {}
        errors = errors or {}

        # Store current form data for nested forms to access
        self._current_form_data = data

        # Store schema definitions for model_list fields
        self._schema_defs = schema.get("$defs", {})
        context = RenderContext(form_data=data, schema_defs=self._schema_defs)

        # Handle SchemaFormValidationError format
        if isinstance(errors, dict) and "errors" in errors:
            errors = {err.get("name", ""): err.get("message", "") for err in errors["errors"]}

        # Start form
        form_attrs = {
            "method": method,
            "action": submit_url,
            "class": self.config["form_class"],
            "novalidate": True,  # Use custom validation
        }
        form_attrs.update(kwargs)
        # Ensure action isn't overridden by kwargs
        form_attrs["action"] = submit_url

        form_parts = [self._build_form_tag(form_attrs)]

        # Add CSRF if requested
        if include_csrf:
            form_parts.append(self._render_csrf_field())

        # Get fields and sort by UI order if specified
        fields = list(schema["properties"].items())
        fields.sort(key=lambda x: x[1].get("ui", {}).get("order", 999))
        required_fields = schema.get("required", [])

        # Check if all fields are layout fields - if so, use tabbed layout automatically
        layout_fields = []
        non_layout_fields = []

        for field_name, field_schema in fields:
            ui_info = field_schema.get("ui", {})
            if not ui_info:
                ui_info = field_schema
            ui_element = (
                ui_info.get("element")
                or ui_info.get("ui_element")
                or ui_info.get("widget")
                or ui_info.get("input_type")
            )

            if ui_element == "layout":
                layout_fields.append((field_name, field_schema))
            else:
                non_layout_fields.append((field_name, field_schema))

        # If we have multiple layout fields and few/no other fields, render as tabs
        if len(layout_fields) > 1 and len(non_layout_fields) == 0:
            # Render layout fields as tabs
            form_parts.extend(
                self._render_layout_fields_as_tabs(
                    layout_fields,
                    data,
                    errors,
                    required_fields,
                    context,
                )
            )
        elif layout == "tabbed":
            form_parts.extend(
                self._render_tabbed_layout(fields, data, errors, required_fields, context)
            )
        elif layout == "side-by-side":
            form_parts.extend(
                self._render_side_by_side_layout(fields, data, errors, required_fields, context)
            )
        else:
            # Render each field with appropriate layout
            for field_name, field_schema in fields:
                field_html = self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    context,
                    layout,
                    errors,  # Pass full errors dictionary
                )
                form_parts.append(field_html)

        # Add submit button if requested
        if include_submit_button:
            form_parts.append(self._render_submit_button())

        form_parts.append("</form>")

        # Add model list JavaScript if any model_list fields were rendered
        if self._has_model_list_fields(schema):
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer(framework=self.framework)
            form_parts.append(list_renderer.get_model_list_javascript())

        return "\n".join(form_parts)

    def _has_model_list_fields(self, schema: Dict[str, Any]) -> bool:
        """Check if the schema contains any model_list fields."""
        properties = schema.get("properties", {})
        for _field_name, field_schema in properties.items():
            ui_info = field_schema.get("ui", {}) or field_schema
            ui_element = (
                ui_info.get("element")
                or ui_info.get("ui_element")
                or ui_info.get("widget")
                or ui_info.get("input_type")
            )
            if ui_element == "model_list":
                return True
        return False

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

        Args:
            model_cls: Pydantic model class with UI element specifications
            data: Form data to populate fields with
            errors: Validation errors to display
            layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
            **kwargs: Additional rendering options

        Returns:
            HTML for form fields only (no <form> tags)
        """
        schema = model_cls.model_json_schema()
        data = data or {}
        errors = errors or {}

        # Store current form data for nested forms to access
        self._current_form_data = data

        # Store schema definitions for model_list fields
        self._schema_defs = schema.get("$defs", {})
        context = RenderContext(form_data=data, schema_defs=self._schema_defs)

        # Handle SchemaFormValidationError format
        if isinstance(errors, dict) and "errors" in errors:
            errors = {err.get("name", ""): err.get("message", "") for err in errors["errors"]}

        # Get fields and sort by UI order if specified
        fields = list(schema["properties"].items())
        fields.sort(key=lambda x: x[1].get("ui", {}).get("order", 999))
        required_fields = schema.get("required", [])

        form_parts = []

        # Render fields based on layout
        for field_name, field_schema in fields:
            field_html = self._render_field(
                field_name,
                field_schema,
                data.get(field_name),
                errors.get(field_name),
                required_fields,
                context,
                layout,
                errors,  # Pass full errors dictionary
            )
            form_parts.append(field_html)

        return "\n".join(form_parts)

    async def render_form_from_model_async(
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
        Async version of render_form_from_model for high-performance applications.

        This method is useful when rendering multiple forms concurrently or when
        integrating with async validation services.
        """
        # For CPU-bound form rendering, we run in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # Use default thread pool
            self.render_form_from_model,
            model_cls,
            data,
            errors,
            submit_url,
            method,
            include_csrf,
            include_submit_button,
            layout,
            **kwargs,
        )

    def _build_form_tag(self, attrs: Dict[str, Any]) -> str:
        """Build opening form tag with attributes."""
        attr_strings = []
        for key, value in attrs.items():
            if value is not None:
                attr_strings.append(f'{key}="{escape(str(value))}"')
        return f'<form {" ".join(attr_strings)}>'

    def _render_field(
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
        """Render a single form field with its UI element."""
        if context is None:
            context = RenderContext(
                form_data=getattr(self, "_current_form_data", {}) or {},
                schema_defs=getattr(self, "_schema_defs", {}) or {},
            )

        # Check for UI info in nested 'ui' key or directly in field schema
        ui_info = field_schema.get("ui", {})
        if not ui_info:
            # UI info might be directly in the field schema (from FormField)
            ui_info = field_schema

        # Skip hidden fields in layout but still render them
        if ui_info.get("hidden"):
            return self._render_hidden_field(field_name, field_schema, value)

        # Determine UI element type - check multiple possible keys
        ui_element = (
            ui_info.get("element")
            or ui_info.get("ui_element")
            or ui_info.get("widget")
            or ui_info.get("input_type")
        )
        if not ui_element:
            ui_element = self._infer_ui_element(field_schema)

        # Handle layout fields specially - render the embedded form
        if ui_element == "layout":
            return self._render_layout_field(
                field_name,
                field_schema,
                value,
                error,
                ui_info,
                context,
            )

        # Handle model_list specially since it doesn't use the standard input component pattern
        if ui_element == "model_list":
            # Special handling for model lists
            from .model_list import ModelListRenderer

            list_renderer = ModelListRenderer(framework=self.framework)
            model_class = ui_info.get("model_class")

            # If model_class not directly provided, try to extract from schema
            if not model_class:
                # Look for items.$ref in the field schema for array types
                items_ref = field_schema.get("items", {}).get("$ref")
                if items_ref:
                    # Extract model name from $ref (e.g., "#/$defs/PetModel" -> "PetModel")
                    model_name = items_ref.split("/")[-1]
                    # Try to get the model class from the schema definitions
                    # For now, we'll work with the schema definition directly
                    schema_def = None
                    if hasattr(self, "_schema_defs"):
                        schema_def = self._schema_defs.get(model_name)

                    if schema_def:
                        # We have the schema definition, we can render the fields
                        pass  # We'll handle this below
                    else:
                        return f"<!-- Error: Could not resolve model reference '{items_ref}' for field '{field_name}' -->"
                else:
                    return f"<!-- Error: model_class not specified and no items.$ref found for model_list field '{field_name}' -->"

            # Convert value to list of dicts if needed
            list_values = []
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

            # Extract nested errors for this model list field
            nested_errors = self._extract_nested_errors_for_field(field_name, all_errors)

            # If we have a model_class, use it; otherwise use the schema definition
            if model_class:
                return list_renderer.render_model_list(
                    field_name=field_name,
                    label=field_schema.get("title", field_name.replace("_", " ").title()),
                    model_class=model_class,
                    values=list_values,
                    error=error,
                    nested_errors=nested_errors,  # Pass nested errors
                    help_text=ui_info.get("help_text"),
                    is_required=field_name in (required_fields or []),
                    min_items=ui_info.get("min_items", 0),
                    max_items=ui_info.get("max_items", 10),
                )
            else:
                # Render using schema definition
                return self._render_model_list_from_schema(
                    field_name=field_name,
                    field_schema=field_schema,
                    schema_def=schema_def,
                    values=list_values,
                    error=error,
                    ui_info=ui_info,
                    required_fields=required_fields,
                    context=context,
                )

        # Get input component
        input_component = get_input_component(ui_element)()

        # Build field attributes
        field_attrs = {
            "name": field_name,
            "id": field_name,
            "class": self._get_input_class(ui_element),
        }

        # Add value if provided (except for password fields for security)
        if value is not None and ui_element != "password":
            if ui_element == "checkbox":
                # For checkboxes, set the checked attribute based on boolean value
                if value is True or value == "true" or value == "1" or value == "on":
                    field_attrs["checked"] = True
                field_attrs["value"] = "1"  # Standard checkbox value
            else:
                field_attrs["value"] = value
        elif value is not None and ui_element == "password":
            # For password fields, set value only if it's a validation scenario
            field_attrs["value"] = value

        # Add validation attributes
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

        # Add UI-specific attributes
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

        # Render the input
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
        except Exception as e:
            input_html = f"<!-- Error rendering {ui_element}: {str(e)} -->"

        # Return the input directly since render_with_label handles the complete field
        return f'<div class="{self.config["field_wrapper_class"]}">{input_html}</div>'

    def _extract_ui_options(
        self, ui_info: Dict[str, Any], field_schema: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Any]]:
        """Extract ui_options mapping and option choices for select-like inputs."""
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
        """Merge ui_options entries into field attributes while skipping choice data."""
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
        """Convert choice definitions into renderer-friendly dictionaries."""
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

                if formatted.get("value") is None:
                    formatted["value"] = formatted.get("label")

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
        """Determine if an option should be marked as selected based on current value."""
        if option_value is None or current_value is None:
            return False

        option_str = str(option_value)

        if isinstance(current_value, (list, tuple, set)):
            return option_str in {str(val) for val in current_value}

        return option_str == str(current_value)

    def _render_hidden_field(
        self, field_name: str, field_schema: Dict[str, Any], value: Any
    ) -> str:
        """Render a hidden input field."""
        hidden_input = HiddenInput()
        return hidden_input.render(name=field_name, id=field_name, value=value or "")

    def _infer_ui_element(self, field_schema: Dict[str, Any]) -> str:
        """Infer UI element type from field schema."""
        field_type = field_schema.get("type", "string")

        if field_type == "string":
            max_length = field_schema.get("maxLength", 0)
            if max_length > 200:
                return "textarea"
            elif "email" in field_schema.get("title", "").lower():
                return "email"
            elif "password" in field_schema.get("title", "").lower():
                return "password"
            else:
                return "text"
        elif field_type in ("integer", "number"):
            return "number"
        elif field_type == "boolean":
            return "checkbox"
        else:
            return "text"

    def _get_input_class(self, ui_element: str) -> str:
        """Get appropriate CSS class for input element."""
        if ui_element == "checkbox":
            return self.config["checkbox_class"]
        elif ui_element in ("select", "radio", "multiselect"):
            return self.config["select_class"]
        else:
            return self.config["input_class"]

    def _wrap_field(
        self,
        field_name: str,
        label: str,
        input_html: str,
        help_text: Optional[str] = None,
        error: Optional[str] = None,
        required: bool = False,
        layout: str = "vertical",
    ) -> str:
        """Wrap field with label, help text, and error message."""
        if layout == "horizontal":
            return self._wrap_field_horizontal(
                field_name, label, input_html, help_text, error, required
            )
        else:
            return self._wrap_field_vertical(
                field_name, label, input_html, help_text, error, required
            )

    def _wrap_field_vertical(
        self,
        field_name: str,
        label: str,
        input_html: str,
        help_text: Optional[str] = None,
        error: Optional[str] = None,
        required: bool = False,
    ) -> str:
        """Wrap field with vertical layout (default)."""
        parts = [f'<div class="{self.config["field_wrapper_class"]}">']

        # Add label
        label_html = build_label(field_name, label, required)
        if self.config["label_class"]:
            label_html = label_html.replace(
                "<label", f'<label class="{self.config["label_class"]}"'
            )
        parts.append(label_html)

        # Add input
        parts.append(input_html)

        # Add help text
        if help_text:
            help_html = build_help_text(field_name, help_text)
            if self.config["help_class"]:
                help_html = help_html.replace(
                    'class="help-text"', f'class="{self.config["help_class"]}"'
                )
            parts.append(help_html)

        # Add error message
        if error:
            error_html = build_error_message(field_name, error)
            if self.config["error_class"]:
                error_html = error_html.replace(
                    'class="error-message"', f'class="{self.config["error_class"]}"'
                )
            parts.append(error_html)

        parts.append("</div>")

        # Filter out None values to prevent join errors
        filtered_parts = [part for part in parts if part is not None]
        return "\n".join(filtered_parts)

    def _wrap_field_horizontal(
        self,
        field_name: str,
        label: str,
        input_html: str,
        help_text: Optional[str] = None,
        error: Optional[str] = None,
        required: bool = False,
    ) -> str:
        """Wrap field with horizontal layout (Bootstrap row/col format)."""
        parts = ['<div class="row mb-3">']

        # Add label in left column
        label_html = build_label(field_name, label, required)
        label_html = label_html.replace("<label", '<label class="col-sm-3 col-form-label"')
        parts.append(label_html)

        # Add input in right column
        parts.append('<div class="col-sm-9">')
        parts.append(input_html)

        # Add help text
        if help_text:
            help_html = build_help_text(field_name, help_text)
            if self.config["help_class"]:
                help_html = help_html.replace(
                    'class="help-text"', f'class="{self.config["help_class"]}"'
                )
            parts.append(help_html)

        # Add error message
        if error:
            error_html = build_error_message(field_name, error)
            if self.config["error_class"]:
                error_html = error_html.replace(
                    'class="error-message"', f'class="{self.config["error_class"]}"'
                )
            parts.append(error_html)

        parts.append("</div>")  # Close col-sm-9
        parts.append("</div>")  # Close row

        # Filter out None values to prevent join errors
        filtered_parts = [part for part in parts if part is not None]
        return "\n".join(filtered_parts)

    def _render_tabbed_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        """Render fields in a tabbed layout."""
        return self._layout_engine.render_tabbed_layout(
            fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _render_layout_fields_as_tabs(
        self,
        layout_fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        """Render layout fields as tabs, with each layout field becoming a tab containing its form."""
        return self._layout_engine.render_layout_fields_as_tabs(
            layout_fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _render_layout_field_content(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        """Render the content of a layout field (the nested form)."""
        return self._layout_engine.render_layout_field_content(
            field_name,
            field_schema,
            value,
            error,
            ui_info,
            context,
        )

    def _get_nested_form_data(
        self,
        field_name: str,
        main_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Adapter to share nested data helper across renderers."""
        data = main_data if main_data is not None else getattr(self, "_current_form_data", {}) or {}
        return get_nested_form_data(field_name, data)

    def _render_side_by_side_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
        context: RenderContext,
    ) -> List[str]:
        """Render fields in a side-by-side layout using Bootstrap grid."""
        return self._layout_engine.render_side_by_side_layout(
            fields,
            data,
            errors,
            required_fields,
            context,
        )

    def _render_side_by_side_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
    ) -> List[str]:
        """Render fields in a side-by-side layout using Bootstrap grid."""
        parts = []

        # Group fields into pairs for side-by-side arrangement
        field_pairs = []
        for i in range(0, len(fields), 2):
            if i + 1 < len(fields):
                field_pairs.append((fields[i], fields[i + 1]))
            else:
                # Odd number of fields - last field goes alone
                field_pairs.append((fields[i], None))

        # Render each pair in a row
        for left_field, right_field in field_pairs:
            parts.append('<div class="row">')

            # Left column
            parts.append('<div class="col-md-6">')
            if left_field:
                field_name, field_schema = left_field
                field_html = self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    "vertical",  # Use vertical layout within each column
                    errors,  # Pass full errors dictionary
                )
                parts.append(field_html)
            parts.append("</div>")

            # Right column
            parts.append('<div class="col-md-6">')
            if right_field:
                field_name, field_schema = right_field
                field_html = self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    "vertical",  # Use vertical layout within each column
                    errors,  # Pass full errors dictionary
                )
                parts.append(field_html)
            parts.append("</div>")

            parts.append("</div>")  # Close row

        return parts

    def _render_model_list_from_schema(
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
        """Render a model list using schema definition instead of model class."""
        # Use simplified rendering for schema-based lists

        html = f"""
        <div class="mb-3">
            <label class="form-label fw-bold">
                {escape(field_schema.get('title', field_name.replace('_', ' ').title()))}
                {' <span class="text-danger">*</span>' if field_name in (required_fields or []) else ''}
            </label>

            <div class="model-list-container"
                 data-field-name="{field_name}"
                 data-min-items="{field_schema.get('minItems', 0)}"
                 data-max-items="{field_schema.get('maxItems', 10)}">

                <div class="model-list-items" id="{field_name}-items">"""

        # Render existing items
        for i, item_data in enumerate(values):
            html += self._render_schema_list_item(
                field_name,
                schema_def,
                i,
                item_data,
                context,
                ui_info,
            )

        # If no items and minItems > 0, add empty items
        min_items = field_schema.get("minItems", 0)
        if not values and min_items > 0:
            for i in range(min_items):
                html += self._render_schema_list_item(
                    field_name,
                    schema_def,
                    i,
                    {},
                    context,
                    ui_info,
                )

        # If no items at all, add one empty item for user convenience
        if not values and min_items == 0:
            html += self._render_schema_list_item(
                field_name,
                schema_def,
                0,
                {},
                context,
                ui_info,
            )

        html += f"""
                </div>

                <div class="model-list-controls mt-2">
                    <button type="button"
                            class="btn btn-outline-primary btn-sm add-item-btn"
                            data-target="{field_name}">
                        <i class="bi bi-plus-circle"></i> Add Item
                    </button>
                </div>
            </div>"""

        help_text = ui_info.get("help_text") or field_schema.get("description")
        if help_text:
            html += f"""
            <div class="form-text text-muted">
                <i class="bi bi-info-circle"></i> {escape(help_text)}
            </div>"""

        if error:
            html += f"""
            <div class="invalid-feedback d-block">
                <i class="bi bi-exclamation-triangle"></i> {escape(error)}
            </div>"""

        html += "</div>"
        return html

    def _extract_nested_errors_for_field(
        self, field_name: str, all_errors: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract nested errors for a specific field from the complete error dictionary.

        For example, if field_name is 'pets' and all_errors contains 'pets[0].weight',
        this returns {'0.weight': 'error message'}.

        Args:
            field_name: The base field name (e.g., 'pets')
            all_errors: Complete error dictionary with nested paths

        Returns:
            Dictionary of nested errors with simplified paths
        """
        nested_errors = {}
        field_prefix = f"{field_name}["

        for error_path, error_message in (all_errors or {}).items():
            if error_path.startswith(field_prefix):
                # Extract the part after the field name prefix
                # e.g., 'pets[0].weight' -> '0].weight' after removing 'pets['
                nested_part = error_path[len(field_prefix) :]  # Remove 'pets['
                if "]." in nested_part:
                    # Replace ]. with . to get '0.weight' from '0].weight'
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
        """Render a single list item from schema definition with collapsible card support."""
        ui_info = ui_info or {}
        collapsible = ui_info.get("collapsible_items", True)
        expanded = ui_info.get("items_expanded", True)
        title_template = ui_info.get("item_title_template", "Item #{index}")

        # Generate dynamic title
        title_vars = {"index": index + 1, **item_data}
        try:
            item_title = title_template.format(**title_vars)
        except (KeyError, ValueError):
            item_title = f"Item #{index + 1}"

        # Determine collapse state
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

        # Card body with collapse support
        if collapsible:
            html += f"""
            <div class="collapse {collapse_class} show" id="{collapse_id}">
                <div class="card-body">"""
        else:
            html += """
            <div class="card-body">"""

        # Render fields in a responsive grid
        html += '<div class="row">'

        # Render each field in the schema
        properties = schema_def.get("properties", {})
        field_count = len([k for k in properties.keys() if not k.startswith("_")])

        # Determine column class based on field count
        if field_count <= 2:
            col_class = "col-12"
        elif field_count <= 4:
            col_class = "col-md-6"
        else:
            col_class = "col-lg-4 col-md-6"

        for field_key, field_schema in properties.items():
            if field_key.startswith("_"):
                continue

            field_value = item_data.get(field_key, "")
            input_name = f"{field_name}[{index}].{field_key}"

            html += f"""
                <div class="{col_class}">
                    {self._render_field(
                        input_name,
                        field_schema,
                        field_value,
                        None,  # error
                        [],   # required_fields
                        context,
                        "vertical",  # layout
                        None  # all_errors (not available in schema rendering)
                    )}
                </div>"""

        html += "</div>"  # Close row

        if collapsible:
            html += """
                </div>
            </div>"""  # Close card-body and collapse
        else:
            html += "</div>"  # Close card-body

        html += "</div>"  # Close card

        return html

    def _render_csrf_field(self) -> str:
        """Render CSRF token field."""
        # This would integrate with your CSRF protection system
        return '<input type="hidden" name="csrf_token" value="__CSRF_TOKEN__" />'

    def _render_layout_field(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        value: Any,
        error: Optional[str],
        ui_info: Dict[str, Any],
        context: RenderContext,
    ) -> str:
        """Render a layout field by extracting and rendering its embedded form."""
        return self._layout_engine.render_layout_field(
            field_name,
            field_schema,
            value,
            error,
            ui_info,
            context,
        )

    def _render_submit_button(self) -> str:
        """Render form submit button."""
        button_class = self.config["button_class"]
        return f'<button type="submit" class="{button_class}">Submit</button>'


def render_form_html(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
    **kwargs,
) -> str:
    """
    Convenience function to render an HTML form for the given FormModel class.

    Args:
        form_model_cls: Pydantic FormModel class with UI elements
        form_data: Form data to populate fields with
        errors: Validation errors (dict or SchemaFormValidationError)
        framework: CSS framework to use
        layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
        **kwargs: Additional rendering options

    Returns:
        Complete HTML form as string
    """
    # Handle SchemaFormValidationError
    if isinstance(errors, SchemaFormValidationError):
        error_dict = {err.get("name", ""): err.get("message", "") for err in errors.errors}
        errors = error_dict

    # Use SimpleMaterialRenderer for Material Design 3
    if framework == "material":
        from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer

        renderer = SimpleMaterialRenderer()
        return renderer.render_form_from_model(
            form_model_cls, data=form_data, errors=errors, **kwargs
        )

    # Use EnhancedFormRenderer for other frameworks
    renderer = EnhancedFormRenderer(framework=framework)
    return renderer.render_form_from_model(
        form_model_cls, data=form_data, errors=errors, layout=layout, **kwargs
    )


async def render_form_html_async(
    form_model_cls: Type[FormModel],
    form_data: Optional[Dict[str, Any]] = None,
    errors: Optional[Union[Dict[str, str], SchemaFormValidationError]] = None,
    framework: str = "bootstrap",
    layout: str = "vertical",
    **kwargs,
) -> str:
    """
    Async convenience function to render an HTML form for the given FormModel class.

    Args:
        form_model_cls: Pydantic FormModel class with UI elements
        form_data: Form data to populate fields with
        errors: Validation errors (dict or SchemaFormValidationError)
        framework: CSS framework to use
        layout: Layout type - "vertical", "horizontal", "side-by-side", or "tabbed"
        **kwargs: Additional rendering options

    Returns:
        Complete HTML form as string
    """
    render_callable = partial(
        render_form_html,
        form_model_cls,
        form_data=form_data,
        errors=errors,
        framework=framework,
        layout=layout,
        **kwargs,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, render_callable)
