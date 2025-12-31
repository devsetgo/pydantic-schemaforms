"""
Text input components using Python 3.14 template strings.
Includes TextInput, PasswordInput, EmailInput, TextArea, and SearchInput.
"""

from typing import Optional

from .base import FormInput, render_template


class TextInput(FormInput):
    """Standard text input field."""

    ui_element = "text"

    def get_input_type(self) -> str:
        return "text"

    def render(self, **kwargs) -> str:
        """Render text input."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return f"<input {attributes_str} />"


class PasswordInput(FormInput):
    """Password input field with masking."""

    ui_element = "password"

    def get_input_type(self) -> str:
        return "password"

    def render(self, **kwargs) -> str:
        """Render password input using Python 3.14 template strings."""
        # Remove autocomplete by default for security
        if "autocomplete" not in kwargs:
            kwargs["autocomplete"] = "new-password"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)


class EmailInput(FormInput):
    """Email input field with built-in validation."""

    ui_element = "email"

    def get_input_type(self) -> str:
        return "email"

    def render(self, **kwargs) -> str:
        """Render email input using Python 3.14 template strings."""
        # Add input mode for mobile keyboards
        if "inputmode" not in kwargs:
            kwargs["inputmode"] = "email"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)


class SearchInput(FormInput):
    """Search input field with search-specific behavior."""

    ui_element = "search"

    def get_input_type(self) -> str:
        return "search"

    def render(self, **kwargs) -> str:
        """Render search input using Python 3.14 template strings."""
        # Add input mode for mobile keyboards
        if "inputmode" not in kwargs:
            kwargs["inputmode"] = "search"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)


class TextArea(FormInput):
    """Multi-line text input area."""

    ui_element = "textarea"

    valid_attributes = FormInput.valid_attributes + ["rows", "cols", "wrap", "resize"]

    def get_input_type(self) -> str:
        return "textarea"  # Not a real input type, but used for identification

    def render(self, **kwargs) -> str:
        """Render textarea element."""
        # Extract value for content
        value = kwargs.pop("value", "")

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)

        # Don't include type attribute for textarea
        if "type" in attrs:
            del attrs["type"]

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Escape the content value
        from html import escape

        escaped_value = escape(str(value)) if value is not None else ""

        return f"<textarea {attributes_str}>{escaped_value}</textarea>"


class URLInput(FormInput):
    """URL input field with URL validation."""

    ui_element = "url"

    def get_input_type(self) -> str:
        return "url"

    def render(self, **kwargs) -> str:
        """Render URL input using Python 3.14 template strings."""
        # Add input mode for mobile keyboards
        if "inputmode" not in kwargs:
            kwargs["inputmode"] = "url"

        # Add default pattern for URL validation if not provided
        if "pattern" not in kwargs:
            kwargs["pattern"] = r"https?://.+"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)


class TelInput(FormInput):
    """Telephone input field with phone number formatting."""

    ui_element = "tel"

    def get_input_type(self) -> str:
        return "tel"

    def render(self, **kwargs) -> str:
        """Render tel input using Python 3.14 template strings."""
        # Add input mode for mobile keyboards
        if "inputmode" not in kwargs:
            kwargs["inputmode"] = "tel"

        # Add autocomplete hint
        if "autocomplete" not in kwargs:
            kwargs["autocomplete"] = "tel"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)


# Specialized text inputs with formatting and validation


class SSNInput(TextInput):
    """Social Security Number input with formatting."""

    def render(self, **kwargs) -> str:
        """Render SSN input using Python 3.14 template strings."""
        # Add SSN-specific attributes
        kwargs["pattern"] = r"\d{3}-\d{2}-\d{4}"
        kwargs["placeholder"] = kwargs.get("placeholder", "123-45-6789")
        kwargs["maxlength"] = "11"
        kwargs["inputmode"] = "numeric"
        kwargs["autocomplete"] = "off"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)


class PhoneInput(TelInput):
    """Phone number input with country code support."""

    def render(self, country_code: Optional[str] = None, **kwargs) -> str:
        """Render phone input using Python 3.14 template strings."""
        if country_code:
            # Add country code to the value or placeholder
            if "value" in kwargs and not kwargs["value"].startswith(country_code):
                kwargs["value"] = f"{country_code} {kwargs['value']}"
            elif "placeholder" in kwargs and not kwargs["placeholder"].startswith(country_code):
                kwargs["placeholder"] = f"{country_code} {kwargs['placeholder']}"

        return super().render(**kwargs)


class CreditCardInput(TextInput):
    """Credit card number input with formatting."""

    def render(self, **kwargs) -> str:
        """Render credit card input using Python 3.14 template strings."""
        # Add credit card specific attributes
        kwargs["pattern"] = r"\d{4}\s?\d{4}\s?\d{4}\s?\d{4}"
        kwargs["placeholder"] = kwargs.get("placeholder", "1234 5678 9012 3456")
        kwargs["maxlength"] = "19"  # Including spaces
        kwargs["inputmode"] = "numeric"
        kwargs["autocomplete"] = "cc-number"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)


class CurrencyInput(TextInput):
    """Currency input with formatting."""

    def render(self, currency_symbol: str = "$", **kwargs) -> str:
        """Render currency input using Python 3.14 template strings."""
        # Add currency-specific attributes
        kwargs["pattern"] = rf"^\{currency_symbol}?\d+(\.\d{{2}})?$"
        kwargs["placeholder"] = kwargs.get("placeholder", f"{currency_symbol}0.00")
        kwargs["inputmode"] = "decimal"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        template = t"<input {attributes_str} />"
        return render_template(template)
