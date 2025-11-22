"""
Live server-side validation system using HTMX for pydantic-forms.

This module provides real-time server-side validation capabilities using HTMX,
allowing complex validation rules that can't be handled client-side.

Requires: Python 3.14+ (uses native template strings)
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from .templates import TemplateString


@dataclass
class ValidationResponse:
    """Response from server-side validation."""

    field_name: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    value: Any = None
    formatted_value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "field_name": self.field_name,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "value": self.value,
            "formatted_value": self.formatted_value,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


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
    success_class: str = "is-valid"
    error_class: str = "is-invalid"
    warning_class: str = "has-warning"
    loading_class: str = "is-validating"

    # HTMX settings
    target_selector: str = "this"
    swap_strategy: str = "outerHTML"
    indicator_selector: str = ".validation-indicator"


class LiveValidator:
    """
    Live validation system using HTMX for real-time server-side validation.

    Provides seamless integration between client-side forms and server-side
    validation using Python 3.14 template strings for optimal performance.
    """

    def __init__(self, config: Optional[HTMXValidationConfig] = None):
        """
        Initialize live validator.

        Args:
            config: HTMX validation configuration
        """
        self.config = config or HTMXValidationConfig()
        self.validators: Dict[str, Callable] = {}
        self.field_configs: Dict[str, Dict[str, Any]] = {}

        # Template for validation responses
        self.validation_template = TemplateString(
            """
<div class="validation-feedback ${feedback_class}"
     id="${field_name}-feedback">
    ${feedback_content}
</div>
"""
        )

        # Template for field with validation
        self.field_template = TemplateString(
            """
<div class="form-group ${group_class}">
    ${label}
    <input type="${input_type}"
           id="${field_name}"
           name="${field_name}"
           class="form-control ${input_class}"
           value="${value}"
           ${validation_attributes}
           ${other_attributes} />
    <div id="${field_name}-feedback" class="validation-feedback">
        ${existing_feedback}
    </div>
</div>
"""
        )

        # HTMX JavaScript template
        self.htmx_script = TemplateString(
            """
<script>
// HTMX Live Validation System
document.addEventListener('DOMContentLoaded', function() {

    // Configure HTMX validation settings
    const validationConfig = ${config_json};

    // Add validation indicators
    function addValidationIndicator(element) {
        if (!element.parentElement.querySelector('.validation-indicator')) {
            const indicator = document.createElement('div');
            indicator.className = 'validation-indicator';
            indicator.innerHTML = '<i class="spinner-border spinner-border-sm" role="status"></i>';
            indicator.style.display = 'none';
            element.parentElement.appendChild(indicator);
        }
    }

    // Show loading state
    function showValidationLoading(element) {
        element.classList.add(validationConfig.loading_class);
        const indicator = element.parentElement.querySelector('.validation-indicator');
        if (indicator) indicator.style.display = 'inline-block';
    }

    // Hide loading state
    function hideValidationLoading(element) {
        element.classList.remove(validationConfig.loading_class);
        const indicator = element.parentElement.querySelector('.validation-indicator');
        if (indicator) indicator.style.display = 'none';
    }

    // Handle validation response
    function handleValidationResponse(element, response) {
        hideValidationLoading(element);

        // Remove previous validation classes
        element.classList.remove(
            validationConfig.success_class,
            validationConfig.error_class,
            validationConfig.warning_class
        );

        if (response.is_valid) {
            if (validationConfig.show_success_indicators) {
                element.classList.add(validationConfig.success_class);
            }
        } else {
            element.classList.add(validationConfig.error_class);
        }

        if (response.warnings && response.warnings.length > 0 && validationConfig.show_warnings) {
            element.classList.add(validationConfig.warning_class);
        }
    }

    // Initialize validation for all form fields
    document.querySelectorAll('[data-validate-endpoint]').forEach(function(element) {
        addValidationIndicator(element);

        // Add event listeners based on configuration
        if (validationConfig.validate_on_blur) {
            element.addEventListener('blur', function() {
                if (this.value.trim() !== '') {
                    showValidationLoading(this);
                }
            });
        }

        if (validationConfig.validate_on_input && validationConfig.debounce_ms > 0) {
            let debounceTimer;
            element.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                const field = this;
                debounceTimer = setTimeout(function() {
                    if (field.value.trim() !== '') {
                        showValidationLoading(field);
                    }
                }, validationConfig.debounce_ms);
            });
        }

        if (validationConfig.clear_on_focus) {
            element.addEventListener('focus', function() {
                const feedbackElement = document.getElementById(this.name + '-feedback');
                if (feedbackElement) {
                    feedbackElement.innerHTML = '';
                }
                this.classList.remove(
                    validationConfig.success_class,
                    validationConfig.error_class,
                    validationConfig.warning_class
                );
            });
        }
    });

    // Handle HTMX validation responses
    document.addEventListener('htmx:afterRequest', function(event) {
        const element = event.detail.elt;
        if (element.hasAttribute('data-validate-endpoint')) {
            try {
                const response = JSON.parse(event.detail.xhr.responseText);
                handleValidationResponse(element, response);
            } catch (e) {
                console.error('Failed to parse validation response:', e);
                hideValidationLoading(element);
            }
        }
    });
});
</script>
"""
        )

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
                            if error["loc"] == (fname,):
                                errors.append(error["msg"])

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
                warnings=["No validator registered for this field"],
                value=value,
            )

        validator = self.validators[field_name]
        return validator(value)

    def generate_validation_endpoint_code(self, framework: str = "flask") -> str:
        """
        Generate code for validation endpoints in various frameworks.

        Args:
            framework: Web framework (flask, fastapi, django)

        Returns:
            Code string for validation endpoints
        """
        if framework.lower() == "flask":
            return self._generate_flask_endpoint()
        elif framework.lower() == "fastapi":
            return self._generate_fastapi_endpoint()
        elif framework.lower() == "django":
            return self._generate_django_endpoint()
        else:
            raise ValueError(f"Unsupported framework: {framework}")

    def _generate_flask_endpoint(self) -> str:
        """Generate Flask validation endpoint code."""
        template = TemplateString(
            """
from flask import request, jsonify
from pydantic_forms.live_validation import ValidationResponse

@app.route('/validate/<field_name>', methods=['POST'])
def validate_field(field_name):
    '''Live validation endpoint for individual fields.'''
    try:
        value = request.form.get('value') or request.json.get('value')

        # Get the validator instance (you need to inject this)
        validator = get_validator_instance()  # Implement this function

        response = validator.validate_field(field_name, value)

        if response.is_valid:
            feedback_html = '<div class="valid-feedback">✓ Valid</div>'
        else:
            errors_html = '<br>'.join(response.errors)
            feedback_html = f'<div class="invalid-feedback">{errors_html}</div>'

        return feedback_html, 200 if response.is_valid else 400

    except Exception as e:
        return f'<div class="invalid-feedback">Validation error: {str(e)}</div>', 500
"""
        )
        return template.render()

    def _generate_fastapi_endpoint(self) -> str:
        """Generate FastAPI validation endpoint code."""
        template = TemplateString(
            """
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_forms.live_validation import ValidationResponse

class ValidationRequest(BaseModel):
    value: Any

@app.post('/validate/{field_name}')
async def validate_field(field_name: str, request: ValidationRequest):
    '''Live validation endpoint for individual fields.'''
    try:
        # Get the validator instance (you need to inject this)
        validator = get_validator_instance()  # Implement this function

        response = validator.validate_field(field_name, request.value)

        if response.is_valid:
            feedback_html = '<div class="valid-feedback">✓ Valid</div>'
        else:
            errors_html = '<br>'.join(response.errors)
            feedback_html = f'<div class="invalid-feedback">{errors_html}</div>'

        return HTMLResponse(
            content=feedback_html,
            status_code=200 if response.is_valid else 400
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Validation error: {str(e)}')
"""
        )
        return template.render()

    def _generate_django_endpoint(self) -> str:
        """Generate Django validation endpoint code."""
        template = TemplateString(
            """
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["POST"])
def validate_field(request, field_name):
    '''Live validation endpoint for individual fields.'''
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            value = data.get('value')
        else:
            value = request.POST.get('value')

        # Get the validator instance (you need to inject this)
        validator = get_validator_instance()  # Implement this function

        response = validator.validate_field(field_name, value)

        if response.is_valid:
            feedback_html = '<div class="valid-feedback">✓ Valid</div>'
            status = 200
        else:
            errors_html = '<br>'.join(response.errors)
            feedback_html = f'<div class="invalid-feedback">{errors_html}</div>'
            status = 400

        return HttpResponse(feedback_html, status=status)

    except Exception as e:
        return HttpResponse(
            f'<div class="invalid-feedback">Validation error: {str(e)}</div>',
            status=500
        )
"""
        )
        return template.render()

    def render_field_with_live_validation(
        self,
        field_name: str,
        field_type: str = "text",
        value: Any = "",
        validation_endpoint: str = None,
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
            validation_endpoint = f"/validate/{field_name}"

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
            trigger = f"input delay:{self.config.debounce_ms}ms"
            validation_attrs.append(f'hx-trigger="{trigger}"')
        elif self.config.validate_on_change:
            validation_attrs.append('hx-trigger="change"')

        # Build other attributes
        other_attrs = []
        for key, val in kwargs.items():
            if key not in ["class", "id", "name"]:
                other_attrs.append(f'{key}="{val}"')

        # Render field
        return self.field_template.render(
            field_name=field_name,
            input_type=field_type,
            value=str(value) if value is not None else "",
            input_class=kwargs.get("class", ""),
            group_class="",
            label=f'<label for="{field_name}">{kwargs.get("label", field_name.title())}</label>',
            validation_attributes=" ".join(validation_attrs),
            other_attributes=" ".join(other_attrs),
            existing_feedback="",
        )

    def render_htmx_script(self) -> str:
        """
        Render the HTMX JavaScript for live validation.

        Returns:
            HTML script tag with HTMX validation code
        """
        config_json = json.dumps(
            {
                "validate_on_blur": self.config.validate_on_blur,
                "validate_on_input": self.config.validate_on_input,
                "validate_on_change": self.config.validate_on_change,
                "debounce_ms": self.config.debounce_ms,
                "show_success_indicators": self.config.show_success_indicators,
                "show_warnings": self.config.show_warnings,
                "show_suggestions": self.config.show_suggestions,
                "clear_on_focus": self.config.clear_on_focus,
                "success_class": self.config.success_class,
                "error_class": self.config.error_class,
                "warning_class": self.config.warning_class,
                "loading_class": self.config.loading_class,
            }
        )

        return self.htmx_script.render(config_json=config_json)


# Convenience functions for common validation patterns
def create_email_validator() -> Callable[[str], ValidationResponse]:
    """Create a validator for email fields."""
    import re

    def validate_email(value: str) -> ValidationResponse:
        if not value:
            return ValidationResponse(
                field_name="email", is_valid=False, errors=["Email is required"], value=value
            )

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            return ValidationResponse(
                field_name="email",
                is_valid=False,
                errors=["Please enter a valid email address"],
                suggestions=["Example: user@example.com"],
                value=value,
            )

        return ValidationResponse(
            field_name="email", is_valid=True, value=value, formatted_value=value.lower()
        )

    return validate_email


def create_password_strength_validator(min_length: int = 8) -> Callable[[str], ValidationResponse]:
    """Create a validator for password strength."""
    import re

    def validate_password(value: str) -> ValidationResponse:
        errors = []
        warnings = []
        suggestions = []

        if len(value) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")

        if not re.search(r"[A-Z]", value):
            warnings.append("Password should contain at least one uppercase letter")
            suggestions.append("Add an uppercase letter (A-Z)")

        if not re.search(r"[a-z]", value):
            warnings.append("Password should contain at least one lowercase letter")
            suggestions.append("Add a lowercase letter (a-z)")

        if not re.search(r"\d", value):
            warnings.append("Password should contain at least one number")
            suggestions.append("Add a number (0-9)")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            warnings.append("Password should contain at least one special character")
            suggestions.append("Add a special character (!@#$%^&*)")

        is_valid = len(errors) == 0

        return ValidationResponse(
            field_name="password",
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            value=value,
        )

    return validate_password
