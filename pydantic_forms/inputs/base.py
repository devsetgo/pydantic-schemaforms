"""
Base classes and utilities for form inputs with Python 3.14 template strings.
"""

from abc import ABC, abstractmethod
from html import escape
from typing import Any, Dict, List, Optional, Tuple


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


class BaseInput(ABC):
    """Common attribute handling + rendering contract for all input widgets."""

    ui_element: Optional[str] = None
    ui_element_aliases: Tuple[str, ...] = ()
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
    ]

    @abstractmethod
    def get_input_type(self) -> str:
        """Return the HTML input type for concrete input classes."""

    def validate_attributes(self, **kwargs) -> Dict[str, Any]:
        """Validate and sanitize input attributes consistently across subclasses."""
        validated: Dict[str, Any] = {}

        name = kwargs.get("name")
        if name:
            validated["name"] = escape(str(name))

        element_id = kwargs.get("id", name)
        if element_id:
            validated["id"] = escape(str(element_id))

        for attr, value in kwargs.items():
            if attr in {"name", "id"}:
                continue

            if attr in self.valid_attributes or attr.startswith("data-") or attr.startswith("aria-"):
                formatted = self._format_attribute_value(attr, value)
                if formatted:
                    validated[attr] = formatted
            else:
                if value is not None:
                    validated[attr] = escape(str(value))

        return validated

    def _format_attribute_value(self, attr: str, value: Any) -> str:
        if isinstance(value, bool):
            return attr if value else ""
        if value is None:
            return ""
        if isinstance(value, (list, tuple, set)):
            return " ".join(str(v) for v in value if v is not None)
        return str(value)

    def _build_attributes_string(self, attrs: Dict[str, Any]) -> str:
        parts: List[str] = []
        for key, value in attrs.items():
            if isinstance(value, bool):
                if value:
                    parts.append(key)
            elif value not in (None, ""):
                escaped_value = str(value).replace('"', "&quot;")
                parts.append(f'{key}="{escaped_value}"')
        return " ".join(parts)

    @abstractmethod
    def render(self, **kwargs) -> str:
        """Concrete inputs must implement HTML rendering."""


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

    def render_with_label(
        self,
        label: Optional[str] = None,
        help_text: Optional[str] = None,
        error: Optional[str] = None,
        icon: Optional[str] = None,
        framework: str = "bootstrap",
        options: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
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

        # Map icon to appropriate framework if provided
        if icon:
            icon = map_icon_for_framework(icon, framework)

        # Get the input HTML - call the render method of the specific input type
        if hasattr(self, "render"):
            if options is not None:
                input_html = self.render(options=options, **kwargs)
            else:
                input_html = self.render(**kwargs)
        else:
            # Fallback rendering
            attrs = self.validate_attributes(**kwargs)
            input_type = getattr(self, "get_input_type", lambda: "text")()
            attrs["type"] = input_type
            attributes_str = self._build_attributes_string(attrs)
            input_html = f"<input {attributes_str} />"

        # Build the complete field HTML based on framework
        field_parts = []

        if framework == "bootstrap":
            # Bootstrap styling
            if label:
                label_html = build_label(
                    kwargs.get("name", "field"),
                    label,
                    kwargs.get("required", False),
                    icon,
                    framework,
                )
                field_parts.append(label_html)

            field_parts.append(input_html)

            if help_text:
                field_parts.append(f'<div class="form-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="invalid-feedback d-block">{escape(error)}</div>')
        else:
            # Material Design or other frameworks
            if label:
                label_html = build_label(
                    kwargs.get("name", "field"),
                    label,
                    kwargs.get("required", False),
                    icon,
                    framework,
                )
                field_parts.append(label_html)

            field_parts.append(input_html)

            if help_text:
                field_parts.append(f'<div class="help-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="error-text">{escape(error)}</div>')

        return "\n".join(field_parts)


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
        **kwargs,
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
        if hasattr(self, "render") and options is not None:
            input_html = self.render(options=options, **kwargs)
        else:
            # Fallback rendering
            attrs = self.validate_attributes(**kwargs)
            attributes_str = self._build_attributes_string(attrs)
            input_html = f"<select {attributes_str}></select>"

        # Build the complete field HTML based on framework
        field_parts = []

        if framework == "bootstrap":
            # Bootstrap styling
            field_parts.append('<div class="mb-3">')

            if label:
                field_parts.append(
                    f'<label for="{kwargs.get("id", "")}" class="form-label">{escape(label)}</label>'
                )

            if icon:
                field_parts.append('<div class="input-group">')
                field_parts.append(
                    f'<span class="input-group-text"><i class="bi bi-{icon}"></i></span>'
                )
                field_parts.append(input_html)
                field_parts.append("</div>")
            else:
                field_parts.append(input_html)

            if help_text:
                field_parts.append(f'<div class="form-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="invalid-feedback d-block">{escape(error)}</div>')

            field_parts.append("</div>")

        elif framework == "material":
            # Material Design styling
            field_parts.append('<div class="md-field">')

            if icon:
                field_parts.append('<div class="md-field-with-icon">')
                field_parts.append(f'<span class="md-icon material-icons">{icon}</span>')
                field_parts.append('<div class="md-input-wrapper">')

            field_parts.append(input_html)

            if label:
                field_parts.append(
                    f'<label class="md-floating-label" for="{kwargs.get("id", "")}">{escape(label)}</label>'
                )

            if icon:
                field_parts.append("</div>")  # Close md-input-wrapper
                field_parts.append("</div>")  # Close md-field-with-icon

            if help_text:
                field_parts.append(f'<div class="md-help-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="md-error-text">{escape(error)}</div>')

            field_parts.append("</div>")

        else:
            # Basic/no framework styling
            field_parts.append('<div class="field">')

            if label:
                field_parts.append(f'<label for="{kwargs.get("id", "")}">{escape(label)}</label>')

            if icon:
                field_parts.append(
                    f'<div class="input-with-icon"><span class="input-icon">{icon}</span>'
                )
                field_parts.append(input_html)
                field_parts.append("</div>")
            else:
                field_parts.append(input_html)

            if help_text:
                field_parts.append(f'<div class="help-text">{escape(help_text)}</div>')

            if error:
                field_parts.append(f'<div class="error-message">{escape(error)}</div>')

            field_parts.append("</div>")

        return "\n".join(field_parts)
