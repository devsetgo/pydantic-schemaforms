"""Renderer theme helpers for enhanced form renderers."""

from __future__ import annotations

from html import escape
from typing import Any

from pydantic_schemaforms.templates import TemplateString
from pydantic_schemaforms.tstring import SafeHTML, html
from pydantic_schemaforms.assets.runtime import (
    bootstrap_icons_css_tag,
    framework_css_tag,
    framework_js_tag,
    material_script_tag,
    material_style_tag,
)
from .field_shell import (
    FieldShellRenderer,
    MaterialFieldShell,
    field_shell_for_framework,
    material_field_kind,
)
from .form_style import FormStyle, get_form_style
from .model_list_markup import ModelListItem, render_default_model_list_item
from .frameworks import get_framework_config
from .material_icons import render_material_icon
from .theme_assets import ACCORDION_COMPONENT_SCRIPT, TAB_COMPONENT_SCRIPT

__all__ = [
    'RendererTheme',
    'DefaultTheme',
    'FrameworkTheme',
    'BootstrapTheme',
    'PlainTheme',
    'MaterialTheme',
    'get_theme_for_framework',
]

_CLOSE_SECTION = '</section>'
_CLOSE_INNER_DIV = '  </div>'


_TABLE_STYLE_CLASSES = {
    'striped': 'table-striped',
    'bordered': 'table-bordered',
    'hover': 'table-hover',
    'compact': 'table-sm',
}

_DATATABLE_CLASSES = {
    'upload_zone': 'mb-3',
    'upload_label': 'form-label',
    'upload_help': 'form-text',
    'load_button': 'btn btn-secondary mt-2',
    'submit_wrapper': 'mt-3',
    'submit_button': 'btn btn-primary',
    'csv_template': 'btn btn-secondary btn-sm mb-2',
}

_MATERIAL_DATATABLE_CLASSES = {
    'upload_zone': 'md-field',
    'upload_label': 'md-field-label',
    'upload_help': 'md-help-text',
    'load_button': 'md-button md-button--tonal',
    'submit_wrapper': 'md-field',
    'submit_button': 'md-button md-button--filled',
    'csv_template': 'md-button md-button--text',
}


class RendererTheme:
    """Lightweight hook points for wrapping rendered forms per framework."""

    name = 'default'
    style_variant = 'default'

    def __init__(self, submit_label: str = 'Submit') -> None:
        self.submit_label = submit_label
        self.form_style: FormStyle = get_form_style('default', 'default')
        self._load_form_style(self.name, self.style_variant)

    def _load_form_style(self, framework: str, variant: str | None = None) -> None:
        try:
            self.form_style = get_form_style(framework, variant)
        except KeyError:
            self.form_style = get_form_style('default', 'default')

    def transform_form_attributes(self, attrs: dict[str, str]) -> dict[str, str]:
        """Adjust form attributes before rendering."""

        return attrs

    def before_form(self) -> str:
        """Markup inserted before the opening form tag."""

        return self.form_style.assets.before_form

    def after_form(self) -> str:
        """Markup appended after the closing form tag."""

        # JavaScript to prevent Enter key from submitting forms
        prevent_enter_script = """
<script>
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        // Prevent Enter key from submitting forms unless on submit button
        const forms = document.querySelectorAll('form.pydantic-form');
        forms.forEach(function(form) {
            form.addEventListener('keydown', function(e) {
                // Check if Enter key is pressed
                if (e.key === 'Enter' || e.keyCode === 13) {
                    const target = e.target;

                    // Allow Enter in textareas (for multi-line input)
                    if (target.tagName === 'TEXTAREA') {
                        return;
                    }

                    // Allow Enter on submit buttons
                    if (target.tagName === 'BUTTON' && target.type === 'submit') {
                        return;
                    }

                    // Allow Enter on input type="submit"
                    if (target.tagName === 'INPUT' && target.type === 'submit') {
                        return;
                    }

                    // Prevent form submission for all other cases
                    e.preventDefault();
                    return false;
                }
            });
        });
    });
})();
</script>
"""

        after_form_assets = self.form_style.assets.after_form
        if after_form_assets:
            return prevent_enter_script + '\n' + after_form_assets
        return prevent_enter_script

    def render_form_wrapper(
        self,
        *,
        form_attrs: dict[str, str],
        csrf_token: str,
        form_content: str,
        submit_markup: str,
        render_time: float | None = None,
    ) -> str:
        template = self.form_wrapper_template()
        attrs = form_attrs.copy()
        form_id = attrs.pop('id', '')
        form_class = attrs.get('class', '')
        form_style = attrs.get('style', '')
        method = attrs.get('method', 'POST')
        action = attrs.get('action', '')

        reserved = {'id', 'class', 'style', 'method', 'action'}
        extra_attrs = []
        for key, value in attrs.items():
            if key in reserved:
                continue
            if value is None or value is False:
                continue
            if value is True:
                extra_attrs.append(key)
            else:
                extra_attrs.append(f'{key}="{escape(str(value))}"')

        # Add timing display if requested
        timing_display = ''
        if render_time is not None:
            render_time_str = f'{render_time:.3f}'
            timing_display = html(
                t'<div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--sf-on-surface-variant, #5c636a); '
                t'text-align: right;">Rendered in {render_time_str}s</div>'
            )

        wrapper = template.render(
            # form_wrapper's t-string template already HTML-escapes these --
            # escaping again here would double-escape (e.g. '&' -> '&amp;amp;').
            form_id=str(form_id) if form_id else '',
            form_class=str(form_class) if form_class else '',
            form_style=str(form_style) if form_style else '',
            method=str(method) if method else 'POST',
            action=str(action) if action else '',
            form_attributes=' '.join(extra_attrs),
            csrf_token=csrf_token,
            form_content=form_content,
            submit_buttons=submit_markup + timing_display,
        )

        blocks = [
            fragment for fragment in [self.before_form(), wrapper, self.after_form()] if fragment
        ]
        return '\n'.join(blocks)

    def render_submit_button(self, button_class: str) -> str:
        """Return HTML for the submit button."""
        # submit_button's t-string template already HTML-escapes these.
        template = self.form_style.templates.submit_button
        return template.render(
            submit_label=self.submit_label,
            button_class=button_class or '',
        )

    # --- Framework-specific extension hooks -------------------------------------------------
    def control_attributes(self, ui_element: str, attrs: dict[str, Any]) -> dict[str, Any]:
        """Adjust a control's HTML attributes before its input renders it."""

        return attrs

    def field_shell(self, framework: str) -> FieldShellRenderer:
        """The markup around each control (label, help, error, wrapper).

        By default the renderer's framework string picks it, so a custom theme
        renders fields exactly as its framework always has.
        """

        return field_shell_for_framework(framework)

    def form_class(self) -> str:
        """Return the base CSS class for <form> elements (if any)."""

        return ''

    def field_wrapper_class(self) -> str:
        """Return the wrapper class for individual input blocks."""

        return ''

    def input_class(self, _ui_element: str) -> str:
        """Return the CSS class applied to rendered inputs."""

        return ''

    def button_class(self) -> str:
        """Return the CSS class used for submit buttons."""

        return ''

    def tab_component_assets(self) -> str:
        """Return CSS/JS assets for tab layouts."""

        return self.form_style.assets.tab_assets

    def accordion_component_assets(self) -> str:
        """Return CSS/JS assets for accordion layouts."""

        return self.form_style.assets.accordion_assets

    def wizard_component_assets(self) -> str:
        """Return CSS/JS assets for the step wizard layout."""

        return self.form_style.assets.wizard_assets

    def form_wrapper_template(self) -> TemplateString:
        """Return the template used for the outer <form> element."""

        return self.form_style.templates.form_wrapper

    def tab_layout_template(self) -> TemplateString:
        """Return the template used when rendering tab layouts."""

        return self.form_style.templates.tab_layout

    def accordion_layout_template(self) -> TemplateString:
        """Return the template used for accordion layouts."""

        return self.form_style.templates.accordion_layout

    def render_layout_section(self, _title: str, _body_html: str, _help_text: str) -> str:
        """Return framework-specific markup for layout/card sections."""

        return ''

    def alert_class(self, kind: str) -> str:
        """Classes for an inline message box; kind is 'danger', 'warning' or 'info'."""

        return f'alert alert-{kind}'

    def render_collapsible_section(
        self, *, title: str, body_html: str, is_open: bool, field_name: str
    ) -> str:
        """A sub-form shown as a section the user can fold away."""

        _body = SafeHTML(body_html)
        if is_open:
            return html(t'''<details class="nested-model-section" data-field-name="{field_name}" open>
    <summary class="nested-model-summary">{title}</summary>
    <div class="nested-model-body">{_body}</div>
</details>''')
        return html(t'''<details class="nested-model-section" data-field-name="{field_name}">
    <summary class="nested-model-summary">{title}</summary>
    <div class="nested-model-body">{_body}</div>
</details>''')

    def render_error_summary(self, items_html: str) -> str:
        """The list of every error, shown at the top of a form that failed."""

        _items = SafeHTML(items_html)
        return html(t"""<div class="alert alert-danger schemaforms-error-summary" role="alert" aria-live="polite">
<strong>Submission failed.</strong> Please correct the following:
<ul class="mb-0 mt-2">{_items}</ul>
</div>""")

    def table_class(self, style: dict[str, Any]) -> str:
        """Classes for a data table; `style` holds its striped/bordered/hover/compact flags."""

        classes = ['table']
        classes.extend(css for flag, css in _TABLE_STYLE_CLASSES.items() if style.get(flag))
        return ' '.join(classes)

    def datatable_class(self, slot: str) -> str:
        """Classes for the chrome around a data table (see `_DATATABLE_CLASSES`)."""

        return _DATATABLE_CLASSES[slot]

    def render_model_list_item(self, item: ModelListItem) -> str:
        """One repeating sub-form item (its header, remove button and fields)."""

        return render_default_model_list_item(item)

    def render_model_list_container(
        self,
        *,
        field_name: str,
        label: str,
        is_required: bool,
        min_items: int,
        max_items: int,
        items_html: str,
        help_text: str | None,
        error: str | None,
        add_button_label: str,
    ) -> str:
        """Render framework-aware markup for schema-driven model lists."""
        # All the model_list_* t-string templates below already HTML-escape
        # their string params -- escaping again here would double-escape.
        templates = self.form_style.templates
        required_indicator = ' <span class="text-danger">*</span>' if is_required else ''
        help_html = templates.model_list_help.render(help_text=help_text) if help_text else ''
        error_html = templates.model_list_error.render(error_text=error) if error else ''

        return templates.model_list_container.render(
            field_name=field_name,
            label=label or '',
            required_indicator=required_indicator,
            min_items=str(min_items),
            max_items=str(max_items),
            items_id=f'{field_name}-items',
            items_html=items_html,
            add_button_label=add_button_label,
            help_html=help_html,
            error_html=error_html,
        )


class DefaultTheme(RendererTheme):
    """Default theme used for Bootstrap/plain frameworks."""

    name = 'default'


class FrameworkTheme(RendererTheme):
    """Renderer theme that mirrors the legacy framework config mapping."""

    def __init__(
        self,
        framework: str,
        include_assets: bool = False,
        *,
        asset_mode: str = 'vendored',
        submit_label: str = 'Submit',
    ) -> None:
        super().__init__(submit_label=submit_label)
        self.framework = framework
        self.config: dict[str, str] = get_framework_config(framework)
        self.include_assets = include_assets
        self.asset_mode = asset_mode

    def before_form(self) -> str:
        blocks = [super().before_form()]
        if self.include_assets:
            css = framework_css_tag(framework=self.framework, asset_mode=self.asset_mode)
            if css:
                blocks.append(css)
        return '\n'.join([b for b in blocks if b])

    def after_form(self) -> str:
        blocks = []
        if self.include_assets:
            js = framework_js_tag(framework=self.framework, asset_mode=self.asset_mode)
            if js:
                blocks.append(js)
        blocks.append(super().after_form())
        return '\n'.join([b for b in blocks if b])

    def form_class(self) -> str:
        return self.config.get('form_class', '')

    def field_wrapper_class(self) -> str:
        return self.config.get('field_wrapper_class', '')

    def input_class(self, ui_element: str) -> str:
        # 'toggle'/aliases render as an HTML checkbox under the hood, and
        # radio/checkbox_group are groups of checkbox-family <input>s -- all
        # need checkbox_class, not select_class (Bootstrap's .form-select
        # paints a dropdown chevron; applying it to a radio/checkbox <input>
        # makes it look like a broken dropdown arrow instead of a radio
        # button). See field_renderer._CHECKBOX_FAMILY_ELEMENTS -- duplicated
        # here rather than imported to avoid a circular import between the
        # two modules.
        if ui_element in {
            'checkbox',
            'toggle',
            'toggle_switch',
            'checkbox_toggle',
            'radio',
            'checkbox_group',
        }:
            return self.config.get('checkbox_class', '')
        if ui_element in {'select', 'multiselect'}:
            return self.config.get('select_class', '')
        return self.config.get('input_class', '')

    def button_class(self) -> str:
        return self.config.get('button_class', '')


class BootstrapTheme(FrameworkTheme):
    name = 'bootstrap'

    def __init__(self, include_assets: bool = False, *, asset_mode: str = 'vendored') -> None:
        super().__init__('bootstrap', include_assets=include_assets, asset_mode=asset_mode)

    def before_form(self) -> str:
        base = super().before_form()
        if not self.include_assets:
            return base
        icons_tag = bootstrap_icons_css_tag(asset_mode=self.asset_mode)
        if icons_tag:
            return f'{base}\n{icons_tag}' if base else icons_tag
        return base


class PlainTheme(FrameworkTheme):
    name = 'plain'

    def __init__(self, include_assets: bool = False, *, asset_mode: str = 'vendored') -> None:
        super().__init__('none', include_assets=include_assets, asset_mode=asset_mode)

    def table_class(self, style: dict[str, Any]) -> str:
        return ''

    def datatable_class(self, slot: str) -> str:
        return '' if slot == 'csv_template' else super().datatable_class(slot)


class MaterialTheme(RendererTheme):
    """Material Design 3, self-contained: its CSS and JS ship inline with the
    form (assets/material/), so the page needs no CSS framework or icon font."""

    name = 'material'
    VARIANTS = ('outlined', 'filled')

    def __init__(
        self,
        include_assets: bool = False,
        *,
        asset_mode: str = 'vendored',
        variant: str = 'outlined',
    ) -> None:
        # The asset options are accepted for parity with the other themes; this
        # theme always inlines its own CSS and JS.
        super().__init__(submit_label='Submit')
        if variant not in self.VARIANTS:
            raise ValueError(f"material_variant must be 'outlined' or 'filled', not {variant!r}")
        self.variant = variant
        self._load_form_style('material')

    def field_shell(self, framework: str) -> FieldShellRenderer:
        return MaterialFieldShell()

    def input_class(self, ui_element: str) -> str:
        kind = material_field_kind(ui_element)
        if kind == 'select':
            return 'md-select'
        if kind == 'textarea':
            return 'md-textarea'
        if kind == 'text':
            return 'md-input'
        if kind == 'checkbox':
            return 'md-checkbox'
        return ''

    def control_attributes(self, ui_element: str, attrs: dict[str, Any]) -> dict[str, Any]:
        # An empty placeholder lets CSS tell an empty field (:placeholder-shown)
        # from a filled one, which is what floats the label.
        if material_field_kind(ui_element) in {'text', 'textarea'} and not attrs.get('placeholder'):
            attrs = {**attrs, 'placeholder': ' '}
        return attrs

    def render_error_summary(self, items_html: str) -> str:
        _items = SafeHTML(items_html)
        return html(t"""<section class="md-field">
<div class="md-error-summary" role="alert" aria-live="polite">
<div class="md-error-summary__title">Submission failed. Please correct the following:</div>
<ul class="md-error-summary__list">{_items}</ul>
</div>
</section>""")

    def alert_class(self, kind: str) -> str:
        return f'md-banner md-banner--{kind}'

    def before_form(self) -> str:
        return '\n'.join(['<!-- pydantic-schemaforms Material Design 3 -->', material_style_tag()])

    def transform_form_attributes(self, attrs: dict[str, str]) -> dict[str, str]:
        attrs = attrs.copy()
        existing_class = attrs.get('class', '').strip()
        classes = ['md-form']
        if self.variant == 'filled':
            classes.append('md-form--filled')
        if existing_class:
            classes.append(existing_class)
        attrs['class'] = ' '.join(classes)
        # Let the browser check required fields on a single-page form; grouped
        # layouts put novalidate back (see render_form_from_model).
        attrs.pop('novalidate', None)
        return attrs

    def after_form(self) -> str:
        return material_script_tag() + '\n' + super().after_form()

    def render_submit_button(self, button_class: str) -> str:
        classes = 'md-button md-button-filled'
        if button_class:
            classes = f'{classes} {button_class}'.strip()
        button_html = html(
            t'    <button type="submit" class="{classes}">{self.submit_label}</button>'
        )
        return '\n'.join(
            [
                '<div class="md-field">',
                button_html,
                '</div>',
            ]
        )

    def render_layout_section(self, title: str, body_html: str, help_text: str) -> str:
        help_markup = html(t'<p class="md-layout-card__help">{help_text}</p>') if help_text else ''
        _body_html = SafeHTML(str(body_html))
        return '\n'.join(
            [
                '<section class="md-layout-card">',
                '  <header class="md-layout-card__header">',
                html(t'    <span class="md-layout-card__title">{title}</span>'),
                '  </header>',
                '  <div class="md-layout-card__body">',
                html(t'    {help_markup}'),
                '    <div class="md-layout-card__content">',
                html(t'      {_body_html}'),
                '    </div>',
                _CLOSE_INNER_DIV,
                _CLOSE_SECTION,
            ]
        )

    def table_class(self, style: dict[str, Any]) -> str:
        flags = [f'md-table--{flag}' for flag in _TABLE_STYLE_CLASSES if style.get(flag)]
        return ' '.join(['md-table', *flags])

    def datatable_class(self, slot: str) -> str:
        return _MATERIAL_DATATABLE_CLASSES[slot]

    def render_model_list_item(self, item: ModelListItem) -> str:
        title = html(
            t'<span class="md-model-item__title" data-model-list-title>{item.item_title}</span>'
        )
        delete_icon = SafeHTML(str(render_material_icon('delete')))
        remove = html(
            t'<button type="button" class="md-icon-button remove-item-btn" '
            t'data-index="{item.index}" data-field-name="{item.field_name}" '
            t'title="Remove this item" aria-label="Remove this item">{delete_icon}</button>'
        )
        cells = SafeHTML(
            ''.join(
                str(
                    html(
                        t'<div class="md-model-item__cell{" md-model-item__cell--full" if full else ""}">'
                        t'{SafeHTML(cell)}</div>'
                    )
                )
                for cell, full in item.cells
            )
        )
        if not item.collapsible:
            return str(
                html(t'''<div class="md-card md-model-item model-list-item" data-index="{item.index}"
     data-title-template="{item.title_template}" data-field-name="{item.field_name}">
<div class="md-model-item__header">{title}{remove}</div>
<div class="md-model-item__body">{cells}</div>
</div>''')
            )
        chevron = SafeHTML(
            str(render_material_icon('expand_more', classes='md-model-item__chevron'))
        )
        open_attr = SafeHTML(' open' if item.expanded else '')
        return str(
            html(t'''<div class="md-card md-model-item model-list-item" data-index="{item.index}"
     data-title-template="{item.title_template}" data-field-name="{item.field_name}">
<div class="md-model-item__remove">{remove}</div>
<details class="md-model-item__details"{open_attr}>
<summary class="md-model-item__header">{chevron}{title}</summary>
<div class="md-model-item__body">{cells}</div>
</details>
</div>''')
        )

    def tab_component_assets(self) -> str:
        return TAB_COMPONENT_SCRIPT

    def accordion_component_assets(self) -> str:
        return ACCORDION_COMPONENT_SCRIPT

    def render_model_list_container(
        self,
        *,
        field_name: str,
        label: str,
        is_required: bool,
        min_items: int,
        max_items: int,
        items_html: str,
        help_text: str | None,
        error: str | None,
        add_button_label: str,
    ) -> str:
        required_class = ' required' if is_required else ''
        help_block = html(t'<p class="md-help-text">{help_text}</p>') if help_text else ''
        error_block = html(t'<p class="md-error-text">{error}</p>') if error else ''
        add_icon = SafeHTML(str(render_material_icon('add', classes='md-button__icon')))

        parts = [
            '<section class="md-model-list-wrapper">',
            html(t'  <label class="md-field-label{required_class}">{label}</label>'),
            html(
                t'  <div class="model-list-container md-model-list-container" '
                t'data-field-name="{field_name}" '
                t'       data-min-items="{min_items}" data-max-items="{max_items}">'
            ),
            html(
                t'    <div class="model-list-items md-model-list-items" '
                t'         id="{field_name}-items">'
            ),
        ]

        if items_html:
            _items_html = SafeHTML(str(items_html))
            parts.append(html(t'      {_items_html}'))

        parts.extend(
            [
                '    </div>',
                '    <div class="md-model-list-actions">',
                html(
                    t'      <button type="button" class="md-button md-button-tonal add-item-btn" '
                    t'              data-target="{field_name}">'
                ),
                html(t'        {add_icon}'),
                html(t'        <span class="md-button__label">{add_button_label}</span>'),
                '      </button>',
                '    </div>',
                _CLOSE_INNER_DIV,
            ]
        )

        if help_block:
            parts.append(html(t'  {help_block}'))
        if error_block:
            parts.append(html(t'  {error_block}'))

        parts.append(_CLOSE_SECTION)
        return '\n'.join(parts)


_THEME_MAP: dict[str, type[RendererTheme]] = {
    'bootstrap': BootstrapTheme,
    'material': MaterialTheme,
    'none': PlainTheme,
}


def get_theme_for_framework(
    framework: str,
    *,
    include_assets: bool = False,
    asset_mode: str = 'vendored',
    material_variant: str | None = None,
) -> RendererTheme:
    """Return a RendererTheme instance that matches the requested framework."""

    theme_cls = _THEME_MAP.get(framework.lower())
    if theme_cls is MaterialTheme:
        return MaterialTheme(variant=material_variant or 'outlined')
    if theme_cls is None:
        return FrameworkTheme(framework, include_assets=include_assets, asset_mode=asset_mode)
    return theme_cls(include_assets=include_assets, asset_mode=asset_mode)  # type: ignore[call-arg]
