"""
Enhanced Form Renderer for Pydantic Models with UI Elements
Supports UI element specifications similar to React JSON Schema Forms
"""

from typing import Any, Dict, List, Optional, Type, Union
from html import escape

from .inputs import (
    TextInput,
    PasswordInput,
    EmailInput,
    NumberInput,
    CheckboxInput,
    SelectInput,
    DateInput,
    DatetimeInput,
    FileInput,
    ColorInput,
    RangeInput,
    HiddenInput,
    RadioGroup,
    TextArea,
    SearchInput,
    TelInput,
    URLInput,
    MonthInput,
    WeekInput,
    TimeInput,
    build_label,
    build_error_message,
    build_help_text,
)
from .schema_form import FormModel
from .icon_mapping import map_icon_for_framework


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

    # Framework configurations
    FRAMEWORKS = {
        "bootstrap": {
            "css_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
            "js_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
            "form_class": "needs-validation",
            "input_class": "form-control",
            "select_class": "form-select",
            "checkbox_class": "form-check-input",
            "radio_class": "form-check-input",
            "button_class": "btn btn-primary",
            "error_class": "invalid-feedback",
            "label_class": "form-label",
            "help_class": "form-text text-muted",
            "field_wrapper_class": "mb-3",
        },
        "material": {
            "css_url": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css",
            "js_url": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js",
            "form_class": "col s12",
            "input_class": "validate",
            "select_class": "browser-default",
            "checkbox_class": "filled-in",
            "radio_class": "",
            "button_class": "btn waves-effect waves-light",
            "error_class": "helper-text red-text",
            "label_class": "",
            "help_class": "helper-text",
            "field_wrapper_class": "input-field col s12",
        },
        "none": {
            "css_url": "",
            "js_url": "",
            "form_class": "",
            "input_class": "",
            "select_class": "",
            "checkbox_class": "",
            "radio_class": "",
            "button_class": "",
            "error_class": "error",
            "label_class": "",
            "help_class": "help-text",
            "field_wrapper_class": "field",
        },
    }

    # UI element to input component mapping
    UI_ELEMENT_MAPPING = {
        "text": TextInput,
        "password": PasswordInput,
        "email": EmailInput,
        "number": NumberInput,
        "range": RangeInput,
        "checkbox": CheckboxInput,
        "select": SelectInput,
        "radio": RadioGroup,
        "textarea": TextArea,
        "date": DateInput,
        "time": TimeInput,
        "datetime": DatetimeInput,
        "datetime-local": DatetimeInput,
        "month": MonthInput,
        "week": WeekInput,
        "file": FileInput,
        "color": ColorInput,
        "hidden": HiddenInput,
        "search": SearchInput,
        "tel": TelInput,
        "url": URLInput,
    }

    def __init__(self, framework: str = "bootstrap"):
        """Initialize renderer with specified framework."""
        self.framework = framework
        self.config = self.FRAMEWORKS.get(framework, self.FRAMEWORKS["bootstrap"])

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
        self._schema_defs = schema.get('$defs', {})

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
            ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")

            if ui_element == "layout":
                layout_fields.append((field_name, field_schema))
            else:
                non_layout_fields.append((field_name, field_schema))

        # If we have multiple layout fields and few/no other fields, render as tabs
        if len(layout_fields) > 1 and len(non_layout_fields) == 0:
            # Render layout fields as tabs
            form_parts.extend(self._render_layout_fields_as_tabs(layout_fields, data, errors, required_fields))
        elif layout == "tabbed":
            form_parts.extend(self._render_tabbed_layout(fields, data, errors, required_fields))
        elif layout == "side-by-side":
            form_parts.extend(self._render_side_by_side_layout(fields, data, errors, required_fields))
        else:
            # Render each field with appropriate layout
            for field_name, field_schema in fields:
                field_html = self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    layout,
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
            ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")
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
        self._schema_defs = schema.get('$defs', {})

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
                layout,
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
            **kwargs
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
        required_fields: List[str] = None,
        layout: str = "vertical",
    ) -> str:
        """Render a single form field with its UI element."""
        # Check for UI info in nested 'ui' key or directly in field schema
        ui_info = field_schema.get("ui", {})
        if not ui_info:
            # UI info might be directly in the field schema (from FormField)
            ui_info = field_schema

        # Skip hidden fields in layout but still render them
        if ui_info.get("hidden"):
            return self._render_hidden_field(field_name, field_schema, value)

        # Determine UI element type - check multiple possible keys
        ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")
        if not ui_element:
            ui_element = self._infer_ui_element(field_schema)

        # Handle layout fields specially - render the embedded form
        if ui_element == "layout":
            return self._render_layout_field(field_name, field_schema, value, error, ui_info)

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
                    if hasattr(self, '_schema_defs'):
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
                        if hasattr(item, 'model_dump'):
                            list_values.append(item.model_dump())
                        elif isinstance(item, dict):
                            list_values.append(item)
                elif hasattr(value, 'model_dump'):
                    list_values = [value.model_dump()]
                elif isinstance(value, dict):
                    list_values = [value]

            # If we have a model_class, use it; otherwise use the schema definition
            if model_class:
                return list_renderer.render_model_list(
                    field_name=field_name,
                    label=field_schema.get('title', field_name.replace('_', ' ').title()),
                    model_class=model_class,
                    values=list_values,
                    error=error,
                    help_text=ui_info.get('help_text'),
                    is_required=field_name in (required_fields or []),
                    min_items=ui_info.get('min_items', 0),
                    max_items=ui_info.get('max_items', 10)
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
                    required_fields=required_fields
                )

        # Get input component
        input_component = self.UI_ELEMENT_MAPPING.get(ui_element, TextInput)()

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
        required_fields = required_fields or []
        if field_name in required_fields:
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

        # Handle select/radio options separately
        ui_options_list = ui_info.get("options", [])

        # Render the input
        try:
            if ui_element in ("select", "radio"):
                # Convert options to proper format for SelectInput/RadioGroup
                if ui_options_list:
                    formatted_options = []
                    for option in ui_options_list:
                        if isinstance(option, dict):
                            formatted_options.append(option)
                        else:
                            # Convert string options to dict format
                            formatted_options.append({
                                "value": str(option),
                                "label": str(option),
                                "selected": str(option) == str(value) if value is not None else False
                            })

                    # Use render_with_label for icon support
                    label_text = field_schema.get("title", field_name.replace("_", " ").title())
                    help_text = ui_info.get("help_text") or field_schema.get("description")
                    icon = ui_info.get("icon")
                    # Map icon to appropriate framework
                    if icon:
                        icon = map_icon_for_framework(icon, self.framework)

                    input_html = input_component.render_with_label(
                        label=label_text,
                        help_text=help_text,
                        error=error,
                        icon=icon,
                        framework=self.framework,
                        options=formatted_options,
                        **field_attrs
                    )
                else:
                    input_html = f"<!-- Warning: No options provided for {ui_element} field '{field_name}' -->"
            else:
                # Regular input rendering with icon support
                label_text = field_schema.get("title", field_name.replace("_", " ").title())
                help_text = ui_info.get("help_text") or field_schema.get("description")
                icon = ui_info.get("icon")
                # Map icon to appropriate framework
                if icon:
                    icon = map_icon_for_framework(icon, self.framework)

                input_html = input_component.render_with_label(
                    label=label_text,
                    help_text=help_text,
                    error=error,
                    icon=icon,
                    framework=self.framework,
                    **field_attrs
                )

            if input_html is None:
                input_html = f"<!-- Error: {ui_element} input returned None -->"
        except Exception as e:
            input_html = f"<!-- Error rendering {ui_element}: {str(e)} -->"

        # Return the input directly since render_with_label handles the complete field
        return f'<div class="{self.config["field_wrapper_class"]}">{input_html}</div>'

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
        elif ui_element in ("select", "radio"):
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
            return self._wrap_field_horizontal(field_name, label, input_html, help_text, error, required)
        else:
            return self._wrap_field_vertical(field_name, label, input_html, help_text, error, required)

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
        label_html = label_html.replace('<label', '<label class="col-sm-3 col-form-label"')
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

        parts.append('</div>')  # Close col-sm-9
        parts.append('</div>')  # Close row

        # Filter out None values to prevent join errors
        filtered_parts = [part for part in parts if part is not None]
        return "\n".join(filtered_parts)

    def _render_tabbed_layout(
        self,
        fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
    ) -> List[str]:
        """Render fields in a tabbed layout."""
        # Group fields into logical tabs
        tabs = self._group_fields_into_tabs(fields)

        parts = []

        # Create tab navigation
        parts.append('<ul class="nav nav-tabs" id="formTabs" role="tablist">')
        for i, (tab_name, _) in enumerate(tabs):
            active_class = " active" if i == 0 else ""
            tab_id = f"tab-{tab_name.lower().replace(' ', '-')}"
            parts.append(f'''
            <li class="nav-item" role="presentation">
                <button class="nav-link{active_class}" id="{tab_id}-tab" data-bs-toggle="tab"
                        data-bs-target="#{tab_id}" type="button" role="tab"
                        aria-controls="{tab_id}" aria-selected="{"true" if i == 0 else "false"}">
                    {tab_name}
                </button>
            </li>
            ''')
        parts.append('</ul>')

        # Create tab content
        parts.append('<div class="tab-content" id="formTabContent">')
        for i, (tab_name, tab_fields) in enumerate(tabs):
            active_class = " show active" if i == 0 else ""
            tab_id = f"tab-{tab_name.lower().replace(' ', '-')}"
            parts.append(f'<div class="tab-pane fade{active_class}" id="{tab_id}" role="tabpanel" aria-labelledby="{tab_id}-tab">')

            # Render fields in this tab
            for field_name, field_schema in tab_fields:
                field_html = self._render_field(
                    field_name,
                    field_schema,
                    data.get(field_name),
                    errors.get(field_name),
                    required_fields,
                    "vertical",  # Use vertical layout within tabs
                )
                parts.append(field_html)

            parts.append('</div>')

        parts.append('</div>')
        return parts

    def _render_layout_fields_as_tabs(
        self,
        layout_fields: List[tuple],
        data: Dict[str, Any],
        errors: Dict[str, Any],
        required_fields: List[str],
    ) -> List[str]:
        """Render layout fields as tabs, with each layout field becoming a tab containing its form."""
        parts = []

        # Create tab navigation
        parts.append('<ul class="nav nav-tabs" id="layoutTabs" role="tablist">')
        for i, (field_name, field_schema) in enumerate(layout_fields):
            active_class = " active" if i == 0 else ""
            tab_id = f"layout-tab-{field_name}"
            tab_title = field_schema.get('title', field_name.replace('_', ' ').title())

            parts.append(f'''
            <li class="nav-item" role="presentation">
                <button class="nav-link{active_class}" id="{tab_id}-tab" data-bs-toggle="tab"
                        data-bs-target="#{tab_id}" type="button" role="tab"
                        aria-controls="{tab_id}" aria-selected="{"true" if i == 0 else "false"}">
                    {tab_title}
                </button>
            </li>
            ''')
        parts.append('</ul>')

        # Create tab content
        parts.append('<div class="tab-content" id="layoutTabContent">')
        for i, (field_name, field_schema) in enumerate(layout_fields):
            active_class = " show active" if i == 0 else ""
            tab_id = f"layout-tab-{field_name}"

            parts.append(f'<div class="tab-pane fade{active_class}" id="{tab_id}" role="tabpanel" aria-labelledby="{tab_id}-tab">')

            # Get the UI info for this layout field
            ui_info = field_schema.get("ui", {})
            if not ui_info:
                ui_info = field_schema

            # Render the layout field content (the nested form)
            layout_content = self._render_layout_field_content(field_name, field_schema, data.get(field_name), errors.get(field_name), ui_info)
            parts.append(layout_content)

            parts.append('</div>')

        parts.append('</div>')
        return parts

    def _render_layout_field_content(self, field_name: str, field_schema: Dict[str, Any], value: Any, error: Optional[str], ui_info: Dict[str, Any]) -> str:
        """
        Render the content of a layout field (the nested form) without the section wrapper.
        This is used when rendering layout fields as tab content.
        """
        try:
            # The value should be a layout instance
            if value and hasattr(value, 'form'):
                # Get the form class from the layout instance
                form_class = value.form

                # Get nested form data based on field name mapping
                nested_data = self._get_nested_form_data(field_name)

                # Create a new renderer for the nested form to avoid data conflicts
                nested_renderer = EnhancedFormRenderer(framework=self.framework)
                nested_renderer._current_form_data = nested_data

                # Render only the form fields (no form wrapper to avoid nested forms)
                return nested_renderer.render_form_fields_only(
                    form_class,
                    data=nested_data,  # Pass relevant data to nested form
                    errors={},
                    layout="vertical"  # Use vertical layout for embedded forms
                )
            else:
                # Fallback: try to get the form class from the field schema
                return self._render_layout_field_content_fallback(field_name, field_schema, ui_info)

        except Exception as e:
            # Error handling: return a placeholder with error message
            return f"""
            <div class="layout-field-error alert alert-warning">
                <p>Error rendering layout field: {str(e)}</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
            </div>
            """

    def _get_nested_form_data(self, field_name: str) -> Dict[str, Any]:
        """
        Get the data for nested forms based on the field name.
        This maps the main form data to the appropriate nested form fields.
        """
        # Access the main form data (stored during form rendering)
        main_data = getattr(self, '_current_form_data', {})

        # First check if there's direct nested data for this field
        if field_name in main_data and isinstance(main_data[field_name], dict):
            return main_data[field_name]

        # Fallback: Map layout field names to their corresponding form data
        field_data_mapping = {
            'vertical_tab': ['first_name', 'last_name', 'email', 'birth_date'],
            'horizontal_tab': ['phone', 'address', 'city', 'postal_code'],
            'tabbed_tab': ['notification_email', 'notification_sms', 'theme', 'language'],
            'list_tab': ['project_name', 'tasks']
        }

        # Get the fields that belong to this nested form
        relevant_fields = field_data_mapping.get(field_name, [])

        # Extract only the relevant data for this nested form
        nested_data = {}
        for field in relevant_fields:
            if field in main_data:
                nested_data[field] = main_data[field]

        return nested_data
        for field in relevant_fields:
            if field in main_data:
                nested_data[field] = main_data[field]

        return nested_data

    def _render_layout_field_content_fallback(self, field_name: str, field_schema: Dict[str, Any], ui_info: Dict[str, Any]) -> str:
        """
        Fallback rendering for layout field content when the layout instance isn't available.
        """
        # Map field names to their corresponding form classes
        form_mapping = {
            'vertical_tab': 'PersonalInfoForm',
            'horizontal_tab': 'ContactInfoForm',
            'tabbed_tab': 'PreferencesForm',
            'list_tab': 'TaskListForm'
        }

        form_name = form_mapping.get(field_name)
        if form_name:
            try:
                # Import and render the form
                if form_name == 'PersonalInfoForm':
                    from examples.shared_models import PersonalInfoForm as FormClass
                elif form_name == 'ContactInfoForm':
                    from examples.shared_models import ContactInfoForm as FormClass
                elif form_name == 'PreferencesForm':
                    from examples.shared_models import PreferencesForm as FormClass
                elif form_name == 'TaskListForm':
                    from examples.shared_models import TaskListForm as FormClass
                else:
                    raise ImportError(f"Unknown form: {form_name}")

                # Get nested form data based on field name mapping
                nested_data = self._get_nested_form_data(field_name)

                # Create a new renderer for the nested form to avoid data conflicts
                nested_renderer = EnhancedFormRenderer(framework=self.framework)
                nested_renderer._current_form_data = nested_data

                # Render only the form fields (no form wrapper to avoid nested forms)
                return nested_renderer.render_form_fields_only(
                    FormClass,
                    data=nested_data,  # Pass relevant data to nested form
                    errors={},
                    layout="vertical"
                )

            except Exception as e:
                return f"""
                <div class="layout-field-placeholder alert alert-info">
                    <p>Layout demonstration: {form_name}</p>
                    <small class="text-muted">{ui_info.get('help_text', '')}</small>
                    <small class="text-danger d-block">Could not render: {str(e)}</small>
                </div>
                """
        else:
            return f"""
            <div class="layout-field-unknown alert alert-secondary">
                <p>Unknown layout field type</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
            </div>
            """

    def _group_fields_into_tabs(self, fields: List[tuple]) -> List[tuple]:
        """Group fields into logical tabs based on field names."""
        # Simple grouping logic - can be enhanced based on field metadata
        personal_fields = []
        contact_fields = []
        other_fields = []

        for field_name, field_schema in fields:
            field_lower = field_name.lower()
            if any(keyword in field_lower for keyword in ['name', 'username', 'password', 'bio', 'role']):
                personal_fields.append((field_name, field_schema))
            elif any(keyword in field_lower for keyword in ['email', 'phone', 'address', 'subject', 'message']):
                contact_fields.append((field_name, field_schema))
            else:
                other_fields.append((field_name, field_schema))

        tabs = []
        if personal_fields:
            tabs.append(("Personal Info", personal_fields))
        if contact_fields:
            tabs.append(("Contact Details", contact_fields))
        if other_fields:
            tabs.append(("Additional", other_fields))

        # If no logical grouping, put all in one tab
        if not tabs:
            tabs.append(("Form Fields", fields))

        return tabs

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
                )
                parts.append(field_html)
            parts.append('</div>')

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
                )
                parts.append(field_html)
            parts.append('</div>')

            parts.append('</div>')  # Close row

        return parts

    def _render_model_list_from_schema(
        self,
        field_name: str,
        field_schema: Dict[str, Any],
        schema_def: Dict[str, Any],
        values: List[Dict[str, Any]],
        error: Optional[str],
        ui_info: Dict[str, Any],
        required_fields: List[str]
    ) -> str:
        """Render a model list using schema definition instead of model class."""
        from html import escape

        # Use simplified rendering for schema-based lists

        html = f'''
        <div class="mb-3">
            <label class="form-label fw-bold">
                {escape(field_schema.get('title', field_name.replace('_', ' ').title()))}
                {' <span class="text-danger">*</span>' if field_name in (required_fields or []) else ''}
            </label>

            <div class="model-list-container"
                 data-field-name="{field_name}"
                 data-min-items="{field_schema.get('minItems', 0)}"
                 data-max-items="{field_schema.get('maxItems', 10)}">

                <div class="model-list-items" id="{field_name}-items">'''

        # Render existing items
        for i, item_data in enumerate(values):
            html += self._render_schema_list_item(
                field_name, schema_def, i, item_data, ui_info
            )

        # If no items and minItems > 0, add empty items
        min_items = field_schema.get('minItems', 0)
        if not values and min_items > 0:
            for i in range(min_items):
                html += self._render_schema_list_item(
                    field_name, schema_def, i, {}, ui_info
                )

        # If no items at all, add one empty item for user convenience
        if not values and min_items == 0:
            html += self._render_schema_list_item(
                field_name, schema_def, 0, {}, ui_info
            )

        html += f'''
                </div>

                <div class="model-list-controls mt-2">
                    <button type="button"
                            class="btn btn-outline-primary btn-sm add-item-btn"
                            data-target="{field_name}">
                        <i class="bi bi-plus-circle"></i> Add Item
                    </button>
                </div>
            </div>'''

        help_text = ui_info.get('help_text') or field_schema.get('description')
        if help_text:
            html += f'''
            <div class="form-text text-muted">
                <i class="bi bi-info-circle"></i> {escape(help_text)}
            </div>'''

        if error:
            html += f'''
            <div class="invalid-feedback d-block">
                <i class="bi bi-exclamation-triangle"></i> {escape(error)}
            </div>'''

        html += '</div>'
        return html

    def _render_schema_list_item(
        self,
        field_name: str,
        schema_def: Dict[str, Any],
        index: int,
        item_data: Dict[str, Any],
        ui_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render a single list item from schema definition with collapsible card support."""
        from html import escape

        ui_info = ui_info or {}
        collapsible = ui_info.get('collapsible_items', True)
        expanded = ui_info.get('items_expanded', True)
        title_template = ui_info.get('item_title_template', 'Item #{index}')

        # Generate dynamic title
        title_vars = {'index': index + 1, **item_data}
        try:
            item_title = title_template.format(**title_vars)
        except (KeyError, ValueError):
            item_title = f"Item #{index + 1}"

        # Determine collapse state
        collapse_class = "" if expanded else "collapse"
        collapse_id = f"{field_name}_item_{index}_content"

        html = f'''
        <div class="model-list-item card border mb-3"
             data-index="{index}"
             data-title-template="{escape(title_template)}"
             data-field-name="{field_name}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">'''

        if collapsible:
            html += f'''
                    <button class="btn btn-link text-decoration-none p-0 text-start"
                            type="button"
                            data-bs-toggle="collapse"
                            data-bs-target="#{collapse_id}"
                            aria-expanded="{str(expanded).lower()}"
                            aria-controls="{collapse_id}">
                        <i class="bi bi-chevron-{'down' if expanded else 'right'} me-2"></i>
                        <i class="bi bi-card-list me-2"></i>
                        {escape(item_title)}
                    </button>'''
        else:
            html += f'''
                    <span>
                        <i class="bi bi-card-list me-2"></i>
                        {escape(item_title)}
                    </span>'''

        html += f'''
                </h6>
                <button type="button"
                        class="btn btn-outline-danger btn-sm remove-item-btn"
                        data-index="{index}"
                        data-field-name="{field_name}"
                        title="Remove this item">
                    <i class="bi bi-trash"></i>
                </button>
            </div>'''

        # Card body with collapse support
        if collapsible:
            html += f'''
            <div class="collapse {collapse_class} show" id="{collapse_id}">
                <div class="card-body">'''
        else:
            html += '''
            <div class="card-body">'''

        # Render fields in a responsive grid
        html += '<div class="row">'

        # Render each field in the schema
        properties = schema_def.get('properties', {})
        field_count = len([k for k in properties.keys() if not k.startswith('_')])

        # Determine column class based on field count
        if field_count <= 2:
            col_class = "col-12"
        elif field_count <= 4:
            col_class = "col-md-6"
        else:
            col_class = "col-lg-4 col-md-6"

        for field_key, field_schema in properties.items():
            if field_key.startswith('_'):
                continue

            field_value = item_data.get(field_key, '')
            input_name = f"{field_name}[{index}].{field_key}"

            html += f'''
                <div class="{col_class}">
                    {self._render_field(
                        input_name,
                        field_schema,
                        field_value,
                        None,  # error
                        [],   # required_fields
                        "vertical"  # layout
                    )}
                </div>'''

        html += '</div>'  # Close row

        if collapsible:
            html += '''
                </div>
            </div>'''  # Close card-body and collapse
        else:
            html += '</div>'  # Close card-body

        html += '</div>'  # Close card

        return html

    def _render_csrf_field(self) -> str:
        """Render CSRF token field."""
        # This would integrate with your CSRF protection system
        return '<input type="hidden" name="csrf_token" value="__CSRF_TOKEN__" />'

    def _render_layout_field(self, field_name: str, field_schema: Dict[str, Any], value: Any, error: Optional[str], ui_info: Dict[str, Any]) -> str:
        """
        Render a layout field by extracting and rendering its embedded form.

        Layout fields contain layout instances (VerticalFormLayout, HorizontalFormLayout, etc.)
        that have a 'form' attribute pointing to the FormModel class to render.
        """
        try:
            # The value should be a layout instance
            if value and hasattr(value, 'form'):
                # Get the form class from the layout instance
                form_class = value.form

                # Render the embedded form
                form_html = self.render_form_from_model(
                    form_class,
                    data={},  # Start with empty data
                    errors={},
                    layout="vertical",  # Use vertical layout for embedded forms
                    include_submit_button=False  # Don't include submit button in nested forms
                )

                # Wrap in a section with the field title
                section_title = field_schema.get('title', field_name.replace('_', ' ').title())
                help_text = ui_info.get('help_text', '')

                section_html = f"""
                <div class="layout-field-section mb-4">
                    <h5 class="layout-field-title">{section_title}</h5>
                    {f'<p class="text-muted">{help_text}</p>' if help_text else ''}
                    <div class="layout-field-content p-3 border rounded">
                        {form_html}
                    </div>
                </div>
                """

                return section_html
            else:
                # Fallback: try to get the form class from the field schema
                # This handles cases where the value might not be properly set
                return self._render_layout_field_fallback(field_name, field_schema, ui_info)

        except Exception as e:
            # Error handling: return a placeholder with error message
            return f"""
            <div class="layout-field-error alert alert-warning">
                <h5>{field_schema.get('title', field_name.replace('_', ' ').title())}</h5>
                <p>Error rendering layout field: {str(e)}</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
            </div>
            """

    def _render_layout_field_fallback(self, field_name: str, field_schema: Dict[str, Any], ui_info: Dict[str, Any]) -> str:
        """
        Fallback rendering for layout fields when the layout instance isn't available.

        This tries to determine the form to render based on the field name and known patterns.
        """
        # Map field names to their corresponding form classes
        # This is based on the LayoutDemonstrationForm structure
        form_mapping = {
            'vertical_tab': 'PersonalInfoForm',
            'horizontal_tab': 'ContactInfoForm',
            'tabbed_tab': 'PreferencesForm',
            'list_tab': 'TaskListForm'
        }

        form_name = form_mapping.get(field_name)
        if form_name:
            # Try to import and render the form
            try:
                # Import the form class - this is a simplified approach
                # In a real implementation, you'd want a more robust form resolution system
                if form_name == 'PersonalInfoForm':
                    from examples.shared_models import PersonalInfoForm as FormClass
                elif form_name == 'ContactInfoForm':
                    from examples.shared_models import ContactInfoForm as FormClass
                elif form_name == 'PreferencesForm':
                    from examples.shared_models import PreferencesForm as FormClass
                elif form_name == 'TaskListForm':
                    from examples.shared_models import TaskListForm as FormClass
                else:
                    raise ImportError(f"Unknown form: {form_name}")

                # Render the form
                form_html = self.render_form_from_model(
                    FormClass,
                    data={},
                    errors={},
                    layout="vertical",
                    include_submit_button=False
                )

                # Wrap in a section
                section_title = field_schema.get('title', field_name.replace('_', ' ').title())
                help_text = ui_info.get('help_text', '')

                return f"""
                <div class="layout-field-section mb-4">
                    <h5 class="layout-field-title">{section_title}</h5>
                    {f'<p class="text-muted">{help_text}</p>' if help_text else ''}
                    <div class="layout-field-content p-3 border rounded">
                        {form_html}
                    </div>
                </div>
                """

            except Exception as e:
                # If we can't import or render the form, show a placeholder
                return f"""
                <div class="layout-field-placeholder alert alert-info">
                    <h5>{field_schema.get('title', field_name.replace('_', ' ').title())}</h5>
                    <p>Layout demonstration: {form_name}</p>
                    <small class="text-muted">{ui_info.get('help_text', '')}</small>
                    <small class="text-danger d-block">Could not render: {str(e)}</small>
                </div>
                """
        else:
            # Unknown layout field
            return f"""
            <div class="layout-field-unknown alert alert-secondary">
                <h5>{field_schema.get('title', field_name.replace('_', ' ').title())}</h5>
                <p>Unknown layout field type</p>
                <small class="text-muted">{ui_info.get('help_text', '')}</small>
            </div>
            """

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
        return renderer.render_form_from_model(form_model_cls, data=form_data, errors=errors, **kwargs)

    # Use EnhancedFormRenderer for other frameworks
    renderer = EnhancedFormRenderer(framework=framework)
    return renderer.render_form_from_model(form_model_cls, data=form_data, errors=errors, layout=layout, **kwargs)


import asyncio


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
    # Handle SchemaFormValidationError
    if isinstance(errors, SchemaFormValidationError):
        error_dict = {err.get("name", ""): err.get("message", "") for err in errors.errors}
        errors = error_dict

    renderer = EnhancedFormRenderer(framework=framework)
    return await renderer.render_form_from_model_async(form_model_cls, data=form_data, errors=errors, layout=layout, **kwargs)
