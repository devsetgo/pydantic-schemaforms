"""PEP 750 t-string form template library for pydantic-schemaforms.

All rendering uses t-strings with the html() processor from tstring.py.
The legacy ${}-interpolation approach is banned — see pyproject.toml [TID251].

Parameter conventions used throughout this module:
  - Plain str params (value, placeholder, title, label_text, help_text as text)
      → auto-escaped by the html() processor.
  - SafeHTML params (pre-rendered HTML fragments: label, help_text as HTML,
      error_message, options, sections, content, attributes, boolean-attr
      strings like required/disabled/checked)
      → passed through unescaped via explicit SafeHTML() cast inside each fn.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Callable

from .tstring import SafeHTML, html

__all__ = ['FormTemplates', 'TemplateString', 'render_template', 'create_custom_template']


def _cast_input_html(
    label: str,
    help_text: str,
    error_message: str,
    required: str,
    disabled: str,
    sixth: str,
    attributes: str,
) -> tuple[SafeHTML, SafeHTML, SafeHTML, SafeHTML, SafeHTML, SafeHTML, SafeHTML]:
    # Wraps the seven per-field HTML-fragment params to avoid CPD across input functions.
    return (
        SafeHTML(label),
        SafeHTML(help_text),
        SafeHTML(error_message),
        SafeHTML(required),
        SafeHTML(disabled),
        SafeHTML(sixth),
        SafeHTML(attributes),
    )


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

# ── Input templates ──────────────────────────────────────────────────────────


def _text_input(
    *,
    id: str = '',
    name: str = '',
    value: str = '',
    wrapper_class: str = '',
    wrapper_style: str = '',
    input_class: str = '',
    input_style: str = '',
    placeholder: str = '',
    required: str = '',
    disabled: str = '',
    readonly: str = '',
    attributes: str = '',
    label: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _label, _help_text, _error_message, _required, _disabled, _readonly, _attributes = (
        _cast_input_html(label, help_text, error_message, required, disabled, readonly, attributes)
    )
    return html(t'''
<div class="form-group {wrapper_class}" style="{wrapper_style}">
    {_label}
    <input type="text"
           id="{id}"
           name="{name}"
           class="form-control {input_class}"
           style="{input_style}"
           value="{value}"
           placeholder="{placeholder}"
           {_required}
           {_disabled}
           {_readonly}
           {_attributes} />
    {_help_text}
    {_error_message}
</div>
''')


def _email_input(
    *,
    id: str = '',
    name: str = '',
    value: str = '',
    wrapper_class: str = '',
    wrapper_style: str = '',
    input_class: str = '',
    input_style: str = '',
    placeholder: str = '',
    required: str = '',
    disabled: str = '',
    readonly: str = '',
    attributes: str = '',
    label: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _label, _help_text, _error_message, _required, _disabled, _readonly, _attributes = (
        _cast_input_html(label, help_text, error_message, required, disabled, readonly, attributes)
    )
    return html(t'''
<div class="form-group {wrapper_class}" style="{wrapper_style}">
    {_label}
    <input type="email"
           id="{id}"
           name="{name}"
           class="form-control {input_class}"
           style="{input_style}"
           value="{value}"
           placeholder="{placeholder}"
           {_required}
           {_disabled}
           {_readonly}
           {_attributes} />
    {_help_text}
    {_error_message}
</div>
''')


def _password_input(
    *,
    id: str = '',
    name: str = '',
    value: str = '',
    wrapper_class: str = '',
    wrapper_style: str = '',
    input_class: str = '',
    input_style: str = '',
    placeholder: str = '',
    required: str = '',
    disabled: str = '',
    readonly: str = '',
    attributes: str = '',
    label: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _label, _help_text, _error_message, _required, _disabled, _readonly, _attributes = (
        _cast_input_html(label, help_text, error_message, required, disabled, readonly, attributes)
    )
    return html(t'''
<div class="form-group {wrapper_class}" style="{wrapper_style}">
    {_label}
    <div class="input-group">
        <input type="password"
               id="{id}"
               name="{name}"
               class="form-control {input_class}"
               style="{input_style}"
               value="{value}"
               placeholder="{placeholder}"
               {_required}
               {_disabled}
               {_readonly}
               {_attributes} />
        <button class="btn btn-outline-secondary" type="button" onclick="togglePassword(&#39;{id}&#39;)">
            <i class="bi bi-eye" id="{id}_toggle_icon"></i>
        </button>
    </div>
    {_help_text}
    {_error_message}
</div>
''')


def _number_input(
    *,
    id: str = '',
    name: str = '',
    value: str = '',
    wrapper_class: str = '',
    wrapper_style: str = '',
    input_class: str = '',
    input_style: str = '',
    placeholder: str = '',
    min_value: str = '',
    max_value: str = '',
    step: str = '',
    required: str = '',
    disabled: str = '',
    readonly: str = '',
    attributes: str = '',
    label: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _label, _help_text, _error_message, _required, _disabled, _readonly, _attributes = (
        _cast_input_html(label, help_text, error_message, required, disabled, readonly, attributes)
    )
    return html(t'''
<div class="form-group {wrapper_class}" style="{wrapper_style}">
    {_label}
    <input type="number"
           id="{id}"
           name="{name}"
           class="form-control {input_class}"
           style="{input_style}"
           value="{value}"
           placeholder="{placeholder}"
           min="{min_value}"
           max="{max_value}"
           step="{step}"
           {_required}
           {_disabled}
           {_readonly}
           {_attributes} />
    {_help_text}
    {_error_message}
</div>
''')


def _select_input(
    *,
    id: str = '',
    name: str = '',
    wrapper_class: str = '',
    wrapper_style: str = '',
    input_class: str = '',
    input_style: str = '',
    required: str = '',
    disabled: str = '',
    multiple: str = '',
    attributes: str = '',
    options: str = '',
    label: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _label, _help_text, _error_message, _required, _disabled, _multiple, _attributes = (
        _cast_input_html(label, help_text, error_message, required, disabled, multiple, attributes)
    )
    _options = SafeHTML(options)
    return html(t'''
<div class="form-group {wrapper_class}" style="{wrapper_style}">
    {_label}
    <select id="{id}"
            name="{name}"
            class="form-select {input_class}"
            style="{input_style}"
            {_required}
            {_disabled}
            {_multiple}
            {_attributes}>
        {_options}
    </select>
    {_help_text}
    {_error_message}
</div>
''')


def _textarea_input(
    *,
    id: str = '',
    name: str = '',
    value: str = '',
    wrapper_class: str = '',
    wrapper_style: str = '',
    input_class: str = '',
    input_style: str = '',
    placeholder: str = '',
    rows: str = '4',
    cols: str = '',
    required: str = '',
    disabled: str = '',
    readonly: str = '',
    attributes: str = '',
    label: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _label, _help_text, _error_message, _required, _disabled, _readonly, _attributes = (
        _cast_input_html(label, help_text, error_message, required, disabled, readonly, attributes)
    )
    return html(t'''
<div class="form-group {wrapper_class}" style="{wrapper_style}">
    {_label}
    <textarea id="{id}"
              name="{name}"
              class="form-control {input_class}"
              style="{input_style}"
              rows="{rows}"
              cols="{cols}"
              placeholder="{placeholder}"
              {_required}
              {_disabled}
              {_readonly}
              {_attributes}>{value}</textarea>
    {_help_text}
    {_error_message}
</div>
''')


def _checkbox_input(
    *,
    id: str = '',
    name: str = '',
    checkbox_value: str = '',
    wrapper_class: str = '',
    wrapper_style: str = '',
    input_class: str = '',
    input_style: str = '',
    checked: str = '',
    required: str = '',
    disabled: str = '',
    attributes: str = '',
    label_text: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _help_text = SafeHTML(help_text)
    _error_message = SafeHTML(error_message)
    _checked = SafeHTML(checked)
    _required = SafeHTML(required)
    _disabled = SafeHTML(disabled)
    _attributes = SafeHTML(attributes)
    return html(t'''
<div class="form-check {wrapper_class}" style="{wrapper_style}">
    <input type="checkbox"
           id="{id}"
           name="{name}"
           class="form-check-input {input_class}"
           style="{input_style}"
           value="{checkbox_value}"
           {_checked}
           {_required}
           {_disabled}
           {_attributes} />
    <label class="form-check-label" for="{id}">
        {label_text}
    </label>
    {_help_text}
    {_error_message}
</div>
''')


def _radio_input(
    *,
    wrapper_class: str = '',
    wrapper_style: str = '',
    label: str = '',
    radio_options: str = '',
    help_text: str = '',
    error_message: str = '',
) -> SafeHTML:
    _label = SafeHTML(label)
    _radio_options = SafeHTML(radio_options)
    _help_text = SafeHTML(help_text)
    _error_message = SafeHTML(error_message)
    return html(t'''
<div class="form-group {wrapper_class}" style="{wrapper_style}">
    {_label}
    <div class="radio-group">
        {_radio_options}
    </div>
    {_help_text}
    {_error_message}
</div>
''')


# ── Layout templates ─────────────────────────────────────────────────────────


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
      class="pydantic-form {form_class}"
      style="{form_style}"
      method="{method}"
      action="{action}"
      {_form_attributes}>
    {_csrf_token}
    {_form_content}
    {_submit_buttons}
</form>
''')


def _vertical_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    sections: str = '',
) -> SafeHTML:
    _sections = SafeHTML(sections)
    return html(t'''
<div class="vertical-layout {layout_class}" style="{layout_style}">
    {_sections}
</div>
''')


def _horizontal_layout(
    *,
    layout_class: str = '',
    layout_style: str = '',
    sections: str = '',
) -> SafeHTML:
    _sections = SafeHTML(sections)
    return html(t'''
<div class="horizontal-layout row {layout_class}" style="{layout_style}">
    {_sections}
</div>
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
<div class="tab-layout {layout_class}" style="{layout_style}">
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
        onclick="switchTab(&#39;{tab_id}&#39;, this)">
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
    return html(t'''
<div id="{tab_id}"
     class="tab-panel{_active_class}"
     role="tabpanel"
     style="display: {display_style};"
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
<div class="accordion-layout {layout_class}" style="{layout_style}">
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
    return html(t'''
<div class="accordion-section">
    <button class="accordion-header{_expanded_class}"
            aria-expanded="{aria_expanded}"
            aria-controls="{section_id}"
            onclick="toggleAccordion(&#39;{section_id}&#39;, this)">
        {title}
    </button>
    <div id="{section_id}"
         class="accordion-content"
         style="display: {display_style};">
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
<div class="form-section {section_class}" style="{section_style}">
    {_section_title}
    {_section_content}
</div>
''')


# ── Helper templates ─────────────────────────────────────────────────────────


def _label(
    *,
    for_id: str = '',
    label_class: str = '',
    label_style: str = '',
    icon: str = '',
    label_text: str = '',
    required_indicator: str = '',
) -> SafeHTML:
    _icon = SafeHTML(icon)
    _required_indicator = SafeHTML(required_indicator)
    return html(t'''
<label for="{for_id}" class="form-label {label_class}" style="{label_style}">
    {_icon}{label_text}{_required_indicator}
</label>
''')


def _help_text(
    *,
    help_class: str = '',
    help_style: str = '',
    help_content: str = '',
) -> SafeHTML:
    return html(t'''
<div class="form-text {help_class}" style="{help_style}">
    {help_content}
</div>
''')


def _error_message(
    *,
    error_class: str = '',
    error_style: str = '',
    error_content: str = '',
) -> SafeHTML:
    return html(t'''
<div class="invalid-feedback {error_class}" style="{error_style}">
    {error_content}
</div>
''')


def _icon(
    *,
    icon_name: str = '',
    icon_class: str = '',
    icon_style: str = '',
) -> SafeHTML:
    return html(t'<i class="bi bi-{icon_name} {icon_class}" style="{icon_style}"></i>')


def _input_group(
    *,
    group_class: str = '',
    group_style: str = '',
    prepend: str = '',
    input_element: str = '',
    append: str = '',
) -> SafeHTML:
    _prepend = SafeHTML(prepend)
    _input_element = SafeHTML(input_element)
    _append = SafeHTML(append)
    return html(t'''
<div class="input-group {group_class}" style="{group_style}">
    {_prepend}
    {_input_element}
    {_append}
</div>
''')


def _form_page(
    *,
    page_title: str = '',
    css_links: str = '',
    custom_styles: str = '',
    page_header: str = '',
    form_content: str = '',
    page_footer: str = '',
    js_links: str = '',
    custom_scripts: str = '',
) -> SafeHTML:
    _css_links = SafeHTML(css_links)
    _custom_styles = SafeHTML(custom_styles)
    _page_header = SafeHTML(page_header)
    _form_content = SafeHTML(form_content)
    _page_footer = SafeHTML(page_footer)
    _js_links = SafeHTML(js_links)
    _custom_scripts = SafeHTML(custom_scripts)
    return html(t"""<!--- Start Pydantic-SchemaForms -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    {_css_links}
    {_custom_styles}
</head>
<body>
    <div class="container">
        {_page_header}
        {_form_content}
        {_page_footer}
    </div>
    {_js_links}
    {_custom_scripts}
</body>
</html>
<!--- End Pydantic-SchemaForms -->""")


# ── Material Design templates ─────────────────────────────────────────────────


def _material_field_container(
    *,
    field_body: str = '',
    help_text: str = '',
    error_text: str = '',
) -> SafeHTML:
    _field_body = SafeHTML(field_body)
    _help_text = SafeHTML(help_text)
    _error_text = SafeHTML(error_text)
    return html(t"""
<div class="md-field">
    {_field_body}
    {_help_text}
    {_error_text}
</div>
""")


def _material_field_with_icon(
    *,
    icon_markup: str = '',
    input_wrapper: str = '',
) -> SafeHTML:
    _icon_markup = SafeHTML(icon_markup)
    _input_wrapper = SafeHTML(input_wrapper)
    return html(t"""
<div class="md-field-with-icon">
    {_icon_markup}
    {_input_wrapper}
</div>
""")


def _material_field_input_wrapper(
    *,
    field_id: str = '',
    input_control: str = '',
    label: str = '',
    required_indicator: str = '',
) -> SafeHTML:
    _input_control = SafeHTML(input_control)
    _required_indicator = SafeHTML(required_indicator)
    return html(t'''
<div class="md-input-wrapper">
    {_input_control}
    <label class="md-floating-label" for="{field_id}">{label}{_required_indicator}</label>
</div>
''')


def _material_icon(*, icon_name: str = '') -> SafeHTML:
    return html(t'<span class="md-icon material-icons">{icon_name}</span>')


def _material_text_input(
    *,
    input_type: str = 'text',
    name: str = '',
    field_id: str = '',
    error_class: str = '',
    value: str = '',
    attributes: str = '',
) -> SafeHTML:
    _error_class = SafeHTML(error_class)
    _attributes = SafeHTML(attributes)
    return html(t'''
<input type="{input_type}"
       name="{name}"
       id="{field_id}"
       class="md-input{_error_class}"
       value="{value}"
    placeholder=" " {_attributes}>
''')


def _material_textarea(
    *,
    name: str = '',
    field_id: str = '',
    error_class: str = '',
    value: str = '',
    attributes: str = '',
) -> SafeHTML:
    _error_class = SafeHTML(error_class)
    _attributes = SafeHTML(attributes)
    return html(t'''
<textarea name="{name}"
          id="{field_id}"
          class="md-textarea{_error_class}"
          placeholder=" " {_attributes}>{value}</textarea>
''')


def _material_select(
    *,
    name: str = '',
    field_id: str = '',
    error_class: str = '',
    options: str = '',
    attributes: str = '',
) -> SafeHTML:
    _error_class = SafeHTML(error_class)
    _options = SafeHTML(options)
    _attributes = SafeHTML(attributes)
    return html(t'''
<select name="{name}"
        id="{field_id}"
        class="md-select{_error_class}" {_attributes}>
    {_options}
</select>
''')


def _material_select_option(
    *,
    value: str = '',
    selected: str = '',
    label: str = '',
) -> SafeHTML:
    _selected = SafeHTML(selected)
    return html(t'<option value="{value}"{_selected}>{label}</option>')


def _material_help_text(*, help_content: str = '') -> SafeHTML:
    return html(t'<div class="md-help-text">{help_content}</div>')


def _material_error_text(*, error_content: str = '') -> SafeHTML:
    return html(t'<div class="md-error-text">{error_content}</div>')


def _material_checkbox_field(
    *,
    name: str = '',
    field_id: str = '',
    label: str = '',
    required_indicator: str = '',
    checked: str = '',
    required: str = '',
    help_text: str = '',
    error_text: str = '',
) -> SafeHTML:
    _required_indicator = SafeHTML(required_indicator)
    _checked = SafeHTML(checked)
    _required = SafeHTML(required)
    _help_text = SafeHTML(help_text)
    _error_text = SafeHTML(error_text)
    return html(t'''
<div class="md-field">
    <div class="md-checkbox-container">
        <input type="checkbox"
               name="{name}"
               id="{field_id}"
               class="md-checkbox"
               value="true"
             {_checked} {_required}>
        <label for="{field_id}" class="md-checkbox-label">{label}{_required_indicator}</label>
    </div>
    {_help_text}
    {_error_text}
</div>
''')


def _material_toggle_field(
    *,
    name: str = '',
    field_id: str = '',
    label: str = '',
    required_indicator: str = '',
    checked: str = '',
    required: str = '',
    help_text: str = '',
    error_text: str = '',
) -> SafeHTML:
    """Material toggle switch. Input and slider must be adjacent siblings inside
    the wrapping <label> for the `input:checked + .md-toggle-slider` CSS to match
    (same requirement as the Bootstrap ToggleSwitch widget)."""
    _required_indicator = SafeHTML(required_indicator)
    _checked = SafeHTML(checked)
    _required = SafeHTML(required)
    _help_text = SafeHTML(help_text)
    _error_text = SafeHTML(error_text)
    return html(t'''
<div class="md-field">
    <label class="md-toggle-wrapper" for="{field_id}">
        <input type="checkbox"
               name="{name}"
               id="{field_id}"
               class="md-toggle-input"
               value="true"
             {_checked} {_required}>
        <span class="md-toggle-slider"></span>
        <span class="md-toggle-label">{label}{_required_indicator}</span>
    </label>
    {_help_text}
    {_error_text}
    <style>
    .md-toggle-wrapper {{
        display: inline-flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
    }}
    .md-toggle-wrapper .md-toggle-input {{
        position: absolute;
        opacity: 0;
        width: 0;
        height: 0;
    }}
    .md-toggle-slider {{
        position: relative;
        display: inline-block;
        width: 40px;
        height: 24px;
        background: #79747e;
        border-radius: 12px;
        transition: background .2s;
        flex-shrink: 0;
    }}
    .md-toggle-slider::before {{
        content: '';
        position: absolute;
        top: 2px;
        left: 2px;
        width: 20px;
        height: 20px;
        background: white;
        border-radius: 50%;
        transition: transform .2s;
        box-shadow: 0 1px 2px rgba(0, 0, 0, .3);
    }}
    .md-toggle-wrapper input:checked + .md-toggle-slider {{
        background: #6750a4;
    }}
    .md-toggle-wrapper input:checked + .md-toggle-slider::before {{
        transform: translateX(16px);
    }}
    .md-toggle-wrapper input:focus + .md-toggle-slider {{
        box-shadow: 0 0 0 2px rgba(103, 80, 164, .3);
    }}
    .md-toggle-wrapper input:disabled + .md-toggle-slider {{
        opacity: .5;
        cursor: not-allowed;
    }}
    .md-toggle-label {{
        color: #1c1b1f;
        font-size: 16px;
    }}
    </style>
</div>
''')


def _material_submit_button(*, label: str = '') -> SafeHTML:
    return html(t"""
<div class="md-field">
    <button type="submit" class="md-button md-button-filled">{label}</button>
</div>
""")


def _material_model_list_wrapper(*, content: str = '') -> SafeHTML:
    _content = SafeHTML(content)
    return html(t"""
<div class="md-field">
    <div class="md-model-list-container">
        {_content}
    </div>
</div>
""")


# ---------------------------------------------------------------------------
# FormTemplates — public collection
# ---------------------------------------------------------------------------


class FormTemplates:
    """Pre-built t-string render functions for common form elements and layouts."""

    # Input templates
    TEXT_INPUT = TemplateString(_text_input)
    EMAIL_INPUT = TemplateString(_email_input)
    PASSWORD_INPUT = TemplateString(_password_input)
    NUMBER_INPUT = TemplateString(_number_input)
    SELECT_INPUT = TemplateString(_select_input)
    TEXTAREA_INPUT = TemplateString(_textarea_input)
    CHECKBOX_INPUT = TemplateString(_checkbox_input)
    RADIO_INPUT = TemplateString(_radio_input)

    # Layout templates
    FORM_WRAPPER = TemplateString(_form_wrapper)
    VERTICAL_LAYOUT = TemplateString(_vertical_layout)
    HORIZONTAL_LAYOUT = TemplateString(_horizontal_layout)
    TAB_LAYOUT = TemplateString(_tab_layout)
    TAB_BUTTON = TemplateString(_tab_button)
    TAB_PANEL = TemplateString(_tab_panel)
    ACCORDION_LAYOUT = TemplateString(_accordion_layout)
    ACCORDION_SECTION = TemplateString(_accordion_section)
    SECTION = TemplateString(_section)

    # Helper templates
    LABEL = TemplateString(_label)
    HELP_TEXT = TemplateString(_help_text)
    ERROR_MESSAGE = TemplateString(_error_message)
    ICON = TemplateString(_icon)
    INPUT_GROUP = TemplateString(_input_group)
    FORM_PAGE = TemplateString(_form_page)

    # Material Design templates
    MATERIAL_FIELD_CONTAINER = TemplateString(_material_field_container)
    MATERIAL_FIELD_WITH_ICON = TemplateString(_material_field_with_icon)
    MATERIAL_FIELD_INPUT_WRAPPER = TemplateString(_material_field_input_wrapper)
    MATERIAL_ICON = TemplateString(_material_icon)
    MATERIAL_TEXT_INPUT = TemplateString(_material_text_input)
    MATERIAL_TEXTAREA = TemplateString(_material_textarea)
    MATERIAL_SELECT = TemplateString(_material_select)
    MATERIAL_SELECT_OPTION = TemplateString(_material_select_option)
    MATERIAL_HELP_TEXT = TemplateString(_material_help_text)
    MATERIAL_ERROR_TEXT = TemplateString(_material_error_text)
    MATERIAL_CHECKBOX_FIELD = TemplateString(_material_checkbox_field)
    MATERIAL_TOGGLE_FIELD = TemplateString(_material_toggle_field)
    MATERIAL_SUBMIT_BUTTON = TemplateString(_material_submit_button)
    MATERIAL_MODEL_LIST_WRAPPER = TemplateString(_material_model_list_wrapper)


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
