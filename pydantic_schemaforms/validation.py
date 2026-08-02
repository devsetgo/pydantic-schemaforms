"""
Advanced validation system for pydantic-schemaforms using Python 3.14 template strings.
Provides both client-side JavaScript validation and server-side Python validation.

Requires: Python 3.14+ (no backward compatibility)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Union, get_args, get_origin
from collections.abc import Callable

from pydantic import BaseModel, ValidationError

from .tstring import SafeHTML

# Import version check to ensure compatibility


_INVALID_VALUE_MSG = 'Invalid value'
_INVALID_EMAIL_MSG = 'Please enter a valid email address'
_INVALID_DATE_MSG = 'Invalid date format'


def _js_str(msg: str) -> str:
    """Escape *msg* for safe embedding in a JS single-quoted string inside a <script> block."""
    return (
        msg.replace('\\', '\\\\')
        .replace("'", "\\'")
        .replace('\n', '\\n')
        .replace('\r', '')
        .replace('<', '\\u003C')
        .replace('>', '\\u003E')
    )


@dataclass
class ValidationResponse:
    """Response from validation (server-side or live HTMX)."""

    field_name: str
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    value: Any = None
    formatted_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'field_name': self.field_name,
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'value': self.value,
            'formatted_value': self.formatted_value,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class ValidationRule:
    """Base class for validation rules."""

    rule_name = 'base'

    def __init__(self, message: str = _INVALID_VALUE_MSG, client_side: bool = True):
        self.message = message
        self.client_side = client_side

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        """
        Validate a value.

        Returns:
            Tuple of (is_valid, error_message)
        """
        raise NotImplementedError

    def get_client_validation(self, field_name: str) -> str:
        """Generate JavaScript validation code."""
        if not self.client_side:
            return ''
        return self._generate_js_validation(field_name)

    def _generate_js_validation(self, _field_name: str) -> str:
        """Override in subclasses to provide JavaScript validation."""
        return ''

    def to_descriptor(self) -> dict[str, Any]:
        """Return a serializable descriptor for this rule."""

        descriptor = {
            'type': self.rule_name,
            'message': self.message,
            'client': self.client_side,
        }
        descriptor.update(self._descriptor_params())
        return descriptor

    def _descriptor_params(self) -> dict[str, Any]:
        return {}


class RequiredRule(ValidationRule):
    """Validates that a field has a value."""

    rule_name = 'required'

    def __init__(self, message: str = 'This field is required'):
        super().__init__(message)

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, self.message
        return True, ''

    def _generate_js_validation(self, field_name: str) -> str:
        return f"""
        if (value === null || value === undefined || (typeof value === 'string' && !value.trim())) {{
            return '{_js_str(self.message)}';
        }}
        """


class MinLengthRule(ValidationRule):
    """Validates minimum string length."""

    rule_name = 'min_length'

    def __init__(self, min_length: int, message: str | None = None):
        self.min_length = min_length
        message = message or f'Must be at least {min_length} characters long'
        super().__init__(message)

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        if value is None:
            return True, ''  # Let RequiredRule handle None values

        if len(str(value)) < self.min_length:
            return False, self.message
        return True, ''

    def _generate_js_validation(self, field_name: str) -> str:
        return f"""
        if (value && value.length < {self.min_length}) {{
            return '{_js_str(self.message)}';
        }}
        """

    def _descriptor_params(self) -> dict[str, Any]:
        return {'min_length': self.min_length}


class MaxLengthRule(ValidationRule):
    """Validates maximum string length."""

    rule_name = 'max_length'

    def __init__(self, max_length: int, message: str | None = None):
        self.max_length = max_length
        message = message or f'Must be no more than {max_length} characters long'
        super().__init__(message)

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        if value is None:
            return True, ''

        if len(str(value)) > self.max_length:
            return False, self.message
        return True, ''

    def _generate_js_validation(self, field_name: str) -> str:
        return f"""
        if (value && value.length > {self.max_length}) {{
            return '{_js_str(self.message)}';
        }}
        """

    def _descriptor_params(self) -> dict[str, Any]:
        return {'max_length': self.max_length}


class RegexRule(ValidationRule):
    """Validates against a regular expression pattern."""

    rule_name = 'regex'

    def __init__(self, pattern: str, message: str = 'Invalid format', flags: int = 0):
        self.pattern = pattern
        self.regex: re.Pattern[str] = re.compile(pattern, flags)
        super().__init__(message)

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        if value is None or value == '':
            return True, ''  # Let RequiredRule handle empty values

        if not self.regex.match(str(value)):
            return False, self.message
        return True, ''

    def _generate_js_validation(self, field_name: str) -> str:
        # Escape the regex pattern for JavaScript
        js_pattern = self.pattern.replace('\\', '\\\\').replace("'", "\\'")
        return f"""
        if (value && !new RegExp('{js_pattern}').test(value)) {{
            return '{_js_str(self.message)}';
        }}
        """

    def _descriptor_params(self) -> dict[str, Any]:
        return {'pattern': self.pattern}


class EmailRule(RegexRule):
    """Validates email addresses."""

    rule_name = 'email'

    def __init__(self, message: str = _INVALID_EMAIL_MSG):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        super().__init__(pattern, message)


class PhoneRule(RegexRule):
    """Validates phone numbers."""

    rule_name = 'phone'

    def __init__(self, message: str = 'Please enter a valid phone number'):
        # Accepts various phone formats
        pattern = r'^[\+]?[1-9]?[\d\s\-\(\)\.]{10,15}$'
        super().__init__(pattern, message)


class NumericRangeRule(ValidationRule):
    """Validates numeric values within a range."""

    rule_name = 'numeric_range'

    def __init__(
        self,
        min_value: float | None = None,
        max_value: float | None = None,
        message: str | None = None,
    ):
        self.min_value = min_value
        self.max_value = max_value

        if message is None:
            if min_value is not None and max_value is not None:
                message = f'Must be between {min_value} and {max_value}'
            elif min_value is not None:
                message = f'Must be at least {min_value}'
            elif max_value is not None:
                message = f'Must be no more than {max_value}'
            else:
                message = 'Invalid numeric value'

        super().__init__(message)

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        if value is None or value == '':
            return True, ''

        try:
            num_value = float(value)

            if self.min_value is not None and num_value < self.min_value:
                return False, self.message

            if self.max_value is not None and num_value > self.max_value:
                return False, self.message

            return True, ''
        except (ValueError, TypeError):  # fmt: skip
            return False, 'Must be a valid number'

    def _generate_js_validation(self, field_name: str) -> str:
        checks = []

        if self.min_value is not None:
            checks.append(f'numValue < {self.min_value}')

        if self.max_value is not None:
            checks.append(f'numValue > {self.max_value}')

        if checks:
            condition = ' || '.join(checks)
            return f"""
            if (value !== '' && value !== null) {{
                const numValue = parseFloat(value);
                if (isNaN(numValue) || {condition}) {{
                    return '{_js_str(self.message)}';
                }}
            }}
            """
        return ''

    def _descriptor_params(self) -> dict[str, Any]:
        return {'min': self.min_value, 'max': self.max_value}


class DateRangeRule(ValidationRule):
    """Validates dates within a range."""

    rule_name = 'date_range'

    def __init__(
        self,
        min_date: date | str | None = None,
        max_date: date | str | None = None,
        message: str | None = None,
    ):
        self.min_date: date | None = self._parse_date(min_date) if min_date else None
        self.max_date: date | None = self._parse_date(max_date) if max_date else None

        if message is None:
            if self.min_date and self.max_date:
                message = f'Date must be between {self.min_date} and {self.max_date}'
            elif self.min_date:
                message = f'Date must be on or after {self.min_date}'
            elif self.max_date:
                message = f'Date must be on or before {self.max_date}'
            else:
                message = 'Invalid date'

        super().__init__(message)

    def _parse_date(self, date_value: date | str) -> date:
        """Parse a date from string or date object."""
        if isinstance(date_value, date):
            return date_value
        elif isinstance(date_value, str):
            return datetime.strptime(date_value, '%Y-%m-%d').date()
        else:
            raise ValueError(f'Invalid date format: {date_value}')

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        if value is None or value == '':
            return True, ''

        try:
            if isinstance(value, str):
                check_date = datetime.strptime(value, '%Y-%m-%d').date()
            elif isinstance(value, date):
                check_date = value
            else:
                return False, _INVALID_DATE_MSG

            if self.min_date and check_date < self.min_date:
                return False, self.message

            if self.max_date and check_date > self.max_date:
                return False, self.message

            return True, ''
        except ValueError:
            return False, _INVALID_DATE_MSG

    def _generate_js_validation(self, field_name: str) -> str:
        checks = []

        if self.min_date:
            min_str = self.min_date.isoformat()
            checks.append(f"dateValue < new Date('{min_str}')")

        if self.max_date:
            max_str = self.max_date.isoformat()
            checks.append(f"dateValue > new Date('{max_str}')")

        if checks:
            condition = ' || '.join(checks)
            return f"""
            if (value !== '' && value !== null) {{
                const dateValue = new Date(value);
                if (isNaN(dateValue.getTime()) || {condition}) {{
                    return '{_js_str(self.message)}';
                }}
            }}
            """
        return ''

    def _descriptor_params(self) -> dict[str, Any]:
        return {
            'min_date': self.min_date.isoformat() if self.min_date else None,
            'max_date': self.max_date.isoformat() if self.max_date else None,
        }


class CustomRule(ValidationRule):
    """Custom validation using a callback function."""

    rule_name = 'custom'

    def __init__(
        self,
        validator_func: Callable[[Any], bool | tuple[bool, str]],
        message: str = _INVALID_VALUE_MSG,
        client_side: bool = False,
    ):
        self.validator_func = validator_func
        super().__init__(message, client_side)

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        try:
            result = self.validator_func(value)

            if isinstance(result, bool):
                return result, self.message if not result else ''
            elif isinstance(result, tuple) and len(result) == 2:
                return result
            else:
                return False, 'Invalid validation result'
        except Exception as e:
            return False, f'Validation error: {str(e)}'


class FieldValidator:
    """Validator for a single field with multiple rules."""

    def __init__(self, field_name: str, rules: list[ValidationRule] | None = None):
        self.field_name = field_name
        self.rules: list[ValidationRule] = rules or []

    def add_rule(self, rule: ValidationRule) -> 'FieldValidator':
        """Add a validation rule."""
        self.rules.append(rule)
        return self

    def required(self, message: str | None = None) -> 'FieldValidator':
        """Add required validation."""
        return self.add_rule(RequiredRule(message or 'This field is required'))

    def min_length(self, length: int, message: str | None = None) -> 'FieldValidator':
        """Add minimum length validation."""
        return self.add_rule(MinLengthRule(length, message))

    def max_length(self, length: int, message: str | None = None) -> 'FieldValidator':
        """Add maximum length validation."""
        return self.add_rule(MaxLengthRule(length, message))

    def email(self, message: str | None = None) -> 'FieldValidator':
        """Add email validation."""
        return self.add_rule(EmailRule(message or _INVALID_EMAIL_MSG))

    def phone(self, message: str | None = None) -> 'FieldValidator':
        """Add phone validation."""
        return self.add_rule(PhoneRule(message or 'Please enter a valid phone number'))

    def numeric_range(
        self,
        min_val: float | None = None,
        max_val: float | None = None,
        message: str | None = None,
    ) -> 'FieldValidator':
        """Add numeric range validation."""
        return self.add_rule(NumericRangeRule(min_val, max_val, message))

    def date_range(
        self,
        min_date: date | str | None = None,
        max_date: date | str | None = None,
        message: str | None = None,
    ) -> 'FieldValidator':
        """Add date range validation."""
        return self.add_rule(DateRangeRule(min_date, max_date, message))

    def regex(self, pattern: str, message: str | None = None) -> 'FieldValidator':
        """Add regex validation."""
        return self.add_rule(RegexRule(pattern, message or 'Invalid format'))

    def custom(self, validator_func: Callable, message: str | None = None) -> 'FieldValidator':
        """Add custom validation."""
        return self.add_rule(CustomRule(validator_func, message or _INVALID_VALUE_MSG))

    def validate(self, value: Any) -> tuple[bool, list[str]]:
        """
        Validate a value against all rules.

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        for rule in self.rules:
            is_valid, error_message = rule.validate(value, self.field_name)
            if not is_valid:
                errors.append(error_message)

        return len(errors) == 0, errors

    def generate_client_validation(self) -> str:
        """Generate JavaScript validation function for this field."""
        js_validations = []

        for rule in self.rules:
            js_code = rule.get_client_validation(self.field_name)
            if js_code.strip():
                js_validations.append(js_code.strip())

        if not js_validations:
            return ''

        field_name_camel = ''.join(word.capitalize() for word in self.field_name.split('_'))
        validations = '\n    '.join(js_validations)
        return f'\nfunction validate{field_name_camel}(value) {{\n    {validations}\n    return null; // No errors\n}}\n'

    def to_rule_descriptors(self) -> list[dict[str, Any]]:
        """Return serializable descriptors for all rules."""

        return [rule.to_descriptor() for rule in self.rules]

    def to_schema(self) -> dict[str, Any]:
        """Return a schema payload for this field."""

        return {
            'field': self.field_name,
            'rules': self.to_rule_descriptors(),
        }


class ValidationSchema:
    """Aggregate FieldValidator instances into a reusable schema."""

    def __init__(self) -> None:
        self._fields: dict[str, FieldValidator] = {}

    def add_field(self, validator: FieldValidator) -> 'ValidationSchema':
        self._fields[validator.field_name] = validator
        return self

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {name: validator.to_rule_descriptors() for name, validator in self._fields.items()}

    def validators(self) -> list[FieldValidator]:
        return list(self._fields.values())

    def build_live_validator(self) -> Any:  # pragma: no cover - thin wrapper
        """Create a LiveValidator pre-populated with this schema."""

        from .live_validation import LiveValidator

        live_validator = LiveValidator()
        for validator in self.validators():
            live_validator.register_field_validator(validator)
        return live_validator


class FormValidator:
    """Validator for entire forms with multiple fields."""

    def __init__(self):
        self.field_validators: dict[str, FieldValidator] = {}
        self.cross_field_rules: list[Callable[[dict[str, Any]], tuple[bool, dict[str, str]]]] = []

    def field(self, field_name: str) -> FieldValidator:
        """Get or create a field validator."""
        if field_name not in self.field_validators:
            self.field_validators[field_name] = FieldValidator(field_name)
        return self.field_validators[field_name]

    def add_cross_field_rule(
        self, rule: Callable[[dict[str, Any]], tuple[bool, dict[str, str]]]
    ) -> None:
        """Add a cross-field validation rule."""
        self.cross_field_rules.append(rule)

    def validate(self, data: dict[str, Any]) -> tuple[bool, dict[str, list[str]]]:
        """
        Validate form data.

        Returns:
            Tuple of (is_valid, dict_of_field_errors)
        """
        all_errors = {}
        is_form_valid = True

        # Validate individual fields
        for field_name, validator in self.field_validators.items():
            value = data.get(field_name)
            is_valid, errors = validator.validate(value)

            if not is_valid:
                all_errors[field_name] = errors
                is_form_valid = False

        # Validate cross-field rules
        for rule in self.cross_field_rules:
            is_valid, errors = rule(data)
            if not is_valid:
                for field_name, error_message in errors.items():
                    if field_name not in all_errors:
                        all_errors[field_name] = []
                    all_errors[field_name].append(error_message)
                is_form_valid = False

        return is_form_valid, all_errors

    def validate_pydantic_model(
        self, model_class: type, data: dict[str, Any]
    ) -> tuple[bool, dict[str, list[str]]]:
        """
        Validate data against a Pydantic model.

        Returns:
            Tuple of (is_valid, dict_of_field_errors)
        """
        try:
            model_class(**data)
            return True, {}
        except ValidationError as e:
            errors = {}
            for error in e.errors():
                field_name = error['loc'][0] if error['loc'] else 'general'
                error_message = error['msg']

                if field_name not in errors:
                    errors[field_name] = []
                errors[field_name].append(error_message)

            return False, errors

    def generate_client_validation_script(self) -> str:
        """Generate complete JavaScript validation script."""
        field_functions = []
        field_validations = []

        for field_name, validator in self.field_validators.items():
            js_function = validator.generate_client_validation()
            if js_function:
                field_functions.append(js_function)

                # Convert field name to camelCase
                field_name_camel = ''.join(word.capitalize() for word in field_name.split('_'))
                field_validations.append(f"    '{field_name}': validate{field_name_camel}")

        fn_block = '\n\n'.join(field_functions)
        validators_block = ',\n'.join(field_validations)
        # JS/CSS-only content below (rule 4 exception): fn_block/validators_block
        # are built from model field names (developer-controlled identifiers)
        # and validator-generated JS, not user input.
        return SafeHTML(f"""<script>
{fn_block}

const formValidators = {{
{validators_block}
}};

function validateField(fieldName, value) {{
    const validator = formValidators[fieldName];
    if (validator) {{
        return validator(value);
    }}
    return null;
}}

function validateForm(formElement) {{
    let isValid = true;
    const errors = {{}};

    // Clear previous errors
    formElement.querySelectorAll('.error-message').forEach(el => el.remove());
    formElement.querySelectorAll('.error').forEach(el => el.classList.remove('error'));

    // Validate each field
    for (const [fieldName, validator] of Object.entries(formValidators)) {{
        const input = formElement.querySelector(`[name="${{fieldName}}"]`);
        if (input) {{
            const error = validator(input.value);
            if (error) {{
                errors[fieldName] = error;
                isValid = false;

                // Show error in UI
                input.classList.add('error');
                const errorElement = document.createElement('div');
                errorElement.className = 'error-message';
                errorElement.textContent = error;
                input.parentNode.insertBefore(errorElement, input.nextSibling);
            }}
        }}
    }}

    return {{ isValid, errors }};
}}

// Add live validation on input events
document.addEventListener('DOMContentLoaded', function() {{
    document.querySelectorAll('form').forEach(form => {{
        form.addEventListener('input', function(e) {{
            const fieldName = e.target.name;
            if (fieldName && formValidators[fieldName]) {{
                const error = validateField(fieldName, e.target.value);

                // Clear previous error
                const existingError = e.target.parentNode.querySelector('.error-message');
                if (existingError) {{
                    existingError.remove();
                }}
                e.target.classList.remove('error');

                // Show new error if any
                if (error) {{
                    e.target.classList.add('error');
                    const errorElement = document.createElement('div');
                    errorElement.className = 'error-message';
                    errorElement.textContent = error;
                    e.target.parentNode.insertBefore(errorElement, e.target.nextSibling);
                }}
            }}
        }});

        form.addEventListener('submit', function(e) {{
            const validation = validateForm(form);
            if (!validation.isValid) {{
                e.preventDefault();
            }}
        }});
    }});
}});
</script>
<style>
.error {{
    border-color: #dc3545 !important;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
}}
.error-message {{
    color: #dc3545;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}}
</style>""")


# Common cross-field validation rules
class CrossFieldRules:
    """Collection of common cross-field validation rules."""

    @staticmethod
    def password_confirmation(
        password_field: str = 'password',
        confirm_field: str = 'confirm_password',
        message: str = 'Passwords do not match',
    ) -> Callable:
        """Validate that password and confirmation match."""

        def validator(data: dict[str, Any]) -> tuple[bool, dict[str, str]]:
            password = data.get(password_field)
            confirm = data.get(confirm_field)

            if password and confirm and password != confirm:
                return False, {confirm_field: message}

            return True, {}

        return validator

    @staticmethod
    def date_range_validation(
        start_field: str, end_field: str, message: str = 'End date must be after start date'
    ) -> Callable:
        """Validate that end date is after start date."""

        def validator(data: dict[str, Any]) -> tuple[bool, dict[str, str]]:
            start_date = data.get(start_field)
            end_date = data.get(end_field)

            if start_date and end_date:
                try:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

                    if start_date >= end_date:
                        return False, {end_field: message}
                except ValueError:
                    return False, {end_field: _INVALID_DATE_MSG}

            return True, {}

        return validator


# Convenience function for creating validators
def create_validator() -> FormValidator:
    """Create a new form validator."""
    return FormValidator()


# Convenience functions for common validation patterns
def create_email_validator() -> Callable[[str], ValidationResponse]:
    """Create a validator for email fields."""

    def validate_email(value: str) -> ValidationResponse:
        if not value:
            return ValidationResponse(
                field_name='email', is_valid=False, errors=['Email is required'], value=value
            )

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return ValidationResponse(
                field_name='email',
                is_valid=False,
                errors=[_INVALID_EMAIL_MSG],
                suggestions=['Example: user@example.com'],
                value=value,
            )

        return ValidationResponse(
            field_name='email', is_valid=True, value=value, formatted_value=value.lower()
        )

    return validate_email


def create_password_strength_validator(min_length: int = 8) -> Callable[[str], ValidationResponse]:
    """Create a validator for password strength."""

    def validate_password(value: str) -> ValidationResponse:
        errors = []
        warnings = []
        suggestions = []

        if len(value) < min_length:
            errors.append(f'Password must be at least {min_length} characters long')

        if not re.search(r'[A-Z]', value):
            warnings.append('Password should contain at least one uppercase letter')
            suggestions.append('Add an uppercase letter (A-Z)')

        if not re.search(r'[a-z]', value):
            warnings.append('Password should contain at least one lowercase letter')
            suggestions.append('Add a lowercase letter (a-z)')

        if not re.search(r'\d', value):
            warnings.append('Password should contain at least one number')
            suggestions.append('Add a number (0-9)')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            warnings.append('Password should contain at least one special character')
            suggestions.append('Add a special character (!@#$%^&*)')

        is_valid = len(errors) == 0

        return ValidationResponse(
            field_name='password',
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            value=value,
        )

    return validate_password


# Validation result class for integration
class ValidationResult:
    """Result of form validation, with optional render context for re-rendering on error."""

    def __init__(
        self,
        is_valid: bool,
        data: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
        form_model_cls: Any | None = None,
        original_data: dict[str, Any] | None = None,
        submit_url: str | None = None,
        framework: str = 'bootstrap',
        render_kwargs: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.data: dict[str, Any] = data or {}
        self.errors: dict[str, Any] = errors or {}
        self.form_model_cls = form_model_cls
        self.original_data: dict[str, Any] = original_data or {}
        self._submit_url = submit_url
        self._framework = framework
        self._render_kwargs: dict[str, Any] = render_kwargs or {}

    def render_with_errors(
        self,
        framework: str | None = None,
        *,
        submit_url: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the form with validation errors displayed.

        Uses the submit_url and framework stored at validate() time when not
        supplied explicitly, so the common case needs no arguments at all.
        """
        if not self.form_model_cls:
            raise ValueError('Cannot render form: form_model_cls not provided')

        url = submit_url or self._submit_url
        if not url:
            raise ValueError(
                'submit_url is required. Pass it here or via FormModel.validate(submit_url=...).'
            )

        return self.form_model_cls.render_form(
            data=self.original_data,
            errors=self.errors,
            framework=framework or self._framework,
            submit_url=url,
            **{**self._render_kwargs, **kwargs},
        )

    async def render_with_errors_async(
        self,
        framework: str | None = None,
        *,
        submit_url: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Async variant of render_with_errors — runs the sync renderer off the event loop.

        Accepts the same arguments as render_with_errors. Prefer this in async
        frameworks (FastAPI / Starlette) to avoid blocking the event loop.
        """
        import asyncio

        def _render():
            return self.render_with_errors(
                framework,
                submit_url=submit_url,
                **kwargs,
            )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        return await loop.run_in_executor(None, _render)

    def __str__(self) -> str:
        if self.is_valid:
            return f'ValidationResult(valid=True, data={self.data})'
        return f'ValidationResult(valid=False, errors={self.errors})'


def _coerce_html_form_values(data: dict[str, Any], model_fields: dict[str, Any]) -> dict[str, Any]:
    """Recursively repair two HTML-form-submission quirks Pydantic won't:

    1. A blank date/datetime/time/number input submits the empty string, not
       an absent key. Pydantic never coerces "" to None for a type like
       ``date | None``, so an intentionally-blank optional field (e.g. a
       certification with no expiry date) fails validation with a confusing
       "input is too short" error instead of being accepted as absent. Fields
       that accept ``str`` (e.g. ``Optional[str]``) are left untouched, since
       "" is a legitimate value for those.
    2. A ``List[<scalar>]`` field (multiselect, checkbox group) submits a
       bare scalar -- not a single-item list -- when exactly one option is
       selected; only two-or-more selections naturally group into a list.
       Wrap a lone scalar back into a single-item list so it validates the
       same way regardless of how many options were chosen.
    3. A date/time/datetime field rendered with a custom ``date_format``/
       ``time_format``/``datetime_format`` (see ``inputs/datetime_inputs.py``)
       submits a string in that custom shape, not ISO 8601 -- Pydantic's
       native parser only understands ISO. Try ``strptime`` against the
       configured format first; on failure, leave the value untouched so
       Pydantic's own ISO parser still gets a try (keeping JSON/API callers
       that submit plain ISO strings working regardless of what display
       format the HTML form uses).
    """
    result = dict(data)

    for field_name, field_info in model_fields.items():
        if field_name not in result:
            continue

        value = result[field_name]
        annotation = field_info.annotation
        union_args = get_args(annotation) if get_origin(annotation) is Union else ()
        non_none_types = (
            [t for t in union_args if t is not type(None)] if union_args else [annotation]
        )
        is_optional = bool(union_args) and type(None) in union_args

        list_type = next((t for t in non_none_types if get_origin(t) is list), None)
        list_item_type = get_args(list_type)[0] if list_type and get_args(list_type) else None
        list_item_model = (
            list_item_type
            if isinstance(list_item_type, type) and issubclass(list_item_type, BaseModel)
            else None
        )

        if list_type is not None and list_item_model is None:
            if value not in (None, '') and not isinstance(value, list):
                result[field_name] = [value]
            continue

        if isinstance(value, dict):
            for candidate in non_none_types:
                if isinstance(candidate, type) and issubclass(candidate, BaseModel):
                    result[field_name] = _coerce_html_form_values(value, candidate.model_fields)
                    break
            continue

        if isinstance(value, list):
            if list_item_model is not None:
                item_fields = list_item_model.model_fields
                result[field_name] = [
                    _coerce_html_form_values(item, item_fields) if isinstance(item, dict) else item
                    for item in value
                ]
            continue

        if value == '' and is_optional:
            allows_string = any(
                isinstance(candidate, type) and issubclass(candidate, str)
                for candidate in non_none_types
            )
            if not allows_string:
                result[field_name] = None
            continue

        if isinstance(value, str) and value != '':
            # time is NOT a subclass of date (only datetime is) -- must check
            # both roots explicitly, then disambiguate datetime (a date
            # subclass) from plain date below.
            date_type = next(
                (t for t in non_none_types if isinstance(t, type) and issubclass(t, (date, time))),
                None,
            )
            if date_type is not None:
                extra = getattr(field_info, 'json_schema_extra', None) or {}
                ui_options = extra.get('ui_options', {}) if isinstance(extra, dict) else {}
                is_datetime = issubclass(date_type, datetime)
                is_time = issubclass(date_type, time)
                if is_datetime:
                    fmt_key = 'datetime_format'
                elif is_time:
                    fmt_key = 'time_format'
                else:
                    fmt_key = 'date_format'
                # fmt_key must match the *_format kwarg names in
                # inputs/datetime_inputs.py's DateInput/TimeInput/DatetimeInput.
                fmt = ui_options.get(fmt_key) if isinstance(ui_options, dict) else None
                if fmt:
                    try:
                        parsed = datetime.strptime(value, fmt)
                    except ValueError, TypeError:
                        pass  # leave value unchanged -- Pydantic's ISO parser tries next
                    else:
                        if is_datetime:
                            result[field_name] = parsed
                        elif is_time:
                            result[field_name] = parsed.time()
                        else:
                            result[field_name] = parsed.date()

    return result


def validate_form_data(
    form_model_class: type[Any], data: dict[str, Any], *, flatten: bool = False
) -> ValidationResult:
    """
    Validate form data against a Pydantic model.

    Args:
        form_model_class: The Pydantic model class to validate against
        data: Dictionary of form data to validate. If ``flatten`` is True,
            this may use bracket+dot flat keys (e.g. ``"pets[0].name"``);
            already-nested data is also accepted (a no-op passthrough).
        flatten: When True, ``data`` is un-flattened via
            ``parse_nested_form_data`` before validation, and the returned
            ``ValidationResult.data`` uses flat bracket+dot keys instead of
            nested dicts/lists.

    Returns:
        ValidationResult with is_valid, data, and errors

    Note:
        Extra keys in ``data`` that are not declared on the model are silently
        stripped from the validated output. This follows Pydantic's default
        ``extra='ignore'`` behaviour and is intentional for HTML form submissions,
        which may include browser-injected fields (CSRF tokens, honeypots, etc.).
    """
    from .form_data import flatten_nested_data, parse_nested_form_data

    if flatten:
        data = parse_nested_form_data(data, coerce_values=False)

    runtime_model = (
        form_model_class.get_runtime_model()
        if hasattr(form_model_class, 'get_runtime_model')
        else form_model_class
    )

    try:
        # Create instance to validate
        coerced_data = _coerce_html_form_values(
            data, getattr(runtime_model, 'model_fields', {}) or {}
        )
        validated_instance = runtime_model(**coerced_data)

        # Convert to dict for consistent return format
        validated_data = validated_instance.model_dump()

        model_fields = getattr(runtime_model, 'model_fields', {}) or {}
        layout_field_names = []
        for field_name, field_info in model_fields.items():
            extra = getattr(field_info, 'json_schema_extra', None) or {}
            if not isinstance(extra, dict):
                continue
            ui_element = extra.get('ui_element') or extra.get('input_type')
            if ui_element == 'layout':
                layout_field_names.append(field_name)

        if layout_field_names:
            from .rendering.layout_engine import get_nested_form_data

            layout_errors: dict[str, str] = {}

            for layout_field_name in layout_field_names:
                layout_value = getattr(validated_instance, layout_field_name, None)
                nested_layout_data = get_nested_form_data(layout_field_name, data, layout_value)
                if nested_layout_data:
                    is_nested_payload = any(
                        isinstance(value, dict) for value in nested_layout_data.values()
                    )

                    # Validate the nested payload against the layout's underlying FormModel(s)
                    # so constraints like `min_length` and required fields are enforced.
                    nested_result: ValidationResult | None = None

                    validate_method = getattr(layout_value, 'validate', None)
                    if callable(validate_method):
                        try:
                            nested_result = validate_method(nested_layout_data)  # type: ignore[assignment]
                        except Exception:
                            nested_result = None

                    # Fallback: validate each nested form class if available.
                    if nested_result is None and hasattr(layout_value, '_get_forms'):
                        get_forms = getattr(layout_value, '_get_forms', None)
                        if callable(get_forms):
                            combined_data: dict[str, Any] = {}
                            combined_errors: dict[str, str] = {}
                            is_valid = True

                            try:
                                for form_cls in get_forms() or []:  # type: ignore[union-attr]
                                    child = validate_form_data(form_cls, nested_layout_data)
                                    if not child.is_valid:
                                        is_valid = False
                                        combined_errors.update(child.errors)
                                    combined_data.update(child.data)
                            except Exception:
                                # If introspection validation fails, fall back to accepting payload.
                                combined_data = {}
                                combined_errors = {}
                                is_valid = True

                            nested_result = ValidationResult(
                                is_valid=is_valid,
                                data=combined_data or nested_layout_data,
                                errors=combined_errors,
                            )

                    if nested_result is not None:
                        # Preserve the schema-derived nested payload shape (e.g. tabbed layouts)
                        # while still preferring coerced values for flat layouts.
                        validated_data[layout_field_name] = nested_layout_data
                        if not is_nested_payload and nested_result.data:
                            validated_data[layout_field_name] = nested_result.data
                        if not nested_result.is_valid:
                            layout_errors.update(nested_result.errors)
                    else:
                        validated_data[layout_field_name] = nested_layout_data

                    continue

                layout_payload = validated_data.get(layout_field_name)
                if isinstance(layout_payload, dict) and layout_payload.get('layout') is True:
                    validated_data.pop(layout_field_name, None)

            if layout_errors:
                return ValidationResult(
                    is_valid=False,
                    data=flatten_nested_data(validated_data) if flatten else validated_data,
                    errors=layout_errors,
                    form_model_cls=form_model_class,
                    original_data=data,
                )

        return ValidationResult(
            is_valid=True,
            data=flatten_nested_data(validated_data) if flatten else validated_data,
            form_model_cls=form_model_class,
            original_data=data,
        )

    except ValidationError as e:
        errors = {}
        for error in e.errors():
            # Create more specific field paths for nested data
            if error['loc']:
                # Handle nested field locations like ('pets', 0, 'weight')
                field_path_parts = []
                for loc_part in error['loc']:
                    if isinstance(loc_part, int):
                        # This is an array index
                        field_path_parts.append(f'[{loc_part}]')
                    else:
                        if field_path_parts:
                            field_path_parts.append(f'.{loc_part}')
                        else:
                            field_path_parts.append(str(loc_part))

                field_name = ''.join(field_path_parts)

                # Create more user-friendly error messages
                error_message = error['msg']
                error_type = error['type']

                # Enhance error messages with context
                if 'greater_than_equal' in error_type:
                    limit = error.get('ctx', {}).get('ge')
                    if limit is not None:
                        error_message = f'Must be {limit} or greater'
                elif 'less_than_equal' in error_type:
                    limit = error.get('ctx', {}).get('le')
                    if limit is not None:
                        error_message = f'Must be {limit} or less'
                elif 'min_length' in error_type:
                    min_length = error.get('ctx', {}).get('min_length')
                    if min_length is not None:
                        error_message = f'Must be at least {min_length} characters'
                elif 'max_length' in error_type:
                    max_length = error.get('ctx', {}).get('max_length')
                    if max_length is not None:
                        error_message = f'Must be no more than {max_length} characters'

                errors[field_name] = error_message
            else:
                errors['general'] = error['msg']

        return ValidationResult(
            is_valid=False,
            errors=errors,
            form_model_cls=form_model_class,
            original_data=data,
        )

    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors={'general': str(e)},
            form_model_cls=form_model_class,
            original_data=data,
        )


# Export validation rules for easy access
__all__ = [
    'ValidationResponse',
    'ValidationRule',
    'RequiredRule',
    'MinLengthRule',
    'MaxLengthRule',
    'RegexRule',
    'EmailRule',
    'PhoneRule',
    'NumericRangeRule',
    'DateRangeRule',
    'CustomRule',
    'FieldValidator',
    'ValidationSchema',
    'FormValidator',
    'CrossFieldRules',
    'create_validator',
    'create_email_validator',
    'create_password_strength_validator',
    'ValidationResult',
    'validate_form_data',
]
