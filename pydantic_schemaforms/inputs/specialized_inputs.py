"""
Specialized input components using Python 3.14 template strings.
Includes FileInput, ColorInput, HiddenInput, ImageInput, ButtonInput, etc.
"""

import hashlib
import hmac
import json
import random
from typing import Any

from pydantic_schemaforms.tstring import SafeHTML, html

from .base import FileInputBase, FormInput, _render_input_tag


class FileInput(FileInputBase):
    """File upload input with drag-and-drop support."""

    ui_element: str = 'file'

    def get_input_type(self) -> str:
        return 'file'

    def render(
        self,
        accept: str | None = None,
        multiple: bool = False,
        capture: str | None = None,
        show_preview: bool = True,
        enable_drag_drop: bool = True,
        **kwargs: Any,
    ) -> str:
        """Render file input with optional preview and drag-and-drop support."""

        if accept:
            kwargs['accept'] = accept
        if multiple:
            kwargs['multiple'] = True
        if capture:
            kwargs['capture'] = capture

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Render the input
        file_html = f'<input {attributes_str} />'

        field_name = kwargs.get('name', '')
        field_id = kwargs.get('id', field_name)

        if enable_drag_drop:
            file_html = f"""
            <div class="file-drop-zone" id="{field_id}_dropzone">
                {file_html}
                <div class="file-drop-zone-hint">Drag and drop files here, or click to browse</div>
            </div>
            """

        preview_html = ''
        if show_preview:
            preview_html = f"""
            <div class="file-preview" id="{field_name}_preview" style="margin-top: 10px;"></div>
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const fileInput = document.getElementById('{field_id}');
                const preview = document.getElementById('{field_name}_preview');

                if (fileInput && preview) {{
                    fileInput.addEventListener('change', function() {{
                        preview.innerHTML = '';

                        if (this.files) {{
                            Array.from(this.files).forEach(function(file) {{
                                const fileItem = document.createElement('div');
                                fileItem.className = 'file-item';
                                fileItem.style.cssText = 'margin: 5px 0; padding: 5px; border: 1px solid #ddd; border-radius: 3px;';

                                // Use file info to create content  # noqa: F821
                                let content = `<strong>${{file.name}}</strong> (${{(file.size / 1024).toFixed(1)}} KB)`;

                                // Show image preview for image files
                                if (file.type.startsWith('image/')) {{  # noqa: F821
                                    const reader = new FileReader();
                                    reader.onload = function(e) {{
                                        const img = document.createElement('img');
                                        img.src = e.target.result;
                                        img.style.cssText = 'max-width: 100px; max-height: 100px; margin-left: 10px;';
                                        fileItem.appendChild(img);
                                    }};
                                    reader.readAsDataURL(file);
                                }}

                                fileItem.innerHTML = content;
                                preview.appendChild(fileItem);
                            }});
                        }}
                    }});
                }}
            }});
            </script>
            """

        drag_drop_script = ''
        if enable_drag_drop:
            drag_drop_script = f"""
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const dropzone = document.getElementById('{field_id}_dropzone');
                const fileInput = document.getElementById('{field_id}');
                if (!dropzone || !fileInput) return;

                ['dragenter', 'dragover'].forEach(function(evt) {{
                    dropzone.addEventListener(evt, function(e) {{
                        e.preventDefault();
                        e.stopPropagation();
                        dropzone.classList.add('file-drop-zone-active');
                    }});
                }});
                ['dragleave', 'drop'].forEach(function(evt) {{
                    dropzone.addEventListener(evt, function(e) {{
                        e.preventDefault();
                        e.stopPropagation();
                        dropzone.classList.remove('file-drop-zone-active');
                    }});
                }});
                dropzone.addEventListener('drop', function(e) {{
                    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {{
                        fileInput.files = e.dataTransfer.files;
                        fileInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }});
            }});
            </script>
            """

        if not (show_preview or enable_drag_drop):
            return file_html

        return f'<div class="file-input-group">{file_html}{preview_html}{drag_drop_script}</div>'


class ImageInput(FormInput):
    """Image input that acts as a submit button."""

    valid_attributes: list[str] = FormInput.valid_attributes + [
        'src',
        'alt',
        'width',
        'height',
        'formaction',
        'formenctype',
        'formmethod',
        'formnovalidate',
        'formtarget',
    ]

    def get_input_type(self) -> str:
        return 'image'

    def render(self, src: str, alt: str, **kwargs: Any) -> str:
        """Render image input with required src and alt attributes."""
        kwargs['src'] = src
        kwargs['alt'] = alt

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Render the input
        return f'<input {attributes_str} />'


class ColorInput(FormInput):
    """Color picker input."""

    ui_element: str = 'color'

    def get_input_type(self) -> str:
        return 'color'

    def render(self, show_value: bool = True, **kwargs: Any) -> str:
        """Render color input with optional color value display."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        color_html = _render_input_tag(self._build_attributes_string(attrs))

        if show_value:
            field_name = kwargs.get('name', '')
            field_id = kwargs.get('id', field_name)
            current_value = kwargs.get('value', '#000000')

            value_display = f"""
            <div class="color-value-display" style="display: inline-flex; align-items: center; margin-left: 10px;">
                <span id="{field_name}_value" style="font-family: monospace;">{current_value}</span>
                <div id="{field_name}_swatch" style="width: 20px; height: 20px; background-color: {current_value}; border: 1px solid #ccc; margin-left: 5px;"></div>
            </div>
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const colorInput = document.getElementById('{field_id}');
                const valueSpan = document.getElementById('{field_name}_value');
                const swatch = document.getElementById('{field_name}_swatch');

                if (colorInput && valueSpan && swatch) {{
                    colorInput.addEventListener('input', function() {{
                        valueSpan.textContent = this.value;
                        swatch.style.backgroundColor = this.value;
                    }});
                }}
            }});
            </script>
            """
            return f'<div class="color-input-group">{color_html}{value_display}</div>'

        return color_html


class HiddenInput(FormInput):
    """Hidden input field."""

    ui_element: str = 'hidden'

    def get_input_type(self) -> str:
        return 'hidden'

    def render(self, **kwargs: Any) -> str:
        """Render hidden input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        return _render_input_tag(self._build_attributes_string(attrs))


class ButtonInput(FormInput):
    """Button input field."""

    valid_attributes: list[str] = FormInput.valid_attributes + [
        'popovertarget',
        'popovertargetaction',
    ]

    def get_input_type(self) -> str:
        return 'button'

    def render(self, **kwargs: Any) -> str:
        """Render button input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        return _render_input_tag(self._build_attributes_string(attrs))


class SubmitInput(FormInput):
    """Submit button input."""

    valid_attributes: list[str] = FormInput.valid_attributes + [
        'formaction',
        'formenctype',
        'formmethod',
        'formnovalidate',
        'formtarget',
    ]

    def get_input_type(self) -> str:
        return 'submit'

    def render(self, **kwargs: Any) -> str:
        """Render submit input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        return _render_input_tag(self._build_attributes_string(attrs))


class ResetInput(FormInput):
    """Reset button input."""

    def get_input_type(self) -> str:
        return 'reset'

    def render(self, **kwargs: Any) -> str:
        """Render reset input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()

        return _render_input_tag(self._build_attributes_string(attrs))


class CSRFInput(HiddenInput):
    """CSRF token hidden input for security."""

    ui_element: str = 'csrf'

    def render(self, token: str, **kwargs: Any) -> str:
        """Render CSRF input with token value."""
        kwargs['name'] = kwargs.get('name', 'csrf_token')
        kwargs['value'] = token
        return super().render(**kwargs)


class HoneypotInput(HiddenInput):
    """Honeypot input for spam protection."""

    ui_element: str = 'honeypot'

    def render(self, **kwargs: Any) -> str:
        """Render honeypot input that should remain empty."""
        # Use a name that looks like a real field but is actually a trap
        kwargs['name'] = kwargs.get('name', 'website_url')
        kwargs['value'] = ''
        kwargs['style'] = 'display: none !important;'
        kwargs['tabindex'] = '-1'
        kwargs['autocomplete'] = 'off'
        return super().render(**kwargs)


def _sign_captcha_challenge(num1: int, num2: int, secret_key: str) -> str:
    payload = f'{num1}:{num2}'
    signature = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f'{payload}:{signature}'


def verify_captcha(*, token: str, answer: str, secret_key: str) -> bool:
    """Verify a CaptchaInput challenge server-side.

    The correct sum is never sent to the browser -- only num1/num2 (the
    human-readable question) and an HMAC-signed token are. This recomputes
    and constant-time-compares the signature before checking the arithmetic,
    so a hand-edited num1/num2 in a tampered token is rejected before the sum
    is even evaluated.
    """
    try:
        num1_str, num2_str, signature = token.split(':', 2)
        num1, num2 = int(num1_str), int(num2_str)
    except ValueError, AttributeError:
        return False

    expected_token = _sign_captcha_challenge(num1, num2, secret_key)
    _, _, expected_signature = expected_token.split(':', 2)
    if not hmac.compare_digest(signature, expected_signature):
        return False

    try:
        return int(answer) == num1 + num2
    except TypeError, ValueError:
        return False


class CaptchaInput(FormInput):
    """Self-hosted arithmetic CAPTCHA. The correct answer is never sent to the client.

    render() emits both the visible answer input (named `{field_name}`) and a
    signed hidden token (named `{field_name}_token`) as part of one composite
    HTML block. Only declare the visible answer as a FormModel field -- do NOT
    also declare a separate `{field_name}_token` field for it: FormModel uses
    Pydantic's `extra='ignore'` on submission, and this widget re-renders (and
    re-signs) a brand new challenge on every render call, so a second,
    independently-declared field would just add its own unrelated, stale
    hidden input rather than carrying the real token through.

    Verify the submission server-side with `verify_captcha()` at the route
    level, mirroring how CSRF is checked in this library -- pop the token from
    the raw submitted form data before validation, not from the model::

        from pydantic_schemaforms.inputs.specialized_inputs import verify_captcha

        class MyForm(FormModel):
            captcha_answer: str = Field(
                ..., ui_element='captcha', ui_options={'secret_key': SECRET}
            )

        # in the POST route, before calling MyForm.validate(...):
        form_dict = dict(await request.form())
        token = form_dict.pop('captcha_answer_token', None)
        if not verify_captcha(token=token, answer=form_dict.get('captcha_answer'), secret_key=SECRET):
            # re-render with a form-level error; a fresh challenge is
            # generated automatically since a new CaptchaInput() is
            # instantiated on every render
            ...

    This is a route-level check like CSRF (not a `@model_validator`) because
    the token only exists in the raw POST body, never as a model attribute.
    """

    ui_element: str = 'captcha'

    def __init__(self) -> None:
        self.num1: int = random.randint(1, 10)
        self.num2: int = random.randint(1, 10)

    def get_input_type(self) -> str:
        return 'text'

    def render(self, *, secret_key: str, name: str = 'captcha', **kwargs: Any) -> str:
        """Render the CAPTCHA question, answer input, and a signed challenge token.

        `secret_key` is required (no default) so a misconfigured app fails
        loudly instead of silently falling back to an insecure key.
        """
        field_id = kwargs.get('id', name)
        token = _sign_captcha_challenge(self.num1, self.num2, secret_key)

        kwargs['name'] = name
        kwargs['id'] = field_id
        kwargs.setdefault('placeholder', 'Enter the answer')
        kwargs.setdefault('autocomplete', 'off')
        kwargs.setdefault('required', True)
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        # NOSONAR comments below: each variable is read via {expr}
        # interpolation in the t-string return statement -- Sonar's Python
        # analyzer doesn't parse PEP 750 t-strings yet, so it can't see the
        # reference and flags a false-positive "unused local variable".
        text_input_html = SafeHTML(
            _render_input_tag(self._build_attributes_string(attrs))
        )  # NOSONAR

        hidden_input = HiddenInput()
        token_html = SafeHTML(hidden_input.render(name=f'{name}_token', value=token))  # NOSONAR

        num1, num2 = self.num1, self.num2  # NOSONAR
        return html(t'''
        <div class="captcha-input">
            <label for="{field_id}">What is {num1} + {num2}?</label>
            {text_input_html}
            {token_html}
        </div>
        ''')


class RatingStarsInput(FormInput):
    """Star rating input: individually clickable stars, not a slider (contrast with RatingInput)."""

    ui_element: str = 'star_rating'

    def get_input_type(self) -> str:
        return 'star-rating'  # not a real HTML input type, used for identification only

    def render(
        self,
        name: str = '',
        max_stars: int = 5,
        value: int | str | None = None,
        current_rating: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Render star rating input.

        Accepts both `value` (the name field_renderer.py passes for a model's
        current value) and `current_rating` (this widget's original direct-call
        parameter name) -- current_rating wins if both are given, so existing
        direct callers are unaffected.
        """
        field_id = kwargs.get('id', name)
        rating_source = current_rating if current_rating is not None else value
        try:
            rating = int(rating_source) if rating_source not in (None, '') else 0
        except TypeError, ValueError:
            rating = 0

        # NOSONAR comments below: each variable is read via {expr}
        # interpolation in the t-string return statement -- Sonar's Python
        # analyzer doesn't parse PEP 750 t-strings yet, so it can't see the
        # reference and flags a false-positive "unused local variable".
        hidden_input = HiddenInput()
        hidden_html = SafeHTML(  # NOSONAR
            hidden_input.render(name=name, id=f'{field_id}_value', value=str(rating))
        )

        star_parts: list[str] = []
        for i in range(1, max_stars + 1):
            star_class = 'star-filled' if i <= rating else 'star-empty'  # NOSONAR
            star_parts.append(
                html(t'<span class="rating-star {star_class}" data-rating="{i}">★</span>')
            )
        stars_html = SafeHTML(''.join(star_parts))  # NOSONAR

        _star_rating_assets_markup = f"""
            <style>
            .star-rating-input .stars {{
                font-size: 24px;
                cursor: pointer;
            }}
            .star-rating-input .rating-star {{
                color: #ddd;
                transition: color 0.2s;
            }}
            .star-rating-input .rating-star.star-filled,
            .star-rating-input .rating-star:hover,
            .star-rating-input .rating-star.hover {{
                color: #ffd700;
            }}
            </style>
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const starsContainer = document.getElementById('{field_id}_stars');
                const hiddenInput = document.getElementById('{field_id}_value');
                const stars = starsContainer.querySelectorAll('.rating-star');

                stars.forEach(function(star, index) {{
                    star.addEventListener('mouseenter', function() {{
                        stars.forEach(function(s, i) {{
                            s.classList.toggle('hover', i <= index);
                        }});
                    }});

                    star.addEventListener('mouseleave', function() {{
                        stars.forEach(function(s) {{
                            s.classList.remove('hover');
                        }});
                    }});

                    star.addEventListener('click', function() {{
                        const rating = parseInt(this.dataset.rating);
                        hiddenInput.value = rating;

                        stars.forEach(function(s, i) {{
                            s.classList.toggle('star-filled', i < rating);
                        }});
                    }});
                }});
            }});
            </script>
        """
        assets = SafeHTML(_star_rating_assets_markup)  # NOSONAR

        return html(t'''
        <div class="star-rating-input" data-name="{name}">
            <div class="stars" id="{field_id}_stars">
                {stars_html}
            </div>
            {hidden_html}
            {assets}
        </div>
        ''')


class TagsInput(FormInput):
    """Tags/chips input: hidden input stores the joined value; text input adds/removes chips."""

    ui_element: str = 'tags'

    def get_input_type(self) -> str:
        return 'text'

    def render(
        self,
        name: str = '',
        placeholder: str = 'Enter tags...',
        separator: str = ',',
        **kwargs: Any,
    ) -> str:
        """Render tags input widget."""
        field_id = kwargs.get('id', name)
        initial_tags = kwargs.get('value', '') or ''

        # NOSONAR comments below: each variable is read via {expr}
        # interpolation in the t-string return statement -- Sonar's Python
        # analyzer doesn't parse PEP 750 t-strings yet, so it can't see the
        # reference and flags a false-positive "unused local variable".
        hidden_input = HiddenInput()
        hidden_html = SafeHTML(  # NOSONAR
            hidden_input.render(name=name, id=f'{field_id}_value', value=initial_tags)
        )

        text_attrs = self.validate_attributes(
            id=f'{field_id}_input', placeholder=placeholder, autocomplete='off'
        )
        text_attrs['type'] = 'text'
        text_input_html = SafeHTML(  # NOSONAR
            _render_input_tag(self._build_attributes_string(text_attrs))
        )

        separator_js = json.dumps(separator)
        _tags_assets_markup = f"""
            <style>
            .tags-input {{
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                min-height: 40px;
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 5px;
            }}
            .tags-input input {{
                border: none;
                outline: none;
                flex: 1;
                min-width: 100px;
            }}
            .tag {{
                background: #007bff;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }}
            .tag .remove {{
                cursor: pointer;
                font-weight: bold;
            }}
            </style>
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const container = document.getElementById('{field_id}_container');
                const input = document.getElementById('{field_id}_input');
                const hiddenInput = document.getElementById('{field_id}_value');
                let tags = [];

                if (hiddenInput.value) {{
                    tags = hiddenInput.value.split({separator_js}).filter(Boolean);
                    renderTags();
                }}

                function renderTags() {{
                    container.innerHTML = '';
                    tags.forEach(function(tag, index) {{
                        const tagEl = document.createElement('span');
                        tagEl.className = 'tag';
                        const label = document.createTextNode(tag + ' ');
                        const remove = document.createElement('span');
                        remove.className = 'remove';
                        remove.textContent = '×';
                        remove.addEventListener('click', function() {{ removeTag(index); }});
                        tagEl.appendChild(label);
                        tagEl.appendChild(remove);
                        container.appendChild(tagEl);
                    }});
                    hiddenInput.value = tags.join({separator_js});
                }}

                function removeTag(index) {{
                    tags.splice(index, 1);
                    renderTags();
                }}

                input.addEventListener('keydown', function(e) {{
                    if (e.key === 'Enter' || e.key === {separator_js}) {{
                        e.preventDefault();
                        const value = this.value.trim();
                        if (value && !tags.includes(value)) {{
                            tags.push(value);
                            renderTags();
                            this.value = '';
                        }}
                    }} else if (e.key === 'Backspace' && this.value === '' && tags.length > 0) {{
                        tags.pop();
                        renderTags();
                    }}
                }});
            }});
            </script>
        """
        assets = SafeHTML(_tags_assets_markup)  # NOSONAR

        return html(t'''
        <div class="tags-input" data-name="{name}">
            <div class="tags-container" id="{field_id}_container"></div>
            {text_input_html}
            {hidden_html}
            {assets}
        </div>
        ''')
