"""
Base classes and utilities for form inputs with Python 3.14 template strings.
"""

from typing import Dict, Any, Optional, List
from html import escape


def render_template(template_obj) -> str:
    """Render a Python 3.14 template string to final HTML."""
    if hasattr(template_obj, 'strings') and hasattr(template_obj, 'values'):
        # This is a Template object from t'...' syntax
        result = ''
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
        "id", "name", "class", "style", "title", "lang", "dir",
        "tabindex", "accesskey", "contenteditable", "draggable",
        "hidden", "spellcheck", "translate", "role", "aria-label",
        "aria-labelledby", "aria-describedby", "aria-hidden", "aria-expanded",
        "aria-controls", "aria-haspopup", "aria-invalid", "aria-required",
        "data-*"  # Allow all data attributes
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
        "value", "placeholder", "required", "disabled", "readonly",
        "autofocus", "autocomplete", "form", "formaction", "formenctype",
        "formmethod", "formnovalidate", "formtarget", "list",
        "maxlength", "minlength", "pattern", "size", "type",
        "accept", "alt", "checked", "dirname", "max", "min", "multiple",
        "step", "wrap", "rows", "cols", "inputmode"
    ]


def build_label(field_name: str, label: Optional[str] = None, required: bool = False) -> str:
    """Build label element using Python 3.14 template strings."""
    display_label = label or field_name.replace("_", " ").title()
    required_indicator = " *" if required else ""
    
    template = t'<label for="{field_name}">{display_label}{required_indicator}</label>'
    return render_template(template)


def build_error_message(field_name: str, error: str) -> str:
    """Build error message element using Python 3.14 template strings."""
    template = t'<div id="{field_name}-error" class="error-message" role="alert">{error}</div>'
    return render_template(template)


def build_help_text(field_name: str, help_text: str) -> str:
    """Build help text element using Python 3.14 template strings."""
    template = t'<div id="{field_name}-help" class="help-text">{help_text}</div>'
    return render_template(template)

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import html
import re


class BaseInput(ABC):
    """
    Abstract base class for all form inputs.
    Provides common functionality for HTML attribute handling and template rendering.
    """
    
    # Valid HTML attributes for this input type
    valid_attributes: List[str] = [
        "name", "id", "class", "style", "title", "dir", "lang", 
        "tabindex", "accesskey", "contenteditable", "draggable",
        "hidden", "spellcheck", "translate"
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
            if attr in self.valid_attributes or attr.startswith("data-") or attr.startswith("aria-"):
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
                    escaped_value = str(value).replace('"', '&quot;')
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
        "type", "value", "placeholder", "required", "disabled", "readonly",
        "maxlength", "minlength", "size", "pattern", "autocomplete",
        "autofocus", "form", "formaction", "formenctype", "formmethod",
        "formnovalidate", "formtarget", "list", "multiple"
    ]


class NumericInput(FormInput):
    """
    Base class for numeric inputs with additional numeric attributes.
    """
    
    valid_attributes = FormInput.valid_attributes + [
        "min", "max", "step"
    ]


class FileInputBase(FormInput):
    """
    Base class for file inputs with file-specific attributes.
    """
    
    valid_attributes = FormInput.valid_attributes + [
        "accept", "capture"
    ]


class SelectInputBase(BaseInput):
    """
    Base class for selection inputs (select, radio, checkbox).
    """
    
    valid_attributes = BaseInput.valid_attributes + [
        "name", "value", "checked", "selected", "disabled", "required",
        "form", "multiple", "size"
    ]



