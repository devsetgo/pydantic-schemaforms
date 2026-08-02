"""
Base classes and utilities for form inputs with Python 3.14 template strings.
"""

from abc import ABC, abstractmethod
from html import escape
from typing import Any

from pydantic_schemaforms.tstring import SafeHTML, html


_CLOSE_DIV = '</div>'


def _render_input_tag(attributes_str: str) -> str:
    _attrs = SafeHTML(attributes_str)
    return html(t'<input {_attrs} />')


class BaseInput(ABC):
    """Common attribute handling + rendering contract for all input widgets."""

    ui_element: str | None = None
    ui_element_aliases: tuple[str, ...] = ()
    valid_attributes: list[str] = [
        'name',
        'id',
        'class',
        'style',
        'title',
        'dir',
        'lang',
        'tabindex',
        'accesskey',
        'contenteditable',
        'draggable',
        'hidden',
        'spellcheck',
        'translate',
        'role',
        'aria-label',
        'aria-labelledby',
        'aria-describedby',
        'aria-hidden',
        'aria-expanded',
        'aria-controls',
        'aria-haspopup',
        'aria-invalid',
        'aria-required',
    ]

    @abstractmethod
    def get_input_type(self) -> str:
        """Return the HTML input type for concrete input classes."""

    def validate_attributes(self, **kwargs: Any) -> dict[str, Any]:
        """Validate and sanitize input attributes consistently across subclasses."""
        validated: dict[str, Any] = {}

        name = kwargs.get('name')
        if name:
            validated['name'] = str(name)

        element_id = kwargs.get('id', name)
        if element_id:
            validated['id'] = str(element_id)

        for attr, value in kwargs.items():
            if attr in {'name', 'id'}:
                continue

            if (
                attr in self.valid_attributes
                or attr.startswith('data-')
                or attr.startswith('aria-')
            ):
                formatted = self._format_attribute_value(attr, value)
                if formatted:
                    validated[attr] = formatted
            else:
                if value is not None:
                    validated[attr] = str(value)

        return validated

    def _format_attribute_value(self, attr: str, value: Any) -> str:
        if isinstance(value, bool):
            return attr if value else ''
        if value is None:
            return ''
        if isinstance(value, (list, tuple, set)):
            return ' '.join(str(v) for v in value if v is not None)
        return str(value)

    def _build_attributes_string(self, attrs: dict[str, Any]) -> str:
        parts: list[str] = []
        for key, value in attrs.items():
            if isinstance(value, bool):
                if value:
                    parts.append(key)
            elif value not in (None, ''):
                escaped_value = escape(str(value), quote=True)
                parts.append(f'{key}="{escaped_value}"')
        return ' '.join(parts)

    @abstractmethod
    def render(self, **kwargs: Any) -> str:
        """Concrete inputs must implement HTML rendering."""


class FormInput(BaseInput):
    """Base class for form input elements with form-specific attributes."""

    valid_attributes: list[str] = BaseInput.valid_attributes + [
        'value',
        'placeholder',
        'required',
        'disabled',
        'readonly',
        'autofocus',
        'autocomplete',
        'form',
        'formaction',
        'formenctype',
        'formmethod',
        'formnovalidate',
        'formtarget',
        'list',
        'maxlength',
        'minlength',
        'pattern',
        'size',
        'type',
        'accept',
        'alt',
        'checked',
        'dirname',
        'max',
        'min',
        'multiple',
        'step',
        'wrap',
        'rows',
        'cols',
        'inputmode',
    ]

    def render_with_label(
        self,
        label: str | None = None,
        help_text: str | None = None,
        error: str | None = None,
        icon: str | None = None,
        framework: str = 'bootstrap',
        options: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the input with its label, help text, and error message."""
        from pydantic_schemaforms.icon_mapping import map_icon_for_framework

        if icon:
            icon = map_icon_for_framework(icon, framework)

        if hasattr(self, 'render'):
            if options is not None:
                input_html = self.render(options=options, **kwargs)
            else:
                input_html = self.render(**kwargs)
        else:
            attrs = self.validate_attributes(**kwargs)
            input_type = getattr(self, 'get_input_type', lambda: 'text')()
            attrs['type'] = input_type
            input_html = _render_input_tag(self._build_attributes_string(attrs))

        _input_html = SafeHTML(str(input_html))
        field_parts: list[str] = []

        if framework == 'bootstrap':
            if label:
                label_html = build_label(
                    kwargs.get('name', 'field'),
                    label,
                    kwargs.get('required', False),
                    icon,
                    framework,
                )
                field_parts.append(label_html)

            field_parts.append(_input_html)

            if help_text:
                field_parts.append(html(t'<div class="form-text">{help_text}</div>'))

            if error:
                field_parts.append(html(t'<div class="invalid-feedback d-block">{error}</div>'))
        else:
            if label:
                label_html = build_label(
                    kwargs.get('name', 'field'),
                    label,
                    kwargs.get('required', False),
                    icon,
                    framework,
                )
                field_parts.append(label_html)

            field_parts.append(_input_html)

            if help_text:
                field_parts.append(html(t'<div class="help-text">{help_text}</div>'))

            if error:
                field_parts.append(html(t'<div class="error-text">{error}</div>'))

        return '\n'.join(field_parts)


def build_label(
    field_name: str,
    label: str | None = None,
    required: bool = False,
    icon: str | None = None,
    framework: str = 'bootstrap',
) -> str:
    """Build label element with optional icon support."""
    display_label = label or field_name.replace('_', ' ').title()
    required_indicator = ' *' if required else ''
    icon_html: SafeHTML = SafeHTML('')
    if icon:
        if framework == 'bootstrap':
            icon_class = icon if icon.startswith('bi bi-') else f'bi bi-{icon}'
            icon_html = html(t'<i class="{icon_class}"></i> ')
        elif framework == 'material':
            icon_html = html(t'<i class="material-icons">{icon}</i> ')
        elif framework == 'fontawesome':
            icon_class = icon if icon.startswith('fas fa-') else f'fas fa-{icon}'
            icon_html = html(t'<i class="{icon_class}"></i> ')

    return html(t'<label for="{field_name}">{icon_html}{display_label}{required_indicator}</label>')


def build_error_message(field_name: str, error: str) -> str:
    """Build error message element."""
    return html(t'<div id="{field_name}-error" class="error-message" role="alert">{error}</div>')


def build_help_text(field_name: str, help_text: str) -> str:
    """Build help text element."""
    return html(t'<div id="{field_name}-help" class="help-text">{help_text}</div>')


class NumericInput(FormInput):
    """
    Base class for numeric inputs with additional numeric attributes.
    """

    valid_attributes: list[str] = FormInput.valid_attributes + ['min', 'max', 'step']

    def render(self, **kwargs: Any) -> str:
        attrs = self.validate_attributes(**kwargs)
        attrs['type'] = self.get_input_type()
        return _render_input_tag(self._build_attributes_string(attrs))


class FileInputBase(FormInput):
    """
    Base class for file inputs with file-specific attributes.
    """

    valid_attributes: list[str] = FormInput.valid_attributes + ['accept', 'capture']


class SelectInputBase(BaseInput):
    """
    Base class for selection inputs (select, radio, checkbox).
    """

    valid_attributes: list[str] = BaseInput.valid_attributes + [
        'name',
        'value',
        'checked',
        'selected',
        'disabled',
        'required',
        'form',
        'multiple',
        'size',
    ]

    def render_with_label(
        self,
        label: str | None = None,
        help_text: str | None = None,
        error: str | None = None,
        icon: str | None = None,
        framework: str = 'bootstrap',
        options: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the selection input with its label, help text, and error message."""
        from pydantic_schemaforms.icon_mapping import map_icon_for_framework

        self.get_input_type()

        if icon:
            icon = map_icon_for_framework(icon, framework)

        if hasattr(self, 'render') and options is not None:
            input_html = SafeHTML(str(self.render(options=options, **kwargs)))
        else:
            attrs = self.validate_attributes(**kwargs)
            _attrs = SafeHTML(self._build_attributes_string(attrs))
            input_html = html(t'<select {_attrs}></select>')

        field_id = kwargs.get('id', '')
        field_parts: list[str] = []

        if framework == 'bootstrap':
            field_parts.append('<div class="mb-3">')

            if label:
                field_parts.append(
                    html(t'<label for="{field_id}" class="form-label">{label}</label>')
                )

            if icon:
                field_parts.append('<div class="input-group">')
                field_parts.append(
                    html(t'<span class="input-group-text"><i class="bi bi-{icon}"></i></span>')
                )
                field_parts.append(input_html)
                field_parts.append(_CLOSE_DIV)
            else:
                field_parts.append(input_html)

            if help_text:
                field_parts.append(html(t'<div class="form-text">{help_text}</div>'))

            if error:
                field_parts.append(html(t'<div class="invalid-feedback d-block">{error}</div>'))

            field_parts.append(_CLOSE_DIV)

        elif framework == 'material':
            field_parts.append('<div class="md-field">')

            if icon:
                field_parts.append('<div class="md-field-with-icon">')
                field_parts.append(html(t'<span class="md-icon material-icons">{icon}</span>'))
                field_parts.append('<div class="md-input-wrapper">')

            # A floating label (.md-floating-label, absolutely positioned on
            # top of the control until CSS ":not(:placeholder-shown)"/":focus"
            # animates it out of the way) only works when paired with
            # Material's own bespoke .md-select/.md-input classes -- this
            # method is also reached for widgets without a bespoke Material
            # template (multiselect, combobox) whose controls carry none of
            # those classes, so the label would sit frozen on top of the
            # control forever. Use the static .md-field-label style instead
            # (already used for the same purpose by model-list containers).
            if label:
                field_parts.append(
                    html(t'<label class="md-field-label" for="{field_id}">{label}</label>')
                )

            field_parts.append(input_html)

            if icon:
                field_parts.append(_CLOSE_DIV)
                field_parts.append(_CLOSE_DIV)

            if help_text:
                field_parts.append(html(t'<div class="md-help-text">{help_text}</div>'))

            if error:
                field_parts.append(html(t'<div class="md-error-text">{error}</div>'))

            field_parts.append(_CLOSE_DIV)

        else:
            field_parts.append('<div class="field">')

            if label:
                field_parts.append(html(t'<label for="{field_id}">{label}</label>'))

            if icon:
                field_parts.append(
                    html(t'<div class="input-with-icon"><span class="input-icon">{icon}</span>')
                )
                field_parts.append(input_html)
                field_parts.append(_CLOSE_DIV)
            else:
                field_parts.append(input_html)

            if help_text:
                field_parts.append(html(t'<div class="help-text">{help_text}</div>'))

            if error:
                field_parts.append(html(t'<div class="error-message">{error}</div>'))

            field_parts.append(_CLOSE_DIV)

        return '\n'.join(field_parts)
