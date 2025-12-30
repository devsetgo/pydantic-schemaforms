"""Extended validation tests for harder-to-test validation rules."""

from datetime import date

from pydantic_forms.validation import (
    PhoneRule,
    DateRangeRule,
    CustomRule,
)


class TestPhoneRule:
    """Test PhoneRule validation."""

    def test_phone_rule_valid_us_format(self):
        """Test PhoneRule with standard US format."""
        rule = PhoneRule()
        is_valid, msg = rule.validate("555-123-4567")
        assert is_valid is True

    def test_phone_rule_valid_with_plus(self):
        """Test PhoneRule with international prefix."""
        rule = PhoneRule()
        is_valid, msg = rule.validate("+1 (555) 123-4567")
        assert is_valid is True

    def test_phone_rule_valid_digits_only(self):
        """Test PhoneRule with digits only."""
        rule = PhoneRule()
        is_valid, msg = rule.validate("5551234567")
        assert is_valid is True

    def test_phone_rule_invalid_too_short(self):
        """Test PhoneRule with too short number."""
        rule = PhoneRule()
        is_valid, msg = rule.validate("123")
        assert is_valid is False

    def test_phone_rule_invalid_format(self):
        """Test PhoneRule with invalid format."""
        rule = PhoneRule()
        is_valid, msg = rule.validate("not-a-phone")
        assert is_valid is False

    def test_phone_rule_descriptor(self):
        """Test PhoneRule descriptor."""
        rule = PhoneRule()
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'phone'


class TestDateRangeRule:
    """Test DateRangeRule validation."""

    def test_date_range_min_date_valid(self):
        """Test DateRangeRule with valid date after min."""
        rule = DateRangeRule(min_date="2000-01-01")
        is_valid, msg = rule.validate("2020-06-15")
        assert is_valid is True

    def test_date_range_min_date_invalid(self):
        """Test DateRangeRule with date before min."""
        rule = DateRangeRule(min_date="2000-01-01")
        is_valid, msg = rule.validate("1999-12-31")
        assert is_valid is False

    def test_date_range_max_date_valid(self):
        """Test DateRangeRule with valid date before max."""
        rule = DateRangeRule(max_date="2025-12-31")
        is_valid, msg = rule.validate("2020-06-15")
        assert is_valid is True

    def test_date_range_max_date_invalid(self):
        """Test DateRangeRule with date after max."""
        rule = DateRangeRule(max_date="2025-12-31")
        is_valid, msg = rule.validate("2026-01-01")
        assert is_valid is False

    def test_date_range_both_bounds_valid(self):
        """Test DateRangeRule with date between min and max."""
        rule = DateRangeRule(min_date="2000-01-01", max_date="2025-12-31")
        is_valid, msg = rule.validate("2020-06-15")
        assert is_valid is True

    def test_date_range_both_bounds_below_min(self):
        """Test DateRangeRule with date before both bounds."""
        rule = DateRangeRule(min_date="2000-01-01", max_date="2025-12-31")
        is_valid, msg = rule.validate("1999-12-31")
        assert is_valid is False

    def test_date_range_both_bounds_above_max(self):
        """Test DateRangeRule with date after both bounds."""
        rule = DateRangeRule(min_date="2000-01-01", max_date="2025-12-31")
        is_valid, msg = rule.validate("2026-01-01")
        assert is_valid is False

    def test_date_range_empty_value(self):
        """Test DateRangeRule with empty value."""
        rule = DateRangeRule(min_date="2000-01-01")
        is_valid, msg = rule.validate("")
        assert is_valid is True

    def test_date_range_none_value(self):
        """Test DateRangeRule with None value."""
        rule = DateRangeRule(min_date="2000-01-01")
        is_valid, msg = rule.validate(None)
        assert is_valid is True

    def test_date_range_date_object(self):
        """Test DateRangeRule with date object."""
        rule = DateRangeRule(min_date=date(2000, 1, 1))
        is_valid, msg = rule.validate(date(2020, 6, 15))
        assert is_valid is True

    def test_date_range_invalid_format(self):
        """Test DateRangeRule with invalid date format."""
        rule = DateRangeRule(min_date="2000-01-01")
        is_valid, msg = rule.validate("not-a-date")
        assert is_valid is False

    def test_date_range_wrong_type(self):
        """Test DateRangeRule with wrong type value."""
        rule = DateRangeRule(min_date="2000-01-01")
        is_valid, msg = rule.validate(12345)
        assert is_valid is False

    def test_date_range_custom_message(self):
        """Test DateRangeRule with custom message."""
        rule = DateRangeRule(
            min_date="2000-01-01",
            message="Date is too old"
        )
        is_valid, msg = rule.validate("1999-12-31")
        assert "too old" in msg

    def test_date_range_descriptor_with_dates(self):
        """Test DateRangeRule descriptor."""
        rule = DateRangeRule(min_date="2000-01-01", max_date="2025-12-31")
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'date_range'
        assert descriptor['min_date'] == '2000-01-01'
        assert descriptor['max_date'] == '2025-12-31'

    def test_date_range_descriptor_min_only(self):
        """Test DateRangeRule descriptor with min only."""
        rule = DateRangeRule(min_date="2000-01-01")
        descriptor = rule.to_descriptor()
        assert descriptor['min_date'] == '2000-01-01'
        assert descriptor['max_date'] is None


class TestCustomRule:
    """Test CustomRule validation."""

    def test_custom_rule_bool_return(self):
        """Test CustomRule with boolean return value."""
        def is_even(value):
            try:
                return int(value) % 2 == 0
            except (ValueError, TypeError):
                return False

        rule = CustomRule(is_even, message="Must be even")
        is_valid, msg = rule.validate(4)
        assert is_valid is True

    def test_custom_rule_bool_return_false(self):
        """Test CustomRule returns False."""
        def is_even(value):
            try:
                return int(value) % 2 == 0
            except (ValueError, TypeError):
                return False

        rule = CustomRule(is_even, message="Must be even")
        is_valid, msg = rule.validate(3)
        assert is_valid is False
        assert "even" in msg

    def test_custom_rule_tuple_return_valid(self):
        """Test CustomRule with tuple return (valid)."""
        def validate_password(value):
            if len(value) < 8:
                return False, "Password must be at least 8 characters"
            return True, ""

        rule = CustomRule(validate_password)
        is_valid, msg = rule.validate("MySecure123!")
        assert is_valid is True

    def test_custom_rule_tuple_return_invalid(self):
        """Test CustomRule with tuple return (invalid)."""
        def validate_password(value):
            if len(value) < 8:
                return False, "Password must be at least 8 characters"
            return True, ""

        rule = CustomRule(validate_password)
        is_valid, msg = rule.validate("short")
        assert is_valid is False
        assert "at least 8" in msg

    def test_custom_rule_complex_validation(self):
        """Test CustomRule with complex validation logic."""
        def validate_username(value):
            if not isinstance(value, str):
                return False, "Username must be a string"
            if len(value) < 3:
                return False, "Username must be at least 3 characters"
            if not value[0].isalpha():
                return False, "Username must start with a letter"
            if not all(c.isalnum() or c == '_' for c in value):
                return False, "Username can only contain letters, numbers, and underscores"
            return True, ""

        rule = CustomRule(validate_username)

        # Valid
        assert rule.validate("valid_user")[0] is True

        # Invalid: too short
        assert rule.validate("ab")[0] is False

        # Invalid: starts with number
        assert rule.validate("1user")[0] is False

    def test_custom_rule_no_client_side(self):
        """Test CustomRule without client-side validation."""
        def always_false(value):
            return False

        rule = CustomRule(always_false, client_side=False)
        js = rule.get_client_validation("field")
        assert js == ""

    def test_custom_rule_descriptor(self):
        """Test CustomRule descriptor."""
        def dummy_validator(value):
            return True

        rule = CustomRule(dummy_validator, message="Custom error")
        descriptor = rule.to_descriptor()
        assert descriptor['type'] == 'custom'
        assert descriptor['message'] == 'Custom error'


class TestNumericRangeRuleAdvanced:
    """Advanced tests for NumericRangeRule."""

    def test_numeric_range_with_float_values(self):
        """Test NumericRangeRule with float values."""
        from pydantic_forms.validation import NumericRangeRule

        rule = NumericRangeRule(min_value=0.5, max_value=99.99)

        assert rule.validate(50.0)[0] is True
        assert rule.validate(0.49)[0] is False
        assert rule.validate(100.0)[0] is False

    def test_numeric_range_string_conversion(self):
        """Test NumericRangeRule converts string numbers."""
        from pydantic_forms.validation import NumericRangeRule

        rule = NumericRangeRule(min_value=0, max_value=100)

        assert rule.validate("50")[0] is True
        assert rule.validate("150")[0] is False

    def test_numeric_range_negative_values(self):
        """Test NumericRangeRule with negative values."""
        from pydantic_forms.validation import NumericRangeRule

        rule = NumericRangeRule(min_value=-100, max_value=-10)

        assert rule.validate(-50)[0] is True
        assert rule.validate(-5)[0] is False
        assert rule.validate(50)[0] is False
