"""
Test suite for consolidated validation engine.

This verifies that the validation system works correctly with both
synchronous validation and live HTMX validation using a single rule set.
"""

import pytest

from pydantic_forms.live_validation import LiveValidator, ValidationResponse
from pydantic_forms.validation import (
    create_email_validator,
    create_password_strength_validator,
    FieldValidator,
    ValidationSchema,
)


class TestConsolidatedValidationEngine:
    """Test the consolidated validation engine."""

    def test_validation_response_in_validation_module(self):
        """ValidationResponse should be exported from validation.py."""
        from pydantic_forms.validation import ValidationResponse as VR

        response = VR(field_name="test", is_valid=True)
        assert response.field_name == "test"
        assert response.is_valid is True

    def test_validation_response_in_live_validation_module(self):
        """ValidationResponse should be accessible from live_validation.py."""
        response = ValidationResponse(field_name="test", is_valid=True)
        assert response.field_name == "test"
        assert response.is_valid is True

    def test_email_validator_from_validation_module(self):
        """Email validator should be in validation.py."""
        validator = create_email_validator()
        
        invalid = validator("notanemail")
        assert not invalid.is_valid
        assert "valid email" in invalid.errors[0].lower()
        
        valid = validator("user@example.com")
        assert valid.is_valid
        assert valid.formatted_value == "user@example.com"

    def test_password_validator_from_validation_module(self):
        """Password validator should be in validation.py."""
        validator = create_password_strength_validator(min_length=8)
        
        weak = validator("weak")
        assert not weak.is_valid
        assert len(weak.errors) > 0
        
        strong = validator("SecureP@ss123")
        assert strong.is_valid

    def test_email_validator_from_live_validation_module(self):
        """Email validator should be accessible from live_validation.py."""
        from pydantic_forms.live_validation import (
            create_email_validator as live_create_email,
        )

        validator = live_create_email()
        valid = validator("user@example.com")
        assert valid.is_valid

    def test_field_validator_with_live_registration(self):
        """FieldValidator should work with LiveValidator registration."""
        field_validator = FieldValidator("username").required().min_length(3)
        
        live_validator = LiveValidator()
        live_validator.register_field_validator(field_validator)
        
        # Test invalid value
        response = live_validator.validate_field("username", "ab")
        assert not response.is_valid
        
        # Test valid value
        response = live_validator.validate_field("username", "john")
        assert response.is_valid

    def test_validation_schema_build_live_validator(self):
        """ValidationSchema.build_live_validator() should create working LiveValidator."""
        schema = ValidationSchema()
        schema.add_field(FieldValidator("email").required().email())
        schema.add_field(
            FieldValidator("password").required().min_length(8)
        )
        
        live_validator = schema.build_live_validator()
        
        # Email validation
        invalid_email = live_validator.validate_field("email", "notanemail")
        assert not invalid_email.is_valid
        
        valid_email = live_validator.validate_field("email", "user@example.com")
        assert valid_email.is_valid
        
        # Password validation
        weak_password = live_validator.validate_field("password", "short")
        assert not weak_password.is_valid
        
        strong_password = live_validator.validate_field("password", "LongPassword123")
        assert strong_password.is_valid

    def test_validation_response_serialization(self):
        """ValidationResponse should serialize to JSON."""
        response = ValidationResponse(
            field_name="email",
            is_valid=False,
            errors=["Invalid email"],
            warnings=["No MX record found"],
            suggestions=["Check spelling"],
        )
        
        json_str = response.to_json()
        assert '"field_name": "email"' in json_str
        assert '"is_valid": false' in json_str
        
        dict_data = response.to_dict()
        assert dict_data["field_name"] == "email"
        assert not dict_data["is_valid"]
        assert "Invalid email" in dict_data["errors"]

    def test_cross_framework_consistency(self):
        """Same validation rules should work in both validation and live_validation."""
        # Define rules in validation module
        field_validator = (
            FieldValidator("username")
            .required()
            .min_length(3)
            .max_length(20)
        )
        
        # Get validation response
        is_valid, errors = field_validator.validate("a")
        assert not is_valid
        assert any("at least 3" in e.lower() for e in errors)
        
        # Same rules in LiveValidator
        live = LiveValidator()
        live.register_field_validator(field_validator)
        
        response = live.validate_field("username", "a")
        assert not response.is_valid
        assert any("at least 3" in e.lower() for e in response.errors)

    def test_field_validator_schema_to_live_validator_flow(self):
        """Test complete flow: FieldValidator -> ValidationSchema -> LiveValidator."""
        # Build schema
        schema = ValidationSchema()
        schema.add_field(
            FieldValidator("email")
            .required()
            .email()
        )
        schema.add_field(
            FieldValidator("username")
            .required()
            .min_length(3)
            .max_length(20)
        )
        
        # Get descriptors
        schema_dict = schema.to_dict()
        assert "email" in schema_dict
        assert "username" in schema_dict
        
        # Build live validator
        live_validator = schema.build_live_validator()
        
        # Verify field configs populated
        assert "email" in live_validator.field_configs
        assert "username" in live_validator.field_configs
        
        # Validate through live validator
        email_response = live_validator.validate_field("email", "invalid")
        assert not email_response.is_valid
        
        username_response = live_validator.validate_field("username", "ab")
        assert not username_response.is_valid
