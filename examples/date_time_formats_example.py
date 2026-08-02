#!/usr/bin/env python3
"""
Date/Time Format Showcase
=========================

Demonstrates the `date_format` / `time_format` / `datetime_format`
`ui_options` on `date`/`time`/`datetime` fields: every field falls back to
the browser's own locale-controlled native picker by default, and only
switches to a live-formatted text input when a custom `strftime` format is
configured (native `<input type="date"/"time"/"datetime-local">` can't be
forced into a custom *display* format -- the browser always controls that;
see `docs/inputs.md` and `docs/recipes.md` for the full explanation).

Every field below holds the exact same kind of value, formatted a different
way -- so this file doubles as a copy-paste-able reference for "what format
string do I use for X region/convention", not just a rendering demo:

- Date formats: USA, Europe (slash and dot conventions), ISO 8601 / most of
  Asia, a compact sortable "year month day" shape, and a long form with a
  month name (which also demonstrates the graceful fallback when a format
  uses a directive -- `%B` -- that has no fixed digit width: the server
  still parses/validates it correctly, it just can't offer a live-typing
  mask for that field).
- Time formats: 24-hour "military" time (the mechanism this feature was
  specifically asked to support), 12-hour with AM/PM, and regional
  separator variants.
- Datetime formats: combinations of the above, including the exact
  "year-month-day-hour(24)-minute-second" compact shape, and one field
  pairing a custom format with the existing `with_set_now_button` option to
  show they compose correctly.
"""

import os
import sys
from datetime import date, datetime, time

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic_schemaforms.form_layouts import TabbedLayout, VerticalLayout
from pydantic_schemaforms.schema_form import Field, FormModel

# ============================================================================
# DATE FORMATS
# ============================================================================


class DateFormatShowcaseForm(FormModel):
    """Every field holds a `date` -- only the display/parse format differs."""

    default_browser_date: date = Field(
        ...,
        title='Default (browser-controlled)',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        help_text=(
            'No date_format set -- native <input type="date">, displayed however '
            "the visitor's browser/OS locale renders it. This is the default for "
            'every date field unless you opt into a custom format below.'
        ),
    )
    usa_date: date = Field(
        ...,
        title='USA -- Month/Day/Year',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        ui_options={'date_format': '%m/%d/%Y'},
        help_text='date_format="%m/%d/%Y" -> 03/05/2026',
    )
    europe_slash_date: date = Field(
        ...,
        title='Europe (UK, France, ...) -- Day/Month/Year',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        ui_options={'date_format': '%d/%m/%Y'},
        help_text='date_format="%d/%m/%Y" -> 05/03/2026',
    )
    europe_dot_date: date = Field(
        ...,
        title='Europe (Germany, Austria, ...) -- Day.Month.Year',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        ui_options={'date_format': '%d.%m.%Y'},
        help_text='date_format="%d.%m.%Y" -> 05.03.2026',
    )
    iso_asia_date: date = Field(
        ...,
        title='ISO 8601 / Asia (Japan, China, Korea) -- Year-Month-Day',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        ui_options={'date_format': '%Y-%m-%d'},
        help_text='date_format="%Y-%m-%d" -> 2026-03-05',
    )
    year_month_day_compact: date = Field(
        ...,
        title='Year Month Day (compact, no separators)',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        ui_options={'date_format': '%Y%m%d'},
        help_text='date_format="%Y%m%d" -> 20260305 -- a common sortable-filename shape',
    )
    year_month_day_words: date = Field(
        ...,
        title='Year Month Day (long form, with month name)',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        ui_options={'date_format': '%Y %B %d'},
        help_text=(
            'date_format="%Y %B %d" -> 2026 March 05. %B has no fixed digit '
            'width, so live-typing assistance is disabled for this field -- but '
            'the server still parses and validates it correctly either way.'
        ),
    )
    short_year_date: date = Field(
        ...,
        title='Short year (two digits)',
        ui_element='date',
        json_schema_extra={'icon': 'calendar-date'},
        ui_options={'date_format': '%m/%d/%y'},
        help_text='date_format="%m/%d/%y" -> 03/05/26',
    )


# ============================================================================
# TIME FORMATS
# ============================================================================


class TimeFormatShowcaseForm(FormModel):
    """Every field holds a `time` -- only the display/parse format differs."""

    default_browser_time: time = Field(
        ...,
        title='Default (browser-controlled)',
        ui_element='time',
        json_schema_extra={'icon': 'clock'},
        help_text='No time_format set -- native <input type="time">.',
    )
    military_time: time = Field(
        ...,
        title='Military / 24-hour time (hours:minutes)',
        ui_element='time',
        json_schema_extra={'icon': 'clock'},
        ui_options={'time_format': '%H:%M'},
        help_text=(
            'time_format="%H:%M" -> 23:30. %H is always 24-hour -- AM/PM never '
            'appears anywhere in this field, which is the core "military time" ask.'
        ),
    )
    military_time_with_seconds: time = Field(
        ...,
        title='Military / 24-hour time with seconds',
        ui_element='time',
        json_schema_extra={'icon': 'clock'},
        ui_options={'time_format': '%H:%M:%S'},
        help_text='time_format="%H:%M:%S" -> 23:30:15',
    )
    usa_12_hour: time = Field(
        ...,
        title='USA -- 12-hour clock with AM/PM',
        ui_element='time',
        json_schema_extra={'icon': 'clock'},
        ui_options={'time_format': '%I:%M %p'},
        help_text=(
            'time_format="%I:%M %p" -> 11:30 PM. %p has no fixed digit width, so '
            'live-typing assistance is disabled (still pattern-validated and '
            'parsed correctly server-side).'
        ),
    )
    europe_dot_time: time = Field(
        ...,
        title='Europe -- hours.minutes (dot separator)',
        ui_element='time',
        json_schema_extra={'icon': 'clock'},
        ui_options={'time_format': '%H.%M'},
        help_text='time_format="%H.%M" -> 23.30',
    )
    compact_time: time = Field(
        ...,
        title='Compact (no separators)',
        ui_element='time',
        json_schema_extra={'icon': 'clock'},
        ui_options={'time_format': '%H%M%S'},
        help_text='time_format="%H%M%S" -> 233015',
    )


# ============================================================================
# DATETIME FORMATS
# ============================================================================


class DatetimeFormatShowcaseForm(FormModel):
    """Every field holds a `datetime` -- only the display/parse format differs."""

    default_browser_datetime: datetime = Field(
        ...,
        title='Default (browser-controlled)',
        ui_element='datetime',
        json_schema_extra={'icon': 'calendar-event'},
        help_text='No datetime_format set -- native <input type="datetime-local">.',
    )
    year_month_day_hour24_min_sec: datetime = Field(
        ...,
        title='Year Month Day, Hour(24) Minute Second (compact)',
        ui_element='datetime',
        json_schema_extra={'icon': 'calendar-event'},
        ui_options={'datetime_format': '%Y%m%d%H%M%S'},
        help_text=(
            'datetime_format="%Y%m%d%H%M%S" -> 20260305233015 -- a common '
            'sortable log/filename timestamp shape.'
        ),
    )
    iso_style_datetime: datetime = Field(
        ...,
        title='ISO-style (space-separated, 24-hour)',
        ui_element='datetime',
        json_schema_extra={'icon': 'calendar-event'},
        ui_options={'datetime_format': '%Y-%m-%d %H:%M:%S'},
        help_text='datetime_format="%Y-%m-%d %H:%M:%S" -> 2026-03-05 23:30:15',
    )
    usa_datetime: datetime = Field(
        ...,
        title='USA -- Month/Day/Year, 12-hour clock',
        ui_element='datetime',
        json_schema_extra={'icon': 'calendar-event'},
        ui_options={'datetime_format': '%m/%d/%Y %I:%M %p'},
        help_text='datetime_format="%m/%d/%Y %I:%M %p" -> 03/05/2026 11:30 PM',
    )
    europe_datetime: datetime = Field(
        ...,
        title='Europe -- Day.Month.Year, 24-hour clock',
        ui_element='datetime',
        json_schema_extra={'icon': 'calendar-event'},
        ui_options={'datetime_format': '%d.%m.%Y %H:%M'},
        help_text='datetime_format="%d.%m.%Y %H:%M" -> 05.03.2026 23:30',
    )
    asia_datetime: datetime = Field(
        ...,
        title='Asia (Japan, China, Korea) -- Year/Month/Day, 24-hour clock',
        ui_element='datetime',
        json_schema_extra={'icon': 'calendar-event'},
        ui_options={'datetime_format': '%Y/%m/%d %H:%M'},
        help_text='datetime_format="%Y/%m/%d %H:%M" -> 2026/03/05 23:30',
    )
    custom_format_with_set_now_button: datetime = Field(
        ...,
        title='Custom format + "Set Now" button',
        ui_element='datetime',
        json_schema_extra={'icon': 'calendar-event'},
        ui_options={
            'datetime_format': '%Y-%m-%d %H:%M',
            'with_set_now_button': True,
        },
        help_text=(
            'datetime_format + with_set_now_button compose correctly -- the '
            'Set Now button writes a value matching this custom format too, '
            'not the library default ISO-ish shape.'
        ),
    )


# ============================================================================
# TABBED WRAPPER
# ============================================================================


class DateFormatsTabLayout(VerticalLayout):
    """Vertical layout wrapper for the Date Formats tab."""

    form = DateFormatShowcaseForm


class TimeFormatsTabLayout(VerticalLayout):
    """Vertical layout wrapper for the Time Formats tab."""

    form = TimeFormatShowcaseForm


class DatetimeFormatsTabLayout(VerticalLayout):
    """Vertical layout wrapper for the Datetime Formats tab."""

    form = DatetimeFormatShowcaseForm


class DateTimeFormatsTabs(TabbedLayout):
    """Combines the date/time/datetime format tabs, in declaration order."""

    def __init__(self, form_config=None):
        super().__init__(form_config=form_config)
        self.dates = DateFormatsTabLayout()
        self.times = TimeFormatsTabLayout()
        self.datetimes = DatetimeFormatsTabLayout()

    def _get_layouts(self):
        # Explicit order -- TabbedLayout's default _get_layouts() scans
        # dir(self), which comes back alphabetical, not declaration order.
        return [
            ('dates', self.dates),
            ('times', self.times),
            ('datetimes', self.datetimes),
        ]


class DateTimeFormatsShowcaseForm(FormModel):
    """Tabbed showcase of custom date/time/datetime display formats.

    Every field across all three tabs holds the same kind of value
    (a `date`, `time`, or `datetime`) -- only the configured `ui_options`
    format string differs, to make the format-string-to-rendered-output
    mapping easy to compare side by side.
    """

    formats: DateTimeFormatsTabs = Field(
        default_factory=DateTimeFormatsTabs,
        title='Date, Time & Datetime Format Showcase',
        ui_element='layout',
    )


def create_sample_date_time_format_data() -> dict:
    """Seed data for the showcase -- every field represents the same date/time
    (2026-03-05, 23:30:15) so the only thing that varies between fields is
    the *display* format, making the comparison obvious.

    Pre-fill values are matched to each field's own configured display
    format: a rendered field's `value=` only gets re-coerced when it's a
    real `date`/`time`/`datetime` object (see DateInput/TimeInput/
    DatetimeInput.render() in inputs/datetime_inputs.py) -- a raw string is
    passed straight through on the assumption it's already correctly
    formatted, exactly like every other example's demo data in this repo
    (e.g. WidgetGalleryForm's plain-ISO 'date_input': '2024-06-15').
    """
    return {
        # Date Formats tab
        'default_browser_date': '2026-03-05',  # native picker -- always ISO
        'usa_date': '03/05/2026',
        'europe_slash_date': '05/03/2026',
        'europe_dot_date': '05.03.2026',
        'iso_asia_date': '2026-03-05',
        'year_month_day_compact': '20260305',
        'year_month_day_words': '2026 March 05',
        'short_year_date': '03/05/26',
        # Time Formats tab
        'default_browser_time': '23:30:15',  # native picker -- always 24-hour ISO-ish
        'military_time': '23:30',
        'military_time_with_seconds': '23:30:15',
        'usa_12_hour': '11:30 PM',
        'europe_dot_time': '23.30',
        'compact_time': '233015',
        # Datetime Formats tab
        'default_browser_datetime': '2026-03-05T23:30:15',  # native picker
        'year_month_day_hour24_min_sec': '20260305233015',
        'iso_style_datetime': '2026-03-05 23:30:15',
        'usa_datetime': '03/05/2026 11:30 PM',
        'europe_datetime': '05.03.2026 23:30',
        'asia_datetime': '2026/03/05 23:30',
        'custom_format_with_set_now_button': '2026-03-05 23:30',
    }
