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
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Union, get_args, get_origin
from collections.abc import Callable

from pydantic import AfterValidator, BaseModel, EmailStr, ValidationError
from pydantic_core import PydanticCustomError, PydanticUndefined, to_jsonable_python

from .tstring import SafeHTML

# Import version check to ensure compatibility


_INVALID_VALUE_MSG = 'Invalid value'
_INVALID_EMAIL_MSG = 'Please enter a valid email address'
_INVALID_EMAIL_DNS_MSG = "This email domain doesn't appear to accept mail"
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
        if value is None or value == '':
            return True, ''  # Let RequiredRule handle missing values, as the JS check does

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


class EmailDeliverabilityRule(ValidationRule):
    """Checks that an email's domain has valid DNS/MX records.

    Unlike ``EmailRule`` (a pure regex format check), this performs a real
    DNS lookup via the optional ``email-validator`` package, so it catches
    typo'd or non-existent domains (``user@gmial.com``) and domains with no
    mail server at all. Requires network access and is therefore always
    ``client_side=False`` — there is no way to run a DNS/MX lookup from
    browser JavaScript, so this only ever runs server-side (e.g. behind a
    ``LiveValidator`` HTMX endpoint for point-of-typing feedback, or in a
    form-submit handler).

    Unless a fixed ``message`` is supplied, the error returned by
    ``validate()`` is ``email-validator``'s own specific reason for the
    failure (e.g. "The domain name X does not exist.", "The domain name X
    does not accept email.", or "...is a special-use or reserved name...")
    rather than one generic string — so the caller can tell a typo'd/missing
    domain apart from a reserved TLD apart from a domain with no MX record.

    Install the dependency with ``pip install pydantic-schemaforms[email]``
    (``[email-dns]`` is an alias for the same package; or plain
    ``pip install email-validator``). Note this is the same package Pydantic's
    own ``EmailStr`` needs just to *define* a field, DNS check or not — see
    ``DeliverableEmailStr`` below.
    """

    rule_name = 'email_deliverability'

    def __init__(self, message: str | None = None, timeout: int | None = None):
        super().__init__(message or _INVALID_EMAIL_DNS_MSG, client_side=False)
        self._explicit_message = message is not None
        self.timeout = timeout

    def validate(self, value: Any, field_name: str = '') -> tuple[bool, str]:
        if value is None or value == '':
            return True, ''  # Let RequiredRule handle empty values

        try:
            from email_validator import EmailNotValidError, validate_email
        except ImportError as e:
            raise ImportError(
                'DNS/MX email deliverability checks require the "email-validator" package. '
                'Install it with `pip install pydantic-schemaforms[email]` '
                '(`[email-dns]` is an alias for the same package) '
                'or `pip install email-validator`.'
            ) from e

        try:
            validate_email(str(value), check_deliverability=True, timeout=self.timeout)
        except EmailNotValidError as e:
            # A caller-supplied message is fixed and always wins; otherwise
            # surface email-validator's own specific reason (bad TLD vs. no
            # DNS record vs. no MX record all say something different).
            return False, self.message if self._explicit_message else str(e)

        return True, ''

    def _descriptor_params(self) -> dict[str, Any]:
        return {'timeout': self.timeout}


def _check_email_deliverability(value: str) -> str:
    """AfterValidator backing DeliverableEmailStr."""
    is_valid, error = EmailDeliverabilityRule().validate(value)
    if not is_valid:
        # PydanticCustomError (rather than a plain ValueError) keeps the
        # message exactly what EmailDeliverabilityRule/email-validator said --
        # a bare ValueError gets a "Value error, " prefix stitched on by
        # Pydantic, which is noise a form field's error text doesn't want.
        raise PydanticCustomError('email_not_deliverable', '{error}', {'error': error})
    return value


DeliverableEmailStr = Annotated[EmailStr, AfterValidator(_check_email_deliverability)]
"""An ``EmailStr`` that also runs a real DNS/MX lookup as an ordinary part of
Pydantic validation -- no ``FieldValidator``/``EmailDeliverabilityRule``
wiring required in your own code:

    class SignupForm(FormModel):
        email: DeliverableEmailStr = Field(..., title="Email")

That one line is enough for ``FormModel.validate()``, ``as_api_model()``, and
``LiveValidator.register_model_validator()`` (see live_validation.py) to all
enforce and live-check the same DNS/MX rule, since it's now part of the
field's own type rather than a separate validator you have to register by
hand. Needs the optional ``email-validator`` package (``pip install
pydantic-schemaforms[email]``) -- note plain ``EmailStr`` already needs this
same package just to *define* a field, DNS check or not, so most apps with
any email field need it regardless of whether they use this type; reach for
``EmailDeliverabilityRule`` directly instead of this type if you need a
custom ``timeout`` or a fixed error message.
"""


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

    def email(
        self,
        message: str | None = None,
        *,
        check_deliverability: bool = False,
        dns_timeout: int | None = None,
    ) -> 'FieldValidator':
        """Add email validation.

        Args:
            message: Custom message for the format check.
            check_deliverability: Also verify the domain has valid DNS/MX
                records (a real DNS lookup — requires the optional
                ``email-validator`` package, see ``EmailDeliverabilityRule``).
            dns_timeout: DNS lookup timeout in seconds, used only when
                check_deliverability is True.
        """
        self.add_rule(EmailRule(message or _INVALID_EMAIL_MSG))
        if check_deliverability:
            self.email_deliverability(dns_timeout=dns_timeout)
        return self

    def email_deliverability(
        self, message: str | None = None, dns_timeout: int | None = None
    ) -> 'FieldValidator':
        """Add a DNS/MX deliverability check (server-side only, real DNS lookup)."""
        return self.add_rule(EmailDeliverabilityRule(message, timeout=dns_timeout))

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
def create_email_validator(
    *, check_deliverability: bool = False, dns_timeout: int | None = None
) -> Callable[[str], ValidationResponse]:
    """Create a validator for email fields.

    Args:
        check_deliverability: Also verify the domain has valid DNS/MX
            records (a real DNS lookup — requires the optional
            ``email-validator`` package; see ``EmailDeliverabilityRule``).
        dns_timeout: DNS lookup timeout in seconds, used only when
            check_deliverability is True.
    """

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

        if check_deliverability:
            is_valid, error = EmailDeliverabilityRule(timeout=dns_timeout).validate(value)
            if not is_valid:
                return ValidationResponse(
                    field_name='email', is_valid=False, errors=[error], value=value
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
        errors: dict[Any, Any] | None = None,
        form_model_cls: Any | None = None,
        original_data: dict[str, Any] | None = None,
        submit_url: str | None = None,
        framework: str = 'bootstrap',
        render_kwargs: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.data: dict[str, Any] = data or {}
        self.errors: dict[Any, Any] = errors or {}
        self.form_model_cls = form_model_cls
        self.original_data: dict[str, Any] = original_data or {}
        self._submit_url = submit_url
        self._framework = framework
        self._render_kwargs: dict[str, Any] = render_kwargs or {}
        self.instance: Any | None = None

    def error_list(self) -> list[dict[str, Any]]:
        """Flat ``[{"loc": [...], "msg": ...}]`` view of ``errors`` (summaries, HTMX, APIs)."""
        from .error_tree import error_list

        return error_list(self.errors)

    def render_with_errors(
        self,
        framework: str | None = None,
        *,
        submit_url: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Render the form with validation errors displayed.

        Pass ``errors=`` to show a different tree, e.g. this result's errors
        merged with a rule-based ``FormValidator``'s.

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
            errors=kwargs.pop('errors', self.errors),
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


_CHECKBOX_ELEMENTS = {None, 'checkbox', 'toggle', 'toggle_switch', 'checkbox_toggle'}
_CURRENCY_ELEMENTS = {'currency', 'money'}


def _ui_element(field_info: Any) -> str | None:
    extra = getattr(field_info, 'json_schema_extra', None)
    return extra.get('ui_element') if isinstance(extra, dict) else None


def _renders_as_checkbox(field_info: Any) -> bool:
    return _ui_element(field_info) in _CHECKBOX_ELEMENTS


def _left_blank(data: dict[str, Any], model: type[BaseModel]) -> bool:
    for key, value in data.items():
        info = model.model_fields.get(key)
        if info is None or value in ('', None, []):
            continue
        if isinstance(value, dict):
            sub_model = next(
                (
                    t
                    for t in (get_args(info.annotation) or (info.annotation,))
                    if isinstance(t, type) and issubclass(t, BaseModel)
                ),
                None,
            )
            if sub_model is None or not _left_blank(value, sub_model):
                return False
            continue
        default = info.default
        if isinstance(default, bool):
            if default:  # a ticked checkbox that starts ticked
                continue
            return False
        if default is PydanticUndefined or isinstance(value, list):
            return False
        if str(to_jsonable_python(default)) != str(value):
            return False
    return True


def _coerce_html_form_values(
    data: dict[str, Any], model_fields: dict[str, Any], *, from_form: bool = False
) -> dict[str, Any]:
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
    4. (``from_form`` only) A repeating sub-form whose items were all removed
       submits no inputs at all, so the field falls back to its default and
       Pydantic, which never validates defaults, skips ``min_length``. An
       absent ``list[Model]`` field is submitted as ``[]`` instead.
    5. (``from_form`` only) An unticked checkbox submits nothing, so a ``bool``
       field defaulting to ``True`` could never be unticked. An absent
       checkbox-rendered ``bool`` with a default is submitted as ``False``
       instead; one without a default must be ticked, so it stays missing.
    6. (``from_form`` only) An optional sub-form (``Address | None``) is
       always rendered, so it is always submitted. When every one of its
       inputs is blank or still at its default, it was left empty: ``None``.
    7. (``from_form`` only) A ``currency`` input shows ``$1,234.50`` as it is
       typed. For a numeric field (``Decimal``, ``float``, ``int``) the
       symbol and thousands separators are stripped so it parses.
    """
    result = dict(data)

    for field_name, field_info in model_fields.items():
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

        if field_name not in result:
            if from_form and list_item_model is not None:
                result[field_name] = []
            elif (
                from_form
                and non_none_types == [bool]
                and not field_info.is_required()
                and _renders_as_checkbox(field_info)
            ):
                result[field_name] = False
            continue

        value = result[field_name]

        if list_type is not None and list_item_model is None:
            if value not in (None, '') and not isinstance(value, list):
                result[field_name] = [value]
            continue

        if isinstance(value, dict):
            for candidate in non_none_types:
                if isinstance(candidate, type) and issubclass(candidate, BaseModel):
                    if from_form and is_optional and _left_blank(value, candidate):
                        result[field_name] = None
                        break
                    result[field_name] = _coerce_html_form_values(
                        value, candidate.model_fields, from_form=from_form
                    )
                    break
            continue

        if isinstance(value, list):
            if list_item_model is not None:
                item_fields = list_item_model.model_fields
                result[field_name] = [
                    _coerce_html_form_values(item, item_fields, from_form=from_form)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            continue

        if value == '' and is_optional:
            # A str-based Enum can't hold "", so it gets None like any other type.
            allows_string = any(
                isinstance(candidate, type)
                and issubclass(candidate, str)
                and not issubclass(candidate, Enum)
                for candidate in non_none_types
            )
            if not allows_string:
                result[field_name] = None
            continue

        if (
            from_form
            and isinstance(value, str)
            and _ui_element(field_info) in _CURRENCY_ELEMENTS
            and any(
                isinstance(t, type) and issubclass(t, (Decimal, float, int)) and t is not bool
                for t in non_none_types
            )
        ):
            value = result[field_name] = re.sub(r'[^\d.\-]', '', value)

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


def validate_form_data(form_model_class: type[Any], data: Any) -> ValidationResult:
    """Validate a submission against a form model.

    Args:
        form_model_class: The FormModel (or plain Pydantic model) to validate against.
        data: The raw request form (Starlette ``FormData``, Werkzeug
            ``MultiDict``, a list of ``(key, value)`` pairs) or an already
            nested dict. See ``form_data.decode_submission``.

    Returns:
        A ``ValidationResult`` whose ``data`` is nested JSON mirroring the
        model and whose ``errors`` is a nested error tree (see ``error_tree``).

    Note:
        Keys not declared on the model (CSRF tokens, honeypots, ...) are
        dropped from ``result.data``, following Pydantic's default
        ``extra='ignore'``.
    """
    from .error_tree import build_error_tree
    from .form_data import decode_submission, is_form_submission

    nested = decode_submission(data)
    runtime_model = (
        form_model_class.get_runtime_model()
        if hasattr(form_model_class, 'get_runtime_model')
        else form_model_class
    )

    coerced = _coerce_html_form_values(
        nested,
        getattr(runtime_model, 'model_fields', {}) or {},
        from_form=is_form_submission(data),
    )
    try:
        instance = runtime_model(**coerced)
    except ValidationError as exc:
        return ValidationResult(
            is_valid=False,
            errors=build_error_tree(exc.errors()),
            form_model_cls=form_model_class,
            original_data=nested,
        )

    result = ValidationResult(
        is_valid=True,
        data=instance.model_dump(),
        form_model_cls=form_model_class,
        original_data=nested,
    )
    result.instance = instance
    return result


# Export validation rules for easy access
__all__ = [
    'ValidationResponse',
    'ValidationRule',
    'RequiredRule',
    'MinLengthRule',
    'MaxLengthRule',
    'RegexRule',
    'EmailRule',
    'EmailDeliverabilityRule',
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
