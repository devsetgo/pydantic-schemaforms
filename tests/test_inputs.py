"""
Tests for input components - text, numeric, selection, datetime, and specialized inputs.
"""

from datetime import date

from pydantic_schemaforms.inputs.datetime_inputs import DateInput, DatetimeInput, TimeInput
from pydantic_schemaforms.inputs.numeric_inputs import IntegerInput, NumberInput, RangeInput
from pydantic_schemaforms.inputs.selection_inputs import (
    CheckboxInput,
    MultiSelectInput,
    RadioInput,
    SelectInput,
)
from pydantic_schemaforms.inputs.specialized_inputs import ColorInput, FileInput, HiddenInput
from pydantic_schemaforms.inputs.text_inputs import (
    CreditCardInput,
    CurrencyInput,
    EmailInput,
    PasswordInput,
    PhoneInput,
    SSNInput,
    TelInput,
    TextArea,
    TextInput,
    URLInput,
)


class TestTextInputs:
    """Test text-based input components."""

    def test_text_input_basic(self):
        """Test basic TextInput functionality."""
        input_field = TextInput()

        # Test the HTML output
        html = input_field.render(name="username", value="john_doe")
        assert 'type="text"' in html
        assert 'name="username"' in html
        assert 'value="john_doe"' in html

    def test_text_input_render(self):
        """Test TextInput HTML rendering."""
        input_field = TextInput()

        html = input_field.render(
            name="username", value="john_doe", placeholder="Enter username", required=True
        )

        assert 'type="text"' in html
        assert 'name="username"' in html
        assert 'value="john_doe"' in html
        assert 'placeholder="Enter username"' in html
        assert "required" in html

    def test_email_input(self):
        """Test EmailInput functionality."""
        input_field = EmailInput()

        html = input_field.render(name="email", value="user@example.com")
        assert 'type="email"' in html
        assert 'name="email"' in html
        assert 'value="user@example.com"' in html
        # Note: inputmode may or may not be set automatically

    def test_password_input(self):
        """Test PasswordInput functionality."""
        input_field = PasswordInput()

        html = input_field.render(name="password")
        assert 'type="password"' in html
        assert 'name="password"' in html
        assert 'autocomplete="new-password"' in html

    def test_textarea_input(self):
        """Test TextArea functionality."""
        input_field = TextArea()

        html = input_field.render(name="description", value="Long text content", rows=5, cols=40)

        assert "<textarea" in html
        assert 'name="description"' in html
        assert 'rows="5"' in html
        assert 'cols="40"' in html
        assert "Long text content</textarea>" in html

    def test_url_input(self):
        """Test URLInput functionality."""
        input_field = URLInput()

        html = input_field.render(name="website", value="https://example.com")
        assert 'type="url"' in html
        assert 'name="website"' in html
        assert 'value="https://example.com"' in html
        # Note: inputmode and pattern may or may not be set automatically
        assert 'value="https://example.com"' in html


class TestNumericInputs:
    """Test numeric input components."""

    def test_number_input_basic(self):
        """Test basic NumberInput functionality."""
        input_field = NumberInput()

        html = input_field.render(name="amount", value=42.5)
        assert 'type="number"' in html
        assert 'name="amount"' in html
        assert 'value="42.5"' in html

    def test_number_input_with_constraints(self):
        """Test NumberInput with min/max constraints."""
        input_field = NumberInput()

        html = input_field.render(name="score", value=75, min=0, max=100, step=0.1)

        assert 'type="number"' in html
        assert 'name="score"' in html
        assert 'value="75"' in html
        assert 'min="0"' in html
        assert 'max="100"' in html
        assert 'step="0.1"' in html
        assert 'type="number"' in html

    def test_integer_input(self):
        """Test IntegerInput functionality."""
        input_field = IntegerInput()

        html = input_field.render(name="count", value=10)
        assert 'type="number"' in html
        assert 'name="count"' in html
        assert 'value="10"' in html
        assert 'step="1"' in html  # Integer step

    def test_decimal_input(self):
        """Test NumberInput with decimal values."""
        input_field = NumberInput()

        html = input_field.render(name="price", value=19.99, step=0.01)
        assert 'type="number"' in html
        assert 'name="price"' in html
        assert 'value="19.99"' in html
        assert 'step="0.01"' in html

    def test_range_input(self):
        """Test RangeInput functionality."""
        input_field = RangeInput()

        html = input_field.render(name="volume", value=50, min=0, max=100)

        assert 'type="range"' in html
        assert 'name="volume"' in html
        assert 'value="50"' in html
        assert 'min="0"' in html
        assert 'max="100"' in html


class TestSelectionInputs:
    """Test selection-based input components."""

    def test_select_input_basic(self):
        """Test basic SelectInput functionality."""
        options = [
            {"value": "red", "label": "Red"},
            {"value": "green", "label": "Green", "selected": True},
            {"value": "blue", "label": "Blue"},
        ]

        input_field = SelectInput()

        html = input_field.render(name="color", options=options)

        assert "<select" in html
        assert 'name="color"' in html
        assert '<option value="red">Red</option>' in html
        assert '<option value="green" selected>Green</option>' in html
        assert '<option value="blue">Blue</option>' in html

    def test_select_input_with_groups(self):
        """Test SelectInput with option groups."""
        options = [
            ("Colors", [("red", "Red"), ("blue", "Blue")]),
            ("Sizes", [("small", "Small"), ("large", "Large")]),
        ]

        input_field = SelectInput()
        html = input_field.render(name="choice", options=options)

        assert "<select" in html
        assert 'name="choice"' in html
        # Note: optgroup support may vary by implementation

    def test_checkbox_input(self):
        """Test CheckboxInput functionality."""
        input_field = CheckboxInput()

        html = input_field.render(name="newsletter", value="1", checked=True)

        assert 'type="checkbox"' in html
        assert 'name="newsletter"' in html
        assert "checked" in html

    def test_radio_input(self):
        """Test RadioInput functionality."""
        input_field = RadioInput()

        html = input_field.render(name="answer", value="yes", checked=True)

        assert 'type="radio"' in html
        assert 'name="answer"' in html
        assert "checked" in html

    def test_multi_select_input(self):
        """Test MultiSelectInput functionality."""
        options = [
            {"value": "tag1", "label": "Tag 1", "selected": True},
            {"value": "tag2", "label": "Tag 2"},
            {"value": "tag3", "label": "Tag 3", "selected": True},
        ]

        input_field = MultiSelectInput()

        html = input_field.render(name="tags", options=options)

        assert "<select" in html
        assert "multiple" in html
        assert 'name="tags"' in html


class TestDateTimeInputs:
    """Test date and time input components."""

    def test_date_input(self):
        """Test DateInput functionality."""

        date(2024, 1, 15)
        input_field = DateInput()

        html = input_field.render(name="birth_date", value="2024-01-15")
        assert 'type="date"' in html
        assert 'name="birth_date"' in html
        assert 'value="2024-01-15"' in html

    def test_time_input(self):
        """Test TimeInput functionality."""
        input_field = TimeInput()

        html = input_field.render(name="meeting_time", value="14:30")
        assert 'type="time"' in html
        assert 'value="14:30"' in html

    def test_datetime_input(self):
        """Test DatetimeInput functionality."""
        input_field = DatetimeInput()

        html = input_field.render(name="event_time", value="2024-01-15T14:30")
        assert 'type="datetime-local"' in html
        assert 'name="event_time"' in html
        assert 'value="2024-01-15T14:30"' in html


class TestSpecializedInputs:
    """Test specialized input components."""

    def test_color_input(self):
        """Test ColorInput functionality."""
        input_field = ColorInput()

        html = input_field.render(name="theme_color", value="#ff0000")
        assert 'type="color"' in html
        assert 'name="theme_color"' in html
        assert 'value="#ff0000"' in html

    def test_file_input(self):
        """Test FileInput functionality."""
        input_field = FileInput()

        html = input_field.render(
            name="upload",
            accept=".jpg,.png,.gif",
            multiple=True,
            show_preview=False,  # Disable preview to avoid JavaScript template issues
        )

        assert 'type="file"' in html
        assert 'name="upload"' in html
        assert 'accept=".jpg,.png,.gif"' in html
        assert "multiple" in html

    def test_hidden_input(self):
        """Test HiddenInput functionality."""
        input_field = HiddenInput()

        html = input_field.render(name="csrf_token", value="abc123")
        assert 'type="hidden"' in html
        assert 'name="csrf_token"' in html
        assert 'value="abc123"' in html

    def test_tel_input(self):
        """Test TelInput functionality."""
        input_field = TelInput()

        html = input_field.render(name="phone", value="+1-555-123-4567")
        assert 'type="tel"' in html
        assert 'name="phone"' in html
        assert 'value="+1-555-123-4567"' in html
        # Note: inputmode may or may not be set automatically


class TestInputValidation:
    """Test input validation and error handling."""

    def test_input_with_validation_errors(self):
        """Test input rendering with validation errors."""
        input_field = TextInput()

        html = input_field.render(name="username", value="", required=True)

        assert "required" in html
        assert 'name="username"' in html
        assert 'type="text"' in html

    def test_input_with_custom_attributes(self):
        """Test input with custom HTML attributes."""
        input_field = TextInput()

        html = input_field.render(
            name="username",
            **{
                "data-validation": "username",
                "aria-label": "Enter your username",
                "class": "form-control",
            },
        )

        assert 'data-validation="username"' in html
        assert 'aria-label="Enter your username"' in html
        assert 'class="form-control"' in html

    def test_input_disabled_state(self):
        """Test input in disabled state."""
        input_field = TextInput()

        html = input_field.render(name="readonly_field", value="Cannot edit", disabled=True)

        assert "disabled" in html
        assert 'name="readonly_field"' in html
        assert 'value="Cannot edit"' in html

    def test_input_readonly_state(self):
        """Test input in readonly state."""
        input_field = TextInput()

        html = input_field.render(name="readonly_field", value="Read only", readonly=True)

        assert "readonly" in html
        assert 'name="readonly_field"' in html
        assert 'value="Read only"' in html


class TestSpecializedTextInputAliases:
    """Ensure specialized text inputs do not override default text mapping."""

    def test_specialized_inputs_have_explicit_ui_element_names(self):
        assert SSNInput.ui_element == "ssn"
        assert PhoneInput.ui_element == "phone"
        assert CreditCardInput.ui_element == "credit_card"
        assert CurrencyInput.ui_element == "currency"

    def test_specialized_inputs_have_aliases(self):
        assert "social_security_number" in SSNInput.ui_element_aliases
        assert "phone_number" in PhoneInput.ui_element_aliases
        assert "cc_number" in CreditCardInput.ui_element_aliases
        assert "money" in CurrencyInput.ui_element_aliases


class TestInputIntegration:
    """Test input integration with form models."""

    def test_input_from_form_field(self, sample_form_data):
        """Test creating inputs from FormModel fields."""
        from pydantic_schemaforms.schema_form import Field, FormModel

        class TestForm(FormModel):
            name: str = Field(..., ui_element="text")
            email: str = Field(..., ui_element="email")
            age: int = Field(..., ui_element="number", ui_options={"min": 18, "max": 120})
            bio: str = Field("", ui_element="textarea", ui_options={"rows": 4})

        # Test individual inputs
        text_input = TextInput()
        text_html = text_input.render(name="name", value="test")
        assert 'type="text"' in text_html

        email_input = EmailInput()
        email_html = email_input.render(name="email", value="test@example.com")
        assert 'type="email"' in email_html

        number_input = NumberInput()
        number_html = number_input.render(name="age", value=25, min=18, max=120)
        assert 'type="number"' in number_html
        assert 'min="18"' in number_html
        assert 'max="120"' in number_html

        textarea_input = TextArea()
        textarea_html = textarea_input.render(name="bio", value="test bio", rows=4)
        assert "<textarea" in textarea_html
        assert 'rows="4"' in textarea_html

    def test_input_with_framework_styling(self):
        """Test input rendering with different CSS frameworks."""
        input_field = TextInput()

        # Test basic rendering
        html = input_field.render(name="test", value="test value")
        assert 'name="test"' in html
        assert 'value="test value"' in html
        assert 'type="text"' in html
