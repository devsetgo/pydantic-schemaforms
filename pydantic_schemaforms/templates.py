"""PEP 750 t-string form template library for pydantic-schemaforms.

All rendering uses t-strings with the html() processor from tstring.py.
The legacy ${}-interpolation approach is banned — see pyproject.toml [TID251].

Parameter conventions used throughout this module:
  - Plain str params (titles, labels as text) → auto-escaped by the html() processor.
  - SafeHTML params (pre-rendered HTML fragments: content, sections, tab buttons
      and panels) → passed through unescaped via explicit SafeHTML() cast inside each fn.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Callable

from .csp import style_attr
from .tstring import SafeHTML, html

__all__ = ['FormTemplates', 'TemplateString', 'render_template', 'create_custom_template']


# ---------------------------------------------------------------------------
# TemplateString — thin callable wrapper; keeps the .render(**kwargs) API
# ---------------------------------------------------------------------------

_RenderFn = Callable[..., SafeHTML]


class TemplateString:
    """Wraps a t-string render function; call .render(**kwargs) to get SafeHTML.

    Stored as class attributes on FormTemplates and as dataclass field defaults
    in FormStyleTemplates — the .render() / .safe_render() API is unchanged
    from the previous template-string-based implementation.
    """

    __slots__ = ('_fn',)

    def __init__(self, fn: _RenderFn) -> None:
        self._fn = fn

    def render(self, **kwargs: Any) -> SafeHTML:
        return self._fn(**kwargs)

    # Alias: old callers used safe_render() for missing-variable tolerance.
    # t-string functions use keyword defaults so the same tolerance applies.
    safe_render = render


# ---------------------------------------------------------------------------
# Private render functions — one per FormTemplates attribute
# ---------------------------------------------------------------------------


def _form_wrapper(
    *,
    form_id: str = '',
    form_class: str = '',
    form_style: str = '',
    method: str = 'post',
    action: str = '',
    form_attributes: str = '',
    csrf_token: str = '',
    form_content: str = '',
    submit_buttons: str = '',
) -> SafeHTML:
    _form_attributes = SafeHTML(form_attributes)
    _csrf_token = SafeHTML(csrf_token)
    _form_content = SafeHTML(form_content)
    _submit_buttons = SafeHTML(submit_buttons)
    return html(t'''
<form id="{form_id}"
      class="pydantic-form {form_class}"{style_attr(form_style)}
      method="{method}"
      action="{action}"
      {_form_attributes}>
    {_csrf_token}
    {_form_content}
    {_submit_buttons}
</form>
''')


def _tab_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    tab_buttons: str = '',
    tab_panels: str = '',
    component_assets: str = '',
) -> SafeHTML:
    _tab_buttons = SafeHTML(tab_buttons)
    _tab_panels = SafeHTML(tab_panels)
    _component_assets = SafeHTML(component_assets)
    return html(t'''
<div class="tab-layout {layout_class}"{style_attr(layout_style)}>
    <div class="tab-navigation" role="tablist">
        {_tab_buttons}
    </div>
    <div class="tab-content">
        {_tab_panels}
    </div>
</div>
{_component_assets}
''')


def _tab_button(
    *,
    tab_id: str = '',
    title: str = '',
    active_class: str = '',
    aria_selected: str = 'false',
) -> SafeHTML:
    _active_class = SafeHTML(active_class)
    return html(t'''
<button class="tab-button{_active_class}"
        type="button"
        role="tab"
        aria-selected="{aria_selected}"
        aria-controls="{tab_id}"
        data-sf-toggle="tab">
    {title}
</button>
''')


def _tab_panel(
    *,
    tab_id: str = '',
    content: str = '',
    active_class: str = '',
    display_style: str = 'none',
    aria_hidden: str = 'true',
) -> SafeHTML:
    _content = SafeHTML(content)
    _active_class = SafeHTML(active_class)
    hidden = SafeHTML(' hidden' if display_style == 'none' else '')
    return html(t'''
<div id="{tab_id}"
     class="tab-panel{_active_class}"
     role="tabpanel"{hidden}
     aria-hidden="{aria_hidden}">
    {_content}
</div>
''')


def _accordion_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    sections: str = '',
    component_assets: str = '',
) -> SafeHTML:
    _sections = SafeHTML(sections)
    _component_assets = SafeHTML(component_assets)
    return html(t'''
<div class="accordion-layout {layout_class}"{style_attr(layout_style)}>
    {_sections}
</div>
{_component_assets}
''')


def _accordion_section(
    *,
    section_id: str = '',
    title: str = '',
    content: str = '',
    expanded_class: str = '',
    aria_expanded: str = 'false',
    display_style: str = 'none',
) -> SafeHTML:
    _content = SafeHTML(content)
    _expanded_class = SafeHTML(expanded_class)
    hidden = SafeHTML(' hidden' if display_style == 'none' else '')
    return html(t'''
<div class="accordion-section">
    <button class="accordion-header{_expanded_class}"
            type="button"
            aria-expanded="{aria_expanded}"
            aria-controls="{section_id}"
            data-sf-toggle="accordion">
        {title}
    </button>
    <div id="{section_id}"
         class="accordion-content"{hidden}>
        {_content}
    </div>
</div>
''')


def _section(
    *,
    section_class: str = '',
    section_style: str = '',
    section_title: str = '',
    section_content: str = '',
) -> SafeHTML:
    _section_title = SafeHTML(section_title)
    _section_content = SafeHTML(section_content)
    return html(t'''
<div class="form-section {section_class}"{style_attr(section_style)}>
    {_section_title}
    {_section_content}
</div>
''')


# ---------------------------------------------------------------------------
# FormTemplates — public collection
# ---------------------------------------------------------------------------


class FormTemplates:
    """Pre-built t-string render functions for common form elements and layouts."""

    FORM_WRAPPER = TemplateString(_form_wrapper)
    TAB_LAYOUT = TemplateString(_tab_layout)
    TAB_BUTTON = TemplateString(_tab_button)
    TAB_PANEL = TemplateString(_tab_panel)
    ACCORDION_LAYOUT = TemplateString(_accordion_layout)
    ACCORDION_SECTION = TemplateString(_accordion_section)
    SECTION = TemplateString(_section)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def render_template(template: TemplateString, **kwargs: Any) -> SafeHTML:
    """Convenience wrapper: render a TemplateString with keyword arguments."""
    return template.render(**kwargs)


def create_custom_template(fn: _RenderFn) -> TemplateString:
    """Wrap a t-string render function as a TemplateString.

    Args:
        fn: A callable that accepts keyword arguments and returns SafeHTML,
            typically defined using t-strings and the html() processor.

    Returns:
        TemplateString wrapping the function.
    """
    return TemplateString(fn)
