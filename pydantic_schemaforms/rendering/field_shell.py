"""The markup around a form control: wrapper, label, icon, help and error.

Every input renders only its control (`BaseInput.render`). The shell around it
comes from a `FieldShellRenderer` chosen by the theme, so the three frameworks
share one rendering path and differ only here. `FormInput` and
`SelectInputBase` build a `FieldShell` in `render_with_label` and hand it to
the theme's shell renderer.

This module must not import `rendering.themes` (themes import it).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic_schemaforms.tstring import SafeHTML, html

_CLOSE_DIV = '</div>'

# Which `render_with_label` built the shell: plain inputs (`FormInput`) and the
# option-list widgets (`SelectInputBase`: select, multiselect, combobox, radio,
# checkbox_group) have always had different wrappers, so the shells keep them.
Family = Literal['input', 'choice']


@dataclass(frozen=True, slots=True)
class FieldShell:
    family: Family
    ui_element: str
    name: str
    field_id: str
    control_html: str
    label: str | None
    required: bool
    help_text: str | None
    error: str | None
    help_id: str
    error_id: str
    icon: str | None


class FieldShellRenderer(Protocol):
    def render(self, shell: FieldShell) -> str: ...


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


class _InputShell:
    """The `FormInput` shell every non-Bootstrap framework has used: label,
    control, help, error, with no wrapper (the field renderer adds one)."""

    def __init__(self, framework: str) -> None:
        self.framework = framework

    def _render_input(self, shell: FieldShell, help_class: str, error_class: str) -> str:
        parts: list[str] = []
        if shell.label:
            parts.append(
                build_label(shell.name, shell.label, shell.required, shell.icon, self.framework)
            )
        parts.append(SafeHTML(shell.control_html))
        if shell.help_text:
            parts.append(
                html(t'<div id="{shell.help_id}" class="{help_class}">{shell.help_text}</div>')
            )
        if shell.error:
            parts.append(
                html(t'<div id="{shell.error_id}" class="{error_class}">{shell.error}</div>')
            )
        return '\n'.join(parts)


class BootstrapFieldShell(_InputShell):
    def __init__(self) -> None:
        super().__init__('bootstrap')

    def render(self, shell: FieldShell) -> str:
        if shell.family == 'input':
            return self._render_input(shell, 'form-text', 'invalid-feedback d-block')

        control = SafeHTML(shell.control_html)
        parts: list[str] = ['<div class="mb-3">']
        if shell.label:
            parts.append(
                html(t'<label for="{shell.field_id}" class="form-label">{shell.label}</label>')
            )
        if shell.icon:
            parts.extend(
                [
                    '<div class="input-group">',
                    html(
                        t'<span class="input-group-text"><i class="bi bi-{shell.icon}"></i></span>'
                    ),
                    control,
                    _CLOSE_DIV,
                ]
            )
        else:
            parts.append(control)
        if shell.help_text:
            parts.append(
                html(t'<div id="{shell.help_id}" class="form-text">{shell.help_text}</div>')
            )
        if shell.error:
            parts.append(
                html(
                    t'<div id="{shell.error_id}" class="invalid-feedback d-block">{shell.error}</div>'
                )
            )
        parts.append(_CLOSE_DIV)
        return '\n'.join(parts)


class PlainFieldShell(_InputShell):
    def render(self, shell: FieldShell) -> str:
        if shell.family == 'input':
            return self._render_input(shell, 'help-text', 'error-text')

        control = SafeHTML(shell.control_html)
        parts: list[str] = ['<div class="field">']
        if shell.label:
            parts.append(html(t'<label for="{shell.field_id}">{shell.label}</label>'))
        if shell.icon:
            parts.extend(
                [
                    html(
                        t'<div class="input-with-icon"><span class="input-icon">{shell.icon}</span>'
                    ),
                    control,
                    _CLOSE_DIV,
                ]
            )
        else:
            parts.append(control)
        if shell.help_text:
            parts.append(
                html(t'<div id="{shell.help_id}" class="help-text">{shell.help_text}</div>')
            )
        if shell.error:
            parts.append(
                html(t'<div id="{shell.error_id}" class="error-message">{shell.error}</div>')
            )
        parts.append(_CLOSE_DIV)
        return '\n'.join(parts)


# Material Design 3 field anatomy per ui_element (see docs/advanced/material.md).
MATERIAL_FLOATING = frozenset(
    {
        'text', 'password', 'email', 'search', 'url', 'tel', 'ssn', 'phone', 'credit_card',
        'currency', 'number', 'integer', 'decimal', 'percentage', 'age', 'score',
        'temperature', 'quantity', 'date', 'time', 'datetime', 'month', 'week', 'textarea',
        'select', 'combobox',
    }
)  # fmt: skip
# Native controls that always show a value or a mask, so the label never rests inside.
MATERIAL_ALWAYS_FLOAT = frozenset({'select', 'date', 'time', 'datetime', 'month', 'week'})
MATERIAL_GROUPS = frozenset({'radio', 'checkbox_group'})


# Registered alias -> the name the sets above use.
_MATERIAL_ALIASES = {
    'card': 'credit_card',
    'cc_number': 'credit_card',
    'money': 'currency',
    'phone_number': 'phone',
    'social_security_number': 'ssn',
    'datetime-local': 'datetime',
    'birthdate': 'date',
    'checkbox_toggle': 'toggle',
    'toggle_switch': 'toggle',
}


def material_field_kind(ui_element: str) -> str:
    ui_element = _MATERIAL_ALIASES.get(ui_element, ui_element)
    if ui_element in MATERIAL_FLOATING:
        return (
            'textarea'
            if ui_element == 'textarea'
            else ('select' if ui_element == 'select' else 'text')
        )
    if ui_element == 'checkbox':
        return 'checkbox'
    if ui_element == 'toggle':
        return 'switch'
    if ui_element in MATERIAL_GROUPS:
        return 'group'
    return 'static'


def _md_icon(name: str, classes: str = 'md-icon') -> SafeHTML:
    from .material_icons import render_material_icon

    return SafeHTML(render_material_icon(name, classes=classes))


class MaterialFieldShell:
    """Material Design 3 fields: an outlined (or filled) box with a floating
    label in a notch, static labels for composite widgets, legends for
    groups and inline labels for checkboxes and switches. Driven by CSS
    alone (assets/material/md3.css)."""

    def render(self, shell: FieldShell) -> str:
        kind = material_field_kind(shell.ui_element)
        # A code editor has a toolbar and a highlight layer, so no floating label.
        if 'code-textarea-wrap' in shell.control_html:
            kind = 'static'
        field_id = shell.field_id or shell.name
        control = SafeHTML(shell.control_html)
        required = (
            SafeHTML('<span class="md-required" aria-hidden="true"> *</span>')
            if shell.required
            else SafeHTML('')
        )
        supporting = self._supporting(shell)
        classes = ['md-field', f'md-field--{kind}']
        if shell.error:
            classes.append('md-field--error')

        if kind in {'text', 'textarea', 'select'}:
            if _MATERIAL_ALIASES.get(shell.ui_element, shell.ui_element) in MATERIAL_ALWAYS_FLOAT:
                classes.append('md-field--float')
            leading = SafeHTML('')
            if shell.icon:
                icon_svg = _md_icon(shell.icon)
                if icon_svg:
                    classes.append('md-field--leading-icon')
                    leading = html(
                        t'<span class="md-field__leading" aria-hidden="true">{icon_svg}</span>'
                    )
            trailing_icons = []
            if shell.error:
                trailing_icons.append(_md_icon('error'))
            if kind == 'select':
                trailing_icons.append(_md_icon('arrow_drop_down', 'md-icon md-chevron'))
            trailing = (
                html(
                    t'<span class="md-field__trailing" aria-hidden="true">{SafeHTML("".join(trailing_icons))}</span>'
                )
                if trailing_icons
                else SafeHTML('')
            )
            label = shell.label or ''
            css = ' '.join(classes)
            return str(
                html(t'''<div class="{css}">
<div class="md-field__box">{leading}{control}<label class="md-floating-label" for="{field_id}">{label}{required}</label><span class="md-field__outline" aria-hidden="true"><span class="md-field__outline-start"></span><span class="md-field__outline-notch"><span class="md-field__notch-text">{label}{required}</span></span><span class="md-field__outline-end"></span></span>{trailing}</div>{supporting}
</div>''')
            )

        css = ' '.join(classes)
        if kind == 'checkbox':
            label = shell.label or ''
            return str(
                html(t'''<div class="{css}">
<div class="md-checkbox-container">{control}<label class="md-checkbox-label" for="{field_id}">{label}{required}</label></div>{supporting}
</div>''')
            )
        if kind == 'switch':
            label = shell.label or ''
            return str(
                html(t'''<div class="{css}">
<div class="md-switch-row"><label class="md-switch-label" for="{field_id}">{label}{required}</label>{control}</div>{supporting}
</div>''')
            )
        if kind == 'group' or not shell.label:
            return str(html(t'<div class="{css}">\n{control}{supporting}\n</div>'))

        label = shell.label
        return str(
            html(t'''<div class="{css}">
<label class="md-field-label" for="{field_id}">{label}{required}</label>
{control}{supporting}
</div>''')
        )

    @staticmethod
    def _supporting(shell: FieldShell) -> SafeHTML:
        parts = []
        if shell.help_text:
            parts.append(
                html(t'<div id="{shell.help_id}" class="md-help-text">{shell.help_text}</div>')
            )
        if shell.error:
            parts.append(
                html(t'<div id="{shell.error_id}" class="md-error-text">{shell.error}</div>')
            )
        if not parts:
            return SafeHTML('')
        inner = SafeHTML(''.join(str(p) for p in parts))
        return html(t'<div class="md-field__supporting">{inner}</div>')


def field_shell_for_framework(framework: str) -> FieldShellRenderer:
    """The shell a framework string selects when no theme supplies one."""
    if framework == 'bootstrap':
        return BootstrapFieldShell()
    if framework == 'material':
        return MaterialFieldShell()
    return PlainFieldShell(framework)
