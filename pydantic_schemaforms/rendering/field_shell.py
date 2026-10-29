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


class LegacyMaterialFieldShell(_InputShell):
    """Today's Material fallback shell; replaced by the MD3 shell later in #265."""

    def __init__(self) -> None:
        super().__init__('material')

    def render(self, shell: FieldShell) -> str:
        if shell.family == 'input':
            return self._render_input(shell, 'help-text', 'error-text')

        parts: list[str] = ['<div class="md-field">']
        if shell.icon:
            parts.extend(
                [
                    '<div class="md-field-with-icon">',
                    html(t'<span class="md-icon material-icons">{shell.icon}</span>'),
                    '<div class="md-input-wrapper">',
                ]
            )
        if shell.label:
            parts.append(
                html(t'<label class="md-field-label" for="{shell.field_id}">{shell.label}</label>')
            )
        parts.append(SafeHTML(shell.control_html))
        if shell.icon:
            parts.append(_CLOSE_DIV)
            parts.append(_CLOSE_DIV)
        if shell.help_text:
            parts.append(
                html(t'<div id="{shell.help_id}" class="md-help-text">{shell.help_text}</div>')
            )
        if shell.error:
            parts.append(
                html(t'<div id="{shell.error_id}" class="md-error-text">{shell.error}</div>')
            )
        parts.append(_CLOSE_DIV)
        return '\n'.join(parts)


def field_shell_for_framework(framework: str) -> FieldShellRenderer:
    """The shell a framework string selects when no theme supplies one."""
    if framework == 'bootstrap':
        return BootstrapFieldShell()
    if framework == 'material':
        return LegacyMaterialFieldShell()
    return PlainFieldShell(framework)
