"""
Date and time input components using Python 3.14 template strings.
Includes DateInput, TimeInput, DatetimeInput, MonthInput, WeekInput.
"""

import json
import re
from datetime import date, datetime, time

from typing import Any

from pydantic_schemaforms.tstring import SafeHTML, html

from .base import FormInput, _render_input_tag

_DATETIME_FMT = '%Y-%m-%dT%H:%M'

_STRFTIME_DIRECTIVE_RE = re.compile(r'(%.)')

# Reserves room for the picker-toggle icon button (see _wrap_with_picker_toggle).
_PICKER_TOGGLE_PADDING_STYLE = 'padding-right: 2.25rem;'

# Directives that map to a fixed-width run of digits -- safe for live
# character-by-character mask-driven input, using the same '#'-per-digit
# convention PhoneInput/_mask_to_pattern already use in text_inputs.py.
_NUMERIC_DIRECTIVES: dict[str, tuple[int, str]] = {
    '%Y': (4, '1970'),
    '%y': (2, '70'),
    '%m': (2, '01'),
    '%d': (2, '31'),
    '%H': (2, '23'),
    '%I': (2, '11'),
    '%M': (2, '59'),
    '%S': (2, '59'),
}

# Directives with no fixed digit-width representation (AM/PM, weekday and
# month names, timezone, ...). These still round-trip correctly through
# Python's own strftime/strptime server-side, but can't be safely live-typed
# character-by-character the way a digit run can -- a format containing any
# of these disables the JS live-mask entirely for that field (falls back to
# plain typing + `pattern` validation + server-side parsing only).
_OPAQUE_PATTERNS: dict[str, tuple[str, str]] = {
    '%p': ('(?:AM|PM|am|pm)', 'PM'),
}

_MONTH_NAMES_FULL_JS = json.dumps(
    [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December',
    ]
)
_MONTH_NAMES_ABBR_JS = json.dumps(
    [
        'Jan',
        'Feb',
        'Mar',
        'Apr',
        'May',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Oct',
        'Nov',
        'Dec',
    ]
)
_WEEKDAY_NAMES_FULL_JS = json.dumps(
    [
        'Sunday',
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
    ]
)
_WEEKDAY_NAMES_ABBR_JS = json.dumps(['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])

# JS expressions (evaluated against a Date instance held in some variable)
# for building a format-aware value from a Date object. Shared by the "Set
# Now" button and the native picker toggle below -- both build the *whole*
# output string once from a complete Date, so unlike the live mask (which
# needs a fixed digit-width per directive for character-by-character typing)
# this can also cover variable-width directives like AM/PM and month/weekday
# names -- deliberately a superset of _NUMERIC_DIRECTIVES's key set.
_JS_DATE_PART_EXPR: dict[str, str] = {
    '%Y': 'String({v}.getFullYear())',
    '%y': 'String({v}.getFullYear()).slice(-2)',
    '%m': "String({v}.getMonth() + 1).padStart(2, '0')",
    '%d': "String({v}.getDate()).padStart(2, '0')",
    '%H': "String({v}.getHours()).padStart(2, '0')",
    '%I': "String((({v}.getHours() + 11) % 12) + 1).padStart(2, '0')",
    '%M': "String({v}.getMinutes()).padStart(2, '0')",
    '%S': "String({v}.getSeconds()).padStart(2, '0')",
    '%p': "({v}.getHours() < 12 ? 'AM' : 'PM')",
    '%B': f'{_MONTH_NAMES_FULL_JS}[{{v}}.getMonth()]',
    '%b': f'{_MONTH_NAMES_ABBR_JS}[{{v}}.getMonth()]',
    '%A': f'{_WEEKDAY_NAMES_FULL_JS}[{{v}}.getDay()]',
    '%a': f'{_WEEKDAY_NAMES_ABBR_JS}[{{v}}.getDay()]',
}


def _build_js_date_expr(tokens: list[str], var_name: str) -> str | None:
    """Build a JS string-concatenation expression rendering a Date held in
    *var_name* using *tokens* (from _tokenize_strftime), or None if any
    directive isn't in _JS_DATE_PART_EXPR -- e.g. timezone/week-number
    directives can't be derived from a bare Date object this way. Broader
    support than the live mask (see _JS_DATE_PART_EXPR docstring)."""
    if any(token.startswith('%') and token not in _JS_DATE_PART_EXPR for token in tokens):
        return None
    return ' + '.join(
        _JS_DATE_PART_EXPR[token].format(v=var_name)
        if token in _JS_DATE_PART_EXPR
        else json.dumps(token)
        for token in tokens
    )


def _picker_toggle_js_expr(fmt: str) -> str | None:
    """Whether/how *fmt* can drive the native-picker toggle's onchange
    handler -- checked separately from _translate_strftime's live-typing
    mask since the toggle only needs to build a value once from a full Date
    (var name doesn't matter here, just whether it resolves)."""
    return _build_js_date_expr(_tokenize_strftime(fmt), 'd')


def _tokenize_strftime(fmt: str) -> list[str]:
    """Split a strftime format string into literal runs and '%x' directive
    tokens, preserving order (e.g. '%Y-%m-%d' -> ['%Y', '-', '%m', '-', '%d'])."""
    return [token for token in _STRFTIME_DIRECTIVE_RE.split(fmt) if token]


def _translate_strftime(fmt: str) -> tuple[str | None, str, str]:
    """Translate a strftime format string into (js_mask, html_pattern, placeholder).

    js_mask: '#' per digit, literal characters pass through unchanged; used
        to drive live character-by-character reformatting as the user types
        (same mechanism PhoneInput's inline script already uses in
        text_inputs.py). None if the format contains any directive without a
        fixed digit width -- live masking is disabled for that field rather
        than attempted with wrong output (see _OPAQUE_PATTERNS above).
    html_pattern: an unanchored regex suitable for the `pattern` attribute
        (HTML5's `pattern` attribute is implicitly anchored already).
    placeholder: a human-readable example matching the configured shape.
    """
    mask_parts: list[str] = []
    pattern_parts: list[str] = []
    placeholder_parts: list[str] = []
    maskable = True

    for token in _tokenize_strftime(fmt):
        if token in _NUMERIC_DIRECTIVES:
            width, example = _NUMERIC_DIRECTIVES[token]
            mask_parts.append('#' * width)
            pattern_parts.append(rf'\d{{{width}}}')
            placeholder_parts.append(example)
        elif token in _OPAQUE_PATTERNS:
            maskable = False
            pattern, example = _OPAQUE_PATTERNS[token]
            pattern_parts.append(pattern)
            placeholder_parts.append(example)
        elif len(token) == 2 and token[0] == '%':
            # Any other strftime directive (%A, %B, %Z, ...): strftime/strptime
            # handle it natively server-side, but it has no fixed shape we can
            # safely live-mask or offer a tight validation pattern for.
            maskable = False
            pattern_parts.append(r'.+?')
            placeholder_parts.append(f'[{token[1:]}]')
        else:
            # Literal run (separators, spaces, etc.)
            mask_parts.append(token)
            pattern_parts.append(re.escape(token))
            placeholder_parts.append(token)

    mask = ''.join(mask_parts) if maskable else None
    pattern = ''.join(pattern_parts)
    placeholder = ''.join(placeholder_parts)
    return mask, pattern, placeholder


def _render_datetime_mask_script(field_id: str, mask: str) -> str:
    """Live '#'-mask character-by-character reformatting for a text-mode
    date/time/datetime field, mirroring PhoneInput's inline script in
    text_inputs.py."""
    return SafeHTML(rf"""
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const el = document.getElementById('{field_id}');
    const mask = {json.dumps(mask)};
    if (el) {{
        el.addEventListener('input', function() {{
            const digits = el.value.replace(/\D/g, '');
            let out = '';
            let di = 0;
            for (let i = 0; i < mask.length && di < digits.length; i++) {{
                if (mask[i] === '#') {{
                    out += digits[di];
                    di++;
                }} else {{
                    out += mask[i];
                }}
            }}
            el.value = out;
        }});
    }}
}});
</script>
""")


def _render_set_now_button(field_id: str, fmt: str) -> str:
    """Render a "Set Now" button that writes the current datetime using *fmt*.

    Only supported for formats _build_js_date_expr can render -- returns ''
    (no button) for anything else rather than writing a value that doesn't
    match the field's own expected shape.
    """
    js_expr = _build_js_date_expr(_tokenize_strftime(fmt), 'now')
    if js_expr is None:
        return ''

    fn_name = f'setCurrentDatetime_{re.sub(r"\W", "_", field_id, flags=re.ASCII)}'
    onclick = f"{fn_name}('{field_id}')"

    button_html = html(t'''
            <button type="button" class="set-now-btn" onclick="{onclick}">
                Set Now
            </button>
            ''')
    # JS-only below (rule 4 exception): fn_name is a sanitized JS identifier
    # and js_expr is developer-generated JS, not user data.
    script_html = SafeHTML(f"""
            <script>
            function {fn_name}(fieldId) {{
                const field = document.getElementById(fieldId);
                if (field) {{
                    const now = new Date();
                    field.value = {js_expr};
                }}
            }}
            </script>
            """)
    return SafeHTML(button_html + script_html)


# Minimal inline SVGs (Bootstrap Icons' "calendar3"/"clock" glyphs, MIT
# licensed) -- kept inline rather than a `<i class="bi bi-...">` reference
# so the picker toggle renders identically regardless of framework/theme or
# whether Bootstrap Icons' CSS happens to be loaded on the page.
_CALENDAR_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" '
    'fill="currentColor" aria-hidden="true" focusable="false">'
    '<path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2'
    ' 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5M1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4z"/>'
    '</svg>'
)
_CLOCK_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" '
    'fill="currentColor" aria-hidden="true" focusable="false">'
    '<path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71z"/>'
    '<path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0"/>'
    '</svg>'
)
_PICKER_ICON_SVG = {
    'date': _CALENDAR_ICON_SVG,
    'time': _CLOCK_ICON_SVG,
    'datetime-local': _CLOCK_ICON_SVG,
}
_PICKER_ARIA_LABEL = {
    'date': 'Open date picker',
    'time': 'Open time picker',
    'datetime-local': 'Open date and time picker',
}


def _append_inline_style(existing: str, addition: str) -> str:
    """Append a CSS declaration to an existing inline `style` value."""
    existing = existing.strip()
    if not existing:
        return addition
    sep = '' if existing.endswith(';') else '; '
    return f'{existing}{sep}{addition}'


def _wrap_with_picker_toggle(input_html: str, field_id: str, fmt: str, native_type: str) -> str:
    """Wrap a custom-formatted text field with a single small icon button
    that opens the browser's own native date/time/datetime-local picker
    (via a visually-hidden companion `<input>`, triggered with
    `showPicker()`) and writes the selected value back into the visible
    field using *fmt* -- one visible box, not two, with the native picker
    UI still available (a native input can't show a custom *display*
    format itself -- see module docstring).

    Caller must have already confirmed *fmt* is renderable by
    _build_js_date_expr / _picker_toggle_js_expr.
    """
    js_expr = _build_js_date_expr(_tokenize_strftime(fmt), 'd')
    picker_id = f'{field_id}__picker'
    toggle_id = f'{field_id}__picker_toggle'

    if native_type == 'date':
        to_date_js = "new Date(this.value + 'T00:00:00')"
    elif native_type == 'time':
        to_date_js = "new Date('1970-01-01T' + this.value)"
    else:
        to_date_js = 'new Date(this.value)'

    icon = SafeHTML(_PICKER_ICON_SVG[native_type])
    aria_label = _PICKER_ARIA_LABEL[native_type]
    _input_html = SafeHTML(str(input_html))

    wrapper_html = html(t'''
<div class="schemaforms-picker-wrap" style="position: relative; display: inline-block; width: 100%;">
{_input_html}
<button type="button" id="{toggle_id}" aria-label="{aria_label}" class="schemaforms-picker-toggle" style="position: absolute; top: 50%; right: 0.4rem; transform: translateY(-50%); background: transparent; border: none; padding: 0.15rem; margin: 0; cursor: pointer; line-height: 0; color: inherit; opacity: 0.6;">{icon}</button>
<input type="{native_type}" id="{picker_id}" tabindex="-1" aria-hidden="true" style="position: absolute; inset: 0; opacity: 0; width: 1px; height: 1px; border: 0; padding: 0; pointer-events: none;" />
</div>
''')
    # JS-only below (rule 4 exception): ids are embedded as JS string
    # literals, not HTML attribute values.
    script_html = SafeHTML(f"""
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const toggle = document.getElementById('{toggle_id}');
    const picker = document.getElementById('{picker_id}');
    const field = document.getElementById('{field_id}');
    if (toggle && picker && field) {{
        toggle.addEventListener('click', function() {{
            if (picker.showPicker) {{
                try {{ picker.showPicker(); }} catch (e) {{ picker.focus(); }}
            }} else {{
                picker.focus();
            }}
        }});
        picker.addEventListener('change', function() {{
            if (!this.value) return;
            const d = {to_date_js};
            field.value = {js_expr};
        }});
    }}
}});
</script>
""")
    return SafeHTML(wrapper_html + script_html)


class DateInput(FormInput):
    """Date input field with date picker."""

    ui_element: str = 'date'

    template = """<input type="date" ${attributes} />"""

    def get_input_type(self) -> str:
        return 'date'

    def render(
        self, date_format: str | None = None, live_format: bool = True, **kwargs: Any
    ) -> str:
        """Render date input with proper formatting."""
        if date_format is None:
            # Convert date objects to string format
            if 'value' in kwargs and isinstance(kwargs['value'], date):
                kwargs['value'] = kwargs['value'].isoformat()
            if 'min' in kwargs and isinstance(kwargs['min'], date):
                kwargs['min'] = kwargs['min'].isoformat()
            if 'max' in kwargs and isinstance(kwargs['max'], date):
                kwargs['max'] = kwargs['max'].isoformat()

            # Validate and format attributes
            attrs = self.validate_attributes(**kwargs)
            attrs['type'] = self.get_input_type()

            # Build the attributes string
            attributes_str = self._build_attributes_string(attrs)

            return _render_input_tag(attributes_str)

        # Custom display format: native <input type="date"> can't show a
        # custom format (the browser always controls its display per the
        # HTML5 spec) -- fall back to a live-formatted text input instead,
        # the same approach PhoneInput/CurrencyInput use in text_inputs.py.
        if 'value' in kwargs and isinstance(kwargs['value'], date):
            kwargs['value'] = kwargs['value'].strftime(date_format)
        if 'min' in kwargs and isinstance(kwargs['min'], date):
            kwargs['min'] = kwargs['min'].strftime(date_format)
        if 'max' in kwargs and isinstance(kwargs['max'], date):
            kwargs['max'] = kwargs['max'].strftime(date_format)

        mask, pattern, placeholder = _translate_strftime(date_format)
        kwargs.setdefault('pattern', pattern)
        kwargs.setdefault('placeholder', placeholder)
        if mask is not None:
            kwargs.setdefault('inputmode', 'numeric')

        field_id = kwargs.get('id', kwargs.get('name', ''))
        show_picker_toggle = bool(
            live_format and field_id and _picker_toggle_js_expr(date_format) is not None
        )
        if show_picker_toggle:
            kwargs['style'] = _append_inline_style(
                str(kwargs.get('style', '')), _PICKER_TOGGLE_PADDING_STYLE
            )

        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = 'text'
        attributes_str = self._build_attributes_string(attrs)
        input_html = _render_input_tag(attributes_str)

        if show_picker_toggle:
            input_html = _wrap_with_picker_toggle(input_html, field_id, date_format, 'date')
        if live_format and field_id and mask is not None:
            input_html += _render_datetime_mask_script(field_id, mask)

        return input_html


class TimeInput(FormInput):
    """Time input field with time picker."""

    ui_element: str = 'time'

    template = """<input type="time" ${attributes} />"""

    def get_input_type(self) -> str:
        return 'time'

    def render(
        self, time_format: str | None = None, live_format: bool = True, **kwargs: Any
    ) -> str:
        """Render time input with proper formatting."""
        if time_format is None:
            # Convert time objects to string format
            if 'value' in kwargs and isinstance(kwargs['value'], time):
                kwargs['value'] = kwargs['value'].strftime('%H:%M')
            if 'min' in kwargs and isinstance(kwargs['min'], time):
                kwargs['min'] = kwargs['min'].strftime('%H:%M')
            if 'max' in kwargs and isinstance(kwargs['max'], time):
                kwargs['max'] = kwargs['max'].strftime('%H:%M')

            # Set default step for seconds if not provided
            if 'step' not in kwargs:
                kwargs['step'] = '60'  # 1 minute steps by default

            # Validate and format attributes
            attrs = self.validate_attributes(**kwargs)
            attrs['type'] = self.get_input_type()

            # Build the attributes string
            attributes_str = self._build_attributes_string(attrs)

            return _render_input_tag(attributes_str)

        # Custom display format (e.g. 24-hour/military time): native
        # <input type="time"> can't show a custom format, so fall back to a
        # live-formatted text input, the same approach PhoneInput/CurrencyInput
        # use in text_inputs.py. `step` (native-picker-only) is not applicable
        # to a text input, so it's deliberately not defaulted here.
        if 'value' in kwargs and isinstance(kwargs['value'], time):
            kwargs['value'] = kwargs['value'].strftime(time_format)
        if 'min' in kwargs and isinstance(kwargs['min'], time):
            kwargs['min'] = kwargs['min'].strftime(time_format)
        if 'max' in kwargs and isinstance(kwargs['max'], time):
            kwargs['max'] = kwargs['max'].strftime(time_format)

        mask, pattern, placeholder = _translate_strftime(time_format)
        kwargs.setdefault('pattern', pattern)
        kwargs.setdefault('placeholder', placeholder)
        if mask is not None:
            kwargs.setdefault('inputmode', 'numeric')

        field_id = kwargs.get('id', kwargs.get('name', ''))
        show_picker_toggle = bool(
            live_format and field_id and _picker_toggle_js_expr(time_format) is not None
        )
        if show_picker_toggle:
            kwargs['style'] = _append_inline_style(
                str(kwargs.get('style', '')), _PICKER_TOGGLE_PADDING_STYLE
            )

        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = 'text'
        attributes_str = self._build_attributes_string(attrs)
        input_html = _render_input_tag(attributes_str)

        if show_picker_toggle:
            input_html = _wrap_with_picker_toggle(input_html, field_id, time_format, 'time')
        if live_format and field_id and mask is not None:
            input_html += _render_datetime_mask_script(field_id, mask)

        return input_html


class DatetimeInput(FormInput):
    """Datetime-local input field with datetime picker."""

    ui_element: str = 'datetime'
    ui_element_aliases: tuple[str, ...] = ('datetime-local',)

    template = """<input type="datetime-local" ${attributes} />"""

    def get_input_type(self) -> str:
        return 'datetime-local'

    def render(
        self,
        auto_set_current: bool = False,
        with_set_now_button: bool = False,
        datetime_format: str | None = None,
        live_format: bool = True,
        **kwargs: Any,
    ) -> str:
        """Render datetime input with optional current time features."""
        if datetime_format is None:
            # Convert datetime objects to string format
            if 'value' in kwargs and isinstance(kwargs['value'], datetime):
                kwargs['value'] = kwargs['value'].strftime(_DATETIME_FMT)
            if 'min' in kwargs and isinstance(kwargs['min'], datetime):
                kwargs['min'] = kwargs['min'].strftime(_DATETIME_FMT)
            if 'max' in kwargs and isinstance(kwargs['max'], datetime):
                kwargs['max'] = kwargs['max'].strftime(_DATETIME_FMT)

            # Auto-set to current datetime if requested and no value provided
            if auto_set_current and 'value' not in kwargs:
                current_time = datetime.now().strftime(_DATETIME_FMT)
                kwargs['value'] = current_time

            # Validate and format attributes
            attrs = self.validate_attributes(**kwargs)
            attrs['type'] = self.get_input_type()

            # Build the attributes string
            attributes_str = self._build_attributes_string(attrs)

            datetime_html = _render_input_tag(attributes_str)

            # Add "Set Now" button if requested
            if with_set_now_button:
                field_name = kwargs.get('name', '')
                field_id = kwargs.get('id', field_name)

                onclick = f"setCurrentDatetime('{field_id}')"
                button_html = html(t'''
                <button type="button" class="set-now-btn" onclick="{onclick}">
                    Set Now
                </button>
                ''')
                # JS-only below (rule 4 exception).
                script_html = SafeHTML("""
                <script>
                function setCurrentDatetime(fieldId) {
                    const field = document.getElementById(fieldId);
                    if (field) {
                        const now = new Date();
                        const datetime = now.getFullYear() + '-' +
                            String(now.getMonth() + 1).padStart(2, '0') + '-' +
                            String(now.getDate()).padStart(2, '0') + 'T' +
                            String(now.getHours()).padStart(2, '0') + ':' +
                            String(now.getMinutes()).padStart(2, '0');
                        field.value = datetime;
                    }
                }
                </script>
                """)
                set_now_button = SafeHTML(button_html + script_html)
                _datetime_html = SafeHTML(str(datetime_html))
                return html(
                    t'<div class="datetime-input-group">{_datetime_html}{set_now_button}</div>'
                )

            return datetime_html

        # Custom display format: native <input type="datetime-local"> can't
        # show a custom format, so fall back to a live-formatted text input,
        # the same approach PhoneInput/CurrencyInput use in text_inputs.py.
        if 'value' in kwargs and isinstance(kwargs['value'], datetime):
            kwargs['value'] = kwargs['value'].strftime(datetime_format)
        if 'min' in kwargs and isinstance(kwargs['min'], datetime):
            kwargs['min'] = kwargs['min'].strftime(datetime_format)
        if 'max' in kwargs and isinstance(kwargs['max'], datetime):
            kwargs['max'] = kwargs['max'].strftime(datetime_format)

        # Auto-set to current datetime if requested and no value provided --
        # uses the custom format so the auto-filled value matches the field's
        # own expected shape instead of the default ISO-ish _DATETIME_FMT.
        if auto_set_current and 'value' not in kwargs:
            kwargs['value'] = datetime.now().strftime(datetime_format)

        mask, pattern, placeholder = _translate_strftime(datetime_format)
        kwargs.setdefault('pattern', pattern)
        kwargs.setdefault('placeholder', placeholder)
        if mask is not None:
            kwargs.setdefault('inputmode', 'numeric')

        field_name = kwargs.get('name', '')
        field_id = kwargs.get('id', field_name)
        show_picker_toggle = bool(
            live_format and field_id and _picker_toggle_js_expr(datetime_format) is not None
        )
        if show_picker_toggle:
            kwargs['style'] = _append_inline_style(
                str(kwargs.get('style', '')), _PICKER_TOGGLE_PADDING_STYLE
            )

        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = 'text'
        attributes_str = self._build_attributes_string(attrs)
        datetime_html = _render_input_tag(attributes_str)

        if show_picker_toggle:
            datetime_html = _wrap_with_picker_toggle(
                datetime_html, field_id, datetime_format, 'datetime-local'
            )
        if live_format and field_id and mask is not None:
            datetime_html += _render_datetime_mask_script(field_id, mask)

        # Add "Set Now" button if requested -- only for formats made
        # entirely of the numeric directives _render_set_now_button can
        # generate matching JS for; silently omitted otherwise rather than
        # writing a value that doesn't match the field's own expected shape.
        if with_set_now_button and field_id:
            set_now_button = _render_set_now_button(field_id, datetime_format)
            if set_now_button:
                _datetime_html = SafeHTML(str(datetime_html))
                _set_now_button = SafeHTML(set_now_button)
                return html(
                    t'<div class="datetime-input-group">{_datetime_html}{_set_now_button}</div>'
                )

        return datetime_html


class MonthInput(FormInput):
    """Month input field for selecting year and month."""

    ui_element: str = 'month'

    template = """<input type="month" ${attributes} />"""

    def get_input_type(self) -> str:
        return 'month'

    def render(self, **kwargs: Any) -> str:
        """Render month input with proper formatting."""
        # Convert date objects to month format (YYYY-MM)
        for key in ('value', 'min', 'max'):
            if key in kwargs and isinstance(kwargs[key], (datetime, date)):
                kwargs[key] = kwargs[key].strftime('%Y-%m')

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return _render_input_tag(attributes_str)


class WeekInput(FormInput):
    """Week input field for selecting year and week number."""

    ui_element: str = 'week'

    template = """<input type="week" ${attributes} />"""

    def get_input_type(self) -> str:
        return 'week'

    def render(self, **kwargs: Any) -> str:
        """Render week input with proper formatting."""
        # Convert date objects to week format (YYYY-W##)
        if 'value' in kwargs:
            if isinstance(kwargs['value'], datetime):
                year, week, _ = kwargs['value'].date().isocalendar()
                kwargs['value'] = f'{year}-W{week:02d}'
            elif isinstance(kwargs['value'], date):
                year, week, _ = kwargs['value'].isocalendar()
                kwargs['value'] = f'{year}-W{week:02d}'

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        return _render_input_tag(attributes_str)


class DateRangeInput:
    """Date range input with start and end date fields."""

    def __init__(self):
        self.start_input: DateInput = DateInput()
        self.end_input: DateInput = DateInput()

    def render(
        self,
        name: str,
        start_label: str = 'Start Date',
        end_label: str = 'End Date',
        start_value: str | date | None = None,
        end_value: str | date | None = None,
        **kwargs: Any,
    ) -> str:
        """Render date range with start and end inputs."""

        # Extract common attributes
        common_attrs = {}
        for attr in ['class', 'style', 'required', 'disabled']:
            if attr in kwargs:
                common_attrs[attr] = kwargs[attr]

        # Render start date
        start_attrs = {
            **common_attrs,
            'name': f'{name}_start',
            'id': f'{name}_start',
            'placeholder': 'Start date',
        }
        if start_value:
            start_attrs['value'] = start_value

        _start_input_html = SafeHTML(str(self.start_input.render(**start_attrs)))
        start_html = html(t'''
        <div class="date-range-start">
            <label for="{name}_start">{start_label}</label>
            {_start_input_html}
        </div>
        ''')

        # Render end date
        end_attrs = {
            **common_attrs,
            'name': f'{name}_end',
            'id': f'{name}_end',
            'placeholder': 'End date',
        }
        if end_value:
            end_attrs['value'] = end_value

        _end_input_html = SafeHTML(str(self.end_input.render(**end_attrs)))
        end_html = html(t'''
        <div class="date-range-end">
            <label for="{name}_end">{end_label}</label>
            {_end_input_html}
        </div>
        ''')

        # Add validation script to ensure end date is after start date
        # (JS-only content, rule 4 exception -- name is embedded as a JS
        # string literal, not an HTML attribute value).
        validation_script = SafeHTML(f"""
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
        """)

        return html(t'''
        <div class="date-range-input" data-name="{name}">
            {start_html}
            {end_html}
            {validation_script}
        </div>
        ''')


class TimeRangeInput:
    """Time range input with start and end time fields."""

    def __init__(self):
        self.start_input: TimeInput = TimeInput()
        self.end_input: TimeInput = TimeInput()

    def render(
        self,
        name: str,
        start_label: str = 'Start Time',
        end_label: str = 'End Time',
        start_value: str | time | None = None,
        end_value: str | time | None = None,
        **kwargs: Any,
    ) -> str:
        """Render time range with start and end inputs."""

        # Extract common attributes
        common_attrs = {}
        for attr in ['class', 'style', 'required', 'disabled', 'step']:
            if attr in kwargs:
                common_attrs[attr] = kwargs[attr]

        # Render start time
        start_attrs = {
            **common_attrs,
            'name': f'{name}_start',
            'id': f'{name}_start',
            'placeholder': 'Start time',
        }
        if start_value:
            start_attrs['value'] = start_value

        _start_input_html = SafeHTML(str(self.start_input.render(**start_attrs)))
        start_html = html(t'''
        <div class="time-range-start">
            <label for="{name}_start">{start_label}</label>
            {_start_input_html}
        </div>
        ''')

        # Render end time
        end_attrs = {
            **common_attrs,
            'name': f'{name}_end',
            'id': f'{name}_end',
            'placeholder': 'End time',
        }
        if end_value:
            end_attrs['value'] = end_value

        _end_input_html = SafeHTML(str(self.end_input.render(**end_attrs)))
        end_html = html(t'''
        <div class="time-range-end">
            <label for="{name}_end">{end_label}</label>
            {_end_input_html}
        </div>
        ''')

        # Add validation script to ensure end time is after start time
        # (JS-only content, rule 4 exception).
        validation_script = SafeHTML(f"""
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
        """)

        return html(t'''
        <div class="time-range-input" data-name="{name}">
            {start_html}
            {end_html}
            {validation_script}
        </div>
        ''')


class BirthdateInput(DateInput):
    """Specialized date input for birthdays with age calculation."""

    ui_element: str = 'birthdate'

    def render(self, show_age: bool = True, **kwargs: Any) -> str:
        """Render birthdate input with optional age display."""
        # Set reasonable constraints for birthdates
        if 'max' not in kwargs:
            kwargs['max'] = date.today().isoformat()
        if 'min' not in kwargs:
            # Default to 150 years ago
            min_year = date.today().year - 150
            kwargs['min'] = f'{min_year}-01-01'

        birthdate_html = super().render(**kwargs)

        if show_age:
            field_name = kwargs.get('name', '')
            field_id = kwargs.get('id', field_name)

            age_div = html(
                t'<div class="age-display" id="{field_name}_age" '
                t'style="margin-top: 5px; font-size: 0.9em; color: #666;"></div>'
            )
            # JS-only below (rule 4 exception).
            age_script = SafeHTML(f"""
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
            """)
            age_display = SafeHTML(age_div + age_script)
            _birthdate_html = SafeHTML(str(birthdate_html))
            return html(t'<div class="birthdate-input-group">{_birthdate_html}{age_display}</div>')

        return birthdate_html
