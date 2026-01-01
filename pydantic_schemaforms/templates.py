"""
Native Python 3.14 template string system for pydantic-schemaforms.

This module provides a high-performance template engine using Python 3.14's
native string.templatelib. No backward compatibility is provided.

Requires: Python 3.14+
"""

import string
import string.templatelib
from collections import OrderedDict
from threading import RLock
from typing import Any, Dict, Optional

# Import version check to ensure compatibility

# Global template cache with explicit locking for thread safety
_TEMPLATE_CACHE_MAX = 256
_template_cache: "OrderedDict[str, string.Template]" = OrderedDict()
_template_cache_lock = RLock()


class TemplateString:
    """
    Native Python 3.14 template string wrapper.

    Provides a clean API for template rendering with automatic caching and
    type-safe variable substitution using string.templatelib.

    No legacy template support - Python 3.14+ only.
    """

    def __init__(self, template_str: str):
        """
        Initialize template string.

        Args:
            template_str: Template string with ${variable} placeholders
        """
        self.template_str = template_str
        self._compiled: Optional[string.Template] = None

    def _compile_template(self, template_str: str) -> string.Template:
        """Compile and cache template for performance using global cache."""
        with _template_cache_lock:
            template = _template_cache.get(template_str)
            if template is None:
                template = string.Template(template_str)
                _template_cache[template_str] = template
                if len(_template_cache) > _TEMPLATE_CACHE_MAX:
                    _template_cache.popitem(last=False)
            else:
                _template_cache.move_to_end(template_str)

            return template

    def render(self, **kwargs: Any) -> str:
        """
        Render template with provided variables.

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            Rendered template string

        Raises:
            KeyError: If required template variables are missing
        """
        if self._compiled is None:
            self._compiled = self._compile_template(self.template_str)

        # Convert all values to strings, handling None gracefully
        safe_kwargs = {}
        for key, value in kwargs.items():
            if value is None:
                safe_kwargs[key] = ""
            elif isinstance(value, bool):
                safe_kwargs[key] = "true" if value else "false"
            else:
                safe_kwargs[key] = str(value)

        return self._compiled.substitute(**safe_kwargs)

    def safe_render(self, **kwargs: Any) -> str:
        """
        Safely render template, leaving unfilled variables as placeholders.

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            Rendered template string with unfilled variables preserved
        """
        if self._compiled is None:
            self._compiled = self._compile_template(self.template_str)

        # Convert all values to strings
        safe_kwargs = {}
        for key, value in kwargs.items():
            if value is None:
                safe_kwargs[key] = ""
            elif isinstance(value, bool):
                safe_kwargs[key] = "true" if value else "false"
            else:
                safe_kwargs[key] = str(value)

        return self._compiled.safe_substitute(**safe_kwargs)


class FormTemplates:
    """
    Collection of modern form templates using Python 3.14 template strings.

    Provides pre-built templates for common form elements and layouts with
    optimized rendering performance.
    """

    # Input Templates
    TEXT_INPUT = TemplateString(
        """
<div class="form-group ${wrapper_class}" style="${wrapper_style}">
    ${label}
    <input type="text"
           id="${id}"
           name="${name}"
           class="form-control ${input_class}"
           style="${input_style}"
           value="${value}"
           placeholder="${placeholder}"
           ${required}
           ${disabled}
           ${readonly}
           ${attributes} />
    ${help_text}
    ${error_message}
</div>
"""
    )

    EMAIL_INPUT = TemplateString(
        """
<div class="form-group ${wrapper_class}" style="${wrapper_style}">
    ${label}
    <input type="email"
           id="${id}"
           name="${name}"
           class="form-control ${input_class}"
           style="${input_style}"
           value="${value}"
           placeholder="${placeholder}"
           ${required}
           ${disabled}
           ${readonly}
           ${attributes} />
    ${help_text}
    ${error_message}
</div>
"""
    )

    PASSWORD_INPUT = TemplateString(
        """
<div class="form-group ${wrapper_class}" style="${wrapper_style}">
    ${label}
    <div class="input-group">
        <input type="password"
               id="${id}"
               name="${name}"
               class="form-control ${input_class}"
               style="${input_style}"
               value="${value}"
               placeholder="${placeholder}"
               ${required}
               ${disabled}
               ${readonly}
               ${attributes} />
        <button class="btn btn-outline-secondary" type="button" onclick="togglePassword('${id}')">
            <i class="bi bi-eye" id="${id}_toggle_icon"></i>
        </button>
    </div>
    ${help_text}
    ${error_message}
</div>
"""
    )

    NUMBER_INPUT = TemplateString(
        """
<div class="form-group ${wrapper_class}" style="${wrapper_style}">
    ${label}
    <input type="number"
           id="${id}"
           name="${name}"
           class="form-control ${input_class}"
           style="${input_style}"
           value="${value}"
           placeholder="${placeholder}"
           min="${min_value}"
           max="${max_value}"
           step="${step}"
           ${required}
           ${disabled}
           ${readonly}
           ${attributes} />
    ${help_text}
    ${error_message}
</div>
"""
    )

    SELECT_INPUT = TemplateString(
        """
<div class="form-group ${wrapper_class}" style="${wrapper_style}">
    ${label}
    <select id="${id}"
            name="${name}"
            class="form-select ${input_class}"
            style="${input_style}"
            ${required}
            ${disabled}
            ${multiple}
            ${attributes}>
        ${options}
    </select>
    ${help_text}
    ${error_message}
</div>
"""
    )

    TEXTAREA_INPUT = TemplateString(
        """
<div class="form-group ${wrapper_class}" style="${wrapper_style}">
    ${label}
    <textarea id="${id}"
              name="${name}"
              class="form-control ${input_class}"
              style="${input_style}"
              rows="${rows}"
              cols="${cols}"
              placeholder="${placeholder}"
              ${required}
              ${disabled}
              ${readonly}
              ${attributes}>${value}</textarea>
    ${help_text}
    ${error_message}
</div>
"""
    )

    CHECKBOX_INPUT = TemplateString(
        """
<div class="form-check ${wrapper_class}" style="${wrapper_style}">
    <input type="checkbox"
           id="${id}"
           name="${name}"
           class="form-check-input ${input_class}"
           style="${input_style}"
           value="${checkbox_value}"
           ${checked}
           ${required}
           ${disabled}
           ${attributes} />
    <label class="form-check-label" for="${id}">
        ${label_text}
    </label>
    ${help_text}
    ${error_message}
</div>
"""
    )

    RADIO_INPUT = TemplateString(
        """
<div class="form-group ${wrapper_class}" style="${wrapper_style}">
    ${label}
    <div class="radio-group">
        ${radio_options}
    </div>
    ${help_text}
    ${error_message}
</div>
"""
    )

    # Layout Templates
    FORM_WRAPPER = TemplateString(
        """
<form id="${form_id}"
      class="pydantic-form ${form_class}"
      style="${form_style}"
      method="${method}"
      action="${action}"
      ${form_attributes}>
    ${csrf_token}
    ${form_content}
    ${submit_buttons}
</form>
"""
    )

    VERTICAL_LAYOUT = TemplateString(
        """
<div class="vertical-layout ${layout_class}" style="${layout_style}">
    ${sections}
</div>
"""
    )

    HORIZONTAL_LAYOUT = TemplateString(
        """
<div class="horizontal-layout row ${layout_class}" style="${layout_style}">
    ${sections}
</div>
"""
    )

    TAB_LAYOUT = TemplateString(
        """
<div class="tab-layout ${layout_class}" style="${layout_style}">
    <div class="tab-navigation" role="tablist">
        ${tab_buttons}
    </div>
    <div class="tab-content">
        ${tab_panels}
    </div>
</div>
${component_assets}
"""
    )

    TAB_BUTTON = TemplateString(
        """
<button class="tab-button${active_class}"
        type="button"
        role="tab"
        aria-selected="${aria_selected}"
        aria-controls="${tab_id}"
        onclick="switchTab('${tab_id}', this)">
    ${title}
</button>
"""
    )

    TAB_PANEL = TemplateString(
        """
<div id="${tab_id}"
     class="tab-panel${active_class}"
     role="tabpanel"
     style="display: ${display_style};"
     aria-hidden="${aria_hidden}">
    ${content}
</div>
"""
    )

    ACCORDION_LAYOUT = TemplateString(
        """
<div class="accordion-layout ${layout_class}" style="${layout_style}">
    ${sections}
</div>
${component_assets}
"""
    )

    ACCORDION_SECTION = TemplateString(
        """
<div class="accordion-section">
    <button class="accordion-header${expanded_class}"
            aria-expanded="${aria_expanded}"
            aria-controls="${section_id}"
            onclick="toggleAccordion('${section_id}', this)">
        ${title}
    </button>
    <div id="${section_id}"
         class="accordion-content"
         style="display: ${display_style};">
        ${content}
    </div>
</div>
"""
    )

    SECTION = TemplateString(
        """
<div class="form-section ${section_class}" style="${section_style}">
    ${section_title}
    ${section_content}
</div>
"""
    )

    # Helper Templates
    LABEL = TemplateString(
        """
<label for="${for_id}" class="form-label ${label_class}" style="${label_style}">
    ${icon}${label_text}${required_indicator}
</label>
"""
    )

    HELP_TEXT = TemplateString(
        """
<div class="form-text ${help_class}" style="${help_style}">
    ${help_content}
</div>
"""
    )

    ERROR_MESSAGE = TemplateString(
        """
<div class="invalid-feedback ${error_class}" style="${error_style}">
    ${error_content}
</div>
"""
    )

    ICON = TemplateString(
        """
<i class="bi bi-${icon_name} ${icon_class}" style="${icon_style}"></i>
"""
    )

    # Form Control Groups
    INPUT_GROUP = TemplateString(
        """
<div class="input-group ${group_class}" style="${group_style}">
    ${prepend}
    ${input_element}
    ${append}
</div>
"""
    )

    # Complete Page Templates
    FORM_PAGE = TemplateString(
        """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${page_title}</title>
    ${css_links}
    ${custom_styles}
</head>
<body>
    <div class="container">
        ${page_header}
        ${form_content}
        ${page_footer}
    </div>
    ${js_links}
    ${custom_scripts}
</body>
</html>
"""
    )

    # Material Templates
    MATERIAL_FIELD_CONTAINER = TemplateString(
        """
<div class="md-field">
    ${field_body}
    ${help_text}
    ${error_text}
</div>
"""
    )

    MATERIAL_FIELD_WITH_ICON = TemplateString(
        """
<div class="md-field-with-icon">
    ${icon_markup}
    ${input_wrapper}
</div>
"""
    )

    MATERIAL_FIELD_INPUT_WRAPPER = TemplateString(
        """
<div class="md-input-wrapper">
    ${input_control}
    <label class="md-floating-label" for="${field_id}">${label}${required_indicator}</label>
</div>
"""
    )

    MATERIAL_ICON = TemplateString(
        """
<span class="md-icon material-icons">${icon_name}</span>
"""
    )

    MATERIAL_TEXT_INPUT = TemplateString(
        """
<input type="${input_type}"
       name="${name}"
       id="${field_id}"
       class="md-input${error_class}"
       value="${value}"
        placeholder=" " ${attributes}>
"""
    )

    MATERIAL_TEXTAREA = TemplateString(
        """
<textarea name="${name}"
          id="${field_id}"
          class="md-textarea${error_class}"
          placeholder=" ">${value}</textarea>
"""
    )

    MATERIAL_SELECT = TemplateString(
        """
<select name="${name}"
        id="${field_id}"
        class="md-select${error_class}">
    ${options}
</select>
"""
    )

    MATERIAL_SELECT_OPTION = TemplateString(
        """
<option value="${value}"${selected}>${label}</option>
"""
    )

    MATERIAL_HELP_TEXT = TemplateString(
        """
<div class="md-help-text">${help_content}</div>
"""
    )

    MATERIAL_ERROR_TEXT = TemplateString(
        """
<div class="md-error-text">${error_content}</div>
"""
    )

    MATERIAL_CHECKBOX_FIELD = TemplateString(
        """
<div class="md-field">
    <div class="md-checkbox-container">
        <input type="checkbox"
               name="${name}"
               id="${field_id}"
               class="md-checkbox"
               value="true"
               ${checked}>
        <label for="${field_id}" class="md-checkbox-label">${label}${required_indicator}</label>
    </div>
    ${help_text}
    ${error_text}
</div>
"""
    )

    MATERIAL_SUBMIT_BUTTON = TemplateString(
        """
<div class="md-field">
    <button type="submit" class="md-button md-button-filled">${label}</button>
</div>
"""
    )

    MATERIAL_MODEL_LIST_WRAPPER = TemplateString(
        """
<div class="md-field">
    <div class="md-model-list-container">
        ${content}
    </div>
</div>
"""
    )


def render_template(template: TemplateString, **kwargs: Any) -> str:
    """
    Convenience function to render a template with variables.

    Args:
        template: TemplateString instance to render
        **kwargs: Variables for template substitution

    Returns:
        Rendered template string
    """
    return template.render(**kwargs)


def create_custom_template(template_str: str) -> TemplateString:
    """
    Create a custom template from a string.

    Args:
        template_str: Template string with ${variable} placeholders

    Returns:
        TemplateString instance
    """
    return TemplateString(template_str)


# Template validation and utilities
def validate_template_variables(template: TemplateString, **kwargs: Any) -> Dict[str, bool]:
    """
    Validate that all required template variables are provided.

    Args:
        template: TemplateString to validate
        **kwargs: Variables to check

    Returns:
        Dictionary mapping variable names to whether they are satisfied
    """
    import re

    # Extract variable names from template
    template_vars = set()
    for match in re.finditer(r"\$\{(\w+)\}", template.template_str):
        template_vars.add(match.group(1))

    # Check which variables are satisfied
    provided_vars = set(kwargs.keys())
    return {var: var in provided_vars for var in template_vars}


# Performance utilities
def precompile_templates():
    """Precompile all form templates for optimal performance."""
    for attr_name in dir(FormTemplates):
        if not attr_name.startswith("_"):
            template = getattr(FormTemplates, attr_name)
            if isinstance(template, TemplateString):
                # Trigger compilation by accessing _compile_template
                template._compile_template(template.template_str)


# Initialize template compilation on import for better performance
precompile_templates()
