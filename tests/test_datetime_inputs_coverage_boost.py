"""Targeted coverage tests for inputs/datetime_inputs.py."""

import re
from datetime import date, datetime, time

from pydantic_schemaforms.inputs.datetime_inputs import (
    BirthdateInput,
    DateRangeInput,
    DatetimeInput,
    MonthInput,
    TimeRangeInput,
)


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
