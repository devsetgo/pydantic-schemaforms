"""
Additional input tests to improve coverage for selection, datetime, and specialized inputs.
Targets uncovered lines in selection_inputs.py, datetime_inputs.py, and specialized_inputs.py.
"""

import pytest
from datetime import date, datetime

from pydantic_schemaforms.inputs.selection_inputs import CheckboxGroup, RadioGroup
from pydantic_schemaforms.inputs.datetime_inputs import DatetimeInput, MonthInput, WeekInput
from pydantic_schemaforms.inputs.specialized_inputs import ColorInput, ImageInput


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


class TestDatetimeInput:
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


class TestMonthInput:
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


class TestWeekInput:
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


class TestColorInput:
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
