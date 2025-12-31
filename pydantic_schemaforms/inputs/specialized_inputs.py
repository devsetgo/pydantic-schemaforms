"""
Specialized input components using Python 3.14 template strings.
Includes FileInput, ColorInput, HiddenInput, ImageInput, ButtonInput, etc.
"""

from typing import Optional

from .base import FileInputBase, FormInput


class FileInput(FileInputBase):
    """File upload input with drag-and-drop support."""

    ui_element = "file"

    def get_input_type(self) -> str:
        return "file"

    def render(
        self,
        accept: Optional[str] = None,
        multiple: bool = False,
        capture: Optional[str] = None,
        show_preview: bool = True,
        **kwargs,
    ) -> str:
        """Render file input with optional preview functionality."""

        if accept:
            kwargs["accept"] = accept
        if multiple:
            kwargs["multiple"] = True
        if capture:
            kwargs["capture"] = capture

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Render the input
        file_html = f"<input {attributes_str} />"

        if show_preview:
            field_name = kwargs.get("name", "")
            field_id = kwargs.get("id", field_name)

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
            return f'<div class="file-input-group">{file_html}{preview_html}</div>'

        return file_html


class ImageInput(FormInput):
    """Image input that acts as a submit button."""

    valid_attributes = FormInput.valid_attributes + [
        "src",
        "alt",
        "width",
        "height",
        "formaction",
        "formenctype",
        "formmethod",
        "formnovalidate",
        "formtarget",
    ]

    def get_input_type(self) -> str:
        return "image"

    def render(self, src: str, alt: str, **kwargs) -> str:
        """Render image input with required src and alt attributes."""
        kwargs["src"] = src
        kwargs["alt"] = alt

        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Render the input
        return f"<input {attributes_str} />"


class ColorInput(FormInput):
    """Color picker input."""

    ui_element = "color"

    def get_input_type(self) -> str:
        return "color"

    def render(self, show_value: bool = True, **kwargs) -> str:
        """Render color input with optional color value display."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        from .base import render_template

        template = t"<input {attributes_str} />"
        color_html = render_template(template)

        if show_value:
            field_name = kwargs.get("name", "")
            field_id = kwargs.get("id", field_name)
            current_value = kwargs.get("value", "#000000")

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

    ui_element = "hidden"

    def get_input_type(self) -> str:
        return "hidden"

    def render(self, **kwargs) -> str:
        """Render hidden input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        from .base import render_template

        template = t"<input {attributes_str} />"
        return render_template(template)


class ButtonInput(FormInput):
    """Button input field."""

    valid_attributes = FormInput.valid_attributes + ["popovertarget", "popovertargetaction"]

    def get_input_type(self) -> str:
        return "button"

    def render(self, **kwargs) -> str:
        """Render button input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        from .base import render_template

        template = t"<input {attributes_str} />"
        return render_template(template)


class SubmitInput(FormInput):
    """Submit button input."""

    valid_attributes = FormInput.valid_attributes + [
        "formaction",
        "formenctype",
        "formmethod",
        "formnovalidate",
        "formtarget",
    ]

    def get_input_type(self) -> str:
        return "submit"

    def render(self, **kwargs) -> str:
        """Render submit input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        from .base import render_template

        template = t"<input {attributes_str} />"
        return render_template(template)


class ResetInput(FormInput):
    """Reset button input."""

    def get_input_type(self) -> str:
        return "reset"

    def render(self, **kwargs) -> str:
        """Render reset input using Python 3.14 template strings."""
        # Validate and format attributes
        attrs = self.validate_attributes(**kwargs)
        attrs["type"] = self.get_input_type()

        # Build the attributes string
        attributes_str = self._build_attributes_string(attrs)

        # Use Python 3.14 template string literal and render it
        from .base import render_template

        template = t"<input {attributes_str} />"
        return render_template(template)


class CSRFInput(HiddenInput):
    """CSRF token hidden input for security."""

    def render(self, token: str, **kwargs) -> str:
        """Render CSRF input with token value."""
        kwargs["name"] = kwargs.get("name", "csrf_token")
        kwargs["value"] = token
        return super().render(**kwargs)


class HoneypotInput(HiddenInput):
    """Honeypot input for spam protection."""

    def render(self, **kwargs) -> str:
        """Render honeypot input that should remain empty."""
        # Use a name that looks like a real field but is actually a trap
        kwargs["name"] = kwargs.get("name", "website_url")
        kwargs["value"] = ""
        kwargs["style"] = "display: none !important;"
        kwargs["tabindex"] = "-1"
        kwargs["autocomplete"] = "off"
        return super().render(**kwargs)


class CaptchaInput:
    """Simple math captcha input for spam protection."""

    def __init__(self):
        import random

        self.num1 = random.randint(1, 10)
        self.num2 = random.randint(1, 10)
        self.answer = self.num1 + self.num2

    def render(self, name: str = "captcha", **kwargs) -> str:
        """Render math captcha with validation."""
        field_id = kwargs.get("id", name)

        # Create hidden input with the answer
        hidden_input = HiddenInput()
        hidden_html = hidden_input.render(name=f"{name}_answer", value=str(self.answer))

        # Create text input for user answer
        text_input = FormInput()
        text_attrs = {
            "name": name,
            "id": field_id,
            "type": "text",
            "required": True,
            "placeholder": "Enter the answer",
            "autocomplete": "off",
            **kwargs,
        }
        text_html = text_input.render(**text_attrs)

        # Create the complete captcha
        captcha_html = f"""
        <div class="captcha-input">
            <label for="{field_id}">What is {self.num1} + {self.num2}?</label>
            {text_html}
            {hidden_html}
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const form = document.querySelector('form');
                if (form) {{
                    form.addEventListener('submit', function(e) {{
                        const captchaInput = document.getElementById('{field_id}');
                        const answerInput = document.querySelector('input[name="{name}_answer"]');

                        if (captchaInput && answerInput) {{
                            if (parseInt(captchaInput.value) !== parseInt(answerInput.value)) {{
                                e.preventDefault();
                                alert('Incorrect captcha answer. Please try again.');
                                captchaInput.focus();
                                return false;
                            }}
                        }}
                    }});
                }}
            }});
            </script>
        </div>
        """

        return captcha_html


class RatingStarsInput:
    """Star rating input widget."""

    def render(self, name: str, max_stars: int = 5, current_rating: int = 0, **kwargs) -> str:
        """Render star rating input."""
        field_id = kwargs.get("id", name)

        # Create hidden input to store the rating value
        hidden_input = HiddenInput()
        hidden_html = hidden_input.render(
            name=name, id=f"{field_id}_value", value=str(current_rating)
        )

        # Create star display
        stars_html = []
        for i in range(1, max_stars + 1):
            star_class = "star-filled" if i <= current_rating else "star-empty"
            stars_html.append(f'<span class="rating-star {star_class}" data-rating="{i}">★</span>')

        rating_html = f"""
        <div class="star-rating-input" data-name="{name}">
            <div class="stars" id="{field_id}_stars">
                {''.join(stars_html)}
            </div>
            {hidden_html}
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
        </div>
        """

        return rating_html


class TagsInput:
    """Tags input widget for entering multiple tags."""

    def render(
        self, name: str, placeholder: str = "Enter tags...", separator: str = ",", **kwargs
    ) -> str:
        """Render tags input widget."""
        field_id = kwargs.get("id", name)
        initial_tags = kwargs.get("value", "")

        # Create hidden input to store tag values
        hidden_input = HiddenInput()
        hidden_html = hidden_input.render(name=name, id=f"{field_id}_value", value=initial_tags)

        # Create visible input for typing
        text_attrs = {
            "type": "text",
            "id": f"{field_id}_input",
            "placeholder": placeholder,
            "autocomplete": "off",
        }

        text_input = FormInput()
        text_html = text_input.render(**text_attrs)

        tags_html = f"""
        <div class="tags-input" data-name="{name}">
            <div class="tags-container" id="{field_id}_container"></div>
            {text_html}
            {hidden_html}
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

                // Initialize with existing tags
                if (hiddenInput.value) {{
                    tags = hiddenInput.value.split('{separator}').filter(Boolean);
                    renderTags();
                }}

                function renderTags() {{
                    container.innerHTML = '';
                    tags.forEach(function(tag, index) {{
                        const tagEl = document.createElement('span');
                        tagEl.className = 'tag';
                        tagEl.innerHTML = `${{tag}} <span class="remove" onclick="removeTag(${{index}})">×</span>`;
                        container.appendChild(tagEl);
                    }});
                    hiddenInput.value = tags.join('{separator}');
                }}

                window.removeTag = function(index) {{
                    tags.splice(index, 1);
                    renderTags();
                }};

                input.addEventListener('keydown', function(e) {{
                    if (e.key === 'Enter' || e.key === '{separator}') {{
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
        </div>
        """

        return tags_html
