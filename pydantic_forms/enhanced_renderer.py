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

        form_parts = [self._build_form_tag(form_attrs)]

        # Add CSRF if requested
        if include_csrf:
            form_parts.append(self._render_csrf_field())

        # Get fields and sort by UI order if specified
        fields = list(schema["properties"].items())
        fields.sort(key=lambda x: x[1].get("ui", {}).get("order", 999))
        required_fields = schema.get("required", [])

        # Render fields based on layout
        if layout == "tabbed":
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
                    input_html = input_component.render(options=formatted_options, **field_attrs)
                else:
                    input_html = f"<!-- Warning: No options provided for {ui_element} field '{field_name}' -->"
            else:
                # Regular input rendering
                input_html = input_component.render(**field_attrs)

            if input_html is None:
                input_html = f"<!-- Error: {ui_element} input returned None -->"
        except Exception as e:
            input_html = f"<!-- Error rendering {ui_element}: {str(e)} -->"

        # Build field wrapper
        return self._wrap_field(
            field_name=field_name,
            label=field_schema.get("title", field_name.replace("_", " ").title()),
            input_html=input_html,
            help_text=ui_info.get("help_text") or field_schema.get("description"),
            error=error,
            required=field_name in (required_fields or []),
            layout=layout,
        )

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

    def _render_csrf_field(self) -> str:
        """Render CSRF token field."""
        # This would integrate with your CSRF protection system
        return '<input type="hidden" name="csrf_token" value="__CSRF_TOKEN__" />'

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

    renderer = EnhancedFormRenderer(framework=framework)
    return renderer.render_form_from_model(form_model_cls, data=form_data, errors=errors, layout=layout, **kwargs)


import asyncio
from typing import Awaitable


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
