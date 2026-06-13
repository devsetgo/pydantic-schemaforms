"""
Live server-side validation system using HTMX for pydantic-schemaforms.

This module provides real-time server-side validation capabilities using HTMX,
allowing complex validation rules that can't be handled client-side.

Requires: Python 3.14+ (uses native template strings)
"""

import json
from dataclasses import dataclass
from html import escape as _html_escape
from typing import TYPE_CHECKING, Any
from collections.abc import Callable

from pydantic import BaseModel, ValidationError

from .templates import TemplateString
from .tstring import SafeHTML, html as _html_proc
from .validation import (
    ValidationResponse,
    create_email_validator,
    create_password_strength_validator,
)

if TYPE_CHECKING:  # pragma: no cover
    from .validation import FieldValidator, ValidationSchema


# JS generation — uses .format() per CLAUDE.md (JS context, not HTML).
# {config_json} is the only substitution; all other braces are doubled.
_HTMX_SCRIPT_TEMPLATE = """\
<script>
// HTMX Live Validation System
document.addEventListener('DOMContentLoaded', function() {{

    const validationConfig = {config_json};

    function addValidationIndicator(element) {{
        if (!element.parentElement.querySelector('.validation-indicator')) {{
            const indicator = document.createElement('div');
            indicator.className = 'validation-indicator';
            indicator.innerHTML = '<i class="spinner-border spinner-border-sm" role="status"></i>';
            indicator.style.display = 'none';
            element.parentElement.appendChild(indicator);
        }}
    }}

    function showValidationLoading(element) {{
        element.classList.add(validationConfig.loading_class);
        const indicator = element.parentElement.querySelector('.validation-indicator');
        if (indicator) indicator.style.display = 'inline-block';
    }}

    function hideValidationLoading(element) {{
        element.classList.remove(validationConfig.loading_class);
        const indicator = element.parentElement.querySelector('.validation-indicator');
        if (indicator) indicator.style.display = 'none';
    }}

    function applyValidationClasses(element, is_valid) {{
        element.classList.remove(
            validationConfig.success_class,
            validationConfig.error_class,
            validationConfig.warning_class
        );
        if (is_valid) {{
            if (validationConfig.show_success_indicators) {{
                element.classList.add(validationConfig.success_class);
            }}
        }} else {{
            element.classList.add(validationConfig.error_class);
        }}
    }}

    document.querySelectorAll('[data-validate-endpoint]').forEach(function(element) {{
        addValidationIndicator(element);

        if (validationConfig.validate_on_blur) {{
            element.addEventListener('blur', function() {{
                if (this.value.trim() !== '') showValidationLoading(this);
            }});
        }}

        if (validationConfig.validate_on_input && validationConfig.debounce_ms > 0) {{
            let debounceTimer;
            element.addEventListener('input', function() {{
                clearTimeout(debounceTimer);
                const field = this;
                debounceTimer = setTimeout(function() {{
                    if (field.value.trim() !== '') showValidationLoading(field);
                }}, validationConfig.debounce_ms);
            }});
        }}

        if (validationConfig.clear_on_focus) {{
            element.addEventListener('focus', function() {{
                const feedbackElement = document.getElementById(this.name + '-feedback');
                if (feedbackElement) feedbackElement.innerHTML = '';
                element.classList.remove(
                    validationConfig.success_class,
                    validationConfig.error_class,
                    validationConfig.warning_class
                );
            }});
        }}
    }});

    // Fired by HX-Trigger: validationResult header from validation_response_headers().
    document.addEventListener('validationResult', function(event) {{
        const field = event.detail.field;
        const valid = event.detail.valid;
        const element = document.getElementById(field);
        if (!element) return;
        hideValidationLoading(element);
        applyValidationClasses(element, valid);
    }});

    document.addEventListener('htmx:afterRequest', function(event) {{
        const element = event.detail.elt;
        if (element.hasAttribute('data-validate-endpoint')) hideValidationLoading(element);
    }});
}});
</script>
"""


@dataclass
class HTMXValidationConfig:
    """Configuration for HTMX validation behavior."""

    # Validation triggers
    validate_on_blur: bool = True
    validate_on_input: bool = False
    validate_on_change: bool = True
    debounce_ms: int = 300

    # Response behavior
    show_success_indicators: bool = True
    show_warnings: bool = True
    show_suggestions: bool = True
    clear_on_focus: bool = True

    # Visual feedback
    success_class: str = 'is-valid'
    error_class: str = 'is-invalid'
    warning_class: str = 'has-warning'
    loading_class: str = 'is-validating'

    # HTMX settings
    target_selector: str = 'this'
    swap_strategy: str = 'outerHTML'
    indicator_selector: str = '.validation-indicator'


class LiveValidator:
    """
    Live validation system using HTMX for real-time server-side validation.

    Provides seamless integration between client-side forms and server-side
    validation using Python 3.14 template strings for optimal performance.
    """

    def __init__(self, config: HTMXValidationConfig | None = None):
        """
        Initialize live validator.

        Args:
            config: HTMX validation configuration
        """
        self.config = config or HTMXValidationConfig()
        self.validators: dict[str, Callable] = {}
        self.field_configs: dict[str, dict[str, Any]] = {}

        def _validation_feedback(
            *, feedback_class: str = '', field_name: str = '', feedback_content: str = '', **_: Any
        ) -> SafeHTML:
            _content = SafeHTML(feedback_content)
            return _html_proc(
                t'<div class="validation-feedback {feedback_class}" id="{field_name}-feedback">{_content}</div>'
            )

        def _field_with_validation(
            *,
            group_class: str = '',
            label: str = '',
            input_type: str = 'text',
            field_name: str = '',
            input_class: str = '',
            value: str = '',
            validation_attributes: str = '',
            other_attributes: str = '',
            existing_feedback: str = '',
            **_: Any,
        ) -> SafeHTML:
            _label = SafeHTML(label)
            _va = SafeHTML(validation_attributes)
            _oa = SafeHTML(other_attributes)
            _fb = SafeHTML(existing_feedback)
            return _html_proc(
                t'<div class="form-group {group_class}">{_label}<input type="{input_type}" id="{field_name}" name="{field_name}" class="form-control {input_class}" value="{value}" {_va} {_oa} /><div id="{field_name}-feedback" class="validation-feedback">{_fb}</div></div>'
            )

        self.validation_template = TemplateString(_validation_feedback)
        self.field_template = TemplateString(_field_with_validation)

        def _htmx_script_fn(*, config_json: str = '{}', **_: Any) -> SafeHTML:
            return SafeHTML(_HTMX_SCRIPT_TEMPLATE.format(config_json=config_json))

        self.htmx_script = TemplateString(_htmx_script_fn)

    def register_validator(
        self, field_name: str, validator: Callable[[Any], ValidationResponse]
    ) -> None:
        """
        Register a custom validator for a field.

        Args:
            field_name: Name of the field to validate
            validator: Function that takes a value and returns ValidationResponse
        """
        self.validators[field_name] = validator

    def register_field_validator(self, field_validator: 'FieldValidator') -> None:
        """Register a FieldValidator for live use."""

        def _runner(value: Any) -> ValidationResponse:
            is_valid, errors = field_validator.validate(value)
            return ValidationResponse(
                field_name=field_validator.field_name,
                is_valid=is_valid,
                errors=errors,
                value=value,
            )

        self.validators[field_validator.field_name] = _runner
        existing = self.field_configs.get(field_validator.field_name, {})
        self.field_configs[field_validator.field_name] = {
            **existing,
            'rules': field_validator.to_rule_descriptors(),
        }

    def register_schema(self, schema: 'ValidationSchema') -> None:
        """Register all FieldValidators contained in a ValidationSchema."""

        for field_validator in schema.validators():
            self.register_field_validator(field_validator)

    def register_model_validator(self, model_class: type[BaseModel]) -> None:
        """
        Register validators for all fields in a Pydantic model.

        Args:
            model_class: Pydantic model class
        """
        model_fields = model_class.model_fields

        for field_name, field_info in model_fields.items():

            def create_model_validator(fname: str, finfo: Any):
                def validator(value: Any) -> ValidationResponse:
                    try:
                        # Create a partial model instance for validation
                        test_data = {fname: value}
                        model_class.model_validate(test_data, strict=False)

                        return ValidationResponse(field_name=fname, is_valid=True, value=value)
                    except ValidationError as e:
                        errors = []
                        for error in e.errors():
                            if error['loc'] == (fname,):
                                errors.append(error['msg'])

                        return ValidationResponse(
                            field_name=fname, is_valid=False, errors=errors, value=value
                        )

                return validator

            self.validators[field_name] = create_model_validator(field_name, field_info)

    def validate_field(self, field_name: str, value: Any) -> ValidationResponse:
        """
        Validate a single field value.

        Args:
            field_name: Name of the field
            value: Value to validate

        Returns:
            ValidationResponse with validation results
        """
        if field_name not in self.validators:
            return ValidationResponse(
                field_name=field_name,
                is_valid=True,
                warnings=['No validator registered for this field'],
                value=value,
            )

        validator = self.validators[field_name]
        return validator(value)

    def generate_validation_endpoint_code(self, framework: str = 'flask') -> str:
        """
        Generate code for validation endpoints in various frameworks.

        Args:
            framework: Web framework (flask or fastapi)

        Returns:
            Code string for validation endpoints
        """
        if framework.lower() == 'flask':
            return self._generate_flask_endpoint()
        elif framework.lower() == 'fastapi':
            return self._generate_fastapi_endpoint()
        else:
            raise ValueError("Unsupported framework. Use 'flask' or 'fastapi'.")

    def _generate_flask_endpoint(self) -> str:
        """Generate Flask validation endpoint code."""
        return """
from html import escape as _html_escape
from flask import request, jsonify
from pydantic_schemaforms.live_validation import ValidationResponse

@app.route('/validate/<field_name>', methods=['POST'])
def validate_field(field_name):
    '''Live validation endpoint for individual fields.'''
    try:
        value = request.form.get('value') or request.json.get('value')
        validator = get_validator_instance()
        response = validator.validate_field(field_name, value)
        if response.is_valid:
            feedback_html = '<div class="valid-feedback">\\u2713 Valid</div>'
        else:
            errors_html = '<br>'.join(_html_escape(e) for e in response.errors)
            feedback_html = f'<div class="invalid-feedback">{errors_html}</div>'
        return feedback_html, 200 if response.is_valid else 400
    except Exception as e:
        return f'<div class="invalid-feedback">Validation error: {_html_escape(str(e))}</div>', 500
"""

    def _generate_fastapi_endpoint(self) -> str:
        """Generate FastAPI validation endpoint code."""
        return """
from html import escape as _html_escape
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_schemaforms.live_validation import ValidationResponse

class ValidationRequest(BaseModel):
    value: Any

@app.post('/validate/{field_name}')
async def validate_field(field_name: str, request: ValidationRequest):
    '''Live validation endpoint for individual fields.'''
    try:
        validator = get_validator_instance()
        response = validator.validate_field(field_name, request.value)
        if response.is_valid:
            feedback_html = '<div class="valid-feedback">\\u2713 Valid</div>'
        else:
            errors_html = '<br>'.join(_html_escape(e) for e in response.errors)
            feedback_html = f'<div class="invalid-feedback">{errors_html}</div>'
        return HTMLResponse(content=feedback_html, status_code=200 if response.is_valid else 400)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Validation error: {_html_escape(str(e))}')
"""

    def render_field_with_live_validation(
        self,
        field_name: str,
        field_type: str = 'text',
        value: Any = '',
        validation_endpoint: str | None = None,
        **kwargs,
    ) -> str:
        """
        Render a form field with live validation capabilities.

        Args:
            field_name: Name of the field
            field_type: HTML input type
            value: Current field value
            validation_endpoint: URL for validation endpoint
            **kwargs: Additional field attributes

        Returns:
            HTML string with live validation setup
        """
        if validation_endpoint is None:
            validation_endpoint = f'/validate/{field_name}'

        # Build validation attributes
        validation_attrs = [
            f'hx-post="{validation_endpoint}"',
            f'hx-target="#{field_name}-feedback"',
            'hx-swap="innerHTML"',
            'data-validate-endpoint="true"',
        ]

        if self.config.validate_on_blur:
            validation_attrs.append('hx-trigger="blur"')
        elif self.config.validate_on_input:
            trigger = f'input delay:{self.config.debounce_ms}ms'
            validation_attrs.append(f'hx-trigger="{trigger}"')
        elif self.config.validate_on_change:
            validation_attrs.append('hx-trigger="change"')

        # Build other attributes
        other_attrs = []
        for key, val in kwargs.items():
            if key not in ['class', 'id', 'name']:
                other_attrs.append(f'{key}="{_html_escape(str(val))}"')

        # Render field
        return self.field_template.render(
            field_name=field_name,
            input_type=field_type,
            value=str(value) if value is not None else '',
            input_class=kwargs.get('class', ''),
            group_class='',
            label=str(
                _html_proc(
                    t'<label for="{field_name}">{kwargs.get("label", field_name.title())}</label>'
                )
            ),
            validation_attributes=' '.join(validation_attrs),
            other_attributes=' '.join(other_attrs),
            existing_feedback='',
        )

    def render_htmx_script(self) -> str:
        """
        Render the HTMX JavaScript for live validation.

        Returns:
            HTML script tag with HTMX validation code
        """
        config_json = json.dumps(
            {
                'validate_on_blur': self.config.validate_on_blur,
                'validate_on_input': self.config.validate_on_input,
                'validate_on_change': self.config.validate_on_change,
                'debounce_ms': self.config.debounce_ms,
                'show_success_indicators': self.config.show_success_indicators,
                'show_warnings': self.config.show_warnings,
                'show_suggestions': self.config.show_suggestions,
                'clear_on_focus': self.config.clear_on_focus,
                'success_class': self.config.success_class,
                'error_class': self.config.error_class,
                'warning_class': self.config.warning_class,
                'loading_class': self.config.loading_class,
            }
        )

        return self.htmx_script.render(config_json=config_json)


def validation_response_headers(field_name: str, is_valid: bool) -> dict[str, str]:
    """Return HTTP headers for a live-validation endpoint response.

    Emits an ``HX-Trigger: validationResult`` header that the bundled
    ``htmx_script`` JS uses to apply ``is-valid`` / ``is-invalid`` CSS
    classes to the input without needing to parse the response body.

    Usage (FastAPI)::

        @app.post("/validate/{field_name}")
        async def validate(field_name: str, value: str = Form("")):
            result = live_validator.validate_field(field_name, value)
            feedback = "<div>✓ OK</div>" if result.is_valid else f"<div>{result.errors[0]}</div>"
            headers = validation_response_headers(field_name, result.is_valid)
            return HTMLResponse(feedback, headers=headers)
    """
    trigger = json.dumps({'validationResult': {'field': field_name, 'valid': is_valid}})
    return {'HX-Trigger': trigger}


__all__ = [
    'ValidationResponse',
    'HTMXValidationConfig',
    'LiveValidator',
    'validation_response_headers',
    'create_email_validator',
    'create_password_strength_validator',
]
