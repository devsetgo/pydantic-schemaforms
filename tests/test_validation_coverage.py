"""Tests for validation.py to improve coverage."""

import pytest
import json

from pydantic_schemaforms.validation import (
    ValidationResponse,
    ValidationRule,
    RequiredRule,
    EmailRule,
    MinLengthRule,
    MaxLengthRule,
    RegexRule,
    NumericRangeRule,
)


class TestValidationResponse:
    """Test ValidationResponse class."""

    def test_validation_response_valid(self):
        """Test ValidationResponse for valid field."""
        response = ValidationResponse(
            field_name="email",
            is_valid=True,
            value="user@example.com"
        )

        assert response.field_name == "email"
        assert response.is_valid is True
        assert response.value == "user@example.com"

    def test_validation_response_with_errors(self):
        """Test ValidationResponse with errors."""
        response = ValidationResponse(
            field_name="age",
            is_valid=False,
            errors=["Must be a number", "Must be at least 18"]
        )

        assert not response.is_valid
        assert len(response.errors) == 2

    def test_validation_response_to_dict(self):
        """Test ValidationResponse.to_dict()."""
        response = ValidationResponse(
            field_name="name",
            is_valid=True,
            value="John",
            warnings=["Name contains special characters"]
        )

        data = response.to_dict()

        assert data['field_name'] == 'name'
        assert data['is_valid'] is True
        assert data['value'] == 'John'
        assert len(data['warnings']) == 1

    def test_validation_response_to_json(self):
        """Test ValidationResponse.to_json()."""
        response = ValidationResponse(
            field_name="email",
            is_valid=False,
            errors=["Invalid format"]
        )

        json_str = response.to_json()
        data = json.loads(json_str)

        assert data['field_name'] == 'email'
        assert not data['is_valid']
        assert "Invalid format" in data['errors']

    def test_validation_response_with_suggestions(self):
        """Test ValidationResponse with suggestions."""
        response = ValidationResponse(
            field_name="zip",
            is_valid=False,
            errors=["Invalid ZIP code"],
            suggestions=["Did you mean 12345?", "Did you mean 54321?"]
        )

        assert len(response.suggestions) == 2


class TestValidationRules:
    """Test validation rules."""

    def test_required_rule_valid(self):
        """Test RequiredRule with valid value."""
        rule = RequiredRule()
        is_valid, msg = rule.validate("John")

        assert is_valid is True

    def test_required_rule_empty_string(self):
        """Test RequiredRule with empty string."""
        rule = RequiredRule()
        is_valid, msg = rule.validate("")

        assert is_valid is False

    def test_required_rule_none(self):
        """Test RequiredRule with None."""
        rule = RequiredRule()
        is_valid, msg = rule.validate(None)

        assert is_valid is False

    def test_required_rule_custom_message(self):
        """Test RequiredRule with custom message."""
        rule = RequiredRule(message="Name is required")
        is_valid, msg = rule.validate("")

        assert "Name is required" in msg

    def test_required_rule_get_client_validation(self):
        """Test RequiredRule generates client-side validation."""
        rule = RequiredRule()
        js = rule.get_client_validation("username")

        assert len(js) > 0

    def test_required_rule_get_client_validation_empty(self):
        """Test ValidationRule without client_side flag."""
        rule = RequiredRule()
        rule.client_side = False
        js = rule.get_client_validation("field")

        assert js == ""

    def test_email_rule_valid(self):
        """Test EmailRule with valid email."""
        rule = EmailRule()
        is_valid, msg = rule.validate("user@example.com")

        assert is_valid is True

    def test_email_rule_invalid(self):
        """Test EmailRule with invalid email."""
        rule = EmailRule()
        is_valid, msg = rule.validate("not-an-email")

        assert is_valid is False

    def test_min_length_rule_valid(self):
        """Test MinLengthRule with valid length."""
        rule = MinLengthRule(min_length=3)
        is_valid, msg = rule.validate("hello")

        assert is_valid is True

    def test_min_length_rule_too_short(self):
        """Test MinLengthRule too short."""
        rule = MinLengthRule(min_length=5)
        is_valid, msg = rule.validate("hi")

        assert is_valid is False

    def test_max_length_rule_valid(self):
        """Test MaxLengthRule with valid length."""
        rule = MaxLengthRule(max_length=10)
        is_valid, msg = rule.validate("hello")

        assert is_valid is True

    def test_max_length_rule_too_long(self):
        """Test MaxLengthRule too long."""
        rule = MaxLengthRule(max_length=5)
        is_valid, msg = rule.validate("hello world")

        assert is_valid is False

    def test_pattern_rule_valid(self):
        """Test RegexRule with matching pattern."""
        rule = RegexRule(pattern=r'^\d{3}-\d{4}$')
        is_valid, msg = rule.validate("123-4567")

        assert is_valid is True

    def test_pattern_rule_invalid(self):
        """Test RegexRule with non-matching pattern."""
        rule = RegexRule(pattern=r'^\d+$')
        is_valid, msg = rule.validate("abc123")

        assert is_valid is False

    def test_min_rule_valid(self):
        """Test NumericRangeRule with valid number."""
        rule = NumericRangeRule(min_value=0)
        is_valid, msg = rule.validate(5)

        assert is_valid is True

    def test_min_rule_too_small(self):
        """Test NumericRangeRule with number too small."""
        rule = NumericRangeRule(min_value=10)
        is_valid, msg = rule.validate(5)

        assert is_valid is False

    def test_max_rule_valid(self):
        """Test NumericRangeRule with valid number."""
        rule = NumericRangeRule(max_value=100)
        is_valid, msg = rule.validate(50)

        assert is_valid is True

    def test_max_rule_too_large(self):
        """Test NumericRangeRule with number too large."""
        rule = NumericRangeRule(max_value=50)
        is_valid, msg = rule.validate(100)

        assert is_valid is False

    def test_numeric_rule_valid(self):
        """Test NumericRangeRule with numeric value."""
        rule = NumericRangeRule()
        is_valid, msg = rule.validate(123)

        assert is_valid is True

    def test_numeric_rule_invalid(self):
        """Test NumericRangeRule with non-numeric value."""
        rule = NumericRangeRule()
        is_valid, msg = rule.validate("abc")

        assert is_valid is False

    def test_validation_rule_base_not_implemented(self):
        """Test ValidationRule base class raises NotImplementedError."""
        rule = ValidationRule()

        with pytest.raises(NotImplementedError):
            rule.validate("value")

    def test_validation_rule_to_descriptor(self):
        """Test ValidationRule.to_descriptor()."""
        rule = RequiredRule(message="Custom message")
        descriptor = rule.to_descriptor()

        assert descriptor['type'] == 'required'
        assert descriptor['message'] == 'Custom message'
        assert 'client' in descriptor
