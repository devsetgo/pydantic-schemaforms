"""
Advanced validation system for pydantic-forms using Python 3.14 template strings.
Provides both client-side JavaScript validation and server-side Python validation.

Requires: Python 3.14+ (no backward compatibility)
"""

import re
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from datetime import datetime, date
import string.templatelib
from pydantic import ValidationError
from html import escape

# Import version check to ensure compatibility


class ValidationRule:
    """Base class for validation rules."""

    def __init__(self, message: str = "Invalid value", client_side: bool = True):
        self.message = message
        self.client_side = client_side

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        """
        Validate a value.

        Returns:
            Tuple of (is_valid, error_message)
        """
        raise NotImplementedError

    def get_client_validation(self, field_name: str) -> str:
        """Generate JavaScript validation code."""
        if not self.client_side:
            return ""
        return self._generate_js_validation(field_name)

    def _generate_js_validation(self, field_name: str) -> str:
        """Override in subclasses to provide JavaScript validation."""
        return ""


class RequiredRule(ValidationRule):
    """Validates that a field has a value."""

    def __init__(self, message: str = "This field is required"):
        super().__init__(message)

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, self.message
        return True, ""

    def _generate_js_validation(self, field_name: str) -> str:
        return f"""
        if (!value || (typeof value === 'string' && !value.trim())) {{
            return '{escape(self.message)}';
        }}
        """


class MinLengthRule(ValidationRule):
    """Validates minimum string length."""

    def __init__(self, min_length: int, message: str = None):
        self.min_length = min_length
        message = message or f"Must be at least {min_length} characters long"
        super().__init__(message)

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        if value is None:
            return True, ""  # Let RequiredRule handle None values

        if len(str(value)) < self.min_length:
            return False, self.message
        return True, ""

    def _generate_js_validation(self, field_name: str) -> str:
        return f"""
        if (value && value.length < {self.min_length}) {{
            return '{escape(self.message)}';
        }}
        """


class MaxLengthRule(ValidationRule):
    """Validates maximum string length."""

    def __init__(self, max_length: int, message: str = None):
        self.max_length = max_length
        message = message or f"Must be no more than {max_length} characters long"
        super().__init__(message)

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        if value is None:
            return True, ""

        if len(str(value)) > self.max_length:
            return False, self.message
        return True, ""

    def _generate_js_validation(self, field_name: str) -> str:
        return f"""
        if (value && value.length > {self.max_length}) {{
            return '{escape(self.message)}';
        }}
        """


class RegexRule(ValidationRule):
    """Validates against a regular expression pattern."""

    def __init__(self, pattern: str, message: str = "Invalid format", flags: int = 0):
        self.pattern = pattern
        self.regex = re.compile(pattern, flags)
        super().__init__(message)

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        if value is None or value == "":
            return True, ""  # Let RequiredRule handle empty values

        if not self.regex.match(str(value)):
            return False, self.message
        return True, ""

    def _generate_js_validation(self, field_name: str) -> str:
        # Escape the regex pattern for JavaScript
        js_pattern = self.pattern.replace("\\", "\\\\").replace("'", "\\'")
        return f"""
        if (value && !new RegExp('{js_pattern}').test(value)) {{
            return '{escape(self.message)}';
        }}
        """


class EmailRule(RegexRule):
    """Validates email addresses."""

    def __init__(self, message: str = "Please enter a valid email address"):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        super().__init__(pattern, message)


class PhoneRule(RegexRule):
    """Validates phone numbers."""

    def __init__(self, message: str = "Please enter a valid phone number"):
        # Accepts various phone formats
        pattern = r"^[\+]?[1-9]?[\d\s\-\(\)\.]{10,15}$"
        super().__init__(pattern, message)


class NumericRangeRule(ValidationRule):
    """Validates numeric values within a range."""

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        message: str = None,
    ):
        self.min_value = min_value
        self.max_value = max_value

        if message is None:
            if min_value is not None and max_value is not None:
                message = f"Must be between {min_value} and {max_value}"
            elif min_value is not None:
                message = f"Must be at least {min_value}"
            elif max_value is not None:
                message = f"Must be no more than {max_value}"
            else:
                message = "Invalid numeric value"

        super().__init__(message)

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        if value is None or value == "":
            return True, ""

        try:
            num_value = float(value)

            if self.min_value is not None and num_value < self.min_value:
                return False, self.message

            if self.max_value is not None and num_value > self.max_value:
                return False, self.message

            return True, ""
        except (ValueError, TypeError):
            return False, "Must be a valid number"

    def _generate_js_validation(self, field_name: str) -> str:
        checks = []

        if self.min_value is not None:
            checks.append(f"numValue < {self.min_value}")

        if self.max_value is not None:
            checks.append(f"numValue > {self.max_value}")

        if checks:
            condition = " || ".join(checks)
            return f"""
            if (value !== '' && value !== null) {{
                const numValue = parseFloat(value);
                if (isNaN(numValue) || {condition}) {{
                    return '{escape(self.message)}';
                }}
            }}
            """
        return ""


class DateRangeRule(ValidationRule):
    """Validates dates within a range."""

    def __init__(
        self,
        min_date: Optional[Union[date, str]] = None,
        max_date: Optional[Union[date, str]] = None,
        message: str = None,
    ):
        self.min_date = self._parse_date(min_date) if min_date else None
        self.max_date = self._parse_date(max_date) if max_date else None

        if message is None:
            if self.min_date and self.max_date:
                message = f"Date must be between {self.min_date} and {self.max_date}"
            elif self.min_date:
                message = f"Date must be on or after {self.min_date}"
            elif self.max_date:
                message = f"Date must be on or before {self.max_date}"
            else:
                message = "Invalid date"

        super().__init__(message)

    def _parse_date(self, date_value: Union[date, str]) -> date:
        """Parse a date from string or date object."""
        if isinstance(date_value, date):
            return date_value
        elif isinstance(date_value, str):
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        else:
            raise ValueError(f"Invalid date format: {date_value}")

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        if value is None or value == "":
            return True, ""

        try:
            if isinstance(value, str):
                check_date = datetime.strptime(value, "%Y-%m-%d").date()
            elif isinstance(value, date):
                check_date = value
            else:
                return False, "Invalid date format"

            if self.min_date and check_date < self.min_date:
                return False, self.message

            if self.max_date and check_date > self.max_date:
                return False, self.message

            return True, ""
        except ValueError:
            return False, "Invalid date format"

    def _generate_js_validation(self, field_name: str) -> str:
        checks = []

        if self.min_date:
            min_str = self.min_date.isoformat()
            checks.append(f"dateValue < new Date('{min_str}')")

        if self.max_date:
            max_str = self.max_date.isoformat()
            checks.append(f"dateValue > new Date('{max_str}')")

        if checks:
            condition = " || ".join(checks)
            return f"""
            if (value !== '' && value !== null) {{
                const dateValue = new Date(value);
                if (isNaN(dateValue.getTime()) || {condition}) {{
                    return '{escape(self.message)}';
                }}
            }}
            """
        return ""


class CustomRule(ValidationRule):
    """Custom validation using a callback function."""

    def __init__(
        self,
        validator_func: Callable[[Any], Union[bool, Tuple[bool, str]]],
        message: str = "Invalid value",
        client_side: bool = False,
    ):
        self.validator_func = validator_func
        super().__init__(message, client_side)

    def validate(self, value: Any, field_name: str = "") -> Tuple[bool, str]:
        try:
            result = self.validator_func(value)

            if isinstance(result, bool):
                return result, self.message if not result else ""
            elif isinstance(result, tuple) and len(result) == 2:
                return result
            else:
                return False, "Invalid validation result"
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class FieldValidator:
    """Validator for a single field with multiple rules."""

    def __init__(self, field_name: str, rules: List[ValidationRule] = None):
        self.field_name = field_name
        self.rules = rules or []

    def add_rule(self, rule: ValidationRule) -> "FieldValidator":
        """Add a validation rule."""
        self.rules.append(rule)
        return self

    def required(self, message: str = None) -> "FieldValidator":
        """Add required validation."""
        return self.add_rule(RequiredRule(message or "This field is required"))

    def min_length(self, length: int, message: str = None) -> "FieldValidator":
        """Add minimum length validation."""
        return self.add_rule(MinLengthRule(length, message))

    def max_length(self, length: int, message: str = None) -> "FieldValidator":
        """Add maximum length validation."""
        return self.add_rule(MaxLengthRule(length, message))

    def email(self, message: str = None) -> "FieldValidator":
        """Add email validation."""
        return self.add_rule(EmailRule(message or "Please enter a valid email address"))

    def phone(self, message: str = None) -> "FieldValidator":
        """Add phone validation."""
        return self.add_rule(PhoneRule(message or "Please enter a valid phone number"))

    def numeric_range(
        self, min_val: float = None, max_val: float = None, message: str = None
    ) -> "FieldValidator":
        """Add numeric range validation."""
        return self.add_rule(NumericRangeRule(min_val, max_val, message))

    def date_range(
        self,
        min_date: Union[date, str] = None,
        max_date: Union[date, str] = None,
        message: str = None,
    ) -> "FieldValidator":
        """Add date range validation."""
        return self.add_rule(DateRangeRule(min_date, max_date, message))

    def regex(self, pattern: str, message: str = None) -> "FieldValidator":
        """Add regex validation."""
        return self.add_rule(RegexRule(pattern, message or "Invalid format"))

    def custom(self, validator_func: Callable, message: str = None) -> "FieldValidator":
        """Add custom validation."""
        return self.add_rule(CustomRule(validator_func, message or "Invalid value"))

    def validate(self, value: Any) -> Tuple[bool, List[str]]:
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
            return ""

        template = string.templatelib.Template(
            """
function validate${field_name_camel}(value) {
    ${validations}
    return null; // No errors
}
        """
        )

        # Convert field name to camelCase for JavaScript function
        field_name_camel = "".join(word.capitalize() for word in self.field_name.split("_"))

        return template.substitute(
            field_name_camel=field_name_camel,
            validations="\n    ".join(js_validations)
        )


class FormValidator:
    """Validator for entire forms with multiple fields."""

    def __init__(self):
        self.field_validators: Dict[str, FieldValidator] = {}
        self.cross_field_rules: List[Callable[[Dict[str, Any]], Tuple[bool, Dict[str, str]]]] = []

    def field(self, field_name: str) -> FieldValidator:
        """Get or create a field validator."""
        if field_name not in self.field_validators:
            self.field_validators[field_name] = FieldValidator(field_name)
        return self.field_validators[field_name]

    def add_cross_field_rule(self, rule: Callable[[Dict[str, Any]], Tuple[bool, Dict[str, str]]]):
        """Add a cross-field validation rule."""
        self.cross_field_rules.append(rule)

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
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
        self, model_class: type, data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, List[str]]]:
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
                field_name = error["loc"][0] if error["loc"] else "general"
                error_message = error["msg"]

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
                field_name_camel = "".join(word.capitalize() for word in field_name.split("_"))
                field_validations.append(f"    '{field_name}': validate{field_name_camel}")

        template = string.templatelib.Template(
            """
<script>
${field_functions}

const formValidators = {
${field_validations}
};

function validateField(fieldName, value) {
    const validator = formValidators[fieldName];
    if (validator) {
        return validator(value);
    }
    return null;
}

function validateForm(formElement) {
    let isValid = true;
    const errors = {};

    // Clear previous errors
    formElement.querySelectorAll('.error-message').forEach(el => el.remove());
    formElement.querySelectorAll('.error').forEach(el => el.classList.remove('error'));

    // Validate each field
    for (const [fieldName, validator] of Object.entries(formValidators)) {
        const input = formElement.querySelector(`[name="${fieldName}"]`);
        if (input) {
            const error = validator(input.value);
            if (error) {
                errors[fieldName] = error;
                isValid = false;

                // Show error in UI
                input.classList.add('error');
                const errorElement = document.createElement('div');
                errorElement.className = 'error-message';
                errorElement.textContent = error;
                input.parentNode.insertBefore(errorElement, input.nextSibling);
            }
        }
    }

    return { isValid, errors };
}

// Add live validation on input events
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('input', function(e) {
            const fieldName = e.target.name;
            if (fieldName && formValidators[fieldName]) {
                const error = validateField(fieldName, e.target.value);

                // Clear previous error
                const existingError = e.target.parentNode.querySelector('.error-message');
                if (existingError) {
                    existingError.remove();
                }
                e.target.classList.remove('error');

                // Show new error if any
                if (error) {
                    e.target.classList.add('error');
                    const errorElement = document.createElement('div');
                    errorElement.className = 'error-message';
                    errorElement.textContent = error;
                    e.target.parentNode.insertBefore(errorElement, e.target.nextSibling);
                }
            }
        });

        form.addEventListener('submit', function(e) {
            const validation = validateForm(form);
            if (!validation.isValid) {
                e.preventDefault();
            }
        });
    });
});
</script>
<style>
.error {
    border-color: #dc3545 !important;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
}
.error-message {
    color: #dc3545;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}
</style>
        """
        )

        return template.substitute(
            field_functions="\n\n".join(field_functions),
            field_validations=",\n".join(field_validations),
        )


# Common cross-field validation rules
class CrossFieldRules:
    """Collection of common cross-field validation rules."""

    @staticmethod
    def password_confirmation(
        password_field: str = "password",
        confirm_field: str = "confirm_password",
        message: str = "Passwords do not match",
    ) -> Callable:
        """Validate that password and confirmation match."""

        def validator(data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
            password = data.get(password_field)
            confirm = data.get(confirm_field)

            if password and confirm and password != confirm:
                return False, {confirm_field: message}

            return True, {}

        return validator

    @staticmethod
    def date_range_validation(
        start_field: str, end_field: str, message: str = "End date must be after start date"
    ) -> Callable:
        """Validate that end date is after start date."""

        def validator(data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
            start_date = data.get(start_field)
            end_date = data.get(end_field)

            if start_date and end_date:
                try:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

                    if start_date >= end_date:
                        return False, {end_field: message}
                except ValueError:
                    return False, {end_field: "Invalid date format"}

            return True, {}

        return validator


# Convenience function for creating validators
def create_validator() -> FormValidator:
    """Create a new form validator."""
    return FormValidator()


# Validation result class for integration
class ValidationResult:
    """Result of form validation."""

    def __init__(self, is_valid: bool, data: Dict[str, Any] = None, errors: Dict[str, str] = None):
        self.is_valid = is_valid
        self.data = data or {}
        self.errors = errors or {}


def validate_form_data(form_model_class: type, data: Dict[str, Any]) -> ValidationResult:
    """
    Validate form data against a Pydantic model.

    Args:
        form_model_class: The Pydantic model class to validate against
        data: Dictionary of form data to validate

    Returns:
        ValidationResult with is_valid, data, and errors
    """
    try:
        # Create instance to validate
        validated_instance = form_model_class(**data)

        # Convert to dict for consistent return format
        validated_data = validated_instance.model_dump()

        return ValidationResult(is_valid=True, data=validated_data)

    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field_name = error["loc"][0] if error["loc"] else "general"
            error_message = error["msg"]
            errors[field_name] = error_message

        return ValidationResult(is_valid=False, errors=errors)

    except Exception as e:
        # Handle unexpected errors
        return ValidationResult(is_valid=False, errors={"general": str(e)})


# Export validation rules for easy access
__all__ = [
    "ValidationRule",
    "RequiredRule",
    "MinLengthRule",
    "MaxLengthRule",
    "RegexRule",
    "EmailRule",
    "PhoneRule",
    "NumericRangeRule",
    "DateRangeRule",
    "CustomRule",
    "FieldValidator",
    "FormValidator",
    "CrossFieldRules",
    "create_validator",
    "ValidationResult",
    "validate_form_data",
]
