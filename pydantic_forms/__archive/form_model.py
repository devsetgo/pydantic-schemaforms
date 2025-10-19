"""
form_model.py
=============

This module provides a base class `FormModel` for defining forms using Pydantic models,
with support for generating HTML forms using the pydantic-forms input components.
It provides an abstraction similar to React JSON Schema Form but for pure Python HTML generation.

Key Features:
-------------
- Define forms as Pydantic models, with field-level UI hints via `Field(..., json_schema_extra={...})`.
- Supports a class-level `UISchema` inner class for additional UI customizations.
- Maps Pydantic fields to appropriate HTML input components automatically.
- Validates allowed input types for each field type.
- Provides form rendering with layouts, validation, and framework support.
- Generates example form data for preview/testing.

Usage:
------
    from pydantic import Field
    from pydantic_forms.form_model import FormModel

    class MyForm(FormModel):
        name: str = Field(..., description="Your name", json_schema_extra={"ui_widget": "text"})
        age: int = Field(..., description="Your age", json_schema_extra={"ui_widget": "number"})
        email: str = Field(..., description="Email address", json_schema_extra={"ui_widget": "email"})
        password: str = Field(..., description="Password", json_schema_extra={"ui_widget": "password"})
        bio: str = Field(..., description="Tell us about yourself", json_schema_extra={"ui_widget": "textarea"})

        class UIConfig:
            framework = "bootstrap"
            name = {"autofocus": True}
            age = {"min": 18, "max": 120}

    # Generate HTML form
    form_html = MyForm.render_form()

    # Generate form with data and errors
    form_html = MyForm.render_form(
        data={"name": "John", "age": 25},
        errors={"email": "Invalid email format"}
    )

See Also:
---------
- inputs/ modules for available input components
- layouts.py for form layout options
- validation.py for form validation
"""

from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel

# Import input components
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
    SubmitInput,
    build_label,
    build_error_message,
    build_help_text,
)
from .layouts import HorizontalLayout, VerticalLayout, GridLayout

# Widget mapping for different field types
INPUT_WIDGETS_BY_TYPE: Dict[str, Set[str]] = {
    # String widgets
    "string": {
        "text",  # default text input
        "textarea",  # multi-line text area
        "password",  # password input
        "email",  # email input
        "url",  # URL input
        "color",  # color picker
        "date",  # date picker
        "datetime",  # datetime picker
        "time",  # time picker
        "search",  # search input
        "tel",  # telephone input
        "hidden",  # hidden input
        "file",  # file upload
    },
    # Number widgets
    "number": {
        "number",  # number input
        "range",  # slider
        "hidden",  # hidden input
    },
    # Integer widgets
    "integer": {
        "number",  # number input
        "range",  # slider
        "hidden",  # hidden input
    },
    # Boolean widgets
    "boolean": {
        "checkbox",  # checkbox (default)
        "hidden",  # hidden input
    },
    # Array widgets (for enums/choices)
    "array": {
        "select",  # multi-select dropdown
        "checkbox",  # checkbox group
        "radio",  # radio group (single select)
    },
}


def _get_field_type_from_annotation(annotation: Any) -> str:
    """Map a Pydantic annotation to its corresponding type string."""
    if annotation in [str]:
        return "string"
    if annotation in [int]:
        return "integer"
    if annotation in [float]:
        return "number"
    if annotation in [bool]:
        return "boolean"
    if hasattr(annotation, "__origin__"):
        if annotation.__origin__ is list:
            return "array"
        elif annotation.__origin__ is Union:
            # Handle Optional[T] (Union[T, None])
            args = getattr(annotation, "__args__", ())
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return _get_field_type_from_annotation(non_none_args[0])
    return "string"


def _validate_widget_for_type(widget: str, field_type: str, field_name: str) -> None:
    """Validate that a widget is allowed for the given field type."""
    allowed_widgets = INPUT_WIDGETS_BY_TYPE.get(field_type, set())
    if widget not in allowed_widgets:
        raise ValueError(
            f"Widget '{widget}' is not valid for field '{field_name}' of type '{field_type}'. "
            f"Allowed widgets: {sorted(allowed_widgets)}"
        )


class FormField:
    """Represents a single form field with its configuration."""

    def __init__(
        self,
        name: str,
        field_type: str,
        widget: str,
        label: Optional[str] = None,
        required: bool = False,
        value: Any = None,
        help_text: Optional[str] = None,
        error: Optional[str] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        self.name = name
        self.field_type = field_type
        self.widget = widget
        self.label = label
        self.required = required
        self.value = value
        self.help_text = help_text
        self.error = error
        self.options = options or []
        self.attrs = kwargs

        # Validate widget for field type
        _validate_widget_for_type(widget, field_type, name)

    def render(self, framework: str = "bootstrap") -> str:
        """Render the field to HTML using the appropriate input component."""
        # Get the input component class
        input_class = self._get_input_class()
        if not input_class:
            raise ValueError(f"No input component found for widget '{self.widget}'")

        # Create input instance
        input_instance = input_class()

        # Prepare render kwargs
        render_kwargs = {
            "name": self.name,
            "value": self.value,
            "required": self.required,
            **self.attrs,
        }

        # Add options for select/radio/checkbox groups
        if (
            self.options
            and hasattr(input_instance, "render")
            and "options" in input_instance.render.__code__.co_varnames
        ):
            render_kwargs["options"] = self.options

        # Render the input
        input_html = input_instance.render(**render_kwargs)

        # Build complete field HTML with label, help text, and error
        parts = []

        # Add label
        if self.label is not False:
            label_html = build_label(self.name, self.label, self.required)
            parts.append(label_html)

        # Add input
        parts.append(input_html)

        # Add help text
        if self.help_text:
            help_html = build_help_text(self.name, self.help_text)
            parts.append(help_html)

        # Add error message
        if self.error:
            error_html = build_error_message(self.name, self.error)
            parts.append(error_html)

        return "\n".join(parts)

    def _get_input_class(self):
        """Get the appropriate input component class for this field's widget."""
        widget_map = {
            "text": TextInput,
            "password": PasswordInput,
            "email": EmailInput,
            "url": URLInput,
            "search": SearchInput,
            "tel": TelInput,
            "textarea": TextArea,
            "number": NumberInput,
            "range": RangeInput,
            "checkbox": CheckboxInput,
            "select": SelectInput,
            "radio": RadioGroup,
            "date": DateInput,
            "datetime": DatetimeInput,
            "time": TimeInput,
            "month": MonthInput,
            "week": WeekInput,
            "file": FileInput,
            "color": ColorInput,
            "hidden": HiddenInput,
        }
        return widget_map.get(self.widget)


class FormModel(BaseModel):
    """
    Base class for form models. Provides UI schema via field extra kwargs and optional UIConfig inner class.

    Inherit from this class to define your form as a Pydantic model, and use the provided
    class methods to generate HTML forms using pydantic-forms input components.
    """

    @classmethod
    def _extract_ui_config(cls) -> Dict[str, Any]:
        """Extract UI configuration from the optional UIConfig inner class."""
        if hasattr(cls, "UIConfig"):
            ui_config = getattr(cls, "UIConfig", None)
            if ui_config:
                if isinstance(ui_config, dict):
                    return ui_config
                elif hasattr(ui_config, "__dict__"):
                    return {k: v for k, v in ui_config.__dict__.items() if not k.startswith("__")}
        return {}

    @classmethod
    def _get_field_widget(
        cls, field_name: str, field_type: str, field_info: Any, ui_config: Dict[str, Any]
    ) -> str:
        """Determine the appropriate widget for a field."""
        # Check field-level json_schema_extra for ui_widget
        extras = getattr(field_info, "json_schema_extra", {}) or {}
        if extras and "ui_widget" in extras:
            return extras["ui_widget"]

        # Check UIConfig for field-specific widget
        field_config = ui_config.get(field_name, {})
        if isinstance(field_config, dict) and "widget" in field_config:
            return field_config["widget"]

        # Auto-detect widget based on field type and name
        if field_type == "string":
            if "password" in field_name.lower():
                return "password"
            elif "email" in field_name.lower():
                return "email"
            elif "url" in field_name.lower() or "website" in field_name.lower():
                return "url"
            elif "phone" in field_name.lower() or "tel" in field_name.lower():
                return "tel"
            elif "search" in field_name.lower():
                return "search"
            elif (
                "bio" in field_name.lower()
                or "description" in field_name.lower()
                or "comment" in field_name.lower()
            ):
                return "textarea"
            else:
                return "text"
        elif field_type == "integer" or field_type == "number":
            return "number"
        elif field_type == "boolean":
            return "checkbox"
        elif field_type == "array":
            return "select"  # Default to multi-select for arrays
        else:
            return "text"

    @classmethod
    def get_form_fields(
        cls, data: Optional[Dict[str, Any]] = None, errors: Optional[Dict[str, str]] = None
    ) -> List[FormField]:
        """Generate FormField instances for all model fields."""
        ui_config = cls._extract_ui_config()
        data = data or {}
        errors = errors or {}
        fields = []

        for field_name, field_info in cls.model_fields.items():
            # Get field type
            field_type = _get_field_type_from_annotation(field_info.annotation)

            # Get widget
            widget = cls._get_field_widget(field_name, field_type, field_info, ui_config)

            # Get field configuration
            field_config = ui_config.get(field_name, {})
            extras = getattr(field_info, "json_schema_extra", {}) or {}

            # Build field
            field = FormField(
                name=field_name,
                field_type=field_type,
                widget=widget,
                label=field_config.get("label")
                or getattr(field_info, "title", None)
                or field_name.replace("_", " ").title(),
                required=(
                    getattr(field_info, "is_required", lambda: False)()
                    if hasattr(field_info, "is_required")
                    else field_info.is_required()
                ),
                value=data.get(field_name),
                help_text=field_config.get("help_text") or getattr(field_info, "description", None),
                error=errors.get(field_name),
                **{**extras, **field_config},
            )
            fields.append(field)

        return fields

    @classmethod
    def render_form(
        cls,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, str]] = None,
        framework: str = "bootstrap",
        layout: str = "vertical",
        form_attrs: Optional[Dict[str, str]] = None,
        submit_button: bool = True,
        submit_text: str = "Submit",
    ) -> str:
        """Render the complete form as HTML."""
        ui_config = cls._extract_ui_config()
        framework = ui_config.get("framework", framework)
        layout = ui_config.get("layout", layout)
        form_attrs = form_attrs or {}

        # Get form fields
        fields = cls.get_form_fields(data, errors)

        # Render each field
        field_htmls = []
        for field in fields:
            field_html = field.render(framework)
            field_htmls.append(field_html)

        # Apply layout
        if layout == "horizontal":
            layout_instance = HorizontalLayout()
        elif layout == "grid":
            layout_instance = GridLayout()
        else:  # vertical (default)
            layout_instance = VerticalLayout()

        content = layout_instance.render(content="\n".join(field_htmls))

        # Add submit button
        if submit_button:
            submit_input = SubmitInput()
            submit_html = submit_input.render(value=submit_text)
            content += "\n" + submit_html

        # Build form tag
        form_attrs_str = " ".join([f'{k}="{v}"' for k, v in form_attrs.items()])
        form_html = f"<form {form_attrs_str}>\n{content}\n</form>"

        return form_html

    @classmethod
    def get_example_form_data(cls) -> Dict[str, Any]:
        """Generate example form data for preview/testing."""
        example = {}
        for field_name, field_info in cls.model_fields.items():
            field_type = _get_field_type_from_annotation(field_info.annotation)

            if field_type == "string":
                if "email" in field_name.lower():
                    example[field_name] = "example@email.com"
                elif "url" in field_name.lower() or "website" in field_name.lower():
                    example[field_name] = "https://example.com"
                elif "phone" in field_name.lower() or "tel" in field_name.lower():
                    example[field_name] = "+1-555-123-4567"
                else:
                    example[field_name] = "Example text"
            elif field_type == "integer":
                example[field_name] = 42
            elif field_type == "number":
                example[field_name] = 3.14
            elif field_type == "boolean":
                example[field_name] = True
            elif field_type == "array":
                example[field_name] = ["option1", "option2"]
            else:
                example[field_name] = None

        return example


# Convenience aliases
FormBase = FormModel  # Alternative name for consistency with your request
