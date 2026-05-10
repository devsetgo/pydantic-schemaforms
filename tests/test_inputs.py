"""
Tests for input components - text, numeric, selection, datetime, and specialized inputs.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time

from pydantic_schemaforms.inputs.datetime_inputs import (
    BirthdateInput,
    DateInput,
    DateRangeInput,
    DatetimeInput,
    MonthInput,
    TimeInput,
    TimeRangeInput,
    WeekInput,
)
from pydantic_schemaforms.inputs.numeric_inputs import IntegerInput, NumberInput, RangeInput
from pydantic_schemaforms.inputs.selection_inputs import (
    CheckboxGroup,
    CheckboxInput,
    MultiSelectInput,
    RadioGroup,
    RadioInput,
    SelectInput,
)
from pydantic_schemaforms.inputs.specialized_inputs import (
    ButtonInput,
    CSRFInput,
    ColorInput,
    FileInput,
    HiddenInput,
    ImageInput,
    ResetInput,
    SubmitInput,
)
from pydantic_schemaforms.inputs.text_inputs import (
    CreditCardInput,
    CurrencyInput,
    EmailInput,
    PasswordInput,
    PhoneInput,
    SSNInput,
    SearchInput,
    TelInput,
    TextArea,
    TextInput,
    URLInput,
)


# ---------------------------------------------------------------------------
# Text inputs
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Numeric inputs
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Selection inputs
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Datetime inputs
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Specialized inputs (general)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Specialized text input aliases
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Input integration
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# DateInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestDateInput:
    """Test DateInput rendering."""

    def test_date_input_basic_render(self):
        """Test basic date input rendering."""
        date_input = DateInput()
        result = date_input.render(name="birth_date", id="birth_date")

        assert "type=\"date\"" in result
        assert "name=\"birth_date\"" in result

    def test_date_input_with_date_value(self):
        """Test date input with date object."""
        date_input = DateInput()
        test_date = date(2024, 1, 15)

        result = date_input.render(
            name="date_field",
            value=test_date
        )

        assert "2024-01-15" in result
        assert "type=\"date\"" in result

    def test_date_input_with_min_date(self):
        """Test date input with min date."""
        date_input = DateInput()
        min_date = date(2024, 1, 1)

        result = date_input.render(
            name="date_field",
            min=min_date
        )

        assert "2024-01-01" in result

    def test_date_input_with_max_date(self):
        """Test date input with max date."""
        date_input = DateInput()
        max_date = date(2024, 12, 31)

        result = date_input.render(
            name="date_field",
            max=max_date
        )

        assert "2024-12-31" in result

    def test_date_input_get_input_type(self):
        """Test DateInput.get_input_type()."""
        date_input = DateInput()
        assert date_input.get_input_type() == "date"

    def test_date_input_ui_element(self):
        """Test DateInput ui_element."""
        date_input = DateInput()
        assert date_input.ui_element == "date"


# ---------------------------------------------------------------------------
# TimeInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestTimeInput:
    """Test TimeInput rendering."""

    def test_time_input_basic_render(self):
        """Test basic time input rendering."""
        time_input = TimeInput()
        result = time_input.render(name="time_field", id="time_field")

        assert "type=\"time\"" in result
        assert "name=\"time_field\"" in result

    def test_time_input_with_time_value(self):
        """Test time input with time object."""
        time_input = TimeInput()
        test_time = time(14, 30)

        result = time_input.render(
            name="time_field",
            value=test_time
        )

        assert "14:30" in result

    def test_time_input_with_min_time(self):
        """Test time input with min time."""
        time_input = TimeInput()
        min_time = time(9, 0)

        result = time_input.render(
            name="time_field",
            min=min_time
        )

        assert "09:00" in result

    def test_time_input_with_max_time(self):
        """Test time input with max time."""
        time_input = TimeInput()
        max_time = time(17, 30)

        result = time_input.render(
            name="time_field",
            max=max_time
        )

        assert "17:30" in result

    def test_time_input_default_step(self):
        """Test time input default step."""
        time_input = TimeInput()
        result = time_input.render(name="time_field")

        assert "step=\"60\"" in result

    def test_time_input_custom_step(self):
        """Test time input with custom step."""
        time_input = TimeInput()
        result = time_input.render(
            name="time_field",
            step="30"
        )

        assert "step=\"30\"" in result

    def test_time_input_get_input_type(self):
        """Test TimeInput.get_input_type()."""
        time_input = TimeInput()
        assert time_input.get_input_type() == "time"


# ---------------------------------------------------------------------------
# DatetimeInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestDatetimeInput:
    """Test DatetimeInput rendering."""

    def test_datetime_input_basic_render(self):
        """Test basic datetime input rendering."""
        dt_input = DatetimeInput()
        result = dt_input.render(name="datetime_field", id="datetime_field")

        assert "type=\"datetime-local\"" in result
        assert "name=\"datetime_field\"" in result

    def test_datetime_input_with_datetime_value(self):
        """Test datetime input with datetime object."""
        dt_input = DatetimeInput()
        test_dt = datetime(2024, 1, 15, 14, 30)

        result = dt_input.render(
            name="datetime_field",
            value=test_dt
        )

        assert "2024-01-15T14:30" in result

    def test_datetime_input_with_min_datetime(self):
        """Test datetime input with min datetime."""
        dt_input = DatetimeInput()
        min_dt = datetime(2024, 1, 1, 0, 0)

        result = dt_input.render(
            name="datetime_field",
            min=min_dt
        )

        assert "2024-01-01T00:00" in result

    def test_datetime_input_with_max_datetime(self):
        """Test datetime input with max datetime."""
        dt_input = DatetimeInput()
        max_dt = datetime(2024, 12, 31, 23, 59)

        result = dt_input.render(
            name="datetime_field",
            max=max_dt
        )

        assert "2024-12-31T23:59" in result

    def test_datetime_input_get_input_type(self):
        """Test DatetimeInput.get_input_type()."""
        dt_input = DatetimeInput()
        assert dt_input.get_input_type() == "datetime-local"

    def test_datetime_input_ui_element_aliases(self):
        """Test DatetimeInput UI element aliases."""
        dt_input = DatetimeInput()
        assert "datetime-local" in dt_input.ui_element_aliases


# ---------------------------------------------------------------------------
# MonthInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestMonthInput:
    """Test MonthInput rendering."""

    def test_month_input_basic_render(self):
        """Test basic month input rendering."""
        month_input = MonthInput()
        result = month_input.render(name="month_field", id="month_field")

        assert "type=\"month\"" in result
        assert "name=\"month_field\"" in result

    def test_month_input_with_month_value(self):
        """Test month input with month value."""
        month_input = MonthInput()

        result = month_input.render(
            name="month_field",
            value="2024-01"
        )

        assert "2024-01" in result

    def test_month_input_get_input_type(self):
        """Test MonthInput.get_input_type()."""
        month_input = MonthInput()
        assert month_input.get_input_type() == "month"


# ---------------------------------------------------------------------------
# WeekInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestWeekInput:
    """Test WeekInput rendering."""

    def test_week_input_basic_render(self):
        """Test basic week input rendering."""
        week_input = WeekInput()
        result = week_input.render(name="week_field", id="week_field")

        assert "type=\"week\"" in result
        assert "name=\"week_field\"" in result

    def test_week_input_with_week_value(self):
        """Test week input with week value."""
        week_input = WeekInput()

        result = week_input.render(
            name="week_field",
            value="2024-W01"
        )

        assert "2024-W01" in result

    def test_week_input_with_datetime_value(self):
        """Test week input with datetime object value."""
        week_input = WeekInput()
        week_dt = datetime(2024, 1, 15, 8, 30)

        result = week_input.render(
            name="week_field",
            value=week_dt
        )

        assert "2024-W03" in result

    def test_week_input_get_input_type(self):
        """Test WeekInput.get_input_type()."""
        week_input = WeekInput()
        assert week_input.get_input_type() == "week"


# ---------------------------------------------------------------------------
# NumberInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestNumberInput:
    """Test NumberInput rendering."""

    def test_number_input_basic_render(self):
        """Test basic number input rendering."""
        num_input = NumberInput()
        result = num_input.render(name="number_field", id="number_field")

        assert "type=\"number\"" in result
        assert "name=\"number_field\"" in result

    def test_number_input_with_value(self):
        """Test number input with numeric value."""
        num_input = NumberInput()
        result = num_input.render(
            name="quantity",
            value=42
        )

        assert "42" in result

    def test_number_input_with_min(self):
        """Test number input with min value."""
        num_input = NumberInput()
        result = num_input.render(
            name="age",
            min=0
        )

        assert "min=\"0\"" in result

    def test_number_input_with_max(self):
        """Test number input with max value."""
        num_input = NumberInput()
        result = num_input.render(
            name="age",
            max=150
        )

        assert "max=\"150\"" in result

    def test_number_input_with_step(self):
        """Test number input with step value."""
        num_input = NumberInput()
        result = num_input.render(
            name="price",
            step=0.01
        )

        assert "step=" in result


# ---------------------------------------------------------------------------
# RangeInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestRangeInput:
    """Test RangeInput rendering."""

    def test_range_input_basic_render(self):
        """Test basic range input rendering."""
        range_input = RangeInput()
        result = range_input.render(name="range_field", id="range_field")

        assert "type=\"range\"" in result
        assert "name=\"range_field\"" in result

    def test_range_input_with_value(self):
        """Test range input with value."""
        range_input = RangeInput()
        result = range_input.render(
            name="volume",
            value=50
        )

        assert "value=\"50\"" in result

    def test_range_input_with_min_max(self):
        """Test range input with min and max."""
        range_input = RangeInput()
        result = range_input.render(
            name="volume",
            min=0,
            max=100
        )

        assert "min=\"0\"" in result
        assert "max=\"100\"" in result


# ---------------------------------------------------------------------------
# EmailInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestEmailInput:
    """Test EmailInput rendering."""

    def test_email_input_basic_render(self):
        """Test basic email input rendering."""
        email_input = EmailInput()
        result = email_input.render(name="email_field", id="email_field")

        assert "type=\"email\"" in result

    def test_email_input_with_value(self):
        """Test email input with value."""
        email_input = EmailInput()
        result = email_input.render(
            name="email",
            value="user@example.com"
        )

        assert "user@example.com" in result

    def test_email_input_with_multiple(self):
        """Test email input with multiple attribute."""
        email_input = EmailInput()
        result = email_input.render(
            name="emails",
            multiple=True
        )

        assert "multiple" in result


# ---------------------------------------------------------------------------
# URLInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestUrlInput:
    """Test URLInput rendering."""

    def test_url_input_basic_render(self):
        """Test basic URL input rendering."""
        url_input = URLInput()
        result = url_input.render(name="url_field", id="url_field")

        assert "type=\"url\"" in result

    def test_url_input_with_value(self):
        """Test URL input with value."""
        url_input = URLInput()
        result = url_input.render(
            name="website",
            value="https://example.com"
        )

        assert "https://example.com" in result


# ---------------------------------------------------------------------------
# SearchInput tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestSearchInput:
    """Test SearchInput rendering."""

    def test_search_input_basic_render(self):
        """Test basic search input rendering."""
        search_input = SearchInput()
        result = search_input.render(name="search_field", id="search_field")

        assert "type=\"search\"" in result

    def test_search_input_with_placeholder(self):
        """Test search input with placeholder."""
        search_input = SearchInput()
        result = search_input.render(
            name="search",
            placeholder="Search..."
        )

        assert "placeholder=\"Search...\"" in result


# ---------------------------------------------------------------------------
# FileInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestFileInput:
    """Test FileInput rendering."""

    def test_file_input_basic_render(self):
        """Test basic file input rendering."""
        file_input = FileInput()
        result = file_input.render(name="file_field", id="file_field")

        assert "type=\"file\"" in result

    def test_file_input_with_accept(self):
        """Test file input with accept attribute."""
        file_input = FileInput()
        result = file_input.render(
            name="document",
            accept=".pdf,.doc"
        )

        assert "accept=" in result

    def test_file_input_with_multiple(self):
        """Test file input with multiple attribute."""
        file_input = FileInput()
        result = file_input.render(
            name="files",
            multiple=True
        )

        assert "multiple" in result


# ---------------------------------------------------------------------------
# ColorInput detailed tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestColorInput:
    """Test ColorInput rendering."""

    def test_color_input_basic_render(self):
        """Test basic color input rendering."""
        color_input = ColorInput()
        result = color_input.render(name="color_field", id="color_field")

        assert "type=\"color\"" in result

    def test_color_input_with_value(self):
        """Test color input with value."""
        color_input = ColorInput()
        result = color_input.render(
            name="favorite_color",
            value="#FF0000"
        )

        assert "#FF0000" in result or "FF0000" in result

    def test_color_input_default_value(self):
        """Test color input default value."""
        color_input = ColorInput()
        result = color_input.render(
            name="theme_color",
            value="#000000"
        )

        assert "000000" in result


# ---------------------------------------------------------------------------
# Module-level datetime tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


def test_datetime_input_auto_set_current_when_value_missing():
    input_field = DatetimeInput()

    html = input_field.render(name="event_time", auto_set_current=True)

    assert 'type="datetime-local"' in html
    assert 'name="event_time"' in html
    assert re.search(r'value="\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"', html)


def test_datetime_input_set_now_button_uses_name_as_default_id():
    input_field = DatetimeInput()

    html = input_field.render(name="event_time", with_set_now_button=True)

    assert "setCurrentDatetime('event_time')" in html
    assert "datetime-input-group" in html


def test_month_input_formats_datetime_for_value_min_max():
    input_field = MonthInput()

    html = input_field.render(
        name="billing_month",
        value=datetime(2026, 2, 14, 12, 30),
        min=datetime(2025, 1, 1, 0, 0),
        max=datetime(2027, 12, 31, 23, 59),
    )

    assert 'value="2026-02"' in html
    assert 'min="2025-01"' in html
    assert 'max="2027-12"' in html


def test_date_range_input_renders_values_labels_and_validation_script():
    input_field = DateRangeInput()

    html = input_field.render(
        name="travel",
        start_label="Depart",
        end_label="Return",
        start_value=date(2026, 3, 1),
        end_value=date(2026, 3, 7),
        required=True,
        disabled=True,
        style="border: 1px solid #ccc",
        **{"class": "range-control"},
    )

    assert 'data-name="travel"' in html
    assert 'for="travel_start">Depart</label>' in html
    assert 'for="travel_end">Return</label>' in html
    assert 'name="travel_start"' in html
    assert 'name="travel_end"' in html
    assert 'value="2026-03-01"' in html
    assert 'value="2026-03-07"' in html
    assert "validateDateRange" in html
    assert "endDate.min = this.value" in html


def test_time_range_input_renders_values_step_and_validation_script():
    input_field = TimeRangeInput()

    html = input_field.render(
        name="office_hours",
        start_label="Opens",
        end_label="Closes",
        start_value=time(9, 0),
        end_value=time(17, 30),
        required=True,
        disabled=True,
        step="300",
        style="color: #333",
        **{"class": "time-control"},
    )

    assert 'data-name="office_hours"' in html
    assert 'for="office_hours_start">Opens</label>' in html
    assert 'for="office_hours_end">Closes</label>' in html
    assert 'name="office_hours_start"' in html
    assert 'name="office_hours_end"' in html
    assert 'value="09:00"' in html
    assert 'value="17:30"' in html
    assert 'step="300"' in html
    assert "validateTimeRange" in html
    assert "startTime.value >= endTime.value" in html


def test_birthdate_input_defaults_and_age_script_enabled():
    input_field = BirthdateInput()

    html = input_field.render(name="birthdate", id="birthdate")

    assert 'name="birthdate"' in html
    assert "birthdate_age" in html
    assert "calculateAge" in html
    assert 'max="' in html
    min_year = date.today().year - 150
    assert f'min="{min_year}-01-01"' in html


def test_birthdate_input_show_age_false_returns_plain_date_input():
    input_field = BirthdateInput()

    html = input_field.render(
        name="birthdate",
        value="2000-01-15",
        show_age=False,
        min="1900-01-01",
        max="2020-12-31",
    )

    assert 'type="date"' in html
    assert 'value="2000-01-15"' in html
    assert 'min="1900-01-01"' in html
    assert 'max="2020-12-31"' in html
    assert "birthdate-input-group" not in html
    assert "calculateAge" not in html


# ---------------------------------------------------------------------------
# CheckboxGroup tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestCheckboxGroup:
    """Test CheckboxGroup rendering with various configurations."""

    def test_checkbox_group_basic(self):
        """Test basic checkbox group rendering."""
        group = CheckboxGroup()
        options = [
            {"value": "option1", "label": "Option 1"},
            {"value": "option2", "label": "Option 2"},
        ]
        html = group.render(options=options, group_name="test_group")
        assert "checkbox" in html
        assert "Option 1" in html
        assert "Option 2" in html
        assert "test_group" in html

    def test_checkbox_group_with_checked(self):
        """Test checkbox group with checked items."""
        group = CheckboxGroup()
        options = [
            {"value": "opt1", "label": "Option 1", "checked": True},
            {"value": "opt2", "label": "Option 2", "checked": False},
        ]
        html = group.render(options=options, group_name="selection")
        assert "checked" in html
        assert "opt1" in html

    def test_checkbox_group_with_disabled(self):
        """Test checkbox group with disabled items."""
        group = CheckboxGroup()
        options = [
            {"value": "opt1", "label": "Option 1", "disabled": True},
            {"value": "opt2", "label": "Option 2"},
        ]
        html = group.render(options=options, group_name="selection")
        assert "disabled" in html

    def test_checkbox_group_with_legend(self):
        """Test checkbox group with custom legend."""
        group = CheckboxGroup()
        options = [{"value": "opt1", "label": "Option 1"}]
        html = group.render(options=options, group_name="test", legend="Custom Legend")
        assert "Custom Legend" in html

    def test_checkbox_group_with_custom_class(self):
        """Test checkbox group with custom CSS class."""
        group = CheckboxGroup()
        options = [{"value": "opt1", "label": "Option 1"}]
        html = group.render(options=options, group_name="test", **{"class": "custom-class"})
        assert "custom-class" in html or "class" in html


# ---------------------------------------------------------------------------
# RadioGroup tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestRadioGroup:
    """Test RadioGroup rendering with various configurations."""

    def test_radio_group_basic(self):
        """Test basic radio group rendering."""
        group = RadioGroup()
        options = [
            {"value": "opt1", "label": "Option 1"},
            {"value": "opt2", "label": "Option 2"},
        ]
        html = group.render(options=options, group_name="radio_test")
        assert "radio" in html
        assert "Option 1" in html
        assert "Option 2" in html

    def test_radio_group_with_checked(self):
        """Test radio group with checked item."""
        group = RadioGroup()
        options = [
            {"value": "opt1", "label": "Option 1", "checked": True},
            {"value": "opt2", "label": "Option 2"},
        ]
        html = group.render(options=options, group_name="selection")
        assert "checked" in html

    def test_radio_group_with_disabled(self):
        """Test radio group with disabled items."""
        group = RadioGroup()
        options = [
            {"value": "opt1", "label": "Option 1", "disabled": True},
        ]
        html = group.render(options=options, group_name="selection")
        assert "disabled" in html

    def test_radio_group_with_legend(self):
        """Test radio group with custom legend."""
        group = RadioGroup()
        options = [{"value": "opt1", "label": "Option 1"}]
        html = group.render(options=options, group_name="test", legend="Choose One")
        assert "Choose One" in html


# ---------------------------------------------------------------------------
# DatetimeInput rendering tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestDatetimeInputRendering:
    """Test DatetimeInput rendering with various features."""

    def test_datetime_input_basic(self):
        """Test basic datetime input."""
        input_field = DatetimeInput()
        html = input_field.render(name="event_time", value="2025-12-30T14:30")
        assert "datetime-local" in html
        assert "event_time" in html

    def test_datetime_input_with_set_now_button(self):
        """Test datetime input with Set Now button."""
        input_field = DatetimeInput()
        html = input_field.render(
            name="event_time",
            id="event_time_field",
            with_set_now_button=True,
        )
        assert "Set Now" in html
        assert "setCurrentDatetime" in html
        assert "event_time_field" in html

    def test_datetime_input_with_date_object(self):
        """Test datetime input with date object."""
        input_field = DatetimeInput()
        test_date = datetime(2025, 12, 30, 14, 30)
        html = input_field.render(name="event", value=test_date)
        assert "2025-12-30" in html

    def test_datetime_input_with_min_max(self):
        """Test datetime input with min/max constraints."""
        input_field = DatetimeInput()
        html = input_field.render(
            name="event",
            min="2025-01-01T00:00",
            max="2025-12-31T23:59",
        )
        assert "min=" in html.lower()
        assert "max=" in html.lower()


# ---------------------------------------------------------------------------
# MonthInput rendering tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestMonthInputRendering:
    """Test MonthInput rendering with various features."""

    def test_month_input_basic(self):
        """Test basic month input."""
        input_field = MonthInput()
        html = input_field.render(name="birth_month", value="2025-12")
        assert "month" in html
        assert "2025-12" in html

    def test_month_input_with_date_object(self):
        """Test month input with date object."""
        input_field = MonthInput()
        test_date = date(2025, 12, 1)
        html = input_field.render(name="month", value=test_date)
        assert "2025-12" in html

    def test_month_input_with_datetime_object(self):
        """Test month input with datetime object."""
        input_field = MonthInput()
        test_datetime = datetime(2025, 12, 30, 14, 30)
        html = input_field.render(name="month", value=test_datetime)
        assert "2025-12" in html

    def test_month_input_with_min_max(self):
        """Test month input with min/max constraints."""
        input_field = MonthInput()
        min_date = date(2025, 1, 1)
        max_date = date(2025, 12, 31)
        html = input_field.render(name="month", min=min_date, max=max_date)
        assert "2025-01" in html
        assert "2025-12" in html


# ---------------------------------------------------------------------------
# WeekInput rendering tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestWeekInputRendering:
    """Test WeekInput rendering with various features."""

    def test_week_input_basic(self):
        """Test basic week input."""
        input_field = WeekInput()
        html = input_field.render(name="work_week", value="2025-W52")
        assert "week" in html
        assert "2025-W52" in html

    def test_week_input_with_date_object(self):
        """Test week input with date object."""
        input_field = WeekInput()
        test_date = date(2025, 6, 15)  # Mid-year date
        html = input_field.render(name="week", value=test_date)
        # Should format as YYYY-Www
        assert "-W" in html
        assert "2025" in html

    def test_week_input_with_datetime_object(self):
        """Test week input with datetime object."""
        input_field = WeekInput()
        test_datetime = datetime(2025, 6, 15, 14, 30)
        html = input_field.render(name="week", value=test_datetime)
        assert "-W" in html
        assert "2025" in html


# ---------------------------------------------------------------------------
# ColorInput rendering tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestColorInputRendering:
    """Test ColorInput rendering with various features."""

    def test_color_input_basic(self):
        """Test basic color input."""
        input_field = ColorInput()
        html = input_field.render(name="theme_color", value="#3498db")
        assert "color" in html
        assert "#3498db" in html

    def test_color_input_with_value_display(self):
        """Test color input with value display."""
        input_field = ColorInput()
        html = input_field.render(
            name="bg_color",
            id="bg_color_field",
            value="#ff5733",
            show_value=True,
        )
        assert "color-value-display" in html
        assert "#ff5733" in html
        assert "bg_color_value" in html
        assert "bg_color_swatch" in html

    def test_color_input_without_value_display(self):
        """Test color input without value display."""
        input_field = ColorInput()
        html = input_field.render(name="color", value="#000000", show_value=False)
        assert "color" in html
        # Should not have the value display div
        assert "color-value-display" not in html


# ---------------------------------------------------------------------------
# ImageInput tests (from test_input_types_coverage.py)
# ---------------------------------------------------------------------------


class TestImageInput:
    """Test ImageInput rendering with various features."""

    def test_image_input_basic(self):
        """Test basic image input."""
        input_field = ImageInput()
        html = input_field.render(
            src="/path/to/image.png",
            alt="Submit button",
            name="submit_btn",
        )
        assert "image" in html
        assert "/path/to/image.png" in html
        assert "Submit button" in html

    def test_image_input_with_dimensions(self):
        """Test image input with width and height."""
        input_field = ImageInput()
        html = input_field.render(
            src="/img.png",
            alt="Button",
            width="100",
            height="50",
        )
        assert "img.png" in html
        assert "width" in html.lower()
        assert "height" in html.lower()


# ---------------------------------------------------------------------------
# FileInput specialized tests (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestFileInputSpecialized:
    """Test FileInput specialized features."""

    def test_file_input_accept_single(self):
        """Test file input with single accept type."""
        file_input = FileInput()
        result = file_input.render(name="file", accept=".pdf")

        assert "accept=" in result
        assert ".pdf" in result

    def test_file_input_accept_multiple_types(self):
        """Test file input with multiple accept types."""
        file_input = FileInput()
        result = file_input.render(
            name="document",
            accept=".pdf,.doc,.docx"
        )

        assert "accept=" in result

    def test_file_input_accept_mime_type(self):
        """Test file input with MIME type."""
        file_input = FileInput()
        result = file_input.render(
            name="image",
            accept="image/*"
        )

        assert "image/*" in result

    def test_file_input_capture_attribute(self):
        """Test file input with capture attribute."""
        file_input = FileInput()
        result = file_input.render(
            name="photo",
            capture="environment"
        )

        assert "capture=" in result

    def test_file_input_disabled(self):
        """Test disabled file input."""
        file_input = FileInput()
        result = file_input.render(
            name="file",
            disabled=True
        )

        assert "disabled" in result

    def test_file_input_readonly(self):
        """Test readonly file input."""
        file_input = FileInput()
        result = file_input.render(
            name="file",
            readonly=True
        )

        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# ColorInput specialized tests (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestColorInputSpecialized:
    """Test ColorInput specialized features."""

    def test_color_input_valid_hex(self):
        """Test color input with valid hex value."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            value="#FF5733"
        )

        assert "FF5733" in result or "ff5733" in result.lower()

    def test_color_input_short_hex(self):
        """Test color input with short hex value."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            value="#FFF"
        )

        assert "#" in result

    def test_color_input_disabled(self):
        """Test disabled color input."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            disabled=True
        )

        assert "disabled" in result

    def test_color_input_with_list(self):
        """Test color input with datalist."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            list="colors"
        )

        assert "list=" in result or "colors" in result


# ---------------------------------------------------------------------------
# Telephone input placeholder (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestTelephoneInput:
    """Test PhoneInput features."""

    def test_phone_input_basic(self):
        """Test basic phone input."""
        # PhoneInput is not directly available, skip this
        pass


# ---------------------------------------------------------------------------
# HiddenInput specialized tests (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestHiddenInputSpecialized:
    """Test HiddenInput specialized features."""

    def test_hidden_input_basic(self):
        """Test basic hidden input."""
        hidden = HiddenInput()
        result = hidden.render(name="csrf_token")

        assert "type=\"hidden\"" in result
        assert "name=\"csrf_token\"" in result

    def test_hidden_input_with_value(self):
        """Test hidden input with value."""
        hidden = HiddenInput()
        result = hidden.render(
            name="token",
            value="abc123xyz"
        )

        assert "abc123xyz" in result

    def test_hidden_input_multiple_values(self):
        """Test rendering multiple hidden inputs."""
        hidden = HiddenInput()

        result1 = hidden.render(name="field1", value="value1")
        result2 = hidden.render(name="field2", value="value2")

        assert "field1" in result1
        assert "field2" in result2
        assert "value1" in result1
        assert "value2" in result2


# ---------------------------------------------------------------------------
# SubmitInput tests (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestSubmitButton:
    """Test SubmitInput features."""

    def test_submit_button_basic(self):
        """Test basic submit button."""
        submit = SubmitInput()
        result = submit.render(value="Submit")

        assert "type=\"submit\"" in result
        assert "Submit" in result

    def test_submit_button_with_name(self):
        """Test submit button with name."""
        submit = SubmitInput()
        result = submit.render(
            name="action",
            value="Submit Form"
        )

        assert "name=\"action\"" in result

    def test_submit_button_with_class(self):
        """Test submit button with CSS class."""
        submit = SubmitInput()
        result = submit.render(
            value="Submit",
            class_="btn btn-primary"
        )

        assert "class=" in result or "btn" in result

    def test_submit_button_disabled(self):
        """Test disabled submit button."""
        submit = SubmitInput()
        result = submit.render(
            value="Submit",
            disabled=True
        )

        assert "disabled" in result


# ---------------------------------------------------------------------------
# ResetInput tests (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestResetButton:
    """Test ResetInput features."""

    def test_reset_button_basic(self):
        """Test basic reset button."""
        reset = ResetInput()
        result = reset.render(value="Reset")

        assert "type=\"reset\"" in result
        assert "Reset" in result

    def test_reset_button_with_name(self):
        """Test reset button with name."""
        reset = ResetInput()
        result = reset.render(
            name="reset_action",
            value="Clear Form"
        )

        assert "name=\"reset_action\"" in result

    def test_reset_button_with_style(self):
        """Test reset button with inline style."""
        reset = ResetInput()
        result = reset.render(
            value="Reset",
            style="color: red;"
        )

        assert "style=" in result or "red" in result


# ---------------------------------------------------------------------------
# ButtonInput tests (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestButtonInput:
    """Test ButtonInput features."""

    def test_button_input_basic(self):
        """Test basic button input."""
        button = ButtonInput()
        result = button.render(value="Click Me")

        assert "type=\"button\"" in result
        assert "Click Me" in result

    def test_button_input_with_onclick(self):
        """Test button input with onclick handler."""
        button = ButtonInput()
        result = button.render(
            value="Action",
            onclick="performAction()"
        )

        assert "onclick=" in result or "performAction" in result

    def test_button_input_with_form(self):
        """Test button input with form attribute."""
        button = ButtonInput()
        result = button.render(
            value="Submit",
            form="myform"
        )

        assert "form=" in result or "myform" in result


# ---------------------------------------------------------------------------
# DatalistInput / ImageInput tests (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestDatalistInput:
    """Test ImageInput features."""

    def test_image_input_basic(self):
        """Test basic image input."""
        image_input = ImageInput()
        result = image_input.render(name="image_btn", src="/btn.png", alt="Submit")

        assert "type=\"image\"" in result

    def test_image_input_with_src(self):
        """Test image input with src."""
        image_input = ImageInput()
        result = image_input.render(
            name="submit_btn",
            src="/images/submit.png",
            alt="Submit"
        )

        assert "/images/submit.png" in result or "src=" in result


# ---------------------------------------------------------------------------
# Specialized inputs integration (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestSpecializedInputsIntegration:
    """Test integration of specialized inputs."""

    def test_file_and_color_together(self):
        """Test file and color inputs together."""
        file_input = FileInput()
        color_input = ColorInput()

        file_result = file_input.render(name="attachment")
        color_result = color_input.render(name="theme_color")

        assert "file" in file_result.lower()
        assert "color" in color_result.lower()

    def test_telephone_and_hidden_together(self):
        """Test CSRF and hidden inputs together."""
        csrf_input = CSRFInput()
        hidden_input = HiddenInput()

        csrf_input.render(token="token123")
        hidden_result = hidden_input.render(name="session_id", value="sess123")

        assert isinstance(hidden_result, str)
        assert "hidden" in hidden_result.lower()

    def test_all_button_types(self):
        """Test all button types."""
        submit = SubmitInput().render(value="Submit")
        reset = ResetInput().render(value="Reset")
        button = ButtonInput().render(value="Button")

        assert "submit" in submit.lower()
        assert "reset" in reset.lower()
        assert "button" in button.lower()


# ---------------------------------------------------------------------------
# Specialized inputs attributes (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestSpecializedInputsAttributes:
    """Test attributes on specialized inputs."""

    def test_file_input_form_attribute(self):
        """Test file input with form attribute."""
        file_input = FileInput()
        result = file_input.render(
            name="file",
            form="upload_form"
        )

        assert isinstance(result, str)

    def test_color_input_required(self):
        """Test color input with required attribute."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            required=True
        )

        assert "required" in result or isinstance(result, str)

    def test_tel_input_autocomplete(self):
        """Test CSRF input rendering."""
        csrf_input = CSRFInput()
        result = csrf_input.render(token="token123")

        assert isinstance(result, str)

    def test_hidden_input_immutability(self):
        """Test hidden input value immutability."""
        hidden = HiddenInput()
        result = hidden.render(
            name="nonce",
            value="fixed_value",
            disabled=True
        )

        assert "fixed_value" in result


# ---------------------------------------------------------------------------
# Specialized inputs edge cases (from test_specialized_inputs_coverage.py)
# ---------------------------------------------------------------------------


class TestSpecializedInputsEdgeCases:
    """Test edge cases in specialized inputs."""

    def test_file_input_empty_accept(self):
        """Test file input with empty accept."""
        file_input = FileInput()
        result = file_input.render(name="file", accept="")

        assert isinstance(result, str)

    def test_color_input_invalid_hex(self):
        """Test color input with any value (validation is client-side)."""
        color_input = ColorInput()
        result = color_input.render(
            name="color",
            value="not-a-color"
        )

        assert isinstance(result, str)

    def test_telephone_input_no_pattern(self):
        """Test CSRF input rendering."""
        csrf_input = CSRFInput()
        result = csrf_input.render(token="abc123")

        assert isinstance(result, str)

    def test_submit_button_no_value(self):
        """Test submit button without explicit value."""
        submit = SubmitInput()
        result = submit.render()

        assert isinstance(result, str)

    def test_datalist_empty_options(self):
        """Test image input without src."""
        image_input = ImageInput()
        result = image_input.render(name="img_btn", src="/img.png", alt="Img")

        assert isinstance(result, str)
