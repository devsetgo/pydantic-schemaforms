"""Comprehensive tests for datetime and other input modules."""

from datetime import date, datetime, time
from pydantic_schemaforms.inputs.datetime_inputs import (
    DateInput,
    TimeInput,
    DatetimeInput,
    MonthInput,
    WeekInput,
)
from pydantic_schemaforms.inputs.numeric_inputs import NumberInput, RangeInput
from pydantic_schemaforms.inputs.text_inputs import EmailInput, URLInput, SearchInput
from pydantic_schemaforms.inputs.specialized_inputs import FileInput, ColorInput


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
