"""
Base classes and utilities for form inputs with Python 3.14 template strings.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from html import escape


# Add t() fallback for Python <3.14 compatibility
def t(template: str) -> str:
    """Fallback for Python 3.14 template strings."""
    return template


def render_template(template_obj) -> str:
    """Render a Python 3.14 template string to final HTML."""
    if hasattr(template_obj, "strings") and hasattr(template_obj, "values"):
        # This is a Template object from t'...' syntax
        result = ""
        strings = template_obj.strings
        values = template_obj.values

        for i, string_part in enumerate(strings):
            result += string_part
            if i < len(values):
                result += str(values[i])

        return result
    else:
        # This is already a string
        return str(template_obj)


class BaseInput:
    """Base class for all form inputs."""

    # Basic HTML attributes that are valid for all input types
    valid_attributes = [
        "id",
        "name",
        "class",
        "style",
        "title",
        "lang",
        "dir",
        "tabindex",
        "accesskey",
        "contenteditable",
        "draggable",
        "hidden",
        "spellcheck",
        "translate",
        "role",
        "aria-label",
        "aria-labelledby",
        "aria-describedby",
        "aria-hidden",
        "aria-expanded",
        "aria-controls",
        "aria-haspopup",
        "aria-invalid",
        "aria-required",
        "data-*",  # Allow all data attributes
    ]

    def validate_attributes(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize input attributes."""
        validated = {}

        for key, value in kwargs.items():
            # Allow data-* attributes
            if key.startswith("data-") or key in self.valid_attributes:
                # Handle boolean attributes
                if isinstance(value, bool):
                    if value:
                        validated[key] = key  # HTML boolean attribute style
                else:
                    validated[key] = escape(str(value))
            else:
                # For now, allow unknown attributes with a warning
                validated[key] = escape(str(value))

        return validated

    def _build_attributes_string(self, attrs: Dict[str, Any]) -> str:
        """Build HTML attributes string from dictionary."""
        if not attrs:
            return ""

        parts = []
        for key, value in attrs.items():
            if isinstance(value, bool):
                if value:
                    parts.append(key)
            elif value is not None:
                parts.append(f'{key}="{value}"')

        return " ".join(parts)


class FormInput(BaseInput):
    """Base class for form input elements with form-specific attributes."""

    # Form-specific attributes
    valid_attributes = BaseInput.valid_attributes + [
        "value",
        "placeholder",
        "required",
        "disabled",
        "readonly",
        "autofocus",
        "autocomplete",
        "form",
        "formaction",
        "formenctype",
        "formmethod",
        "formnovalidate",
        "formtarget",
        "list",
        "maxlength",
        "minlength",
        "pattern",
        "size",
        "type",
        "accept",
        "alt",
        "checked",
        "dirname",
        "max",
        "min",
        "multiple",
        "step",
        "wrap",
        "rows",
        "cols",
        "inputmode",
    ]


def build_label(
    field_name: str,
    label: Optional[str] = None,
    required: bool = False,
    icon: Optional[str] = None,
    framework: str = "bootstrap",
) -> str:
    """Build label element with optional icon support."""
    display_label = label or field_name.replace("_", " ").title()
    required_indicator = " *" if required else ""

    # Add icon if provided
    icon_html = ""
    if icon:
        if framework == "bootstrap":
            # Handle both with and without bi bi- prefix
            icon_class = icon if icon.startswith("bi bi-") else f"bi bi-{icon}"
            icon_html = f'<i class="{icon_class}"></i> '
        elif framework == "material":
            icon_html = f'<i class="material-icons">{icon}</i> '
        elif framework == "fontawesome":
            icon_class = icon if icon.startswith("fas fa-") else f"fas fa-{icon}"
            icon_html = f'<i class="{icon_class}"></i> '

    return f'<label for="{escape(field_name)}">{icon_html}{escape(display_label)}{required_indicator}</label>'


def build_error_message(field_name: str, error: str) -> str:
    """Build error message element."""
    return f'<div id="{escape(field_name)}-error" class="error-message" role="alert">{escape(error)}</div>'


def build_help_text(field_name: str, help_text: str) -> str:
    """Build help text element."""
    return f'<div id="{escape(field_name)}-help" class="help-text">{escape(help_text)}</div>'


class BaseInput(ABC):
    """
    Abstract base class for all form inputs.
    Provides common functionality for HTML attribute handling and template rendering.
    """

    # Valid HTML attributes for this input type
    valid_attributes: List[str] = [
        "name",
        "id",
        "class",
        "style",
        "title",
        "dir",
        "lang",
        "tabindex",
        "accesskey",
        "contenteditable",
        "draggable",
        "hidden",
        "spellcheck",
        "translate",
    ]

    @abstractmethod
    def get_input_type(self) -> str:
        """Return the HTML input type for this input."""
        pass

    def validate_attributes(self, **kwargs) -> Dict[str, Any]:
        """
        Validate and filter attributes for this input type.
        Removes invalid attributes and formats values properly.
        """
        validated = {}

        # Always include basic required attributes
        validated["name"] = kwargs.get("name", "")
        validated["id"] = kwargs.get("id", kwargs.get("name", ""))

        # Process all provided attributes
        for attr, value in kwargs.items():
            if (
                attr in self.valid_attributes
                or attr.startswith("data-")
                or attr.startswith("aria-")
            ):
                if value is not None and value != "":
                    validated[attr] = self._format_attribute_value(attr, value)

        return validated

    def _format_attribute_value(self, attr: str, value: Any) -> str:
        """Format attribute values for HTML output."""
        if isinstance(value, bool):
            # Boolean attributes in HTML5
            return attr if value else ""
        elif isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value)
        else:
            return str(value)

    def _build_attributes_string(self, attrs: Dict[str, Any]) -> str:
        """Build HTML attributes string from dictionary."""
        attr_parts = []

        for attr, value in attrs.items():
            if value and value != "":
                if isinstance(value, bool) and value:
                    attr_parts.append(attr)
                else:
                    # Escape quotes in attribute values
                    escaped_value = str(value).replace('"', "&quot;")
                    attr_parts.append(f'{attr}="{escaped_value}"')

        return " ".join(attr_parts)

    @abstractmethod
    def render(self, **kwargs) -> str:
        """
        Render the input as HTML string.
        Must be implemented by subclasses using Python 3.14 template strings.
        """
        pass


class FormInput(BaseInput):
    """
    Standard form input with enhanced attribute support.
    Base class for most HTML input types using Python 3.14 template strings.
    """

    # Extended list of valid attributes for form inputs
    valid_attributes = BaseInput.valid_attributes + [
        "type",
        "value",
        "placeholder",
        "required",
        "disabled",
        "readonly",
        "maxlength",
        "minlength",
        "size",
        "pattern",
        "autocomplete",
        "autofocus",
        "form",
        "formaction",
        "formenctype",
        "formmethod",
        "formnovalidate",
        "formtarget",
        "list",
        "multiple",
    ]

    def render(self, **kwargs) -> str:
        """Render form input."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return f"<input {attributes_str} />"

    def render_with_label(self, label: Optional[str] = None, help_text: Optional[str] = None,
                         error: Optional[str] = None, icon: Optional[str] = None, framework: str = "bootstrap", **kwargs) -> str:
        """Render input with label, help text, error message, and icon support."""
        field_name = kwargs.get("name", "")
        required = kwargs.get("required", False)

        parts = []

        # Add label (without icon, since icon will be outside)
        if label is not False:  # Allow explicit False to skip label
            label_html = build_label(field_name, label, required, None, framework)  # No icon in label
            parts.append(render_template(label_html))

        # Create input wrapper with icon if provided
        if icon:
            # Start input group with icon outside on the left
            if framework == "bootstrap":
                # Handle both with and without bi bi- prefix
                icon_class = icon if icon.startswith("bi bi-") else f"bi bi-{icon}"
                icon_html = f'<span class="input-icon"><i class="{icon_class}"></i></span>'
            elif framework == "material":
                icon_html = f'<span class="input-icon"><i class="material-icons">{icon}</i></span>'
            elif framework == "fontawesome":
                icon_class = icon if icon.startswith("fas fa-") else f"fas fa-{icon}"
                icon_html = f'<span class="input-icon"><i class="{icon_class}"></i></span>'
            else:
                icon_html = f'<span class="input-icon">{icon}</span>'

            # Start wrapper div for icon + input
            parts.append('<div class="input-with-icon">')
            parts.append(icon_html)

        # Add input
        if help_text:
            kwargs["aria-describedby"] = f"{field_name}-help"
        if error:
            kwargs["aria-invalid"] = "true"
            kwargs["aria-describedby"] = f"{field_name}-error"

        parts.append(self.render(**kwargs))

        # Close wrapper if icon was added
        if icon:
            parts.append('</div>')

        # Add help text
        if help_text:
            help_html = build_help_text(field_name, help_text)
            parts.append(render_template(help_html))

        # Add error message
        if error:
            error_html = build_error_message(field_name, error)
            parts.append(render_template(error_html))

        return "\n".join(parts)


class NumericInput(FormInput):
    """
    Base class for numeric inputs with additional numeric attributes.
    """

    valid_attributes = FormInput.valid_attributes + ["min", "max", "step"]

    def render(self, **kwargs) -> str:
        """Render numeric input."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return f"<input {attributes_str} />"


class FileInputBase(FormInput):
    """
    Base class for file inputs with file-specific attributes.
    """

    valid_attributes = FormInput.valid_attributes + ["accept", "capture"]


class SelectInputBase(BaseInput):
    """
    Base class for selection inputs (select, radio, checkbox).
    """

    valid_attributes = BaseInput.valid_attributes + [
        "name",
        "value",
        "checked",
        "selected",
        "disabled",
        "required",
        "form",
        "multiple",
        "size",
    ]

    def render_with_label(
        self,
        label: Optional[str] = None,
        help_text: Optional[str] = None,
        error: Optional[str] = None,
        icon: Optional[str] = None,
        framework: str = "bootstrap",
        options: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> str:
        """
        Render the input with its label, help text, error message, and optional icon.
        This method is required for all input components to work with the form renderer.

        Args:
            label: Label text for the input
            help_text: Help text to display
            error: Error message to display
            icon: Icon name (will be mapped to framework)
            framework: UI framework being used
            options: Options for select/radio inputs
            **kwargs: Additional attributes for the input

        Returns:
            Complete HTML for the input with label and decorations
        """
        from ..icon_mapping import map_icon_for_framework

        # Ensure we have an input type
        self.get_input_type()

        # Map icon to appropriate framework if provided
        if icon:
            icon = map_icon_for_framework(icon, framework)

        # For selection inputs, we need options
        if hasattr(self, 'render') and options is not None:
            input_html = self.render(options=options, **kwargs)
        else:
            # Fallback rendering
            attrs = self.validate_attributes(**kwargs)
            attributes_str = self._build_attributes_string(attrs)
            input_html = f'<select {attributes_str}></select>'

        # Build the complete field HTML based on framework
        field_parts = []

        if framework == "bootstrap":
            # Bootstrap styling
            field_parts.append('<div class="mb-3">')

            if label:
                field_parts.append(f'<label for="{kwargs.get("id", "")}" class="form-label">{escape(label)}</label>')

            if icon:
                field_parts.append('<div class="input-group">')
                field_parts.append(f'<span class="input-group-text"><i class="bi bi-{icon}"></i></span>')
                field_parts.append(input_html)
                field_parts.append('</div>')
            else:
                field_parts.append(input_html)

            if help_text:
                field_parts.append(f'<div class="form-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="invalid-feedback d-block">{escape(error)}</div>')

            field_parts.append('</div>')

        elif framework == "material":
            # Material Design styling
            field_parts.append('<div class="md-field">')

            if icon:
                field_parts.append('<div class="md-field-with-icon">')
                field_parts.append(f'<span class="md-icon material-icons">{icon}</span>')
                field_parts.append('<div class="md-input-wrapper">')

            field_parts.append(input_html)

            if label:
                field_parts.append(f'<label class="md-floating-label" for="{kwargs.get("id", "")}">{escape(label)}</label>')

            if icon:
                field_parts.append('</div>')  # Close md-input-wrapper
                field_parts.append('</div>')  # Close md-field-with-icon

            if help_text:
                field_parts.append(f'<div class="md-help-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="md-error-text">{escape(error)}</div>')

            field_parts.append('</div>')

        else:
            # Basic/no framework styling
            field_parts.append('<div class="field">')

            if label:
                field_parts.append(f'<label for="{kwargs.get("id", "")}">{escape(label)}</label>')

            if icon:
                field_parts.append(f'<div class="input-with-icon"><span class="input-icon">{icon}</span>')
                field_parts.append(input_html)
                field_parts.append('</div>')
            else:
                field_parts.append(input_html)

            if help_text:
                field_parts.append(f'<div class="help-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="error-message">{escape(error)}</div>')

            field_parts.append('</div>')

        return '\n'.join(field_parts)
