"""Text input components: TextInput, PasswordInput, EmailInput, TextArea, SearchInput, and specialised variants."""

import json
import re
from typing import Any

from pydantic_schemaforms.assets.runtime import read_asset_text
from pydantic_schemaforms.tstring import SafeHTML, html

from .base import FormInput, _render_input_tag


def _mask_to_pattern(mask: str) -> str:
    """Turn a '#'-placeholder mask (e.g. '(###) ###-####') into a matching regex."""
    return ''.join(r'\d' if ch == '#' else re.escape(ch) for ch in mask)


_CODE_LANGUAGES: tuple[str, ...] = ('json', 'yaml', 'toml', 'bash', 'python')
_CODE_FORMAT_LABELS: dict[str, str] = {
    'json': 'Format',
    'yaml': 'Format',
    'toml': 'Format',
    'bash': 'Clean up whitespace',
    'python': 'Clean up whitespace',
}


def _vendored_code_asset(relative_path: str) -> str:
    """Read a vendored code-mode asset; '' if it hasn't been vendored (yet)."""
    try:
        return read_asset_text(relative_path)
    except FileNotFoundError:
        return ''


def _code_format_library_js(language: str) -> str:
    """JS defining the real parser/serializer global for yaml/toml, if vendored.

    JSON needs no library (native JSON.parse/stringify); bash/python use a
    hand-rolled normalizer inlined directly in the format function, not a
    vendored dependency.
    """
    if language == 'yaml':
        js = _vendored_code_asset('assets/vendor/js-yaml/js-yaml.umd.min.js')
        return f'if (!window.jsyaml) {{\n{js}\n}}' if js else ''
    if language == 'toml':
        js = _vendored_code_asset('assets/vendor/smol-toml/smol-toml.min.js')
        if not js:
            return ''
        # smol-toml ships dist/index.cjs (CommonJS); this shim is the only
        # non-upstream code involved -- the vendored file itself stays
        # byte-identical to what was downloaded and checksummed.
        return (
            'if (!window.TOML) {\n'
            '(function(){ var module = { exports: {} }; var exports = module.exports;\n'
            f'{js}\n'
            'window.TOML = module.exports; })();\n'
            '}'
        )
    return ''


def _code_highlight_assets(language: str) -> tuple[str, str]:
    """Return (js, css) for Prism core + this language's grammar; ('', '') if not vendored."""
    core = _vendored_code_asset('assets/vendor/prismjs/prism-core.min.js')
    grammar = _vendored_code_asset(f'assets/vendor/prismjs/prism-{language}.min.js')
    if not core or not grammar:
        return '', ''
    css = _vendored_code_asset('assets/vendor/prismjs/prism-theme.min.css')
    # Wrapped in its own IIFE (not just an `if` block) so the guard actually
    # skips re-declaring `Prism` when multiple code-mode fields share a page --
    # `var` inside a plain skipped `if` block still hoists into the enclosing
    # closure and would shadow `window.Prism` with `undefined` for every field
    # after the first.
    js = f'if (!window.Prism) {{\n(function(){{\n{core}\n}})();\n}}\n{grammar}'
    return js, css


def _code_area_enhancement(
    *,
    field_id: str,
    language: str,
    textarea_html: str,
    code_format: bool,
    code_highlight: bool,
    code_tab_indent: bool,
    indent_size: int,
) -> str:
    """Wrap a rendered <textarea> with optional format/highlight/tab-indent enhancement.

    The native <textarea> is always present unmodified and is what actually
    submits -- the wrapper/script only layer optional client-side behavior
    on top, following the same resilience pattern as PhoneInput/CurrencyInput/
    MultiSelectInput (progressive enhancement, never crash, never hide the
    native control until the enhancement has actually built).
    """
    library_js = _code_format_library_js(language) if code_format else ''
    highlight_js, highlight_css = _code_highlight_assets(language) if code_highlight else ('', '')
    format_label = _CODE_FORMAT_LABELS.get(language, 'Format')

    _textarea = SafeHTML(textarea_html)

    _toolbar: SafeHTML | str = ''
    if code_format:
        _toolbar = html(
            t'<div class="code-format-toolbar">'
            t'<button type="button" class="code-format-btn" '
            t'id="{field_id}_code_format_btn">{format_label}</button></div>'
        )

    _highlight_layer: SafeHTML | str = ''
    if highlight_js:
        _highlight_layer = html(
            t'<pre class="code-highlight-layer" id="{field_id}_code_layer" aria-hidden="true">'
            t'<code id="{field_id}_code_layer_inner" class="language-{language}"></code></pre>'
        )

    _error_el = html(t'<div class="code-format-error" id="{field_id}_code_error"></div>')

    wrapper = html(
        t'<div class="code-textarea-wrap">{_toolbar}{_highlight_layer}{_textarea}{_error_el}</div>'
    )

    tab_js = ''
    if code_tab_indent:
        tab_js = """
    el.addEventListener('keydown', function(e) {
        if (e.key !== 'Tab') return;
        e.preventDefault();
        const start = el.selectionStart;
        const end = el.selectionEnd;
        const pad = ' '.repeat(indentSize);
        el.value = el.value.slice(0, start) + pad + el.value.slice(end);
        el.selectionStart = el.selectionEnd = start + pad.length;
        el.dispatchEvent(new Event('input', { bubbles: true }));
    });"""

    format_js = ''
    if code_format:
        format_js = f"""
    function formatCode(text) {{
        if (language === 'json') {{
            try {{
                return {{ ok: true, text: JSON.stringify(JSON.parse(text), null, indentSize) }};
            }} catch (e) {{ return {{ ok: false, error: e.message }}; }}
        }}
        if (language === 'yaml' && window.jsyaml) {{
            try {{
                return {{
                    ok: true,
                    text: window.jsyaml.dump(window.jsyaml.load(text), {{ indent: indentSize }})
                }};
            }} catch (e) {{ return {{ ok: false, error: e.message }}; }}
        }}
        if (language === 'toml' && window.TOML) {{
            try {{
                return {{ ok: true, text: window.TOML.stringify(window.TOML.parse(text)) }};
            }} catch (e) {{ return {{ ok: false, error: e.message }}; }}
        }}
        if (language === 'bash' || language === 'python') {{
            const pad = ' '.repeat(indentSize);
            const lines = text.replace(/\\r\\n/g, '\\n').split('\\n').map(function(line) {{
                return line.replace(/\\t/g, pad).replace(/[ \\t]+$/, '');
            }});
            const collapsed = [];
            let blankRun = 0;
            for (const line of lines) {{
                if (line === '') {{
                    blankRun++;
                    if (blankRun <= 1) collapsed.push(line);
                }} else {{
                    blankRun = 0;
                    collapsed.push(line);
                }}
            }}
            while (collapsed.length && collapsed[collapsed.length - 1] === '') collapsed.pop();
            return {{ ok: true, text: collapsed.join('\\n') + '\\n' }};
        }}
        return {{ ok: false, error: 'Formatter unavailable' }};
    }}

    const errorEl = document.getElementById('{field_id}_code_error');
    const btnEl = document.getElementById('{field_id}_code_format_btn');
    if (btnEl) {{
        btnEl.addEventListener('click', function() {{
            const result = formatCode(el.value);
            if (result.ok) {{
                el.value = result.text;
                el.classList.remove('code-invalid');
                if (errorEl) {{ errorEl.style.display = 'none'; errorEl.textContent = ''; }}
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }} else {{
                el.classList.add('code-invalid');
                if (errorEl) {{
                    errorEl.style.display = 'block';
                    errorEl.textContent = result.error;
                }}
            }}
        }});
    }}
    el.addEventListener('input', function() {{
        if (el.classList.contains('code-invalid')) {{
            el.classList.remove('code-invalid');
            if (errorEl) {{ errorEl.style.display = 'none'; errorEl.textContent = ''; }}
        }}
    }});"""

    highlight_wire_js = ''
    if highlight_js:
        highlight_wire_js = f"""
    const codeEl = document.getElementById('{field_id}_code_layer_inner');
    const preEl = document.getElementById('{field_id}_code_layer');
    if (codeEl && preEl && window.Prism && window.Prism.languages['{language}']) {{
        function syncHighlight() {{
            codeEl.textContent = el.value;
            window.Prism.highlightElement(codeEl);
            preEl.scrollTop = el.scrollTop;
            preEl.scrollLeft = el.scrollLeft;
        }}
        el.addEventListener('input', syncHighlight);
        el.addEventListener('scroll', function() {{
            preEl.scrollTop = el.scrollTop;
            preEl.scrollLeft = el.scrollLeft;
        }});
        syncHighlight();
        el.classList.add('code-highlight-active');
    }}"""

    if not (tab_js or format_js or highlight_wire_js):
        return str(wrapper)

    library_js_block = f'\n    {library_js}' if library_js else ''
    highlight_js_block = f'\n    {highlight_js}' if highlight_js else ''

    css = f"""
.code-textarea-wrap {{ position: relative; }}
.code-textarea-wrap textarea, .code-highlight-layer {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.875rem;
    line-height: 1.5;
    white-space: pre;
    padding: 8px;
    border: 1px solid #79747e;
    border-radius: 4px;
    box-sizing: border-box;
    margin: 0;
    tab-size: {indent_size};
}}
.code-highlight-layer {{
    position: absolute;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
    z-index: 0;
    border-color: transparent;
}}
.code-textarea-wrap textarea.code-highlight-active {{
    position: relative;
    z-index: 1;
    background: transparent;
    color: transparent;
    caret-color: currentColor;
}}
.code-format-toolbar {{ display: flex; justify-content: flex-end; margin-bottom: 4px; }}
.code-format-btn {{ font-size: 0.75rem; padding: 2px 8px; cursor: pointer; }}
.code-format-error {{ color: #b91c1c; font-size: 0.75rem; margin-top: 2px; display: none; }}
textarea.code-invalid {{ outline: 2px solid #b91c1c; }}
{highlight_css}"""

    # Style/script block is developer-authored markup, not user data; `field_id`
    # and `language` are interpolated into JS string literals/selectors (not an
    # HTML-attribute position), so f-strings are used per CLAUDE.md's JS exception.
    script = SafeHTML(f"""
<style>{css}
</style>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    const el = document.getElementById('{field_id}');
    if (!el) return;
    const language = {json.dumps(language)};
    const indentSize = {indent_size};
{library_js_block}
{highlight_js_block}
{tab_js}
{format_js}
{highlight_wire_js}
}});
</script>""")

    return str(wrapper) + str(script)


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

    def render(
        self,
        language: str | None = None,
        code_format: bool = True,
        code_highlight: bool = True,
        code_tab_indent: bool = True,
        indent_size: int = 2,
        **kwargs: Any,
    ) -> str:
        value = kwargs.pop('value', '')
        resize = kwargs.pop('resize', None)
        attrs = self.validate_attributes(**kwargs)
        if 'type' in attrs:
            del attrs['type']  # <textarea> has no type attribute.
        if resize:
            # 'resize' is a CSS property, not an HTML attribute -- merge it into
            # `style` rather than emitting it as a bare (invalid) attribute.
            existing_style = str(attrs.get('style') or '').strip().rstrip(';')
            resize_style = f'resize: {resize}'
            attrs['style'] = f'{existing_style}; {resize_style}' if existing_style else resize_style
        _attrs = SafeHTML(self._build_attributes_string(attrs))
        display_value = str(value) if value is not None else ''
        textarea_html = html(t'<textarea {_attrs}>{display_value}</textarea>')

        if language not in _CODE_LANGUAGES:
            return textarea_html

        field_id = kwargs.get('id', kwargs.get('name', ''))
        if not field_id:
            return textarea_html

        return _code_area_enhancement(
            field_id=field_id,
            language=language,
            textarea_html=textarea_html,
            code_format=code_format,
            code_highlight=code_highlight,
            code_tab_indent=code_tab_indent,
            indent_size=indent_size,
        )


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
