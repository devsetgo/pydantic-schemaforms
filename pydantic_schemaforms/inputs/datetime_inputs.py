"""
Date and time input components using Python 3.14 template strings.
Includes DateInput, TimeInput, DatetimeInput, MonthInput, WeekInput.
"""

from datetime import date, datetime, time
from typing import Optional, Union

from .base import FormInput


class DateInput(FormInput):
    """Date input field with date picker."""

    ui_element = "date"

    template = """<input type="date" ${attributes} />"""

    def get_input_type(self) -> str:
        return "date"

    def render(self, **kwargs) -> str:
        """Render date input with proper formatting."""
        # Convert date objects to string format
        if "value" in kwargs and isinstance(kwargs["value"], date):
            kwargs["value"] = kwargs["value"].isoformat()
        if "min" in kwargs and isinstance(kwargs["min"], date):
            kwargs["min"] = kwargs["min"].isoformat()
        if "max" in kwargs and isinstance(kwargs["max"], date):
            kwargs["max"] = kwargs["max"].isoformat()

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return f"<input {attributes_str} />"


class TimeInput(FormInput):
    """Time input field with time picker."""

    ui_element = "time"

    template = """<input type="time" ${attributes} />"""

    def get_input_type(self) -> str:
        return "time"

    def render(self, **kwargs) -> str:
        """Render time input with proper formatting."""
        # Convert time objects to string format
        if "value" in kwargs and isinstance(kwargs["value"], time):
            kwargs["value"] = kwargs["value"].strftime("%H:%M")
        if "min" in kwargs and isinstance(kwargs["min"], time):
            kwargs["min"] = kwargs["min"].strftime("%H:%M")
        if "max" in kwargs and isinstance(kwargs["max"], time):
            kwargs["max"] = kwargs["max"].strftime("%H:%M")

        # Set default step for seconds if not provided
        if "step" not in kwargs:
            kwargs["step"] = "60"  # 1 minute steps by default

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return f"<input {attributes_str} />"


class DatetimeInput(FormInput):
    """Datetime-local input field with datetime picker."""

    ui_element = "datetime"
    ui_element_aliases = ("datetime-local",)

    template = """<input type="datetime-local" ${attributes} />"""

    def get_input_type(self) -> str:
        return "datetime-local"

    def render(
        self, auto_set_current: bool = False, with_set_now_button: bool = False, **kwargs
    ) -> str:
        """Render datetime input with optional current time features."""
        # Convert datetime objects to string format
        if "value" in kwargs and isinstance(kwargs["value"], datetime):
            kwargs["value"] = kwargs["value"].strftime("%Y-%m-%dT%H:%M")
        if "min" in kwargs and isinstance(kwargs["min"], datetime):
            kwargs["min"] = kwargs["min"].strftime("%Y-%m-%dT%H:%M")
        if "max" in kwargs and isinstance(kwargs["max"], datetime):
            kwargs["max"] = kwargs["max"].strftime("%Y-%m-%dT%H:%M")

        # Auto-set to current datetime if requested and no value provided
        if auto_set_current and "value" not in kwargs:
            current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
            kwargs["value"] = current_time

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        datetime_html = f"<input {attributes_str} />"

        # Add "Set Now" button if requested
        if with_set_now_button:
            field_name = kwargs.get("name", "")
            field_id = kwargs.get("id", field_name)

            set_now_button = f"""
            <button type="button" class="set-now-btn" onclick="setCurrentDatetime('{field_id}')">
                Set Now
            </button>
            <script>
            function setCurrentDatetime(fieldId) {{
                const field = document.getElementById(fieldId);
                if (field) {{
                    const now = new Date();
                    const datetime = now.getFullYear() + '-' +
                        String(now.getMonth() + 1).padStart(2, '0') + '-' +
                        String(now.getDate()).padStart(2, '0') + 'T' +
                        String(now.getHours()).padStart(2, '0') + ':' +
                        String(now.getMinutes()).padStart(2, '0');
                    field.value = datetime;
                }}
            }}
            </script>
            """
            return f'<div class="datetime-input-group">{datetime_html}{set_now_button}</div>'

        return datetime_html


class MonthInput(FormInput):
    """Month input field for selecting year and month."""

    ui_element = "month"

    template = """<input type="month" ${attributes} />"""

    def get_input_type(self) -> str:
        return "month"

    def render(self, **kwargs) -> str:
        """Render month input with proper formatting."""
        # Convert date objects to month format (YYYY-MM)
        if "value" in kwargs:
            if isinstance(kwargs["value"], date):
                kwargs["value"] = kwargs["value"].strftime("%Y-%m")
            elif isinstance(kwargs["value"], datetime):
                kwargs["value"] = kwargs["value"].strftime("%Y-%m")

        if "min" in kwargs:
            if isinstance(kwargs["min"], date):
                kwargs["min"] = kwargs["min"].strftime("%Y-%m")
            elif isinstance(kwargs["min"], datetime):
                kwargs["min"] = kwargs["min"].strftime("%Y-%m")

        if "max" in kwargs:
            if isinstance(kwargs["max"], date):
                kwargs["max"] = kwargs["max"].strftime("%Y-%m")
            elif isinstance(kwargs["max"], datetime):
                kwargs["max"] = kwargs["max"].strftime("%Y-%m")

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return f"<input {attributes_str} />"


class WeekInput(FormInput):
    """Week input field for selecting year and week number."""

    ui_element = "week"

    template = """<input type="week" ${attributes} />"""

    def get_input_type(self) -> str:
        return "week"

    def render(self, **kwargs) -> str:
        """Render week input with proper formatting."""
        # Convert date objects to week format (YYYY-W##)
        if "value" in kwargs:
            if isinstance(kwargs["value"], date):
                year, week, _ = kwargs["value"].isocalendar()
                kwargs["value"] = f"{year}-W{week:02d}"
            elif isinstance(kwargs["value"], datetime):
                year, week, _ = kwargs["value"].date().isocalendar()
                kwargs["value"] = f"{year}-W{week:02d}"

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return f"<input {attributes_str} />"


class DateRangeInput:
    """Date range input with start and end date fields."""

    def __init__(self):
        self.start_input = DateInput()
        self.end_input = DateInput()

    def render(
        self,
        name: str,
        start_label: str = "Start Date",
        end_label: str = "End Date",
        start_value: Optional[Union[str, date]] = None,
        end_value: Optional[Union[str, date]] = None,
        **kwargs,
    ) -> str:
        """Render date range with start and end inputs."""

        # Extract common attributes
        common_attrs = {}
        for attr in ["class", "style", "required", "disabled"]:
            if attr in kwargs:
                common_attrs[attr] = kwargs[attr]

        # Render start date
        start_attrs = {
            **common_attrs,
            "name": f"{name}_start",
            "id": f"{name}_start",
            "placeholder": "Start date",
        }
        if start_value:
            start_attrs["value"] = start_value

        start_html = f"""
        <div class="date-range-start">
            <label for="{name}_start">{start_label}</label>
            {self.start_input.render(**start_attrs)}
        </div>
        """

        # Render end date
        end_attrs = {
            **common_attrs,
            "name": f"{name}_end",
            "id": f"{name}_end",
            "placeholder": "End date",
        }
        if end_value:
            end_attrs["value"] = end_value

        end_html = f"""
        <div class="date-range-end">
            <label for="{name}_end">{end_label}</label>
            {self.end_input.render(**end_attrs)}
        </div>
        """

        # Add validation script to ensure end date is after start date
        validation_script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const startDate = document.getElementById('{name}_start');
            const endDate = document.getElementById('{name}_end');

            function validateDateRange() {{
                if (startDate.value && endDate.value) {{
                    if (new Date(startDate.value) > new Date(endDate.value)) {{
                        endDate.setCustomValidity('End date must be after start date');
                    }} else {{
                        endDate.setCustomValidity('');
                    }}
                }}
            }}

            if (startDate && endDate) {{
                startDate.addEventListener('change', function() {{
                    endDate.min = this.value;
                    validateDateRange();
                }});

                endDate.addEventListener('change', validateDateRange);
            }}
        }});
        </script>
        """

        return f"""
        <div class="date-range-input" data-name="{name}">
            {start_html}
            {end_html}
            {validation_script}
        </div>
        """


class TimeRangeInput:
    """Time range input with start and end time fields."""

    def __init__(self):
        self.start_input = TimeInput()
        self.end_input = TimeInput()

    def render(
        self,
        name: str,
        start_label: str = "Start Time",
        end_label: str = "End Time",
        start_value: Optional[Union[str, time]] = None,
        end_value: Optional[Union[str, time]] = None,
        **kwargs,
    ) -> str:
        """Render time range with start and end inputs."""

        # Extract common attributes
        common_attrs = {}
        for attr in ["class", "style", "required", "disabled", "step"]:
            if attr in kwargs:
                common_attrs[attr] = kwargs[attr]

        # Render start time
        start_attrs = {
            **common_attrs,
            "name": f"{name}_start",
            "id": f"{name}_start",
            "placeholder": "Start time",
        }
        if start_value:
            start_attrs["value"] = start_value

        start_html = f"""
        <div class="time-range-start">
            <label for="{name}_start">{start_label}</label>
            {self.start_input.render(**start_attrs)}
        </div>
        """

        # Render end time
        end_attrs = {
            **common_attrs,
            "name": f"{name}_end",
            "id": f"{name}_end",
            "placeholder": "End time",
        }
        if end_value:
            end_attrs["value"] = end_value

        end_html = f"""
        <div class="time-range-end">
            <label for="{name}_end">{end_label}</label>
            {self.end_input.render(**end_attrs)}
        </div>
        """

        # Add validation script to ensure end time is after start time
        validation_script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const startTime = document.getElementById('{name}_start');
            const endTime = document.getElementById('{name}_end');

            function validateTimeRange() {{
                if (startTime.value && endTime.value) {{
                    if (startTime.value >= endTime.value) {{
                        endTime.setCustomValidity('End time must be after start time');
                    }} else {{
                        endTime.setCustomValidity('');
                    }}
                }}
            }}

            if (startTime && endTime) {{
                startTime.addEventListener('change', validateTimeRange);
                endTime.addEventListener('change', validateTimeRange);
            }}
        }});
        </script>
        """

        return f"""
        <div class="time-range-input" data-name="{name}">
            {start_html}
            {end_html}
            {validation_script}
        </div>
        """


class BirthdateInput(DateInput):
    """Specialized date input for birthdays with age calculation."""

    def render(self, show_age: bool = True, **kwargs) -> str:
        """Render birthdate input with optional age display."""
        # Set reasonable constraints for birthdates
        if "max" not in kwargs:
            kwargs["max"] = date.today().isoformat()
        if "min" not in kwargs:
            # Default to 150 years ago
            min_year = date.today().year - 150
            kwargs["min"] = f"{min_year}-01-01"

        birthdate_html = super().render(**kwargs)

        if show_age:
            field_name = kwargs.get("name", "")
            field_id = kwargs.get("id", field_name)

            age_display = f"""
            <div class="age-display" id="{field_name}_age" style="margin-top: 5px; font-size: 0.9em; color: #666;"></div>
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const birthdateField = document.getElementById('{field_id}');
                const ageDisplay = document.getElementById('{field_name}_age');

                function calculateAge() {{
                    if (birthdateField.value && ageDisplay) {{
                        const birthDate = new Date(birthdateField.value);
                        const today = new Date();
                        let age = today.getFullYear() - birthDate.getFullYear();
                        const monthDiff = today.getMonth() - birthDate.getMonth();

                        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {{
                            age--;
                        }}

                        ageDisplay.textContent = age >= 0 ? `Age: ${{age}} years` : '';
                    }}
                }}

                if (birthdateField) {{
                    birthdateField.addEventListener('change', calculateAge);
                    calculateAge(); // Calculate on load if value is set
                }}
            }});
            </script>
            """
            return f'<div class="birthdate-input-group">{birthdate_html}{age_display}</div>'

        return birthdate_html
