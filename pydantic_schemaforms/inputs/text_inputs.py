"""Text input components: TextInput, PasswordInput, EmailInput, TextArea, SearchInput, and specialised variants."""

import json
import re
from typing import Any

from pydantic_schemaforms.tstring import SafeHTML, html

from .base import FormInput, _render_input_tag


def _mask_to_pattern(mask: str) -> str:
    """Turn a '#'-placeholder mask (e.g. '(###) ###-####') into a matching regex."""
    return ''.join(r'\d' if ch == '#' else re.escape(ch) for ch in mask)


class TextInput(FormInput):
    """Standard text input field."""

    ui_element: str = 'text'

    def get_input_type(self) -> str:
        return 'text'

    def render(self, **kwargs: Any) -> str:
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class PasswordInput(FormInput):
    """Password input field with masking."""

    ui_element: str = 'password'

    def get_input_type(self) -> str:
        return 'password'

    def render(self, **kwargs: Any) -> str:
        # Suppress autocomplete so browsers don't pre-fill saved passwords into new-password fields.
        if 'autocomplete' not in kwargs:
            kwargs['autocomplete'] = 'new-password'
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class EmailInput(FormInput):
    """Email input field with built-in validation."""

    ui_element: str = 'email'

    def get_input_type(self) -> str:
        return 'email'

    def render(self, **kwargs: Any) -> str:
        if 'inputmode' not in kwargs:
            kwargs['inputmode'] = 'email'  # numeric-friendly keyboard on mobile
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class SearchInput(FormInput):
    """Search input field with search-specific behavior."""

    ui_element: str = 'search'

    def get_input_type(self) -> str:
        return 'search'

    def render(self, **kwargs: Any) -> str:
        if 'inputmode' not in kwargs:
            kwargs['inputmode'] = 'search'
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class TextArea(FormInput):
    """Multi-line text input area."""

    ui_element: str = 'textarea'
    valid_attributes: list[str] = FormInput.valid_attributes + ['rows', 'cols', 'wrap', 'resize']

    def get_input_type(self) -> str:
        return 'textarea'  # Not a real input type, but used for identification.

    def render(self, **kwargs: Any) -> str:
        value = kwargs.pop('value', '')
        attrs = self.validate_attributes(**kwargs)
        if 'type' in attrs:
            del attrs['type']  # <textarea> has no type attribute.
        _attrs = SafeHTML(self._build_attributes_string(attrs))
        display_value = str(value) if value is not None else ''
        return html(t'<textarea {_attrs}>{display_value}</textarea>')


class URLInput(FormInput):
    """URL input field with URL validation."""

    ui_element: str = 'url'

    def get_input_type(self) -> str:
        return 'url'

    def render(self, **kwargs: Any) -> str:
        if 'inputmode' not in kwargs:
            kwargs['inputmode'] = 'url'
        if 'pattern' not in kwargs:
            kwargs['pattern'] = r'https?://.+'
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class TelInput(FormInput):
    """Telephone input field with phone number formatting."""

    ui_element: str = 'tel'

    def get_input_type(self) -> str:
        return 'tel'

    def render(self, **kwargs: Any) -> str:
        if 'inputmode' not in kwargs:
            kwargs['inputmode'] = 'tel'
        if 'autocomplete' not in kwargs:
            kwargs['autocomplete'] = 'tel'
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


# Specialised text inputs with formatting constraints.


class SSNInput(TextInput):
    """Social Security Number input with formatting."""

    ui_element: str = 'ssn'
    ui_element_aliases: tuple[str, ...] = ('social_security_number',)

    def render(self, **kwargs: Any) -> str:
        kwargs['pattern'] = r'\d{3}-\d{2}-\d{4}'
        kwargs['placeholder'] = kwargs.get('placeholder', '123-45-6789')
        kwargs['maxlength'] = '11'
        kwargs['inputmode'] = 'numeric'
        kwargs['autocomplete'] = 'off'
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class PhoneInput(TelInput):
    """Phone number input with country code support and an optional formatting mask."""

    ui_element: str = 'phone'
    ui_element_aliases: tuple[str, ...] = ('phone_number',)

    def render(
        self,
        country_code: str | None = None,
        phone_format: str | None = None,
        live_format: bool = True,
        **kwargs: Any,
    ) -> str:
        if country_code:
            if 'value' in kwargs and not kwargs['value'].startswith(country_code):
                kwargs['value'] = f'{country_code} {kwargs["value"]}'
            elif 'placeholder' in kwargs and not kwargs['placeholder'].startswith(country_code):
                kwargs['placeholder'] = f'{country_code} {kwargs["placeholder"]}'

        if phone_format is None:
            return super().render(**kwargs)

        kwargs.setdefault('maxlength', str(len(phone_format)))
        kwargs.setdefault('pattern', _mask_to_pattern(phone_format))
        kwargs.setdefault('placeholder', phone_format.replace('#', '0'))
        field_id = kwargs.get('id', kwargs.get('name', ''))
        input_html = super().render(**kwargs)

        if not live_format or not field_id:
            return input_html

        script = SafeHTML(rf"""
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const el = document.getElementById('{field_id}');
    const mask = {json.dumps(phone_format)};
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
        return input_html + script


class CreditCardInput(TextInput):
    """Credit card number input with formatting."""

    ui_element: str = 'credit_card'
    ui_element_aliases: tuple[str, ...] = ('card', 'cc_number')

    def render(self, **kwargs: Any) -> str:
        kwargs['pattern'] = r'\d{4}\s?\d{4}\s?\d{4}\s?\d{4}'
        kwargs['placeholder'] = kwargs.get('placeholder', '1234 5678 9012 3456')
        kwargs['maxlength'] = '19'  # 16 digits + 3 separator spaces
        kwargs['inputmode'] = 'numeric'
        kwargs['autocomplete'] = 'cc-number'
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class CurrencyInput(TextInput):
    """Currency input with live thousands-separator formatting."""

    ui_element: str = 'currency'
    ui_element_aliases: tuple[str, ...] = ('money',)

    def render(self, currency_symbol: str = '$', live_format: bool = True, **kwargs: Any) -> str:
        kwargs['pattern'] = rf'^\{currency_symbol}?[\d,]*(\.\d{{2}})?$'
        kwargs['placeholder'] = kwargs.get('placeholder', f'{currency_symbol}0.00')
        kwargs['inputmode'] = 'decimal'
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        input_html = _render_input_tag(self._build_attributes_string(attrs))

        field_id = kwargs.get('id', kwargs.get('name', ''))
        if not live_format or not field_id:
            return input_html

        script = SafeHTML(rf"""
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const el = document.getElementById('{field_id}');
    const symbol = {json.dumps(currency_symbol)};
    if (el) {{
        el.addEventListener('input', function() {{
            const caretFromEnd = el.value.length - (el.selectionEnd || 0);
            const raw = el.value.replace(/[^0-9.]/g, '');
            const parts = raw.split('.');
            let whole = parts[0].replace(/^0+(?=\d)/, '');
            const cents = parts.length > 1 ? '.' + parts[1].slice(0, 2) : '';
            whole = whole.replace(/\B(?=(\d{{3}})+(?!\d))/g, ',');
            el.value = whole || cents ? symbol + whole + cents : '';
            const pos = Math.max(0, el.value.length - caretFromEnd);
            el.setSelectionRange(pos, pos);
        }});
    }}
}});
</script>
""")
        return input_html + script
