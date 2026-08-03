"""
Consolidated validation tests.

Merged from:
  - test_validation_rules.py        (55 tests — base)
  - test_validation_coverage.py     (39 tests)
  - test_validation_extended.py     (31 tests)
  - test_validation_consolidation.py (10 tests)
  - test_validation_schema.py
"""

from __future__ import annotations

import json
from datetime import date, datetime, time
from typing import Optional
from unittest.mock import patch

import pytest
from pydantic import Field, model_validator

from pydantic_schemaforms.form_field import FormField
from pydantic_schemaforms.form_layouts import TabbedLayout, VerticalLayout
from pydantic_schemaforms.live_validation import LiveValidator
from pydantic_schemaforms.live_validation import ValidationResponse as LiveValidationResponse
from pydantic_schemaforms.schema_form import FormModel
from pydantic_schemaforms.validation import (
    CrossFieldRules,
    CustomRule,
    DateRangeRule,
    EmailDeliverabilityRule,
    EmailRule,
    FieldValidator,
    FormValidator,
    MaxLengthRule,
    MinLengthRule,
    NumericRangeRule,
    PhoneRule,
    RegexRule,
    RequiredRule,
    ValidationResponse,
    ValidationResult,
    ValidationRule,
    ValidationSchema,
    create_email_validator,
    create_password_strength_validator,
    validate_form_data,
)


# ---------------------------------------------------------------------------
# ValidationResponse
# (merged from test_validation_rules.py and test_validation_coverage.py)
# ---------------------------------------------------------------------------


class TestValidationResponse:
    """Test ValidationResponse dataclass."""

    # --- from test_validation_rules.py ---

    def test_basic_response(self):
        """Test basic validation response creation."""
        response = ValidationResponse(
            field_name='email',
            is_valid=True,
            value='test@example.com',
        )
        assert response.field_name == 'email'
        assert response.is_valid is True
        assert response.errors == []
        assert response.warnings == []

    def test_response_with_errors(self):
        """Test validation response with errors."""
        response = ValidationResponse(
            field_name='password',
            is_valid=False,
            errors=['Too short', 'Must contain uppercase'],
            warnings=['Consider using symbols'],
            value='weak',
        )
        assert response.is_valid is False
        assert len(response.errors) == 2
        assert len(response.warnings) == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        response = ValidationResponse(
            field_name='username',
            is_valid=True,
            value='johndoe',
            formatted_value='John Doe',
        )
        result = response.to_dict()
        assert isinstance(result, dict)
        assert result['field_name'] == 'username'
        assert result['is_valid'] is True
        assert result['formatted_value'] == 'John Doe'

    def test_to_json(self):
        """Test JSON serialization."""
        response = ValidationResponse(
            field_name='age',
            is_valid=False,
            errors=['Must be 18 or older'],
            value=15,
        )
        json_str = response.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed['field_name'] == 'age'
        assert parsed['is_valid'] is False
        assert 'Must be 18 or older' in parsed['errors']

    # --- from test_validation_coverage.py ---

    def test_validation_response_valid(self):
        """Test ValidationResponse for valid field."""
        response = ValidationResponse(
            field_name='email',
            is_valid=True,
            value='user@example.com',
        )
        assert response.field_name == 'email'
        assert response.is_valid is True
        assert response.value == 'user@example.com'

    def test_validation_response_with_errors(self):
        """Test ValidationResponse with errors."""
        response = ValidationResponse(
            field_name='age',
            is_valid=False,
            errors=['Must be a number', 'Must be at least 18'],
        )
        assert not response.is_valid
        assert len(response.errors) == 2

    def test_validation_response_to_dict(self):
        """Test ValidationResponse.to_dict()."""
        response = ValidationResponse(
            field_name='name',
            is_valid=True,
            value='John',
            warnings=['Name contains special characters'],
        )
        data = response.to_dict()
        assert data['field_name'] == 'name'
        assert data['is_valid'] is True
        assert data['value'] == 'John'
        assert len(data['warnings']) == 1

    def test_validation_response_to_json(self):
        """Test ValidationResponse.to_json()."""
        response = ValidationResponse(
            field_name='email',
            is_valid=False,
            errors=['Invalid format'],
        )
        json_str = response.to_json()
        data = json.loads(json_str)
        assert data['field_name'] == 'email'
        assert not data['is_valid']
        assert 'Invalid format' in data['errors']

    def test_validation_response_with_suggestions(self):
        """Test ValidationResponse with suggestions."""
        response = ValidationResponse(
            field_name='zip',
            is_valid=False,
            errors=['Invalid ZIP code'],
            suggestions=['Did you mean 12345?', 'Did you mean 54321?'],
        )
        assert len(response.suggestions) == 2


# ---------------------------------------------------------------------------
# ValidationRule (base class)
# ---------------------------------------------------------------------------


class TestValidationRule:
    """Test base ValidationRule class."""

    def test_base_rule_not_implemented(self):
        """Test that base rule validate raises NotImplementedError."""
        rule = ValidationRule(message='Test message')
        with pytest.raises(NotImplementedError):
            rule.validate('value')

    def test_rule_client_side_flag(self):
        """Test client_side flag."""
        rule = ValidationRule(client_side=False)
        assert rule.client_side is False
        assert rule.get_client_validation('field') == ''

    def test_to_descriptor(self):
        """Test rule descriptor generation."""
        rule = ValidationRule(message='Custom message', client_side=True)
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'base'
        assert descriptor['message'] == 'Custom message'
        assert descriptor['client'] is True


# ---------------------------------------------------------------------------
# RequiredRule
# ---------------------------------------------------------------------------


class TestRequiredRule:
    """Test RequiredRule validation."""

    def test_required_valid(self):
        """Test required rule with valid value."""
        rule = RequiredRule()
        is_valid, message = rule.validate('has value')
        assert is_valid is True
        assert message == ''

    def test_required_invalid_none(self):
        """Test required rule with None."""
        rule = RequiredRule(message='Custom required message')
        is_valid, message = rule.validate(None)
        assert is_valid is False
        assert message == 'Custom required message'

    def test_required_invalid_empty_string(self):
        """Test required rule with empty string."""
        rule = RequiredRule()
        is_valid, message = rule.validate('')
        assert is_valid is False

    def test_required_invalid_whitespace(self):
        """Test required rule with whitespace only."""
        rule = RequiredRule()
        is_valid, message = rule.validate('   ')
        assert is_valid is False

    def test_client_validation(self):
        """Test JavaScript generation for required rule."""
        rule = RequiredRule()
        js_code = rule.get_client_validation('username')
        assert len(js_code) > 0
        assert 'required' in js_code.lower() or 'value' in js_code.lower()

    def test_descriptor(self):
        """Test required rule descriptor."""
        rule = RequiredRule(message='Field required')
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'required'
        assert descriptor['message'] == 'Field required'


# ---------------------------------------------------------------------------
# MinLengthRule
# ---------------------------------------------------------------------------


class TestMinLengthRule:
    """Test MinLengthRule validation."""

    def test_min_length_valid(self):
        """Test minimum length validation - valid."""
        rule = MinLengthRule(min_length=3)
        is_valid, _ = rule.validate('abcd')
        assert is_valid is True

    def test_min_length_invalid(self):
        """Test minimum length validation - invalid."""
        rule = MinLengthRule(min_length=5, message='Too short')
        is_valid, message = rule.validate('abc')
        assert is_valid is False
        assert 'Too short' in message

    def test_min_length_exact(self):
        """Test exact minimum length."""
        rule = MinLengthRule(min_length=5)
        assert rule.validate('exact')[0] is True
        assert rule.validate('tiny')[0] is False

    def test_descriptor(self):
        """Test min length rule descriptor."""
        rule = MinLengthRule(min_length=3)
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'min_length'
        assert descriptor['min_length'] == 3


# ---------------------------------------------------------------------------
# MaxLengthRule
# ---------------------------------------------------------------------------


class TestMaxLengthRule:
    """Test MaxLengthRule validation."""

    def test_max_length_valid(self):
        """Test maximum length validation - valid."""
        rule = MaxLengthRule(max_length=10)
        is_valid, _ = rule.validate('short')
        assert is_valid is True

    def test_max_length_invalid(self):
        """Test maximum length validation - invalid."""
        rule = MaxLengthRule(max_length=5)
        is_valid, message = rule.validate('toolongtext')
        assert is_valid is False
        assert '5' in message

    def test_max_length_exact(self):
        """Test exact maximum length."""
        rule = MaxLengthRule(max_length=5)
        assert rule.validate('exact')[0] is True
        assert rule.validate('toolong')[0] is False

    def test_descriptor(self):
        """Test max length rule descriptor."""
        rule = MaxLengthRule(max_length=50)
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'max_length'
        assert descriptor['max_length'] == 50


# ---------------------------------------------------------------------------
# RegexRule
# ---------------------------------------------------------------------------


class TestRegexRule:
    """Test RegexRule validation."""

    def test_pattern_valid(self):
        """Test pattern validation - valid."""
        rule = RegexRule(pattern=r'^\d{3}-\d{4}$', message='Invalid format')
        is_valid, _ = rule.validate('123-4567')
        assert is_valid is True

    def test_pattern_invalid(self):
        """Test pattern validation - invalid."""
        rule = RegexRule(pattern=r'^[A-Z]+$')
        is_valid, message = rule.validate('abc123')
        assert is_valid is False

    def test_pattern_email_like(self):
        """Test email-like pattern."""
        rule = RegexRule(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
        assert rule.validate('test@example.com')[0] is True
        assert rule.validate('invalid-email')[0] is False

    def test_descriptor(self):
        """Test regex rule descriptor."""
        rule = RegexRule(pattern=r'^[A-Z0-9]+$')
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'regex'
        assert 'pattern' in descriptor


# ---------------------------------------------------------------------------
# NumericRangeRule
# ---------------------------------------------------------------------------


class TestNumericRangeRule:
    """Test NumericRangeRule validation."""

    def test_min_value_valid(self):
        """Test minimum value validation - valid."""
        rule = NumericRangeRule(min_value=0)
        assert rule.validate(5)[0] is True
        assert rule.validate(0)[0] is True

    def test_min_value_invalid(self):
        """Test minimum value validation - invalid."""
        rule = NumericRangeRule(min_value=10)
        is_valid, message = rule.validate(5)
        assert is_valid is False
        assert '10' in message

    def test_max_value_valid(self):
        """Test maximum value validation - valid."""
        rule = NumericRangeRule(max_value=100)
        assert rule.validate(50)[0] is True
        assert rule.validate(100)[0] is True

    def test_max_value_invalid(self):
        """Test maximum value validation - invalid."""
        rule = NumericRangeRule(max_value=10)
        is_valid, message = rule.validate(15)
        assert is_valid is False

    def test_range_valid(self):
        """Test full range validation."""
        rule = NumericRangeRule(min_value=1, max_value=100)
        assert rule.validate(50)[0] is True
        assert rule.validate(1)[0] is True
        assert rule.validate(100)[0] is True

    def test_range_invalid(self):
        """Test full range - outside bounds."""
        rule = NumericRangeRule(min_value=10, max_value=20)
        assert rule.validate(5)[0] is False
        assert rule.validate(25)[0] is False

    def test_non_numeric_value(self):
        """Test with non-numeric value."""
        rule = NumericRangeRule(min_value=0)
        is_valid, message = rule.validate('not a number')
        assert is_valid is False

    def test_client_validation(self):
        """Test JavaScript generation for numeric range rule."""
        rule = NumericRangeRule(min_value=1, max_value=10)
        js_code = rule.get_client_validation('age')
        assert len(js_code) > 0

    def test_descriptor(self):
        """Test numeric range rule descriptor."""
        rule = NumericRangeRule(min_value=0, max_value=999)
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'numeric_range'
        assert descriptor['min'] == 0
        assert descriptor['max'] == 999


# ---------------------------------------------------------------------------
# PhoneRule
# (merged from test_validation_rules.py and test_validation_extended.py)
# Renamed extended class to TestPhoneRuleExtended to avoid collision.
# ---------------------------------------------------------------------------


class TestPhoneRule:
    """Test PhoneRule validation (from test_validation_rules.py)."""

    def test_valid_phone_numbers(self):
        """Test valid phone numbers."""
        rule = PhoneRule()
        valid_phones = [
            '+1-555-123-4567',
            '(555) 123-4567',
            '555-123-4567',
        ]
        for phone in valid_phones:
            rule.validate(phone)

    def test_descriptor(self):
        """Test phone rule descriptor."""
        rule = PhoneRule(message='Invalid phone format')
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'phone'


class TestPhoneRuleExtended:
    """Extended PhoneRule tests (from test_validation_extended.py)."""

    def test_phone_rule_valid_us_format(self):
        """Test PhoneRule with standard US format."""
        rule = PhoneRule()
        is_valid, msg = rule.validate('555-123-4567')
        assert is_valid is True

    def test_phone_rule_valid_with_plus(self):
        """Test PhoneRule with international prefix."""
        rule = PhoneRule()
        is_valid, msg = rule.validate('+1 (555) 123-4567')
        assert is_valid is True

    def test_phone_rule_valid_digits_only(self):
        """Test PhoneRule with digits only."""
        rule = PhoneRule()
        is_valid, msg = rule.validate('5551234567')
        assert is_valid is True

    def test_phone_rule_invalid_too_short(self):
        """Test PhoneRule with too short number."""
        rule = PhoneRule()
        is_valid, msg = rule.validate('123')
        assert is_valid is False

    def test_phone_rule_invalid_format(self):
        """Test PhoneRule with invalid format."""
        rule = PhoneRule()
        is_valid, msg = rule.validate('not-a-phone')
        assert is_valid is False

    def test_phone_rule_descriptor(self):
        """Test PhoneRule descriptor."""
        rule = PhoneRule()
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'phone'


# ---------------------------------------------------------------------------
# EmailRule
# ---------------------------------------------------------------------------


class TestEmailRule:
    """Test EmailRule validation."""

    def test_valid_emails(self):
        """Test valid email addresses."""
        rule = EmailRule()
        valid_emails = [
            'test@example.com',
            'user+tag@domain.co.uk',
            'first.last@subdomain.example.com',
        ]
        for email in valid_emails:
            is_valid, _ = rule.validate(email)
            assert is_valid is True, f'Email {email} should be valid'

    def test_invalid_emails(self):
        """Test invalid email addresses."""
        rule = EmailRule()
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
        ]
        for email in invalid_emails:
            is_valid, _ = rule.validate(email)
            assert is_valid is False, f'Email {email} should be invalid'

    def test_descriptor(self):
        """Test email rule descriptor."""
        rule = EmailRule(message='Invalid email format')
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'email'
        assert descriptor['message'] == 'Invalid email format'


class TestEmailDeliverabilityRule:
    """Test EmailDeliverabilityRule (DNS/MX check). Mocks email_validator so
    the suite never makes real network calls."""

    def test_client_side_always_false(self):
        """DNS lookups can't run in browser JS — must never emit client validation."""
        rule = EmailDeliverabilityRule()
        assert rule.client_side is False
        assert rule.get_client_validation('email') == ''

    def test_empty_value_is_valid(self):
        """Emptiness is RequiredRule's job, not this rule's."""
        rule = EmailDeliverabilityRule()
        is_valid, _ = rule.validate('')
        assert is_valid is True

    def test_valid_domain(self):
        """A domain with valid MX records passes."""
        rule = EmailDeliverabilityRule()
        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.return_value = object()
            is_valid, error = rule.validate('user@example.com')
        assert is_valid is True
        assert error == ''
        mock_validate.assert_called_once()
        _, kwargs = mock_validate.call_args
        assert kwargs['check_deliverability'] is True

    def test_domain_with_no_mx_records(self):
        """A syntactically valid address whose domain can't receive mail fails
        with email-validator's own specific reason, not a generic message —
        so a caller can tell "no such domain" apart from "no MX record"."""
        from email_validator import EmailNotValidError

        rule = EmailDeliverabilityRule()
        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.side_effect = EmailNotValidError('The domain name does not exist.')
            is_valid, error = rule.validate('user@this-domain-does-not-exist-xyz.invalid')
        assert is_valid is False
        assert error == 'The domain name does not exist.'

    def test_different_failure_reasons_surface_distinct_messages(self):
        """Different underlying DNS/MX/TLD failures should produce different
        error text, not a single one-size-fits-all message."""
        from email_validator import EmailNotValidError

        rule = EmailDeliverabilityRule()
        reasons = [
            'The domain name example.zzz does not exist.',
            'The domain name example.com does not accept email.',
            'The part after the @-sign is a special-use or reserved name that cannot be used with email.',
        ]
        seen_errors = set()
        for reason in reasons:
            with patch('email_validator.validate_email') as mock_validate:
                mock_validate.side_effect = EmailNotValidError(reason)
                is_valid, error = rule.validate('user@example.zzz')
            assert is_valid is False
            assert error == reason
            seen_errors.add(error)
        assert len(seen_errors) == len(reasons)

    def test_custom_message_used_on_failure(self):
        from email_validator import EmailNotValidError

        rule = EmailDeliverabilityRule(message='Custom DNS error')
        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.side_effect = EmailNotValidError('boom')
            is_valid, error = rule.validate('user@example.com')
        assert is_valid is False
        assert error == 'Custom DNS error'

    def test_timeout_passed_through(self):
        rule = EmailDeliverabilityRule(timeout=5)
        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.return_value = object()
            rule.validate('user@example.com')
        _, kwargs = mock_validate.call_args
        assert kwargs['timeout'] == 5

    def test_descriptor(self):
        rule = EmailDeliverabilityRule(timeout=3)
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'email_deliverability'
        assert descriptor['client'] is False
        assert descriptor['timeout'] == 3

    def test_missing_dependency_raises_helpful_error(self):
        """If email-validator isn't installed, fail loudly with install instructions
        rather than silently treating every address as valid or invalid."""
        rule = EmailDeliverabilityRule()
        with patch.dict('sys.modules', {'email_validator': None}):
            with pytest.raises(ImportError, match='email-dns'):
                rule.validate('user@example.com')


# ---------------------------------------------------------------------------
# DateRangeRule
# (merged from test_validation_rules.py and test_validation_extended.py)
# Renamed extended class to TestDateRangeRuleExtended to avoid collision.
# ---------------------------------------------------------------------------


class TestDateRangeRule:
    """Test DateRangeRule validation (from test_validation_rules.py)."""

    def test_min_date_valid(self):
        """Test minimum date validation - valid."""
        min_date = date(2020, 1, 1)
        rule = DateRangeRule(min_date=min_date)
        assert rule.validate(date(2021, 6, 15))[0] is True

    def test_min_date_invalid(self):
        """Test minimum date validation - invalid."""
        min_date = date(2020, 1, 1)
        rule = DateRangeRule(min_date=min_date)
        is_valid, message = rule.validate(date(2019, 12, 31))
        assert is_valid is False

    def test_max_date_valid(self):
        """Test maximum date validation - valid."""
        max_date = date(2025, 12, 31)
        rule = DateRangeRule(max_date=max_date)
        assert rule.validate(date(2025, 6, 15))[0] is True

    def test_max_date_invalid(self):
        """Test maximum date validation - invalid."""
        max_date = date(2025, 12, 31)
        rule = DateRangeRule(max_date=max_date)
        is_valid, _ = rule.validate(date(2026, 1, 1))
        assert is_valid is False

    def test_date_range_valid(self):
        """Test full date range validation."""
        rule = DateRangeRule(
            min_date=date(2020, 1, 1),
            max_date=date(2025, 12, 31),
        )
        assert rule.validate(date(2023, 6, 15))[0] is True

    def test_date_range_invalid(self):
        """Test full date range - outside bounds."""
        rule = DateRangeRule(
            min_date=date(2020, 1, 1),
            max_date=date(2025, 12, 31),
        )
        assert rule.validate(date(2019, 12, 31))[0] is False
        assert rule.validate(date(2026, 1, 1))[0] is False

    def test_non_date_value(self):
        """Test with non-date value."""
        rule = DateRangeRule(min_date=date(2020, 1, 1))
        is_valid, message = rule.validate('not a date')
        assert is_valid is False

    def test_client_validation(self):
        """Test JavaScript generation for date range rule."""
        rule = DateRangeRule(min_date=date(2020, 1, 1))
        js_code = rule.get_client_validation('birthdate')
        assert len(js_code) > 0

    def test_descriptor(self):
        """Test date range rule descriptor."""
        rule = DateRangeRule(
            min_date=date(2020, 1, 1),
            max_date=date(2025, 12, 31),
        )
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'date_range'
        assert 'min_date' in descriptor or 'min' in descriptor


class TestDateRangeRuleExtended:
    """Extended DateRangeRule tests (from test_validation_extended.py)."""

    def test_date_range_min_date_valid(self):
        """Test DateRangeRule with valid date after min."""
        rule = DateRangeRule(min_date='2000-01-01')
        is_valid, msg = rule.validate('2020-06-15')
        assert is_valid is True

    def test_date_range_min_date_invalid(self):
        """Test DateRangeRule with date before min."""
        rule = DateRangeRule(min_date='2000-01-01')
        is_valid, msg = rule.validate('1999-12-31')
        assert is_valid is False

    def test_date_range_max_date_valid(self):
        """Test DateRangeRule with valid date before max."""
        rule = DateRangeRule(max_date='2025-12-31')
        is_valid, msg = rule.validate('2020-06-15')
        assert is_valid is True

    def test_date_range_max_date_invalid(self):
        """Test DateRangeRule with date after max."""
        rule = DateRangeRule(max_date='2025-12-31')
        is_valid, msg = rule.validate('2026-01-01')
        assert is_valid is False

    def test_date_range_both_bounds_valid(self):
        """Test DateRangeRule with date between min and max."""
        rule = DateRangeRule(min_date='2000-01-01', max_date='2025-12-31')
        is_valid, msg = rule.validate('2020-06-15')
        assert is_valid is True

    def test_date_range_both_bounds_below_min(self):
        """Test DateRangeRule with date before both bounds."""
        rule = DateRangeRule(min_date='2000-01-01', max_date='2025-12-31')
        is_valid, msg = rule.validate('1999-12-31')
        assert is_valid is False

    def test_date_range_both_bounds_above_max(self):
        """Test DateRangeRule with date after both bounds."""
        rule = DateRangeRule(min_date='2000-01-01', max_date='2025-12-31')
        is_valid, msg = rule.validate('2026-01-01')
        assert is_valid is False

    def test_date_range_empty_value(self):
        """Test DateRangeRule with empty value."""
        rule = DateRangeRule(min_date='2000-01-01')
        is_valid, msg = rule.validate('')
        assert is_valid is True

    def test_date_range_none_value(self):
        """Test DateRangeRule with None value."""
        rule = DateRangeRule(min_date='2000-01-01')
        is_valid, msg = rule.validate(None)
        assert is_valid is True

    def test_date_range_date_object(self):
        """Test DateRangeRule with date object."""
        rule = DateRangeRule(min_date=date(2000, 1, 1))
        is_valid, msg = rule.validate(date(2020, 6, 15))
        assert is_valid is True

    def test_date_range_invalid_format(self):
        """Test DateRangeRule with invalid date format."""
        rule = DateRangeRule(min_date='2000-01-01')
        is_valid, msg = rule.validate('not-a-date')
        assert is_valid is False

    def test_date_range_wrong_type(self):
        """Test DateRangeRule with wrong type value."""
        rule = DateRangeRule(min_date='2000-01-01')
        is_valid, msg = rule.validate(12345)
        assert is_valid is False

    def test_date_range_custom_message(self):
        """Test DateRangeRule with custom message."""
        rule = DateRangeRule(
            min_date='2000-01-01',
            message='Date is too old',
        )
        is_valid, msg = rule.validate('1999-12-31')
        assert 'too old' in msg

    def test_date_range_descriptor_with_dates(self):
        """Test DateRangeRule descriptor."""
        rule = DateRangeRule(min_date='2000-01-01', max_date='2025-12-31')
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'date_range'
        assert descriptor['min_date'] == '2000-01-01'
        assert descriptor['max_date'] == '2025-12-31'

    def test_date_range_descriptor_min_only(self):
        """Test DateRangeRule descriptor with min only."""
        rule = DateRangeRule(min_date='2000-01-01')
        descriptor = rule.to_descriptor()
        assert descriptor['min_date'] == '2000-01-01'
        assert descriptor['max_date'] is None


# ---------------------------------------------------------------------------
# ConvenienceValidators
# ---------------------------------------------------------------------------


class TestConvenienceValidators:
    """Test convenience validator factory functions."""

    def test_create_email_validator(self):
        """Test email validator factory."""
        validator = create_email_validator()
        assert callable(validator)
        result = validator('test@example.com')
        assert isinstance(result, ValidationResponse)
        assert result.is_valid is True

    def test_create_email_validator_invalid(self):
        """Test email validator with invalid email."""
        validator = create_email_validator()
        result = validator('not-an-email')
        assert isinstance(result, ValidationResponse)
        assert result.is_valid is False

    def test_create_email_validator_check_deliverability_valid(self):
        """DNS/MX check is skipped by default, opt-in via check_deliverability."""
        validator = create_email_validator(check_deliverability=True)
        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.return_value = object()
            result = validator('user@example.com')
        assert result.is_valid is True
        mock_validate.assert_called_once()

    def test_create_email_validator_check_deliverability_invalid_domain(self):
        """A well-formed address with no valid MX record fails when opted in."""
        from email_validator import EmailNotValidError

        validator = create_email_validator(check_deliverability=True)
        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.side_effect = EmailNotValidError('no MX record')
            result = validator('user@this-domain-does-not-exist-xyz.invalid')
        assert result.is_valid is False
        assert result.errors

    def test_create_email_validator_skips_dns_when_format_invalid(self):
        """Malformed addresses fail on the regex check before any DNS lookup happens."""
        validator = create_email_validator(check_deliverability=True)
        with patch('email_validator.validate_email') as mock_validate:
            result = validator('not-an-email')
        assert result.is_valid is False
        mock_validate.assert_not_called()

    def test_create_password_strength_validator(self):
        """Test password strength validator factory."""
        validator = create_password_strength_validator(min_length=8)
        assert callable(validator)
        result = validator('WeakPwd1')
        assert isinstance(result, ValidationResponse)


# ---------------------------------------------------------------------------
# ValidateFormData
# ---------------------------------------------------------------------------


class TestValidateFormData:
    """Test validate_form_data function."""

    def test_validate_simple_form(self):
        """Test validation of a simple form."""

        class SimpleForm(FormModel):
            username: str = Field(min_length=3, max_length=20)
            email: str
            age: int = Field(ge=18)

        result = validate_form_data(
            SimpleForm,
            {
                'username': 'johndoe',
                'email': 'john@example.com',
                'age': 25,
            },
        )
        assert result.is_valid is True
        assert result.data is not None
        assert result.data['username'] == 'johndoe'

    def test_validate_form_with_errors(self):
        """Test validation with errors."""

        class UserForm(FormModel):
            username: str = Field(min_length=5)
            age: int = Field(ge=18, le=100)

        result = validate_form_data(
            UserForm,
            {
                'username': 'abc',  # Too short
                'age': 15,  # Too young
            },
        )
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_form_missing_required(self):
        """Test validation with missing required field."""

        class RequiredForm(FormModel):
            name: str
            email: str

        result = validate_form_data(
            RequiredForm,
            {'name': 'John'},  # Missing email
        )
        assert result.is_valid is False
        assert 'email' in str(result.errors)

    def test_validate_form_with_optional(self):
        """Test validation with optional fields."""

        class OptionalForm(FormModel):
            name: str
            nickname: Optional[str] = None

        result = validate_form_data(
            OptionalForm,
            {'name': 'John'},  # nickname is optional
        )
        assert result.is_valid is True
        assert result.data['name'] == 'John'
        assert result.data.get('nickname') is None


# ---------------------------------------------------------------------------
# TestValidationRules (from test_validation_coverage.py)
# ---------------------------------------------------------------------------


class TestValidationRules:
    """Test validation rules (coverage-focused)."""

    def test_required_rule_valid(self):
        rule = RequiredRule()
        is_valid, msg = rule.validate('John')
        assert is_valid is True

    def test_required_rule_empty_string(self):
        rule = RequiredRule()
        is_valid, msg = rule.validate('')
        assert is_valid is False

    def test_required_rule_none(self):
        rule = RequiredRule()
        is_valid, msg = rule.validate(None)
        assert is_valid is False

    def test_required_rule_custom_message(self):
        rule = RequiredRule(message='Name is required')
        is_valid, msg = rule.validate('')
        assert 'Name is required' in msg

    def test_required_rule_get_client_validation(self):
        rule = RequiredRule()
        js = rule.get_client_validation('username')
        assert len(js) > 0

    def test_required_rule_get_client_validation_empty(self):
        rule = RequiredRule()
        rule.client_side = False
        js = rule.get_client_validation('field')
        assert js == ''

    def test_email_rule_valid(self):
        rule = EmailRule()
        is_valid, msg = rule.validate('user@example.com')
        assert is_valid is True

    def test_email_rule_invalid(self):
        rule = EmailRule()
        is_valid, msg = rule.validate('not-an-email')
        assert is_valid is False

    def test_min_length_rule_valid(self):
        rule = MinLengthRule(min_length=3)
        is_valid, msg = rule.validate('hello')
        assert is_valid is True

    def test_min_length_rule_too_short(self):
        rule = MinLengthRule(min_length=5)
        is_valid, msg = rule.validate('hi')
        assert is_valid is False

    def test_max_length_rule_valid(self):
        rule = MaxLengthRule(max_length=10)
        is_valid, msg = rule.validate('hello')
        assert is_valid is True

    def test_max_length_rule_too_long(self):
        rule = MaxLengthRule(max_length=5)
        is_valid, msg = rule.validate('hello world')
        assert is_valid is False

    def test_pattern_rule_valid(self):
        rule = RegexRule(pattern=r'^\d{3}-\d{4}$')
        is_valid, msg = rule.validate('123-4567')
        assert is_valid is True

    def test_pattern_rule_invalid(self):
        rule = RegexRule(pattern=r'^\d+$')
        is_valid, msg = rule.validate('abc123')
        assert is_valid is False

    def test_min_rule_valid(self):
        rule = NumericRangeRule(min_value=0)
        is_valid, msg = rule.validate(5)
        assert is_valid is True

    def test_min_rule_too_small(self):
        rule = NumericRangeRule(min_value=10)
        is_valid, msg = rule.validate(5)
        assert is_valid is False

    def test_max_rule_valid(self):
        rule = NumericRangeRule(max_value=100)
        is_valid, msg = rule.validate(50)
        assert is_valid is True

    def test_max_rule_too_large(self):
        rule = NumericRangeRule(max_value=50)
        is_valid, msg = rule.validate(100)
        assert is_valid is False

    def test_numeric_rule_valid(self):
        rule = NumericRangeRule()
        is_valid, msg = rule.validate(123)
        assert is_valid is True

    def test_numeric_rule_invalid(self):
        rule = NumericRangeRule()
        is_valid, msg = rule.validate('abc')
        assert is_valid is False

    def test_validation_rule_base_not_implemented(self):
        rule = ValidationRule()
        with pytest.raises(NotImplementedError):
            rule.validate('value')

    def test_validation_rule_to_descriptor(self):
        rule = RequiredRule(message='Custom message')
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'required'
        assert descriptor['message'] == 'Custom message'
        assert 'client' in descriptor


# ---------------------------------------------------------------------------
# Standalone functions from test_validation_coverage.py
# ---------------------------------------------------------------------------


def test_base_generate_js_validation_default_empty():
    assert ValidationRule()._generate_js_validation('field') == ''


def test_min_max_length_none_and_js_generation():
    min_rule = MinLengthRule(3)
    max_rule = MaxLengthRule(5)

    assert min_rule.validate(None) == (True, '')
    assert max_rule.validate(None) == (True, '')
    assert 'value.length < 3' in min_rule.get_client_validation('name')
    assert 'value.length > 5' in max_rule.get_client_validation('name')


def test_regex_empty_value_is_valid():
    rule = RegexRule(r'^a+$')
    assert rule.validate('') == (True, '')


def test_numeric_range_empty_and_no_check_js():
    rule = NumericRangeRule()
    assert rule.validate(None) == (True, '')
    assert rule.get_client_validation('age') == ''


def test_date_range_constructor_and_parse_errors_and_js_paths():
    rule = DateRangeRule()
    assert rule.message == 'Invalid date'
    assert rule.get_client_validation('start_date') == ''

    max_only_rule = DateRangeRule(max_date='2024-12-31')
    js = max_only_rule.get_client_validation('start_date')
    assert "dateValue > new Date('2024-12-31')" in js

    try:
        DateRangeRule()._parse_date(123)
        raise AssertionError('Expected ValueError')
    except ValueError as exc:
        assert 'Invalid date format' in str(exc)


def test_custom_rule_invalid_result_and_exception_branches():
    invalid_result_rule = CustomRule(lambda _v: 'unexpected')
    is_valid, msg = invalid_result_rule.validate('value')
    assert is_valid is False
    assert msg == 'Invalid validation result'

    exploding_rule = CustomRule(lambda _v: 1 / 0)
    is_valid, msg = exploding_rule.validate('value')
    assert is_valid is False
    assert msg.startswith('Validation error:')


def test_field_validator_helpers_and_no_client_js_branch():
    validator = (
        FieldValidator('contact')
        .phone()
        .date_range(min_date='2024-01-01', max_date='2024-12-31')
        .regex(r'^.*$')
        .custom(lambda _v: True)
    )

    schema = validator.to_schema()
    rule_types = {rule['type'] for rule in schema['rules']}
    assert {'phone', 'date_range', 'regex', 'custom'}.issubset(rule_types)
    js = validator.generate_client_validation()
    assert 'function validateContact' in js

    custom_only = FieldValidator('only_custom').custom(lambda _v: True)
    assert custom_only.generate_client_validation() == ''


def test_form_validator_field_and_cross_field_errors():
    form_validator = FormValidator()
    form_validator.field('age').numeric_range(min_val=18)

    def cross_rule(data):
        return False, {'age': 'cross age error', 'name': 'name mismatch'}

    form_validator.add_cross_field_rule(cross_rule)

    is_valid, errors = form_validator.validate({'age': 10, 'name': 'x'})
    assert is_valid is False
    assert 'age' in errors and len(errors['age']) >= 2
    assert 'name' in errors


def test_cross_field_rules_password_confirmation_and_date_range_validation():
    password_rule = CrossFieldRules.password_confirmation()
    assert password_rule({'password': 'abc', 'confirm_password': 'xyz'}) == (
        False,
        {'confirm_password': 'Passwords do not match'},
    )
    assert password_rule({'password': 'abc', 'confirm_password': 'abc'}) == (True, {})

    date_rule = CrossFieldRules.date_range_validation('start', 'end')
    assert date_rule({'start': '2024-01-10', 'end': '2024-01-09'}) == (
        False,
        {'end': 'End date must be after start date'},
    )
    assert date_rule({'start': 'not-a-date', 'end': '2024-01-09'}) == (
        False,
        {'end': 'Invalid date format'},
    )
    assert date_rule({'start': '2024-01-01', 'end': '2024-01-02'}) == (True, {})


def test_email_and_password_factory_validators_edge_paths():
    email_validator = create_email_validator()
    response = email_validator('')
    assert response.is_valid is False
    assert response.errors == ['Email is required']

    password_validator = create_password_strength_validator(min_length=4)
    response = password_validator('AAAA1111!')
    assert response.is_valid is True
    assert 'lowercase' in ' '.join(response.warnings).lower()


# ---------------------------------------------------------------------------
# Model helpers used by validate_form_data tests (from coverage file)
# ---------------------------------------------------------------------------


class _LayoutFieldModel(FormModel):
    layout_field: dict = Field(
        default_factory=lambda: {'layout': True},
        json_schema_extra={'ui_element': 'layout'},
    )


class _CallableExtraModel(FormModel):
    name: str = Field(default='ok', json_schema_extra=lambda schema, _cls: schema.update({'x': 1}))


class _LeLengthModel(FormModel):
    small: int = Field(le=5)
    short: str = Field(min_length=3, max_length=4)


class _GeneralModelError(FormModel):
    x: int = Field(default=1)

    @model_validator(mode='after')
    def ensure_invalid(self):
        raise ValueError('model invalid')


def test_validate_form_data_layout_cleanup_and_non_dict_extra(monkeypatch):
    import pydantic_schemaforms.rendering.layout_engine as layout_engine

    monkeypatch.setattr(layout_engine, 'get_nested_form_data', lambda *args, **kwargs: {})

    result = validate_form_data(_LayoutFieldModel, {})
    assert result.is_valid is True
    assert 'layout_field' not in result.data

    callable_extra_result = validate_form_data(_CallableExtraModel, {'name': 'ok'})
    assert callable_extra_result.is_valid is True
    assert callable_extra_result.data['name'] == 'ok'


def test_validate_form_data_error_message_paths_and_general_and_exception():
    result = validate_form_data(_LeLengthModel, {'small': 10, 'short': 'x'})
    assert result.is_valid is False
    assert result.errors['small'] == 'Must be 5 or less'
    assert result.errors['short']

    max_length_result = validate_form_data(_LeLengthModel, {'small': 2, 'short': 'abcde'})
    assert max_length_result.is_valid is False
    assert max_length_result.errors['short']

    import pydantic_schemaforms.validation as validation_module

    class _FakeValidationError(Exception):
        def __init__(self, payload):
            self._payload = payload

        def errors(self):
            return self._payload

    class _RaisesFakeValidationError:
        def __init__(self, payload):
            self.payload = payload

        def __call__(self, **_kwargs):
            raise _FakeValidationError(self.payload)

    fake_payload = [
        {'loc': ('n',), 'msg': 'bad', 'type': 'less_than_equal', 'ctx': {'le': 4}},
        {'loc': ('min_field',), 'msg': 'bad', 'type': 'min_length', 'ctx': {'min_length': 3}},
        {'loc': ('max_field',), 'msg': 'bad', 'type': 'max_length', 'ctx': {'max_length': 7}},
        {'loc': (), 'msg': 'general bad', 'type': 'value_error'},
    ]

    original_validation_error = validation_module.ValidationError
    try:
        validation_module.ValidationError = _FakeValidationError
        mapped_errors_result = validate_form_data(_RaisesFakeValidationError(fake_payload), {})
    finally:
        validation_module.ValidationError = original_validation_error

    assert mapped_errors_result.is_valid is False
    assert mapped_errors_result.errors['n'] == 'Must be 4 or less'
    assert mapped_errors_result.errors['min_field'] == 'Must be at least 3 characters'
    assert mapped_errors_result.errors['max_field'] == 'Must be no more than 7 characters'
    assert mapped_errors_result.errors['general'] == 'general bad'

    general_result = validate_form_data(_GeneralModelError, {'x': 1})
    assert general_result.is_valid is False
    assert 'general' in general_result.errors

    class _ExplodingRuntimeProvider:
        @staticmethod
        def get_runtime_model():
            def _explode(**_kwargs):
                raise RuntimeError('boom')

            return _explode

    exception_result = validate_form_data(_ExplodingRuntimeProvider, {})
    assert exception_result.is_valid is False
    assert exception_result.errors == {'general': 'boom'}


# ---------------------------------------------------------------------------
# Custom date/time/datetime format coercion (_coerce_html_form_values)
# ---------------------------------------------------------------------------


class _CustomDateTimeFormatForm(FormModel):
    start_date: date = Field(json_schema_extra={'ui_options': {'date_format': '%d/%m/%Y'}})
    military_time: time = Field(json_schema_extra={'ui_options': {'time_format': '%H:%M'}})
    combo: datetime = Field(json_schema_extra={'ui_options': {'datetime_format': '%Y%m%d%H%M%S'}})
    end_date: Optional[date] = Field(
        default=None, json_schema_extra={'ui_options': {'date_format': '%d/%m/%Y'}}
    )


class TestCustomDateTimeFormatCoercion:
    """Test the custom date/time/datetime format branch in _coerce_html_form_values."""

    def test_custom_format_roundtrip(self):
        result = validate_form_data(
            _CustomDateTimeFormatForm,
            {
                'start_date': '05/03/2026',
                'military_time': '23:15',
                'combo': '20260801143005',
            },
        )
        assert result.is_valid is True
        assert result.data['start_date'] == date(2026, 3, 5)
        assert result.data['military_time'] == time(23, 15)
        assert result.data['combo'] == datetime(2026, 8, 1, 14, 30, 5)

    def test_military_time_has_no_am_pm(self):
        """time_format='%H:%M' is 24-hour by construction -- no AM/PM anywhere."""
        result = validate_form_data(
            _CustomDateTimeFormatForm,
            {
                'start_date': '05/03/2026',
                'military_time': '23:15',
                'combo': '20260801143005',
            },
        )
        assert result.is_valid is True
        assert result.data['military_time'] == time(23, 15)

    def test_pure_time_field_with_non_iso_compatible_format(self):
        """Regression guard: `time` is NOT a subclass of `date` in Python, so
        a naive `issubclass(t, date)` type-detection check silently skips
        every plain `time` field. Use a format ('%I:%M %p') whose output
        ('11:15 PM') Pydantic's own native ISO time parser would also reject,
        so this test only passes if the custom-format branch itself actually
        ran -- unlike '23:15'-style values, which happen to parse via
        Pydantic's native fallback regardless of whether the branch fired."""

        class _PureTimeForm(FormModel):
            meeting_time: time = Field(
                json_schema_extra={'ui_options': {'time_format': '%I:%M %p'}}
            )

        result = validate_form_data(_PureTimeForm, {'meeting_time': '11:15 PM'})
        assert result.is_valid is True
        assert result.data['meeting_time'] == time(23, 15)

    def test_custom_format_still_accepts_plain_iso_string(self):
        """A JSON API caller submitting plain ISO strings still validates,
        regardless of what display format the HTML form is configured with."""
        result = validate_form_data(
            _CustomDateTimeFormatForm,
            {
                'start_date': '2026-03-05',
                'military_time': '23:15:00',
                'combo': '2026-08-01T14:30:05',
            },
        )
        assert result.is_valid is True
        assert result.data['start_date'] == date(2026, 3, 5)
        assert result.data['military_time'] == time(23, 15)
        assert result.data['combo'] == datetime(2026, 8, 1, 14, 30, 5)

    def test_invalid_custom_format_string_produces_field_error(self):
        """A string matching neither the custom format nor ISO fails cleanly,
        attributed to the correct field (not a generic/'general' error)."""
        result = validate_form_data(
            _CustomDateTimeFormatForm,
            {
                'start_date': 'not-a-date',
                'military_time': '23:15',
                'combo': '20260801143005',
            },
        )
        assert result.is_valid is False
        assert 'start_date' in result.errors
        assert 'general' not in result.errors

    def test_optional_custom_format_field_empty_string_becomes_none(self):
        """Empty-optional-scalar coercion still wins over the new branch --
        an empty string never reaches strptime and correctly becomes None."""
        result = validate_form_data(
            _CustomDateTimeFormatForm,
            {
                'start_date': '05/03/2026',
                'military_time': '23:15',
                'combo': '20260801143005',
                'end_date': '',
            },
        )
        assert result.is_valid is True
        assert result.data['end_date'] is None

    def test_nested_model_field_with_custom_date_format(self):
        """The new branch composes correctly with the existing nested-model
        recursion in _coerce_html_form_values."""

        class _Event(FormModel):
            name: str
            starts_on: date = Field(json_schema_extra={'ui_options': {'date_format': '%d/%m/%Y'}})

        class _Schedule(FormModel):
            events: list[_Event]

        result = validate_form_data(
            _Schedule,
            {'events': [{'name': 'Launch', 'starts_on': '05/03/2026'}]},
        )
        assert result.is_valid is True
        assert result.data['events'][0]['starts_on'] == date(2026, 3, 5)

    def test_nested_model_field_with_invalid_custom_date_format(self):
        class _Event(FormModel):
            name: str
            starts_on: date = Field(json_schema_extra={'ui_options': {'date_format': '%d/%m/%Y'}})

        class _Schedule(FormModel):
            events: list[_Event]

        result = validate_form_data(
            _Schedule,
            {'events': [{'name': 'Launch', 'starts_on': 'nope'}]},
        )
        assert result.is_valid is False
        assert 'events[0].starts_on' in result.errors


# ---------------------------------------------------------------------------
# CustomRule (from test_validation_extended.py)
# ---------------------------------------------------------------------------


class TestCustomRule:
    """Test CustomRule validation."""

    def test_custom_rule_bool_return(self):
        """Test CustomRule with boolean return value."""

        def is_even(value):
            try:
                return int(value) % 2 == 0
            except ValueError, TypeError:
                return False

        rule = CustomRule(is_even, message='Must be even')
        is_valid, msg = rule.validate(4)
        assert is_valid is True

    def test_custom_rule_bool_return_false(self):
        """Test CustomRule returns False."""

        def is_even(value):
            try:
                return int(value) % 2 == 0
            except ValueError, TypeError:
                return False

        rule = CustomRule(is_even, message='Must be even')
        is_valid, msg = rule.validate(3)
        assert is_valid is False
        assert 'even' in msg

    def test_custom_rule_tuple_return_valid(self):
        """Test CustomRule with tuple return (valid)."""

        def validate_password(value):
            if len(value) < 8:
                return False, 'Password must be at least 8 characters'
            return True, ''

        rule = CustomRule(validate_password)
        is_valid, msg = rule.validate('MySecure123!')
        assert is_valid is True

    def test_custom_rule_tuple_return_invalid(self):
        """Test CustomRule with tuple return (invalid)."""

        def validate_password(value):
            if len(value) < 8:
                return False, 'Password must be at least 8 characters'
            return True, ''

        rule = CustomRule(validate_password)
        is_valid, msg = rule.validate('short')
        assert is_valid is False
        assert 'at least 8' in msg

    def test_custom_rule_complex_validation(self):
        """Test CustomRule with complex validation logic."""

        def validate_username(value):
            if not isinstance(value, str):
                return False, 'Username must be a string'
            if len(value) < 3:
                return False, 'Username must be at least 3 characters'
            if not value[0].isalpha():
                return False, 'Username must start with a letter'
            if not all(c.isalnum() or c == '_' for c in value):
                return False, 'Username can only contain letters, numbers, and underscores'
            return True, ''

        rule = CustomRule(validate_username)
        assert rule.validate('valid_user')[0] is True
        assert rule.validate('ab')[0] is False
        assert rule.validate('1user')[0] is False

    def test_custom_rule_no_client_side(self):
        """Test CustomRule without client-side validation."""

        def always_false(value):
            return False

        rule = CustomRule(always_false, client_side=False)
        js = rule.get_client_validation('field')
        assert js == ''

    def test_custom_rule_descriptor(self):
        """Test CustomRule descriptor."""

        def dummy_validator(value):
            return True

        rule = CustomRule(dummy_validator, message='Custom error')
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'custom'
        assert descriptor['message'] == 'Custom error'


# ---------------------------------------------------------------------------
# NumericRangeRule — advanced tests (from test_validation_extended.py)
# ---------------------------------------------------------------------------


class TestNumericRangeRuleAdvanced:
    """Advanced tests for NumericRangeRule."""

    def test_numeric_range_with_float_values(self):
        """Test NumericRangeRule with float values."""
        rule = NumericRangeRule(min_value=0.5, max_value=99.99)
        assert rule.validate(50.0)[0] is True
        assert rule.validate(0.49)[0] is False
        assert rule.validate(100.0)[0] is False

    def test_numeric_range_string_conversion(self):
        """Test NumericRangeRule converts string numbers."""
        rule = NumericRangeRule(min_value=0, max_value=100)
        assert rule.validate('50')[0] is True
        assert rule.validate('150')[0] is False

    def test_numeric_range_negative_values(self):
        """Test NumericRangeRule with negative values."""
        rule = NumericRangeRule(min_value=-100, max_value=-10)
        assert rule.validate(-50)[0] is True
        assert rule.validate(-5)[0] is False
        assert rule.validate(50)[0] is False


# ---------------------------------------------------------------------------
# Consolidated validation engine (from test_validation_consolidation.py)
# ---------------------------------------------------------------------------


class TestConsolidatedValidationEngine:
    """Test the consolidated validation engine."""

    def test_validation_response_in_validation_module(self):
        """ValidationResponse should be exported from validation.py."""
        from pydantic_schemaforms.validation import ValidationResponse as VR

        response = VR(field_name='test', is_valid=True)
        assert response.field_name == 'test'
        assert response.is_valid is True

    def test_validation_response_in_live_validation_module(self):
        """ValidationResponse should be accessible from live_validation.py."""
        response = LiveValidationResponse(field_name='test', is_valid=True)
        assert response.field_name == 'test'
        assert response.is_valid is True

    def test_email_validator_from_validation_module(self):
        """Email validator should be in validation.py."""
        validator = create_email_validator()

        invalid = validator('notanemail')
        assert not invalid.is_valid
        assert 'valid email' in invalid.errors[0].lower()

        valid = validator('user@example.com')
        assert valid.is_valid
        assert valid.formatted_value == 'user@example.com'

    def test_field_validator_email_check_deliverability_adds_dns_rule(self):
        """FieldValidator.email(check_deliverability=True) appends an
        EmailDeliverabilityRule alongside the regular EmailRule."""
        fv = FieldValidator('email').email(check_deliverability=True, dns_timeout=5)
        rule_types = [type(r) for r in fv.rules]
        assert EmailRule in rule_types
        assert EmailDeliverabilityRule in rule_types
        dns_rule = next(r for r in fv.rules if isinstance(r, EmailDeliverabilityRule))
        assert dns_rule.timeout == 5

    def test_field_validator_email_default_skips_dns_rule(self):
        """Default behavior is unchanged — no DNS rule unless opted in."""
        fv = FieldValidator('email').email()
        assert not any(isinstance(r, EmailDeliverabilityRule) for r in fv.rules)

    def test_field_validator_email_check_deliverability_end_to_end(self):
        """A field validator with check_deliverability=True rejects a
        well-formed address whose domain has no MX record."""
        from email_validator import EmailNotValidError

        fv = FieldValidator('email').email(check_deliverability=True)
        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.side_effect = EmailNotValidError('no MX record')
            is_valid, errors = fv.validate('user@this-domain-does-not-exist-xyz.invalid')
        assert is_valid is False
        assert errors

    def test_password_validator_from_validation_module(self):
        """Password validator should be in validation.py."""
        validator = create_password_strength_validator(min_length=8)

        weak = validator('weak')
        assert not weak.is_valid
        assert len(weak.errors) > 0

        strong = validator('SecureP@ss123')
        assert strong.is_valid

    def test_email_validator_from_live_validation_module(self):
        """Email validator should be accessible from live_validation.py."""
        from pydantic_schemaforms.live_validation import create_email_validator as live_create_email

        validator = live_create_email()
        valid = validator('user@example.com')
        assert valid.is_valid

    def test_field_validator_with_live_registration(self):
        """FieldValidator should work with LiveValidator registration."""
        field_validator = FieldValidator('username').required().min_length(3)

        live_validator = LiveValidator()
        live_validator.register_field_validator(field_validator)

        response = live_validator.validate_field('username', 'ab')
        assert not response.is_valid

        response = live_validator.validate_field('username', 'john')
        assert response.is_valid

    def test_live_validator_dns_check_for_point_of_typing_feedback(self):
        """A field validator with an email(check_deliverability=True) rule works
        through LiveValidator — this is the wiring an HTMX endpoint would use to
        give DNS/MX feedback as the user types/blurs the email field."""
        from email_validator import EmailNotValidError

        field_validator = FieldValidator('email').required().email(check_deliverability=True)
        live_validator = LiveValidator()
        live_validator.register_field_validator(field_validator)

        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.side_effect = EmailNotValidError('no MX record')
            response = live_validator.validate_field(
                'email', 'user@this-domain-does-not-exist-xyz.invalid'
            )
        assert response.is_valid is False

        with patch('email_validator.validate_email') as mock_validate:
            mock_validate.return_value = object()
            response = live_validator.validate_field('email', 'user@example.com')
        assert response.is_valid is True

    def test_validation_schema_build_live_validator(self):
        """ValidationSchema.build_live_validator() should create working LiveValidator."""
        schema = ValidationSchema()
        schema.add_field(FieldValidator('email').required().email())
        schema.add_field(FieldValidator('password').required().min_length(8))

        live_validator = schema.build_live_validator()

        invalid_email = live_validator.validate_field('email', 'notanemail')
        assert not invalid_email.is_valid

        valid_email = live_validator.validate_field('email', 'user@example.com')
        assert valid_email.is_valid

        weak_password = live_validator.validate_field('password', 'short')
        assert not weak_password.is_valid

        strong_password = live_validator.validate_field('password', 'LongPassword123')
        assert strong_password.is_valid

    def test_validation_response_serialization(self):
        """ValidationResponse should serialize to JSON."""
        response = LiveValidationResponse(
            field_name='email',
            is_valid=False,
            errors=['Invalid email'],
            warnings=['No MX record found'],
            suggestions=['Check spelling'],
        )

        json_str = response.to_json()
        assert '"field_name": "email"' in json_str
        assert '"is_valid": false' in json_str

        dict_data = response.to_dict()
        assert dict_data['field_name'] == 'email'
        assert not dict_data['is_valid']
        assert 'Invalid email' in dict_data['errors']

    def test_cross_framework_consistency(self):
        """Same validation rules should work in both validation and live_validation."""
        field_validator = FieldValidator('username').required().min_length(3).max_length(20)

        is_valid, errors = field_validator.validate('a')
        assert not is_valid
        assert any('at least 3' in e.lower() for e in errors)

        live = LiveValidator()
        live.register_field_validator(field_validator)

        response = live.validate_field('username', 'a')
        assert not response.is_valid
        assert any('at least 3' in e.lower() for e in response.errors)

    def test_field_validator_schema_to_live_validator_flow(self):
        """Test complete flow: FieldValidator -> ValidationSchema -> LiveValidator."""
        schema = ValidationSchema()
        schema.add_field(FieldValidator('email').required().email())
        schema.add_field(FieldValidator('username').required().min_length(3).max_length(20))

        schema_dict = schema.to_dict()
        assert 'email' in schema_dict
        assert 'username' in schema_dict

        live_validator = schema.build_live_validator()

        assert 'email' in live_validator.field_configs
        assert 'username' in live_validator.field_configs

        email_response = live_validator.validate_field('email', 'invalid')
        assert not email_response.is_valid

        username_response = live_validator.validate_field('username', 'ab')
        assert not username_response.is_valid


# ---------------------------------------------------------------------------
# Layout-related tests (from test_validation_coverage.py)
# ---------------------------------------------------------------------------


class LeafForm(FormModel):
    first_name: str = Field(..., min_length=2)


class RaisingValidateLayout(VerticalLayout):
    form = LeafForm

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        raise RuntimeError('boom')


class BadGetFormsLayout(VerticalLayout):
    form = LeafForm

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        raise RuntimeError('boom')

    def _get_forms(self):  # pragma: no cover - executed in tests
        raise RuntimeError('boom')


class NoCallableGetFormsLayout(VerticalLayout):
    form = LeafForm

    def __init__(self):
        super().__init__()
        # Make the attribute present but not callable.
        self._get_forms = None

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        raise RuntimeError('boom')


class EmptyDataValidateLayout(VerticalLayout):
    form = LeafForm

    def validate(self, form_data, files=None):  # pragma: no cover - executed in tests
        # Return an empty dict to hit the `nested_result.data` falsey branch.
        return ValidationResult(is_valid=True, data={}, errors={})


class WrapperRaising(FormModel):
    personal_info: RaisingValidateLayout = FormField(
        default_factory=RaisingValidateLayout, input_type='layout'
    )


class WrapperBadGetForms(FormModel):
    personal_info: BadGetFormsLayout = FormField(
        default_factory=BadGetFormsLayout, input_type='layout'
    )


class WrapperNoCallableGetForms(FormModel):
    personal_info: NoCallableGetFormsLayout = FormField(
        default_factory=NoCallableGetFormsLayout, input_type='layout'
    )


class WrapperEmptyData(FormModel):
    personal_info: EmptyDataValidateLayout = FormField(
        default_factory=EmptyDataValidateLayout, input_type='layout'
    )


class OrgForm(FormModel):
    company_name: str


class SettingsForm(FormModel):
    username: str
    theme: str


class OrgLayout(VerticalLayout):
    form = OrgForm


class SettingsLayout(VerticalLayout):
    form = SettingsForm


class GenericTabbed(TabbedLayout):
    def __init__(self, form_config=None):
        super().__init__(form_config=form_config)
        self.org = OrgLayout()
        self.settings = SettingsLayout()

    def _get_layouts(self):
        return [('org', self.org), ('settings', self.settings)]


class WrapperTabbed(FormModel):
    tabs: GenericTabbed = FormField(default_factory=GenericTabbed, input_type='layout')


def test_layout_validate_raises_falls_back_to_get_forms_and_reports_errors():
    result = validate_form_data(WrapperRaising, {'first_name': 'A'})
    assert result.is_valid is False
    assert 'first_name' in result.errors


def test_layout_get_forms_raises_is_safely_ignored():
    result = validate_form_data(WrapperBadGetForms, {'first_name': 'A'})
    assert result.is_valid is True
    assert result.data.get('personal_info') == {'first_name': 'A'}


def test_layout_get_forms_not_callable_skips_fallback():
    result = validate_form_data(WrapperNoCallableGetForms, {'first_name': 'A'})
    assert result.is_valid is True
    assert result.data.get('personal_info') == {'first_name': 'A'}


def test_layout_validate_returns_empty_data_does_not_replace_payload():
    payload = {'first_name': 'Ok'}
    result = validate_form_data(WrapperEmptyData, payload)
    assert result.is_valid is True
    # Because validate() returned empty data, validate_form_data keeps nested payload.
    assert result.data.get('personal_info') == {'first_name': 'Ok'}


def test_layout_payload_removed_when_no_nested_data_extracted():
    result = validate_form_data(WrapperTabbed, {})
    assert result.is_valid is True
    assert result.data == {}


def test_tabbed_layout_nested_payload_validation_sets_layout_errors():
    result = validate_form_data(
        WrapperTabbed,
        {'username': 'alice', 'theme': 'dark'},
    )
    assert result.is_valid is False
    assert 'company_name' in result.errors
    assert 'tabs' in result.data
    assert 'settings' in result.data['tabs']


# ---------------------------------------------------------------------------
# Standalone tests from test_validation_schema.py
# ---------------------------------------------------------------------------


def test_field_validator_schema_descriptors():
    validator = FieldValidator('username').required().min_length(3)

    schema = validator.to_schema()
    rule_types = {rule['type'] for rule in schema['rules']}

    assert schema['field'] == 'username'
    assert rule_types == {'required', 'min_length'}
    min_length_rule = next(rule for rule in schema['rules'] if rule['type'] == 'min_length')
    assert min_length_rule['min_length'] == 3


def test_validation_schema_registration_and_live_execution():
    age_validator = FieldValidator('age').required().numeric_range(min_val=18)
    email_validator = FieldValidator('email').required().email()

    schema = ValidationSchema().add_field(age_validator).add_field(email_validator)
    assert set(schema.to_dict().keys()) == {'age', 'email'}

    live_validator = schema.build_live_validator()

    underage_response = live_validator.validate_field('age', '12')
    assert not underage_response.is_valid
    assert 'Must be' in underage_response.errors[0]

    adult_response = live_validator.validate_field('age', '32')
    assert adult_response.is_valid

    invalid_email = live_validator.validate_field('email', 'invalid')
    assert not invalid_email.is_valid
    assert any('valid email' in msg.lower() for msg in invalid_email.errors)

    valid_email = live_validator.validate_field('email', 'user@example.com')
    assert valid_email.is_valid


def test_live_validator_direct_field_registration():
    validator = FieldValidator('code').required().min_length(4)
    live_validator = LiveValidator()
    live_validator.register_field_validator(validator)

    assert 'rules' in live_validator.field_configs['code']
    rule_types = {rule['type'] for rule in live_validator.field_configs['code']['rules']}
    assert rule_types == {'required', 'min_length'}

    response = live_validator.validate_field('code', 'abc')
    assert not response.is_valid
    assert response.errors

    assert live_validator.validate_field('code', 'abcd').is_valid
