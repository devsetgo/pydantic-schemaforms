from pydantic_forms.live_validation import LiveValidator
from pydantic_forms.validation import FieldValidator, ValidationSchema


def test_field_validator_schema_descriptors():
    validator = FieldValidator("username").required().min_length(3)

    schema = validator.to_schema()
    rule_types = {rule["type"] for rule in schema["rules"]}

    assert schema["field"] == "username"
    assert rule_types == {"required", "min_length"}
    min_length_rule = next(rule for rule in schema["rules"] if rule["type"] == "min_length")
    assert min_length_rule["min_length"] == 3


def test_validation_schema_registration_and_live_execution():
    age_validator = FieldValidator("age").required().numeric_range(min_val=18)
    email_validator = FieldValidator("email").required().email()

    schema = ValidationSchema().add_field(age_validator).add_field(email_validator)
    assert set(schema.to_dict().keys()) == {"age", "email"}

    live_validator = schema.build_live_validator()

    underage_response = live_validator.validate_field("age", "12")
    assert not underage_response.is_valid
    assert "Must be" in underage_response.errors[0]

    adult_response = live_validator.validate_field("age", "32")
    assert adult_response.is_valid

    invalid_email = live_validator.validate_field("email", "invalid")
    assert not invalid_email.is_valid
    assert any("valid email" in msg.lower() for msg in invalid_email.errors)

    valid_email = live_validator.validate_field("email", "user@example.com")
    assert valid_email.is_valid


def test_live_validator_direct_field_registration():
    validator = FieldValidator("code").required().min_length(4)
    live_validator = LiveValidator()
    live_validator.register_field_validator(validator)

    assert "rules" in live_validator.field_configs["code"]
    rule_types = {rule["type"] for rule in live_validator.field_configs["code"]["rules"]}
    assert rule_types == {"required", "min_length"}

    response = live_validator.validate_field("code", "abc")
    assert not response.is_valid
    assert response.errors

    assert live_validator.validate_field("code", "abcd").is_valid
