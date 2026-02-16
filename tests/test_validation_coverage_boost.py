from __future__ import annotations

from pydantic import Field, model_validator

from pydantic_schemaforms.schema_form import FormModel
from pydantic_schemaforms.validation import (
    CustomRule,
    DateRangeRule,
    FieldValidator,
    FormValidator,
    MaxLengthRule,
    MinLengthRule,
    NumericRangeRule,
    RegexRule,
    ValidationRule,
    create_email_validator,
    create_password_strength_validator,
    validate_form_data,
    CrossFieldRules,
)


def test_base_generate_js_validation_default_empty():
    assert ValidationRule()._generate_js_validation("field") == ""


def test_min_max_length_none_and_js_generation():
    min_rule = MinLengthRule(3)
    max_rule = MaxLengthRule(5)

    assert min_rule.validate(None) == (True, "")
    assert max_rule.validate(None) == (True, "")
    assert "value.length < 3" in min_rule.get_client_validation("name")
    assert "value.length > 5" in max_rule.get_client_validation("name")


def test_regex_empty_value_is_valid():
    rule = RegexRule(r"^a+$")
    assert rule.validate("") == (True, "")


def test_numeric_range_empty_and_no_check_js():
    rule = NumericRangeRule()
    assert rule.validate(None) == (True, "")
    assert rule.get_client_validation("age") == ""


def test_date_range_constructor_and_parse_errors_and_js_paths():
    rule = DateRangeRule()
    assert rule.message == "Invalid date"
    assert rule.get_client_validation("start_date") == ""

    max_only_rule = DateRangeRule(max_date="2024-12-31")
    js = max_only_rule.get_client_validation("start_date")
    assert "dateValue > new Date('2024-12-31')" in js

    try:
        DateRangeRule()._parse_date(123)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid date format" in str(exc)


def test_custom_rule_invalid_result_and_exception_branches():
    invalid_result_rule = CustomRule(lambda _v: "unexpected")
    is_valid, msg = invalid_result_rule.validate("value")
    assert is_valid is False
    assert msg == "Invalid validation result"

    exploding_rule = CustomRule(lambda _v: 1 / 0)
    is_valid, msg = exploding_rule.validate("value")
    assert is_valid is False
    assert msg.startswith("Validation error:")


def test_field_validator_helpers_and_no_client_js_branch():
    validator = (
        FieldValidator("contact")
        .phone()
        .date_range(min_date="2024-01-01", max_date="2024-12-31")
        .regex(r"^.*$")
        .custom(lambda _v: True)
    )

    schema = validator.to_schema()
    rule_types = {rule["type"] for rule in schema["rules"]}
    assert {"phone", "date_range", "regex", "custom"}.issubset(rule_types)
    js = validator.generate_client_validation()
    assert "function validateContact" in js

    custom_only = FieldValidator("only_custom").custom(lambda _v: True)
    assert custom_only.generate_client_validation() == ""


def test_form_validator_field_and_cross_field_errors():
    form_validator = FormValidator()
    form_validator.field("age").numeric_range(min_val=18)

    def cross_rule(data):
        return False, {"age": "cross age error", "name": "name mismatch"}

    form_validator.add_cross_field_rule(cross_rule)

    is_valid, errors = form_validator.validate({"age": 10, "name": "x"})
    assert is_valid is False
    assert "age" in errors and len(errors["age"]) >= 2
    assert "name" in errors


def test_cross_field_rules_password_confirmation_and_date_range_validation():
    password_rule = CrossFieldRules.password_confirmation()
    assert password_rule({"password": "abc", "confirm_password": "xyz"}) == (
        False,
        {"confirm_password": "Passwords do not match"},
    )
    assert password_rule({"password": "abc", "confirm_password": "abc"}) == (True, {})

    date_rule = CrossFieldRules.date_range_validation("start", "end")
    assert date_rule({"start": "2024-01-10", "end": "2024-01-09"}) == (
        False,
        {"end": "End date must be after start date"},
    )
    assert date_rule({"start": "not-a-date", "end": "2024-01-09"}) == (
        False,
        {"end": "Invalid date format"},
    )
    assert date_rule({"start": "2024-01-01", "end": "2024-01-02"}) == (True, {})


def test_email_and_password_factory_validators_edge_paths():
    email_validator = create_email_validator()
    response = email_validator("")
    assert response.is_valid is False
    assert response.errors == ["Email is required"]

    password_validator = create_password_strength_validator(min_length=4)
    response = password_validator("AAAA1111!")
    assert response.is_valid is True
    assert "lowercase" in " ".join(response.warnings).lower()


class _LayoutFieldModel(FormModel):
    layout_field: dict = Field(
        default_factory=lambda: {"layout": True},
        json_schema_extra={"ui_element": "layout"},
    )


class _CallableExtraModel(FormModel):
    name: str = Field(default="ok", json_schema_extra=lambda schema, _cls: schema.update({"x": 1}))


class _LeLengthModel(FormModel):
    small: int = Field(le=5)
    short: str = Field(min_length=3, max_length=4)


class _GeneralModelError(FormModel):
    x: int = Field(default=1)

    @model_validator(mode="after")
    def ensure_invalid(self):
        raise ValueError("model invalid")


def test_validate_form_data_layout_cleanup_and_non_dict_extra(monkeypatch):
    import pydantic_schemaforms.rendering.layout_engine as layout_engine

    monkeypatch.setattr(layout_engine, "get_nested_form_data", lambda *args, **kwargs: {})

    result = validate_form_data(_LayoutFieldModel, {})
    assert result.is_valid is True
    assert "layout_field" not in result.data

    callable_extra_result = validate_form_data(_CallableExtraModel, {"name": "ok"})
    assert callable_extra_result.is_valid is True
    assert callable_extra_result.data["name"] == "ok"


def test_validate_form_data_error_message_paths_and_general_and_exception():
    result = validate_form_data(_LeLengthModel, {"small": 10, "short": "x"})
    assert result.is_valid is False
    assert result.errors["small"] == "Must be 5 or less"
    assert result.errors["short"]

    max_length_result = validate_form_data(_LeLengthModel, {"small": 2, "short": "abcde"})
    assert max_length_result.is_valid is False
    assert max_length_result.errors["short"]

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
        {"loc": ("n",), "msg": "bad", "type": "less_than_equal", "ctx": {"le": 4}},
        {"loc": ("min_field",), "msg": "bad", "type": "min_length", "ctx": {"min_length": 3}},
        {"loc": ("max_field",), "msg": "bad", "type": "max_length", "ctx": {"max_length": 7}},
        {"loc": (), "msg": "general bad", "type": "value_error"},
    ]

    original_validation_error = validation_module.ValidationError
    try:
        validation_module.ValidationError = _FakeValidationError
        mapped_errors_result = validate_form_data(_RaisesFakeValidationError(fake_payload), {})
    finally:
        validation_module.ValidationError = original_validation_error

    assert mapped_errors_result.is_valid is False
    assert mapped_errors_result.errors["n"] == "Must be 4 or less"
    assert mapped_errors_result.errors["min_field"] == "Must be at least 3 characters"
    assert mapped_errors_result.errors["max_field"] == "Must be no more than 7 characters"
    assert mapped_errors_result.errors["general"] == "general bad"

    general_result = validate_form_data(_GeneralModelError, {"x": 1})
    assert general_result.is_valid is False
    assert "general" in general_result.errors

    class _ExplodingRuntimeProvider:
        @staticmethod
        def get_runtime_model():
            def _explode(**_kwargs):
                raise RuntimeError("boom")

            return _explode

    exception_result = validate_form_data(_ExplodingRuntimeProvider, {})
    assert exception_result.is_valid is False
    assert exception_result.errors == {"general": "boom"}
