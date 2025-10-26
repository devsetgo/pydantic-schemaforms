"""
Modern form renderer using Python 3.14 template strings.

This module provides a high-performance form renderer that leverages Python 3.14's
native template string support for optimal rendering speed and developer experience.
"""

from typing import Any, Dict, List, Optional, Union, get_type_hints, get_origin, get_args
from pydantic import BaseModel
from dataclasses import dataclass, field

from .templates import FormTemplates, TemplateString


@dataclass
class RenderContext:
    """Context for template rendering with all necessary variables."""

    # Framework and styling
    framework: str = "bootstrap"
    theme: str = "default"
    css_framework: str = "bootstrap"

    # Form configuration
    form_id: str = "main-form"
    form_class: str = ""
    form_style: str = ""
    form_method: str = "POST"
    form_action: str = "/submit"

    # Input styling
    input_class: str = ""
    input_style: str = ""
    wrapper_class: str = ""
    wrapper_style: str = ""

    # Labels and help text
    show_labels: bool = True
    show_help_text: bool = True
    show_icons: bool = True
    required_indicator: str = "*"

    # Validation and errors
    show_errors: bool = True
    error_class: str = "is-invalid"
    live_validation: bool = False

    # Layout
    layout_class: str = ""
    layout_style: str = ""

    # Custom attributes
    custom_attributes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for template rendering."""
        return {
            'framework': self.framework,
            'theme': self.theme,
            'css_framework': self.css_framework,
            'form_id': self.form_id,
            'form_class': self.form_class,
            'form_style': self.form_style,
            'method': self.form_method,
            'action': self.form_action,
            'input_class': self.input_class,
            'input_style': self.input_style,
            'wrapper_class': self.wrapper_class,
            'wrapper_style': self.wrapper_style,
            'show_labels': self.show_labels,
            'show_help_text': self.show_help_text,
            'show_icons': self.show_icons,
            'required_indicator': self.required_indicator,
            'show_errors': self.show_errors,
            'error_class': self.error_class,
            'live_validation': self.live_validation,
            'layout_class': self.layout_class,
            'layout_style': self.layout_style,
            **self.custom_attributes
        }


class ModernFormRenderer:
    """
    Modern form renderer using Python 3.14 template strings.

    Provides high-performance form rendering with clean template syntax,
    automatic type inference, and comprehensive theming support.
    """

    def __init__(self, framework: str = "bootstrap", theme: str = "default"):
        """
        Initialize modern form renderer.

        Args:
            framework: CSS framework (bootstrap, material, shadcn)
            theme: Theme variant within framework
        """
        self.framework = framework
        self.theme = theme
        self._template_cache = {}

    def render_input(
        self,
        field_name: str,
        field_info: Any,
        field_type: type,
        value: Any = None,
        errors: Optional[List[str]] = None,
        context: Optional[RenderContext] = None
    ) -> str:
        """
        Render a single input field using modern templates.

        Args:
            field_name: Name of the field
            field_info: Pydantic field info
            field_type: Python type of the field
            value: Current field value
            errors: Validation errors for this field
            context: Rendering context

        Returns:
            Rendered HTML for the input field
        """
        if context is None:
            context = RenderContext(framework=self.framework, theme=self.theme)

        # Determine input type from Python type
        input_type = self._get_input_type(field_type, field_info)

        # Build template variables
        template_vars = self._build_template_vars(
            field_name, field_info, field_type, value, errors, context
        )

        # Select appropriate template
        template = self._select_template(input_type)

        # Render the template
        return template.render(**template_vars)

    def render_form(
        self,
        model_class: type[BaseModel],
        values: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, List[str]]] = None,
        context: Optional[RenderContext] = None
    ) -> str:
        """
        Render complete form from Pydantic model.

        Args:
            model_class: Pydantic model class
            values: Current form values
            errors: Validation errors by field
            context: Rendering context

        Returns:
            Complete HTML form
        """
        if context is None:
            context = RenderContext(framework=self.framework, theme=self.theme)

        if values is None:
            values = {}

        if errors is None:
            errors = {}

        # Get model fields and type hints
        model_fields = model_class.model_fields
        type_hints = get_type_hints(model_class)

        # Render each field
        field_html_parts = []
        for field_name, field_info in model_fields.items():
            field_type = type_hints.get(field_name, str)
            field_value = values.get(field_name)
            field_errors = errors.get(field_name, [])

            field_html = self.render_input(
                field_name, field_info, field_type, field_value, field_errors, context
            )
            field_html_parts.append(field_html)

        # Combine fields into form
        form_content = '\n'.join(field_html_parts)

        # Add submit button
        submit_button = self._render_submit_button(context)

        # Render complete form
        form_vars = {
            **context.to_dict(),
            'form_content': form_content,
            'submit_buttons': submit_button,
            'csrf_token': self._render_csrf_token(context),
            'form_attributes': self._build_form_attributes(context)
        }

        return FormTemplates.FORM_WRAPPER.render(**form_vars)

    def render_complete_page(
        self,
        model_class: type[BaseModel],
        title: str = "Form",
        values: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, List[str]]] = None,
        context: Optional[RenderContext] = None
    ) -> str:
        """
        Render complete HTML page with form.

        Args:
            model_class: Pydantic model class
            title: Page title
            values: Current form values
            errors: Validation errors by field
            context: Rendering context

        Returns:
            Complete HTML page
        """
        if context is None:
            context = RenderContext(framework=self.framework, theme=self.theme)

        # Render the form
        form_html = self.render_form(model_class, values, errors, context)

        # Build page variables
        page_vars = {
            'page_title': title,
            'form_content': form_html,
            'css_links': self._get_css_links(context),
            'js_links': self._get_js_links(context),
            'custom_styles': self._get_custom_styles(context),
            'custom_scripts': self._get_custom_scripts(context),
            'page_header': self._render_page_header(title, context),
            'page_footer': self._render_page_footer(context)
        }

        return FormTemplates.FORM_PAGE.render(**page_vars)

    def _get_input_type(self, field_type: type, field_info: Any) -> str:
        """Determine HTML input type from Python type and field info."""
        # Check for explicit input_type in field info
        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
            if 'input_type' in field_info.json_schema_extra:
                return field_info.json_schema_extra['input_type']

        # Check for FormField metadata
        if hasattr(field_info, 'metadata'):
            for meta in field_info.metadata:
                if hasattr(meta, 'input_type'):
                    return meta.input_type

        # Infer from Python type
        return self._infer_input_type_from_python_type(field_type)

    def _infer_input_type_from_python_type(self, python_type: type) -> str:
        """Infer HTML input type from Python type."""
        # Handle Optional types
        origin = get_origin(python_type)
        if origin is Union:
            args = get_args(python_type)
            if len(args) == 2 and type(None) in args:
                # This is Optional[T]
                python_type = args[0] if args[1] is type(None) else args[1]

        # Basic type mapping
        type_mapping = {
            int: 'number',
            float: 'number',
            bool: 'checkbox',
            str: 'text',
        }

        # Check for email in field name (common pattern)
        if python_type == str:
            return 'text'  # Default to text, can be overridden

        return type_mapping.get(python_type, 'text')

    def _build_template_vars(
        self,
        field_name: str,
        field_info: Any,
        field_type: type,
        value: Any,
        errors: Optional[List[str]],
        context: RenderContext
    ) -> Dict[str, Any]:
        """Build template variables for field rendering."""
        # Base variables
        vars_dict = {
            'id': field_name,
            'name': field_name,
            'value': str(value) if value is not None else '',
            'placeholder': '',
            'required': 'required' if field_info.is_required() else '',
            'disabled': '',
            'readonly': '',
            'attributes': '',
        }

        # Add context variables
        vars_dict.update(context.to_dict())

        # Handle field-specific attributes from field_info
        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if 'placeholder' in extra:
                vars_dict['placeholder'] = extra['placeholder']
            if 'title' in extra:
                vars_dict['label_text'] = extra['title']
            if 'help_text' in extra:
                vars_dict['help_content'] = extra['help_text']
            if 'icon' in extra:
                vars_dict['icon'] = self._render_icon(extra['icon'], context)

        # Handle FormField metadata
        if hasattr(field_info, 'metadata'):
            for meta in field_info.metadata:
                if hasattr(meta, 'title'):
                    vars_dict['label_text'] = meta.title
                if hasattr(meta, 'help_text'):
                    vars_dict['help_content'] = meta.help_text
                if hasattr(meta, 'icon'):
                    vars_dict['icon'] = self._render_icon(meta.icon, context)

        # Default label if not set
        if 'label_text' not in vars_dict:
            vars_dict['label_text'] = field_name.replace('_', ' ').title()

        # Render sub-components
        vars_dict['label'] = self._render_label(vars_dict, context)
        vars_dict['help_text'] = self._render_help_text(vars_dict, context)
        vars_dict['error_message'] = self._render_error_message(errors, context)

        # Handle numeric field attributes
        if field_type in (int, float):
            vars_dict.update(self._get_numeric_attributes(field_info))

        # Handle select field options
        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
            if 'choices' in field_info.json_schema_extra:
                vars_dict['options'] = self._render_select_options(
                    field_info.json_schema_extra['choices'], value
                )

        return vars_dict

    def _select_template(self, input_type: str) -> TemplateString:
        """Select appropriate template based on input type."""
        template_mapping = {
            'text': FormTemplates.TEXT_INPUT,
            'email': FormTemplates.EMAIL_INPUT,
            'password': FormTemplates.PASSWORD_INPUT,
            'number': FormTemplates.NUMBER_INPUT,
            'select': FormTemplates.SELECT_INPUT,
            'textarea': FormTemplates.TEXTAREA_INPUT,
            'checkbox': FormTemplates.CHECKBOX_INPUT,
            'radio': FormTemplates.RADIO_INPUT,
        }

        return template_mapping.get(input_type, FormTemplates.TEXT_INPUT)

    def _render_label(self, vars_dict: Dict[str, Any], context: RenderContext) -> str:
        """Render field label."""
        if not context.show_labels:
            return ''

        label_vars = {
            'for_id': vars_dict['id'],
            'label_class': 'form-label',
            'label_style': '',
            'label_text': vars_dict.get('label_text', ''),
            'icon': vars_dict.get('icon', ''),
            'required_indicator': context.required_indicator if vars_dict.get('required') else ''
        }

        return FormTemplates.LABEL.render(**label_vars)

    def _render_help_text(self, vars_dict: Dict[str, Any], context: RenderContext) -> str:
        """Render help text."""
        if not context.show_help_text or 'help_content' not in vars_dict:
            return ''

        help_vars = {
            'help_class': 'form-text text-muted',
            'help_style': '',
            'help_content': vars_dict['help_content']
        }

        return FormTemplates.HELP_TEXT.render(**help_vars)

    def _render_error_message(self, errors: Optional[List[str]], context: RenderContext) -> str:
        """Render error messages."""
        if not context.show_errors or not errors:
            return ''

        error_content = '<br>'.join(errors)
        error_vars = {
            'error_class': 'invalid-feedback',
            'error_style': 'display: block;',
            'error_content': error_content
        }

        return FormTemplates.ERROR_MESSAGE.render(**error_vars)

    def _render_icon(self, icon_name: str, context: RenderContext) -> str:
        """Render icon."""
        if not context.show_icons or not icon_name:
            return ''

        icon_vars = {
            'icon_name': icon_name,
            'icon_class': 'me-1',
            'icon_style': ''
        }

        return FormTemplates.ICON.render(**icon_vars)

    def _render_submit_button(self, context: RenderContext) -> str:
        """Render submit button."""
        if context.framework == 'bootstrap':
            return '<button type="submit" class="btn btn-primary">Submit</button>'
        elif context.framework == 'material':
            return '<button type="submit" class="btn waves-effect waves-light">Submit</button>'
        else:
            return '<button type="submit">Submit</button>'

    def _render_csrf_token(self, context: RenderContext) -> str:
        """Render CSRF token (placeholder for now)."""
        return ''

    def _build_form_attributes(self, context: RenderContext) -> str:
        """Build additional form attributes."""
        attributes = []
        if context.live_validation:
            attributes.append('data-live-validation="true"')

        return ' '.join(attributes)

    def _get_numeric_attributes(self, field_info: Any) -> Dict[str, str]:
        """Get numeric field attributes like min, max, step."""
        attrs = {
            'min_value': '',
            'max_value': '',
            'step': ''
        }

        # Check constraints
        if hasattr(field_info, 'constraints'):
            constraints = field_info.constraints
            if hasattr(constraints, 'ge') and constraints.ge is not None:
                attrs['min_value'] = str(constraints.ge)
            if hasattr(constraints, 'le') and constraints.le is not None:
                attrs['max_value'] = str(constraints.le)

        return attrs

    def _render_select_options(self, choices: List, selected_value: Any) -> str:
        """Render select options."""
        options = []
        for choice in choices:
            if isinstance(choice, (list, tuple)) and len(choice) == 2:
                value, label = choice
            else:
                value = label = choice

            selected = 'selected' if str(value) == str(selected_value) else ''
            options.append(f'<option value="{value}" {selected}>{label}</option>')

        return '\n'.join(options)

    def _get_css_links(self, context: RenderContext) -> str:
        """Get CSS links for the framework."""
        if context.framework == 'bootstrap':
            return '''
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
            '''
        elif context.framework == 'material':
            return '''
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
            '''
        else:
            return ''

    def _get_js_links(self, context: RenderContext) -> str:
        """Get JavaScript links for the framework."""
        base_js = '<script src="https://unpkg.com/htmx.org@2.0.4"></script>'

        if context.framework == 'bootstrap':
            return base_js + '''
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            '''
        elif context.framework == 'material':
            return base_js + '''
            <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
            '''
        else:
            return base_js

    def _get_custom_styles(self, context: RenderContext) -> str:
        """Get custom styles."""
        return '''
        <style>
        .pydantic-form {
            margin: 1rem 0;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .invalid-feedback {
            display: block;
        }
        </style>
        '''

    def _get_custom_scripts(self, context: RenderContext) -> str:
        """Get custom JavaScript."""
        return '''
        <script>
        function togglePassword(fieldId) {
            const field = document.getElementById(fieldId);
            const icon = document.getElementById(fieldId + '_toggle_icon');
            if (field.type === 'password') {
                field.type = 'text';
                icon.className = 'bi bi-eye-slash';
            } else {
                field.type = 'password';
                icon.className = 'bi bi-eye';
            }
        }
        </script>
        '''

    def _render_page_header(self, title: str, context: RenderContext) -> str:
        """Render page header."""
        return f'<div class="mb-4"><h1>{title}</h1></div>'

    def _render_page_footer(self, context: RenderContext) -> str:
        """Render page footer."""
        return ''
