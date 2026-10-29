"""
Base classes and utilities for form inputs with Python 3.14 template strings.
"""

from abc import ABC, abstractmethod
from html import escape
from typing import Any

from pydantic_schemaforms.rendering.field_shell import (
    FieldShell,
    FieldShellRenderer,
    build_label,  # noqa: F401  (defined with the shells; public via inputs)
    field_shell_for_framework,
)
from pydantic_schemaforms.tstring import SafeHTML, html


def _shell_renderer(theme: Any, framework: str) -> FieldShellRenderer:
    if theme is not None:
        return theme.field_shell(framework)
    return field_shell_for_framework(framework)


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


def _describe_field(
    kwargs: dict[str, Any], help_text: str | None, error: str | None
) -> tuple[str, str]:
    """Point the control at its help text and error so screen readers announce
    them with it, and flag it invalid; returns the (help, error) element ids."""
    field_id = str(kwargs.get('id') or kwargs.get('name') or 'field')
    help_id, error_id = f'{field_id}-help', f'{field_id}-error'
    described_by = [help_id] if help_text else []
    if error:
        described_by.append(error_id)
        kwargs['aria-invalid'] = 'true'
    if described_by:
        kwargs['aria-describedby'] = ' '.join(described_by)
    return help_id, error_id


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
        *,
        theme: Any = None,
        **kwargs: Any,
    ) -> str:
        """Render the input with its label, help text, and error message."""
        from pydantic_schemaforms.icon_mapping import map_icon_for_framework

        if icon:
            icon = map_icon_for_framework(icon, framework)

        help_id, error_id = _describe_field(kwargs, help_text, error)

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

        shell = FieldShell(
            family='input',
            ui_element=self.ui_element or '',
            name=kwargs.get('name', 'field'),
            field_id=str(kwargs.get('id', '')),
            control_html=str(input_html),
            label=label,
            required=bool(kwargs.get('required', False)),
            help_text=help_text,
            error=error,
            help_id=help_id,
            error_id=error_id,
            icon=icon,
        )
        return _shell_renderer(theme, framework).render(shell)


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
        *,
        theme: Any = None,
        **kwargs: Any,
    ) -> str:
        """Render the selection input with its label, help text, and error message."""
        from pydantic_schemaforms.icon_mapping import map_icon_for_framework

        self.get_input_type()

        if icon:
            icon = map_icon_for_framework(icon, framework)

        help_id, error_id = _describe_field(kwargs, help_text, error)

        if hasattr(self, 'render') and options is not None:
            input_html = str(self.render(options=options, **kwargs))
        else:
            attrs = self.validate_attributes(**kwargs)
            _attrs = SafeHTML(self._build_attributes_string(attrs))
            input_html = html(t'<select {_attrs}></select>')

        shell = FieldShell(
            family='choice',
            ui_element=self.ui_element or '',
            name=kwargs.get('name', 'field'),
            field_id=kwargs.get('id', ''),
            control_html=str(input_html),
            label=label,
            required=bool(kwargs.get('required', False)),
            help_text=help_text,
            error=error,
            help_id=help_id,
            error_id=error_id,
            icon=icon,
        )
        return _shell_renderer(theme, framework).render(shell)
