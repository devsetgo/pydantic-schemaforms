"""Renderer theme helpers for enhanced form renderers."""

from __future__ import annotations

from html import escape
from typing import Dict, Optional, Type

from ..templates import TemplateString
from ..assets.runtime import framework_css_tag, framework_js_tag
from .form_style import FormStyle, get_form_style
from .frameworks import get_framework_config
from .material_icons import render_material_icon

__all__ = [
    "RendererTheme",
    "DefaultTheme",
    "FrameworkTheme",
    "BootstrapTheme",
    "MaterialTheme",
    "PlainTheme",
    "MaterialEmbeddedTheme",
    "get_theme_for_framework",
]


class RendererTheme:
    """Lightweight hook points for wrapping rendered forms per framework."""

    name = "default"
    style_variant = "default"

    def __init__(self, submit_label: str = "Submit") -> None:
        self.submit_label = submit_label
        self.form_style: FormStyle = get_form_style("default", "default")
        self._load_form_style(self.name, self.style_variant)

    def _load_form_style(self, framework: str, variant: str | None = None) -> None:
        try:
            self.form_style = get_form_style(framework, variant)
        except KeyError:
            self.form_style = get_form_style("default", "default")

    def transform_form_attributes(self, attrs: Dict[str, str]) -> Dict[str, str]:
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
            return prevent_enter_script + "\n" + after_form_assets
        return prevent_enter_script

    def render_form_wrapper(
        self,
        *,
        form_attrs: Dict[str, str],
        csrf_token: str,
        form_content: str,
        submit_markup: str,
    ) -> str:
        template = self.form_wrapper_template()
        attrs = form_attrs.copy()
        form_id = attrs.pop("id", "")
        form_class = attrs.get("class", "")
        form_style = attrs.get("style", "")
        method = attrs.get("method", "POST")
        action = attrs.get("action", "")

        reserved = {"id", "class", "style", "method", "action"}
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

        wrapper = template.render(
            form_id=escape(str(form_id)) if form_id else "",
            form_class=escape(str(form_class)) if form_class else "",
            form_style=escape(str(form_style)) if form_style else "",
            method=escape(str(method)) if method else "POST",
            action=escape(str(action)) if action else "",
            form_attributes=" ".join(extra_attrs),
            csrf_token=csrf_token,
            form_content=form_content,
            submit_buttons=submit_markup,
        )

        blocks = [fragment for fragment in [self.before_form(), wrapper, self.after_form()] if fragment]
        return "\n".join(blocks)

    def render_submit_button(self, button_class: str) -> str:
        """Return HTML for the submit button."""
        template = self.form_style.templates.submit_button
        return template.render(
            submit_label=escape(self.submit_label),
            button_class=escape(button_class) if button_class else "",
        )

    # --- Framework-specific extension hooks -------------------------------------------------
    def form_class(self) -> str:
        """Return the base CSS class for <form> elements (if any)."""

        return ""

    def field_wrapper_class(self) -> str:
        """Return the wrapper class for individual input blocks."""

        return ""

    def input_class(self, ui_element: str) -> str:
        """Return the CSS class applied to rendered inputs."""

        return ""

    def button_class(self) -> str:
        """Return the CSS class used for submit buttons."""

        return ""

    def tab_component_assets(self) -> str:
        """Return CSS/JS assets for tab layouts."""

        return self.form_style.assets.tab_assets

    def accordion_component_assets(self) -> str:
        """Return CSS/JS assets for accordion layouts."""

        return self.form_style.assets.accordion_assets

    def form_wrapper_template(self) -> TemplateString:
        """Return the template used for the outer <form> element."""

        return self.form_style.templates.form_wrapper

    def tab_layout_template(self) -> TemplateString:
        """Return the template used when rendering tab layouts."""

        return self.form_style.templates.tab_layout

    def accordion_layout_template(self) -> TemplateString:
        """Return the template used for accordion layouts."""

        return self.form_style.templates.accordion_layout

    def render_layout_section(self, title: str, body_html: str, help_text: str) -> str:
        """Return framework-specific markup for layout/card sections."""

        return ""

    def render_model_list_container(
        self,
        *,
        field_name: str,
        label: str,
        is_required: bool,
        min_items: int,
        max_items: int,
        items_html: str,
        help_text: Optional[str],
        error: Optional[str],
        add_button_label: str,
    ) -> str:
        """Render framework-aware markup for schema-driven model lists."""
        templates = self.form_style.templates
        required_indicator = ' <span class="text-danger">*</span>' if is_required else ""
        help_html = (
            templates.model_list_help.render(help_text=escape(help_text)) if help_text else ""
        )
        error_html = (
            templates.model_list_error.render(error_text=escape(error)) if error else ""
        )

        return templates.model_list_container.render(
            field_name=escape(field_name, quote=True),
            label=escape(label) if label else "",
            required_indicator=required_indicator,
            min_items=str(min_items),
            max_items=str(max_items),
            items_id=escape(f"{field_name}-items", quote=True),
            items_html=items_html,
            add_button_label=escape(add_button_label),
            help_html=help_html,
            error_html=error_html,
        )

    def render_model_list_item(
        self,
        *,
        field_name: str,
        model_label: str,
        index: int,
        body_html: str,
        remove_button_aria_label: str,
    ) -> str:
        """Render a single model list item wrapper."""
        templates = self.form_style.templates
        return templates.model_list_item.render(
            field_name=escape(field_name, quote=True),
            model_label=escape(model_label),
            index=str(index),
            display_index=str(index + 1),
            body_html=body_html,
            remove_button_aria_label=escape(remove_button_aria_label),
        )


class DefaultTheme(RendererTheme):
    """Default theme used for Bootstrap/plain frameworks."""

    name = "default"


class FrameworkTheme(RendererTheme):
    """Renderer theme that mirrors the legacy framework config mapping."""

    def __init__(
        self,
        framework: str,
        include_assets: bool = False,
        *,
        asset_mode: str = "vendored",
        submit_label: str = "Submit",
    ) -> None:
        super().__init__(submit_label=submit_label)
        self.framework = framework
        self.config = get_framework_config(framework)
        self.include_assets = include_assets
        self.asset_mode = asset_mode

    def before_form(self) -> str:
        blocks = [super().before_form()]
        if self.include_assets:
            css = framework_css_tag(framework=self.framework, asset_mode=self.asset_mode)
            if css:
                blocks.append(css)
        return "\n".join([b for b in blocks if b])

    def after_form(self) -> str:
        blocks = []
        if self.include_assets:
            js = framework_js_tag(framework=self.framework, asset_mode=self.asset_mode)
            if js:
                blocks.append(js)
        blocks.append(super().after_form())
        return "\n".join([b for b in blocks if b])

    def form_class(self) -> str:
        return self.config.get("form_class", "")

    def field_wrapper_class(self) -> str:
        return self.config.get("field_wrapper_class", "")

    def input_class(self, ui_element: str) -> str:
        if ui_element == "checkbox":
            return self.config.get("checkbox_class", "")
        if ui_element in {"select", "radio", "multiselect"}:
            return self.config.get("select_class", "")
        return self.config.get("input_class", "")

    def button_class(self) -> str:
        return self.config.get("button_class", "")


class BootstrapTheme(FrameworkTheme):
    name = "bootstrap"

    def __init__(self, include_assets: bool = False, *, asset_mode: str = "vendored") -> None:
        super().__init__("bootstrap", include_assets=include_assets, asset_mode=asset_mode)


class MaterialTheme(FrameworkTheme):
    name = "material"

    def __init__(self, include_assets: bool = False, *, asset_mode: str = "vendored") -> None:
        super().__init__("material", include_assets=include_assets, asset_mode=asset_mode)

    def render_model_list_item(
        self,
        *,
        field_name: str,
        model_label: str,
        index: int,
        body_html: str,
        remove_button_aria_label: str,
    ) -> str:
        return super().render_model_list_item(
            field_name=field_name,
            model_label=model_label,
            index=index,
            body_html=body_html,
            remove_button_aria_label=remove_button_aria_label,
        )


class PlainTheme(FrameworkTheme):
    name = "plain"

    def __init__(self, include_assets: bool = False, *, asset_mode: str = "vendored") -> None:
        super().__init__("none", include_assets=include_assets, asset_mode=asset_mode)


class MaterialEmbeddedTheme(RendererTheme):
    """Self-contained Material Design 3 theme with inline assets."""

    name = "material-embedded"

    def __init__(self) -> None:
        super().__init__(submit_label="Submit")
        self._css = self._build_css()
        self._js = self._build_js()


    def before_form(self) -> str:
        return "\n".join(
            [
                "<!-- Material Design 3 Self-Contained Form -->",
                self._css,
                '<div class="md-form-container">',
            ]
        )

    def transform_form_attributes(self, attrs: Dict[str, str]) -> Dict[str, str]:
        attrs = attrs.copy()
        existing_class = attrs.get("class", "").strip()
        combined = "md-form" if not existing_class else f"md-form {existing_class}"
        attrs["class"] = combined
        attrs.setdefault("novalidate", "novalidate")
        return attrs

    def after_form(self) -> str:
        # JavaScript to prevent Enter key from submitting forms
        prevent_enter_script = """
<script>
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        // Prevent Enter key from submitting forms unless on submit button
        const forms = document.querySelectorAll('form.md-form, form.pydantic-form');
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
        return "\n".join(
            [
                "</div>",
                self._js,
                prevent_enter_script,
            ]
        )

    def render_submit_button(self, button_class: str) -> str:
        classes = "md-button md-button-filled"
        if button_class:
            classes = f"{classes} {button_class}".strip()
        return "\n".join(
            [
                '<div class="md-field">',
                f'    <button type="submit" class="{classes}">{escape(self.submit_label)}</button>',
                '</div>',
            ]
        )

    def render_layout_section(self, title: str, body_html: str, help_text: str) -> str:
        help_markup = (
            f'<p class="md-layout-card__help">{escape(help_text)}</p>' if help_text else ""
        )
        return "\n".join(
            [
                '<section class="md-layout-card">',
                '  <header class="md-layout-card__header">',
                f'    <span class="md-layout-card__title">{escape(title)}</span>',
                '  </header>',
                '  <div class="md-layout-card__body">',
                f"    {help_markup}",
                '    <div class="md-layout-card__content">',
                f"      {body_html}",
                '    </div>',
                '  </div>',
                '</section>',
            ]
        )

    def tab_component_assets(self) -> str:
        return """
<script>
function switchTab(tabId, buttonElement) {
    const tabLayout = buttonElement.closest('.tab-layout');
    const panels = tabLayout.querySelectorAll('.tab-panel');
    const buttons = tabLayout.querySelectorAll('.tab-button');

    panels.forEach(panel => {
        panel.style.display = 'none';
        panel.setAttribute('aria-hidden', 'true');
    });

    buttons.forEach(button => {
        button.classList.remove('active');
        button.setAttribute('aria-selected', 'false');
    });

    const selectedPanel = document.getElementById(tabId);
    if (selectedPanel) {
        selectedPanel.style.display = 'block';
        selectedPanel.setAttribute('aria-hidden', 'false');
    }

    buttonElement.classList.add('active');
    buttonElement.setAttribute('aria-selected', 'true');
}
</script>
<style>
.md-form-container .tab-layout {
    border-radius: 28px !important;
    background: #fff !important;
    border: 1px solid #e7e0ec !important;
    padding: 16px 24px !important;
    margin-bottom: 28px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
}

.md-form-container .tab-layout .tab-navigation {
    display: flex !important;
    gap: 4px !important;
    border-bottom: 1px solid #e7e0ec !important;
    margin-bottom: 16px !important;
}

.md-form-container .tab-layout .tab-button {
    border: none !important;
    background: transparent !important;
    color: #49454f !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    transition: color 0.15s ease, border-color 0.15s ease !important;
}

.md-form-container .tab-layout .tab-button.active {
    color: #6750a4 !important;
    border-bottom-color: #6750a4 !important;
    font-weight: 600 !important;
}

.md-form-container .tab-layout .tab-button:hover {
    background: rgba(103, 80, 164, 0.08) !important;
}

.md-form-container .tab-layout .tab-panel {
    padding: 8px 0 !important;
}
</style>
"""

    def accordion_component_assets(self) -> str:
        return """
<script>
function toggleAccordion(sectionId, buttonElement) {
    const content = document.getElementById(sectionId);
    const isExpanded = buttonElement.getAttribute('aria-expanded') === 'true';

    if (isExpanded) {
        content.style.display = 'none';
        buttonElement.setAttribute('aria-expanded', 'false');
        buttonElement.classList.remove('expanded');
    } else {
        content.style.display = 'block';
        buttonElement.setAttribute('aria-expanded', 'true');
        buttonElement.classList.add('expanded');
    }
}
</script>
<style>
.md-form-container .accordion-layout {
    border: none !important;
    padding: 0 !important;
}

.md-form-container .accordion-layout .accordion-section {
    border: 1px solid #e7e0ec !important;
    border-radius: 24px !important;
    margin-bottom: 16px !important;
    background: #ffffff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

.md-form-container .accordion-layout .accordion-header {
    background: transparent !important;
    color: #1c1b1f !important;
    font-weight: 600 !important;
    padding: 1rem 1.25rem !important;
    border: none !important;
    border-radius: 24px 24px 0 0 !important;
}

.md-form-container .accordion-layout .accordion-header.expanded {
    background: #e8def8 !important;
    color: #1c1b1f !important;
}

.md-form-container .accordion-layout .accordion-content {
    padding: 1rem 1.25rem 1.5rem !important;
}
</style>
"""

    def render_model_list_container(
        self,
        *,
        field_name: str,
        label: str,
        is_required: bool,
        min_items: int,
        max_items: int,
        items_html: str,
        help_text: Optional[str],
        error: Optional[str],
        add_button_label: str,
    ) -> str:
        required_class = " required" if is_required else ""
        help_block = (
            f'<p class="md-help-text">{escape(help_text)}</p>' if help_text else ""
        )
        error_block = (
            f'<p class="md-error-text">{escape(error)}</p>' if error else ""
        )

        parts = [
            '<section class="md-model-list-wrapper">',
            f'  <label class="md-field-label{required_class}">{escape(label)}</label>',
            f'  <div class="model-list-container md-model-list-container" data-field-name="{field_name}" '
            f'       data-min-items="{min_items}" data-max-items="{max_items}">',
            '    <div class="model-list-items md-model-list-items" '
            f'         id="{field_name}-items">',
        ]

        if items_html:
            parts.append(f"      {items_html}")

        parts.extend(
            [
                "    </div>",
                '    <div class="md-model-list-actions">',
                f'      <button type="button" class="md-button md-button-tonal add-item-btn" '
                f'              data-target="{field_name}">',
                f'        {render_material_icon("add", classes="md-button__icon")}',
                f'        <span class="md-button__label">{escape(add_button_label)}</span>',
                '      </button>',
                '    </div>',
                '  </div>',
            ]
        )

        if help_block:
            parts.append(f'  {help_block}')
        if error_block:
            parts.append(f'  {error_block}')

        parts.append('</section>')
        return "\n".join(parts)

    def render_model_list_item(
        self,
        *,
        field_name: str,
        model_label: str,
        index: int,
        body_html: str,
        remove_button_aria_label: str,
    ) -> str:
        safe_label = escape(model_label)
        safe_field = escape(field_name, quote=True)
        safe_remove_label = escape(remove_button_aria_label)

        return "\n".join(
            [
                '<section class="md-model-card" '
                f'data-index="{index}" data-field-name="{safe_field}">',
                '  <header class="md-model-card__header">',
                '    <h6 class="mdc-typography--subtitle2 mb-0">',
                f'      {safe_label} #{index + 1}',
                '    </h6>',
                '    <button type="button" class="md-icon-button remove-item-btn"',
                f'            data-index="{index}" aria-label="{safe_remove_label}">',
                f'      {render_material_icon("delete", classes="md-icon")}',
                '    </button>',
                '  </header>',
                '  <div class="md-model-card__body">',
                f'    {body_html}',
                '  </div>',
                '</section>',
            ]
        )

    @staticmethod
    def _build_css() -> str:
        return """<style>
/* Material Design 3 Self-Contained Styles - Using !important to override any conflicting styles */
.md-form-container {
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 20px !important;
    line-height: 1.5 !important;
    color: #1c1b1f !important;
    background: #fef7ff !important;
    border: none !important;
    box-sizing: border-box !important;
    position: relative !important;
}

.md-form {
    width: 100% !important;
    background: #ffffff !important;
    border-radius: 28px !important;
    padding: 32px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 2px 6px 2px rgba(0,0,0,0.15) !important;
    border: none !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Reset any Bootstrap interference */
.md-form * {
    box-sizing: border-box !important;
}

/* Material Design Form Fields */
.md-field {
    margin-bottom: 32px !important;
    position: relative !important;
    width: 100% !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Model list container styling to blend with Material Design */
.md-model-list-container {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Override Bootstrap styles for model list items within Material Design */
.md-model-list-container .card {
    border: 1px solid #79747e !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    margin-bottom: 16px !important;
    background: #ffffff !important;
}

.md-model-list-container .card-header {
    background: #f7f2fa !important;
    border-bottom: 1px solid #e7e0ec !important;
    border-radius: 12px 12px 0 0 !important;
    color: #1c1b1f !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 500 !important;
}

.md-model-list-container .btn {
    border-radius: 20px !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 500 !important;
    text-transform: none !important;
}

.md-model-list-container .btn-primary {
    background: #6750a4 !important;
    border-color: #6750a4 !important;
}

.md-model-list-container .btn-danger {
    background: #ba1a1a !important;
    border-color: #ba1a1a !important;
}

.md-model-list-wrapper {
    background: transparent !important;
    margin-bottom: 32px !important;
}

.md-model-list-container {
    border: 1px solid #e7e0ec !important;
    border-radius: 24px !important;
    padding: 16px 20px !important;
    background: #fff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

.md-model-list-items {
    display: flex !important;
    flex-direction: column !important;
    gap: 16px !important;
}

.md-model-card {
    border: 1px solid #e7e0ec !important;
    border-radius: 20px !important;
    background: #ffffff !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

.md-model-card__header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 12px !important;
}

.md-model-card__body {
    padding: 0 !important;
}

.md-model-list-actions {
    margin-top: 12px !important;
    display: flex !important;
    justify-content: flex-end !important;
}

.md-button-tonal {
    background: #e8def8 !important;
    color: #1c1b1f !important;
}

.md-button-tonal:hover {
    background: #cdc2db !important;
}

.md-button__icon {
    margin-right: 8px !important;
    width: 20px !important;
    height: 20px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex: 0 0 20px !important;
    fill: currentColor !important;
}

.md-button__label {
    font-weight: 500 !important;
}

/* Layout card styling */
.md-layout-card {
    background: #ffffff !important;
    border-radius: 24px !important;
    padding: 24px 28px !important;
    margin-bottom: 32px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2), 0 4px 8px rgba(0,0,0,0.1) !important;
    border: 1px solid #e7e0ec !important;
}

.md-layout-card__header {
    margin-bottom: 12px !important;
}

.md-layout-card__title {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #1c1b1f !important;
}

.md-layout-card__help {
    color: #49454f !important;
    font-size: 14px !important;
    margin-bottom: 12px !important;
}

.md-layout-card__content {
    display: flex !important;
    flex-direction: column !important;
    gap: 16px !important;
}

.md-field-label {
    display: block !important;
    color: #49454f !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    margin-bottom: 8px !important;
    position: relative !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    line-height: 1.4 !important;
}

.md-field-label.required::after {
    content: ' *' !important;
    color: #ba1a1a !important;
}

/* Material Design Outlined Text Fields */
.md-text-field {
    position: relative;
    width: 100%;
}

/* Field container */
.md-field {
    margin: 16px 0;
}

/* Field with icon layout */
.md-field-with-icon {
    display: flex !important;
    align-items: flex-start !important;
    gap: 12px !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Input wrapper for proper label positioning */
.md-input-wrapper {
    position: relative !important;
    flex: 1 !important;
    width: 100% !important;
}

.md-input {
    width: 100% !important;
    padding: 16px !important;
    border: 1px solid #79747e !important;
    border-radius: 4px !important;
    background: transparent !important;
    color: #1c1b1f !important;
    font-size: 16px !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    outline: none !important;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-sizing: border-box !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}

.md-input:focus {
    border-color: #6750a4 !important;
    border-width: 2px !important;
    padding: 15px !important; /* Adjust for thicker border */
    box-shadow: none !important;
}

/* Icon styling - positioned outside to the left of input */
.md-icon {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 24px !important;
    height: 24px !important;
    margin-top: 16px !important; /* Align with input padding */
    color: #49454f !important;
    flex-shrink: 0 !important;
    transition: color 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
    fill: currentColor !important;
}

.md-field-with-icon:focus-within .md-icon {
    color: #6750a4 !important;
}

.md-input:focus + .md-floating-label,
.md-input:not(:placeholder-shown) + .md-floating-label,
.md-textarea:focus + .md-floating-label,
.md-textarea:not(:placeholder-shown) + .md-floating-label,
.md-select:focus + .md-floating-label {
    transform: translateY(-28px) scale(0.75) !important;
    color: #6750a4 !important;
    background: #ffffff !important;
    padding: 0 4px !important;
}

.md-floating-label {
    position: absolute !important;
    left: 16px !important;
    top: 16px !important;
    color: #49454f !important;
    font-size: 16px !important;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
    pointer-events: none !important;
    background: transparent !important;
    z-index: 1 !important;
    transform-origin: left top !important;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-weight: 400 !important;
    line-height: 1.4 !important;
}

.md-input:focus + .md-floating-label,
.md-input:not(:placeholder-shown) + .md-floating-label {
    transform: translateY(-28px) scale(0.75) !important;
    color: #6750a4;
    background: #ffffff;
    padding: 0 4px;
}

.md-input.error {
    border-color: #ba1a1a;
}

.md-input.error:focus {
    border-color: #ba1a1a;
}

.md-input.error + .md-floating-label {
    color: #ba1a1a;
}

/* Material Design Select */
.md-select {
    width: 100%;
    padding: 16px;
    border: 1px solid #79747e;
    border-radius: 4px;
    background: transparent;
    color: #1c1b1f;
    font-size: 16px;
    font-family: inherit;
    outline: none;
    cursor: pointer;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    box-sizing: border-box;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2349454f' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
    background-position: right 12px center;
    background-repeat: no-repeat;
    background-size: 16px;
    padding-right: 40px;
}

.md-select:focus {
    border-color: #6750a4;
    border-width: 2px;
    padding: 15px 39px 15px 15px; /* Adjust for thicker border */
}

.md-select:focus + .md-floating-label {
    transform: translateY(-28px) scale(0.75);
    color: #6750a4;
    background: #ffffff;
    padding: 0 4px;
}

/* Material Design Textarea */
.md-textarea {
    width: 100%;
    min-height: 120px;
    padding: 16px;
    border: 1px solid #79747e;
    border-radius: 4px;
    background: transparent;
    color: #1c1b1f;
    font-size: 16px;
    font-family: inherit;
    outline: none;
    resize: vertical;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    box-sizing: border-box;
}

.md-textarea:focus {
    border-color: #6750a4;
    border-width: 2px;
    padding: 15px; /* Adjust for thicker border */
}

.md-textarea:focus + .md-floating-label,
.md-textarea:not(:placeholder-shown) + .md-floating-label {
    transform: translateY(-28px) scale(0.75);
    color: #6750a4;
    background: #ffffff;
    padding: 0 4px;
}

/* Material Design Checkboxes */
.md-checkbox-container {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin: 16px 0;
    cursor: pointer;
}

.md-checkbox {
    width: 18px;
    height: 18px;
    border: 2px solid #79747e;
    border-radius: 2px;
    background: transparent;
    cursor: pointer;
    position: relative;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    margin-top: 2px; /* Align with text baseline */
    flex-shrink: 0;
}

.md-checkbox:checked {
    background: #6750a4;
    border-color: #6750a4;
}

.md-checkbox:checked::after {
    content: '';
    position: absolute;
    top: 1px;
    left: 4px;
    width: 6px;
    height: 10px;
    border: solid white;
    border-width: 0 2px 2px 0;
    transform: rotate(45deg);
}

.md-checkbox-label {
    color: #1c1b1f;
    font-size: 16px;
    cursor: pointer;
    line-height: 1.5;
}

/* Material Design Buttons */
.md-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 24px;
    border: none;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    text-decoration: none;
    box-sizing: border-box;
    min-width: 64px;
    height: 40px;
    position: relative;
    overflow: hidden;
}

.md-button-filled {
    background: #6750a4;
    color: #ffffff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 1px 3px 1px rgba(0,0,0,0.15);
}

.md-button-filled:hover {
    background: #5a43a0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 2px 6px 2px rgba(0,0,0,0.15);
    transform: translateY(-1px);
}

.md-button-filled:active {
    transform: translateY(0);
    box-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 1px 3px 1px rgba(0,0,0,0.15);
}

/* Help Text */
.md-help-text {
    font-size: 12px;
    color: #49454f;
    margin-top: 4px;
    line-height: 1.33;
    padding-left: 16px;
}

/* Error Text */
.md-error-text {
    font-size: 12px;
    color: #ba1a1a;
    margin-top: 4px;
    line-height: 1.33;
    font-weight: 400;
    padding-left: 16px;
}

/* Number and Date Inputs */
.md-input[type="number"],
.md-input[type="date"],
.md-input[type="email"],
.md-input[type="password"],
.md-input[type="tel"],
.md-input[type="url"] {
    /* Inherit all md-input styles */
}

.md-input[type="color"] {
    height: 56px;
    padding: 8px;
    cursor: pointer;
}

.md-input[type="range"] {
    padding: 16px 8px;
}

/* Placeholder styling */
.md-input::placeholder {
    color: transparent;
}

.md-input:focus::placeholder {
    color: #49454f;
}

/* State layers for interactive elements */
.md-button-filled::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: currentColor;
    opacity: 0;
    transition: opacity 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: inherit;
}

.md-button-filled:hover::before {
    opacity: 0.08;
}

.md-button-filled:focus::before {
    opacity: 0.12;
}

.md-button-filled:active::before {
    opacity: 0.16;
}

/* Responsive Design */
@media (max-width: 768px) {
    .md-form {
        padding: 24px 16px;
        border-radius: 28px;
    }

    .md-field {
        margin-bottom: 24px;
    }
}

/* Typography Scale */
.md-headline-small {
    font-size: 24px;
    font-weight: 400;
    line-height: 32px;
    color: #1c1b1f;
}

.md-body-large {
    font-size: 16px;
    font-weight: 400;
    line-height: 24px;
    color: #1c1b1f;
}

.md-body-medium {
    font-size: 14px;
    font-weight: 400;
    line-height: 20px;
    color: #49454f;
}

.md-label-large {
    font-size: 14px;
    font-weight: 500;
    line-height: 20px;
    color: #1c1b1f;
}

/* Surface colors and elevation */
.md-surface {
    background: #fef7ff;
    color: #1c1b1f;
}

.md-surface-container {
    background: #f3f0ff;
    color: #1c1b1f;
}

.md-surface-container-high {
    background: #e7e0ec;
    color: #1c1b1f;
}
</style>
"""

    @staticmethod
    def _build_js() -> str:
        return """<script>
document.addEventListener('DOMContentLoaded', function() {
    // Material Design 3 form enhancements

    // Floating label functionality for outlined text fields
    function initializeFloatingLabels() {
        const textFields = document.querySelectorAll('.md-input, .md-textarea, .md-select');

        textFields.forEach(input => {
            const label = input.nextElementSibling;
            if (label && label.classList.contains('md-floating-label')) {

                // Check initial state
                function updateLabelState() {
                    const hasValue = input.value && input.value.trim() !== '';
                    const isFocused = document.activeElement === input;

                    if (hasValue || isFocused) {
                        label.style.transform = 'translateY(-28px) scale(0.75)';
                        label.style.color = isFocused ? '#6750a4' : '#49454f';
                        label.style.background = '#ffffff';
                        label.style.padding = '0 4px';
                    } else {
                        label.style.transform = 'translateY(0) scale(1)';
                        label.style.color = '#49454f';
                        label.style.background = 'transparent';
                        label.style.padding = '0';
                    }
                }

                // Set up event listeners
                input.addEventListener('focus', updateLabelState);
                input.addEventListener('blur', updateLabelState);
                input.addEventListener('input', updateLabelState);

                // Initial state check
                updateLabelState();
            }
        });
    }

    // Enhanced focus and blur effects
    const inputs = document.querySelectorAll('.md-input, .md-select, .md-textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)';
        });

        input.addEventListener('blur', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Checkbox interactions with Material Design ripple effect
    const checkboxes = document.querySelectorAll('.md-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const container = this.closest('.md-checkbox-container');
            if (this.checked) {
                // Create ripple effect
                const ripple = document.createElement('div');
                ripple.style.position = 'absolute';
                ripple.style.borderRadius = '50%';
                ripple.style.background = 'rgba(103, 80, 164, 0.3)';
                ripple.style.width = '40px';
                ripple.style.height = '40px';
                ripple.style.left = '-11px';
                ripple.style.top = '-11px';
                ripple.style.pointerEvents = 'none';
                ripple.style.transform = 'scale(0)';
                ripple.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

                this.style.position = 'relative';
                this.appendChild(ripple);

                // Animate ripple
                setTimeout(() => {
                    ripple.style.transform = 'scale(1)';
                    setTimeout(() => {
                        ripple.style.opacity = '0';
                        setTimeout(() => {
                            if (ripple.parentNode) {
                                ripple.parentNode.removeChild(ripple);
                            }
                        }, 300);
                    }, 200);
                }, 10);
            }
        });
    });

    // Enhanced form validation with Material Design styling
    const form = document.querySelector('.md-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const requiredInputs = this.querySelectorAll('input[required], select[required], textarea[required]');
            let hasErrors = false;

            requiredInputs.forEach(input => {
                const value = input.type === 'checkbox' ? input.checked : input.value.trim();
                const fieldContainer = input.closest('.md-field');

                if (!value) {
                    input.classList.add('error');

                    // Add error styling to label
                    const label = input.nextElementSibling;
                    if (label && label.classList.contains('md-floating-label')) {
                        label.style.color = '#ba1a1a';
                    }

                    // Create or update error message
                    let errorDiv = fieldContainer.querySelector('.md-error-text');
                    if (!errorDiv) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'md-error-text';
                        fieldContainer.appendChild(errorDiv);
                    }
                    errorDiv.textContent = 'This field is required';

                    hasErrors = true;
                } else {
                    input.classList.remove('error');

                    // Remove error styling from label
                    const label = input.nextElementSibling;
                    if (label && label.classList.contains('md-floating-label')) {
                        label.style.color = input === document.activeElement ? '#6750a4' : '#49454f';
                    }

                    // Remove error message if it was dynamically added
                    const errorDiv = fieldContainer.querySelector('.md-error-text');
                    if (errorDiv && errorDiv.textContent === 'This field is required') {
                        errorDiv.remove();
                    }
                }
            });

            if (hasErrors) {
                e.preventDefault();
                // Scroll to first error with smooth animation
                const firstError = this.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'nearest'
                    });
                    // Focus the field for better UX
                    setTimeout(() => {
                        firstError.focus();
                    }, 500);
                }
            }
        });

        // Real-time validation for better UX
        const allInputs = form.querySelectorAll('input, select, textarea');
        allInputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.hasAttribute('required')) {
                    const value = this.type === 'checkbox' ? this.checked : this.value.trim();
                    const fieldContainer = this.closest('.md-field');

                    if (!value) {
                        this.classList.add('error');
                        const label = this.nextElementSibling;
                        if (label && label.classList.contains('md-floating-label')) {
                            label.style.color = '#ba1a1a';
                        }
                    } else {
                        this.classList.remove('error');
                        const label = this.nextElementSibling;
                        if (label && label.classList.contains('md-floating-label')) {
                            label.style.color = '#49454f';
                        }
                    }
                }
            });
        });
    }

    # Initialize floating labels
    initializeFloatingLabels();

    # Reinitialize for dynamically added content
    window.reinitializeMaterialForms = function() {
        initializeFloatingLabels();
    };
});
</script>
"""


_THEME_MAP: Dict[str, Type[RendererTheme]] = {
    "bootstrap": BootstrapTheme,
    "material": MaterialTheme,
    "none": PlainTheme,
}


def get_theme_for_framework(
    framework: str,
    *,
    include_assets: bool = False,
    asset_mode: str = "vendored",
) -> RendererTheme:
    """Return a RendererTheme instance that matches the requested framework."""

    theme_cls = _THEME_MAP.get(framework.lower())
    if theme_cls is None:
        return FrameworkTheme(framework, include_assets=include_assets, asset_mode=asset_mode)
    return theme_cls(include_assets=include_assets, asset_mode=asset_mode)
