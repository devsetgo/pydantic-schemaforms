"""
Modern Form Renderer using Python 3.14 template strings and modular input system.
Provides high-performance form generation with multiple framework support.
"""

from typing import Any, Dict, List, Optional, Callable
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .inputs import (
    TextInput, PasswordInput, EmailInput, NumberInput, CheckboxInput,
    SelectInput, DateInput, DatetimeInput, FileInput, ColorInput, RangeInput,
    HiddenInput, RadioGroup, TextArea, SearchInput, TelInput, URLInput,
    MonthInput, WeekInput, TimeInput, SubmitInput, ResetInput, ButtonInput,
    CSRFInput, HoneypotInput, ToggleSwitch, MultiSelectInput,
    build_label
)
from html import escape


class FormField:
    """Enhanced form field configuration with validation support."""

    def __init__(
        self,
        name: str,
        field_type: str = "text",
        label: Optional[str] = None,
        required: bool = False,
        placeholder: Optional[str] = None,
        help_text: Optional[str] = None,
        value: Any = None,
        options: Optional[List[Dict[str, Any]]] = None,
        validators: Optional[List[Callable]] = None,
        **kwargs
    ):
        self.name = name
        self.field_type = field_type
        self.label = label or name.replace("_", " ").title()
        self.required = required
        self.placeholder = placeholder
        self.help_text = help_text
        self.value = value
        self.options = options or []
        self.validators = validators or []
        self.extra_attrs = kwargs
        self.errors: List[str] = []

    def validate(self, value: Any) -> bool:
        """Run field-level validation."""
        self.errors = []

        # Required field validation
        if self.required and (value is None or value == ""):
            self.errors.append(f"{self.label} is required")
            return False

        # Run custom validators
        for validator in self.validators:
            try:
                validator(value)
            except ValueError as e:
                self.errors.append(str(e))

        return len(self.errors) == 0


class FormSection:
    """Form section for organizing fields into logical groups."""

    def __init__(
        self,
        title: str,
        fields: List[FormField],
        layout: str = "vertical",
        collapsible: bool = False,
        collapsed: bool = False,
        **kwargs
    ):
        self.title = title
        self.fields = fields
        self.layout = layout  # 'vertical', 'horizontal', 'grid'
        self.collapsible = collapsible
        self.collapsed = collapsed
        self.extra_attrs = kwargs


class FormDefinition:
    """Enhanced form definition with sections and advanced configuration."""

    def __init__(
        self,
        title: str = "Form",
        sections: Optional[List[FormSection]] = None,
        fields: Optional[List[FormField]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        css_framework: str = "bootstrap",
        live_validation: bool = True,
        csrf_protection: bool = False,
        honeypot_protection: bool = False,
        **kwargs
    ):
        self.title = title
        self.sections = sections or []
        self.fields = fields or []
        self.submit_url = submit_url
        self.method = method
        self.css_framework = css_framework
        self.live_validation = live_validation
        self.csrf_protection = csrf_protection
        self.honeypot_protection = honeypot_protection
        self.extra_attrs = kwargs

        # If fields are provided without sections, create a default section
        if self.fields and not self.sections:
            self.sections = [FormSection("Main", self.fields)]


class ModernFormRenderer:
    """
    Modern form renderer with Python 3.14 template strings and async support.
    """

    # Framework configurations with enhanced theming
    FRAMEWORKS = {
        "bootstrap": {
            "css_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
            "js_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
            "form_class": "needs-validation",
            "input_class": "form-control",
            "select_class": "form-select",
            "checkbox_class": "form-check-input",
            "radio_class": "form-check",
            "button_class": "btn btn-primary",
            "container_class": "container-fluid",
            "row_class": "row",
            "col_class": "col-md-12",
            "field_wrapper": "mb-3",
            "error_class": "invalid-feedback",
            "help_class": "form-text"
        },
        "material": {
            "css_url": "https://fonts.googleapis.com/icon?family=Material+Icons",
            "css_url2": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css",
            "js_url": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js",
            "form_class": "card-panel",
            "input_class": "validate",
            "select_class": "browser-default",
            "checkbox_class": "filled-in",
            "radio_class": "",
            "button_class": "btn waves-effect waves-light",
            "container_class": "container",
            "row_class": "row",
            "col_class": "col s12",
            "field_wrapper": "input-field",
            "error_class": "helper-text red-text",
            "help_class": "helper-text"
        },
        "tailwind": {
            "css_url": "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
            "form_class": "space-y-6 bg-white p-6 rounded-lg shadow-md",
            "input_class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
            "select_class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
            "checkbox_class": "rounded",
            "radio_class": "",
            "button_class": "bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded",
            "container_class": "max-w-2xl mx-auto",
            "row_class": "grid grid-cols-1 gap-6",
            "col_class": "",
            "field_wrapper": "mb-4",
            "error_class": "text-red-500 text-sm mt-1",
            "help_class": "text-gray-500 text-sm mt-1"
        }
    }

    # Input type mapping to renderer classes
    INPUT_RENDERERS = {
        "text": TextInput,
        "password": PasswordInput,
        "email": EmailInput,
        "number": NumberInput,
        "checkbox": CheckboxInput,
        "select": SelectInput,
        "multiselect": MultiSelectInput,
        "date": DateInput,
        "datetime": DatetimeInput,
        "time": TimeInput,
        "month": MonthInput,
        "week": WeekInput,
        "file": FileInput,
        "color": ColorInput,
        "range": RangeInput,
        "hidden": HiddenInput,
        "radio": RadioGroup,
        "textarea": TextArea,
        "search": SearchInput,
        "tel": TelInput,
        "url": URLInput,
        "submit": SubmitInput,
        "reset": ResetInput,
        "button": ButtonInput,
        "toggle": ToggleSwitch,
        "csrf": CSRFInput,
        "honeypot": HoneypotInput
    }

    def __init__(self, framework: str = "bootstrap", enable_async: bool = False):
        self.framework = framework
        self.config = self.FRAMEWORKS.get(framework, self.FRAMEWORKS["bootstrap"])
        self.enable_async = enable_async
        self.executor = ThreadPoolExecutor(max_workers=4) if enable_async else None

    async def render_form_async(self, form_def: FormDefinition, **kwargs) -> str:
        """Async form rendering for high-performance applications."""
        if not self.enable_async:
            return self.render_form(form_def, **kwargs)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.render_form,
            form_def,
            **kwargs
        )

    def render_form(self, form_def: FormDefinition, **kwargs) -> str:
        """Render complete HTML form from FormDefinition."""

        # Update framework config if different from instance
        if form_def.css_framework != self.framework:
            config = self.FRAMEWORKS.get(form_def.css_framework, self.config)
        else:
            config = self.config

        # Render form sections
        sections_html = self._render_sections(form_def.sections, config)

        # Generate CSRF field if enabled
        csrf_field = ""
        if form_def.csrf_protection:
            csrf_token = kwargs.get("csrf_token", "dummy_token")
            csrf_input = CSRFInput()
            csrf_field = csrf_input.render(token=csrf_token)

        # Generate honeypot field if enabled
        honeypot_field = ""
        if form_def.honeypot_protection:
            honeypot_input = HoneypotInput()
            honeypot_field = honeypot_input.render()

        # Generate action buttons
        submit_button = self._render_submit_button(config, kwargs.get("submit_text", "Submit"))
        reset_button = self._render_reset_button(config, kwargs.get("reset_text", "Reset"))

        # Build CSS and JS links
        css_links = self._build_css_links(config)
        js_links = self._build_js_links(config)

        # Generate validation script
        validation_script = self._generate_validation_script(form_def, config)

        # Build form attributes
        form_attributes = self._build_form_attributes(form_def, **kwargs)

        # Custom CSS for framework-specific styling
        custom_css = self._generate_custom_css(config)

        # Create the complete HTML using Python 3.14 template strings
        title = escape(form_def.title)
        container_class = config["container_class"]
        row_class = config["row_class"]
        col_class = config["col_class"]
        form_class = config["form_class"]
        method = form_def.method
        submit_url = form_def.submit_url

        # Build the complete form template
        template = t'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css_links}
    {custom_css}
</head>
<body>
    <div class="{container_class}">
        <div class="{row_class}">
            <div class="{col_class}">
                <h1 class="form-title">{title}</h1>
                <form id="main-form" method="{method}" action="{submit_url}"
                      class="{form_class}" {form_attributes}>
                    {csrf_field}
                    {honeypot_field}
                    {sections_html}
                    <div class="form-actions">
                        {submit_button}
                        {reset_button}
                    </div>
                </form>
                <div id="form-response" class="form-response"></div>
            </div>
        </div>
    </div>
    {js_links}
    {validation_script}
</body>
</html>'''

        # Import render_template function
        from .inputs.base import render_template
        return render_template(template)

    def _render_sections(self, sections: List[FormSection], config: Dict[str, str]) -> str:
        """Render form sections with different layouts."""
        sections_html = []

        for section in sections:
            section_html = self._render_section(section, config)
            sections_html.append(section_html)

        return "\n".join(sections_html)

    def _render_section(self, section: FormSection, config: Dict[str, str]) -> str:
        """Render a single form section."""
        fields_html = []

        for field in section.fields:
            field_html = self._render_field(field, config)
            fields_html.append(field_html)

        # Apply layout
        if section.layout == "horizontal":
            field_divs = [f'<div class="col">{field}</div>' for field in fields_html]
            fields_container = f'<div class="row">{" ".join(field_divs)}</div>'
        elif section.layout == "grid":
            grid_cols = section.extra_attrs.get("grid_columns", 2)
            field_divs = [f'<div class="col">{field}</div>' for field in fields_html]
            fields_container = f'<div class="row row-cols-{grid_cols}">{" ".join(field_divs)}</div>'
        else:  # vertical (default)
            fields_container = "\n".join(fields_html)

        # Wrap in section container
        section_class = "form-section"
        if section.collapsible:
            section_class += " collapsible"
            if section.collapsed:
                section_class += " collapsed"

        section_html = f'''
        <fieldset class="{section_class}">
            <legend class="section-title">{escape(section.title)}</legend>
            <div class="section-content">
                {fields_container}
            </div>
        </fieldset>
        '''

        return section_html

    def _render_field(self, field: FormField, config: Dict[str, str]) -> str:
        """Render a single form field with proper wrapper and styling."""

        # Get the appropriate input renderer
        renderer_class = self.INPUT_RENDERERS.get(field.field_type, TextInput)
        renderer = renderer_class()

        # Build field attributes
        field_attrs = {
            "name": field.name,
            "id": field.name,
            "class": self._get_field_class(field.field_type, config),
            **field.extra_attrs
        }

        # Add common attributes
        if field.required:
            field_attrs["required"] = True
        if field.placeholder:
            field_attrs["placeholder"] = field.placeholder
        if field.value is not None:
            field_attrs["value"] = field.value

        # Handle special field types
        if field.field_type in ["select", "multiselect"] and field.options:
            field_attrs["options"] = field.options
        elif field.field_type == "radio" and field.options:
            field_attrs["options"] = field.options
            field_attrs["group_name"] = field.name
            field_attrs["legend"] = field.label

        # Render the input
        if hasattr(renderer, 'render_with_label'):
            # Use enhanced rendering with label, help text, and errors
            input_html = renderer.render_with_label(
                label=field.label,
                help_text=field.help_text,
                error=field.errors[0] if field.errors else None,
                **field_attrs
            )
        else:
            # Basic rendering
            input_html = renderer.render(**field_attrs)

            # Add label, help text, and errors manually
            parts = []
            if field.field_type not in ["hidden", "csrf", "honeypot"]:
                parts.append(build_label(field.name, field.label, field.required))
            parts.append(input_html)
            if field.help_text:
                parts.append(f'<div class="{config["help_class"]}">{escape(field.help_text)}</div>')
            if field.errors:
                parts.append(f'<div class="{config["error_class"]}">{escape(field.errors[0])}</div>')

            input_html = "\n".join(parts)

        # Wrap in field container
        wrapper_class = config.get("field_wrapper", "mb-3")
        if field.errors:
            wrapper_class += " has-error"

        return f'<div class="{wrapper_class}">{input_html}</div>'

    def _get_field_class(self, field_type: str, config: Dict[str, str]) -> str:
        """Get CSS class for field type based on framework."""
        if field_type in ["select", "multiselect"]:
            return config["select_class"]
        elif field_type in ["checkbox", "toggle"]:
            return config["checkbox_class"]
        elif field_type == "radio":
            return config["radio_class"]
        else:
            return config["input_class"]

    def _render_submit_button(self, config: Dict[str, str], text: str) -> str:
        """Render submit button."""
        submit_input = SubmitInput()
        return submit_input.render(
            value=text,
            class_=config["button_class"]
        )

    def _render_reset_button(self, config: Dict[str, str], text: str) -> str:
        """Render reset button."""
        reset_input = ResetInput()
        return reset_input.render(
            value=text,
            class_=f"{config['button_class']} btn-secondary"
        )

    def _build_css_links(self, config: Dict[str, str]) -> str:
        """Build CSS links for the framework."""
        links = []
        if "css_url" in config:
            links.append(f'<link href="{config["css_url"]}" rel="stylesheet">')
        if "css_url2" in config:
            links.append(f'<link href="{config["css_url2"]}" rel="stylesheet">')

        # Add HTMX for dynamic interactions
        links.append('<script src="https://unpkg.com/htmx.org@1.9.6"></script>')

        return "\n".join(links)

    def _build_js_links(self, config: Dict[str, str]) -> str:
        """Build JavaScript links for the framework."""
        links = []
        if "js_url" in config:
            links.append(f'<script src="{config["js_url"]}"></script>')

        return "\n".join(links)

    def _generate_validation_script(self, form_def: FormDefinition, config: Dict[str, str]) -> str:
        """Generate client-side validation JavaScript."""
        if not form_def.live_validation:
            return ""

        return '''
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('main-form');

            // Enable Bootstrap validation styling
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });

            // Live validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(function(input) {
                input.addEventListener('blur', function() {
                    this.classList.add('was-validated');
                });
            });
        });
        </script>
        '''

    def _build_form_attributes(self, form_def: FormDefinition, **kwargs) -> str:
        """Build additional form attributes."""
        attrs = []

        if form_def.live_validation:
            attrs.append('novalidate')

        # Add HTMX attributes if specified
        if "hx_post" in kwargs:
            attrs.append(f'hx-post="{kwargs["hx_post"]}"')
        if "hx_target" in kwargs:
            attrs.append(f'hx-target="{kwargs["hx_target"]}"')
        if "hx_swap" in kwargs:
            attrs.append(f'hx-swap="{kwargs["hx_swap"]}"')

        return " ".join(attrs)

    def _generate_custom_css(self, config: Dict[str, str]) -> str:
        """Generate framework-specific custom CSS."""
        return '''
        <style>
        .form-section {
            margin-bottom: 2rem;
        }
        .form-section.collapsible .section-title {
            cursor: pointer;
        }
        .form-section.collapsed .section-content {
            display: none;
        }
        .form-response {
            margin-top: 1rem;
        }
        .was-validated .form-control:invalid {
            border-color: #dc3545;
        }
        .was-validated .form-control:valid {
            border-color: #28a745;
        }
        </style>
        '''
