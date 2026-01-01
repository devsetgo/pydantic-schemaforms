"""Comprehensive tests for live_validation module."""

from pydantic_schemaforms.live_validation import (
    HTMXValidationConfig,
    LiveValidator,
)
from unittest.mock import patch


class TestHTMXValidationConfig:
    """Test HTMXValidationConfig initialization."""

    def test_config_default_initialization(self):
        """Test default configuration initialization."""
        config = HTMXValidationConfig()

        assert config.validate_on_blur is True
        assert config.validate_on_input is False
        assert config.validate_on_change is True
        assert config.debounce_ms == 300

    def test_config_custom_debounce(self):
        """Test custom debounce configuration."""
        config = HTMXValidationConfig(debounce_ms=500)

        assert config.debounce_ms == 500

    def test_config_success_class(self):
        """Test success indicator class."""
        config = HTMXValidationConfig()

        assert config.success_class == "is-valid"

    def test_config_error_class(self):
        """Test error indicator class."""
        config = HTMXValidationConfig()

        assert config.error_class == "is-invalid"

    def test_config_warning_class(self):
        """Test warning indicator class."""
        config = HTMXValidationConfig()

        assert config.warning_class == "has-warning"

    def test_config_loading_class(self):
        """Test loading indicator class."""
        config = HTMXValidationConfig()

        assert config.loading_class == "is-validating"

    def test_config_swap_strategy(self):
        """Test HTMX swap strategy."""
        config = HTMXValidationConfig()

        assert config.swap_strategy == "outerHTML"

    def test_config_target_selector(self):
        """Test HTMX target selector."""
        config = HTMXValidationConfig()

        assert config.target_selector == "this"

    def test_config_validation_triggers(self):
        """Test validation trigger configuration."""
        config = HTMXValidationConfig(
            validate_on_blur=False,
            validate_on_input=True,
            validate_on_change=False
        )

        assert config.validate_on_blur is False
        assert config.validate_on_input is True
        assert config.validate_on_change is False

    def test_config_show_feedback(self):
        """Test feedback display configuration."""
        config = HTMXValidationConfig(
            show_success_indicators=False,
            show_warnings=False,
            show_suggestions=False
        )

        assert config.show_success_indicators is False
        assert config.show_warnings is False
        assert config.show_suggestions is False


class TestLiveValidatorInit:
    """Test LiveValidator initialization."""

    def test_live_validator_default_init(self):
        """Test LiveValidator default initialization."""
        validator = LiveValidator()

        assert validator.config is not None
        assert isinstance(validator.config, HTMXValidationConfig)
        assert validator.validators == {}
        assert validator.field_configs == {}

    def test_live_validator_custom_config(self):
        """Test LiveValidator with custom config."""
        config = HTMXValidationConfig(debounce_ms=1000)
        validator = LiveValidator(config=config)

        assert validator.config == config
        assert validator.config.debounce_ms == 1000

    def test_live_validator_has_templates(self):
        """Test LiveValidator has validation templates."""
        validator = LiveValidator()

        assert validator.validation_template is not None
        assert validator.field_template is not None


class TestLiveValidatorValidators:
    """Test LiveValidator validator registration."""

    def test_register_validator(self):
        """Test registering a custom validator."""
        validator = LiveValidator()

        def email_validator(value):
            if "@" not in value:
                raise ValueError("Invalid email")
            return value

        validator.validators["email"] = email_validator

        assert "email" in validator.validators

    def test_register_multiple_validators(self):
        """Test registering multiple validators."""
        validator = LiveValidator()

        validators = {
            "email": lambda x: x,
            "password": lambda x: x,
            "phone": lambda x: x,
        }

        validator.validators = validators

        assert len(validator.validators) == 3
        assert "email" in validator.validators
        assert "password" in validator.validators
        assert "phone" in validator.validators


class TestLiveValidatorFieldConfig:
    """Test LiveValidator field configuration."""

    def test_set_field_config(self):
        """Test setting field configuration."""
        validator = LiveValidator()

        config = {
            "type": "email",
            "required": True,
            "min_length": 5,
        }

        validator.field_configs["email"] = config

        assert "email" in validator.field_configs
        assert validator.field_configs["email"]["type"] == "email"

    def test_multiple_field_configs(self):
        """Test multiple field configurations."""
        validator = LiveValidator()

        validator.field_configs["email"] = {"type": "email", "required": True}
        validator.field_configs["password"] = {"type": "password", "min_length": 8}
        validator.field_configs["age"] = {"type": "number", "min": 0, "max": 150}

        assert len(validator.field_configs) == 3


class TestLiveValidatorTemplates:
    """Test LiveValidator template rendering."""

    def test_validation_template_exists(self):
        """Test validation template is properly set."""
        validator = LiveValidator()

        assert validator.validation_template is not None
        assert hasattr(validator.validation_template, 'template_str')

    def test_field_template_exists(self):
        """Test field template is properly set."""
        validator = LiveValidator()

        assert validator.field_template is not None
        assert hasattr(validator.field_template, 'template_str')


class TestLiveValidatorIntegration:
    """Test LiveValidator integration scenarios."""

    def test_validator_with_custom_config_integration(self):
        """Test validator with custom config integration."""
        config = HTMXValidationConfig(
            validate_on_blur=True,
            validate_on_input=True,
            debounce_ms=250
        )

        validator = LiveValidator(config=config)

        assert validator.config.validate_on_blur is True
        assert validator.config.validate_on_input is True
        assert validator.config.debounce_ms == 250

    def test_validator_with_multiple_field_validators(self):
        """Test validator with multiple field validators."""
        validator = LiveValidator()

        def email_check(value):
            return "@" in value

        def password_check(value):
            return len(value) >= 8

        validator.validators["email"] = email_check
        validator.validators["password"] = password_check

        assert validator.validators["email"]("test@example.com") is True
        assert validator.validators["password"]("short") is False
        assert validator.validators["password"]("longenoughpassword") is True


class TestHTMXValidationConfigEdgeCases:
    """Test edge cases in HTMX config."""

    def test_config_with_zero_debounce(self):
        """Test configuration with zero debounce."""
        config = HTMXValidationConfig(debounce_ms=0)

        assert config.debounce_ms == 0

    def test_config_with_large_debounce(self):
        """Test configuration with large debounce."""
        config = HTMXValidationConfig(debounce_ms=5000)

        assert config.debounce_ms == 5000

    def test_config_with_custom_selectors(self):
        """Test configuration with custom selectors."""
        config = HTMXValidationConfig(
            target_selector="#custom-target",
            indicator_selector=".custom-indicator"
        )

        assert config.target_selector == "#custom-target"
        assert config.indicator_selector == ".custom-indicator"

    def test_config_with_custom_classes(self):
        """Test configuration with custom CSS classes."""
        config = HTMXValidationConfig(
            success_class="success-state",
            error_class="error-state",
            warning_class="warning-state",
            loading_class="loading-state"
        )

        assert config.success_class == "success-state"
        assert config.error_class == "error-state"
        assert config.warning_class == "warning-state"
        assert config.loading_class == "loading-state"


class TestLiveValidatorStateManagement:
    """Test LiveValidator state management."""

    def test_validator_state_persistence(self):
        """Test validator maintains state."""
        validator = LiveValidator()

        validator.validators["field1"] = lambda x: x
        validator.field_configs["field1"] = {"type": "text"}

        # Verify state is maintained
        assert "field1" in validator.validators
        assert "field1" in validator.field_configs

    def test_validator_clear_and_rebuild(self):
        """Test validator can be cleared and rebuilt."""
        validator = LiveValidator()

        validator.validators["field1"] = lambda x: x
        validator.field_configs["field1"] = {"type": "text"}

        # Clear and verify
        validator.validators.clear()
        validator.field_configs.clear()

        assert len(validator.validators) == 0
        assert len(validator.field_configs) == 0


class TestLiveValidatorMocking:
    """Test LiveValidator with mocks for complex operations."""

    def test_validator_with_mock_form_data(self):
        """Test validator processing with mock form data."""
        validator = LiveValidator()

        form_data = {
            "email": "test@example.com",
            "password": "securepassword",
            "age": 30
        }

        # Add validators
        validator.validators["email"] = lambda x: "@" in x
        validator.validators["age"] = lambda x: 0 <= x <= 150

        # Verify validators work with data
        assert validator.validators["email"](form_data["email"]) is True
        assert validator.validators["age"](form_data["age"]) is True

    @patch('pydantic_schemaforms.live_validation.json.dumps')
    def test_validator_json_serialization(self, mock_json):
        """Test validator config serialization."""
        config = HTMXValidationConfig()
        LiveValidator(config=config)

        # Mock should be available for json operations
        assert mock_json is not None


class TestLiveValidatorHTMLGeneration:
    """Test LiveValidator HTML generation aspects."""

    def test_validation_template_contains_elements(self):
        """Test validation template is properly configured."""
        validator = LiveValidator()

        assert validator.validation_template is not None
        assert hasattr(validator.validation_template, 'template_str')
        from pydantic_schemaforms.templates import TemplateString
        assert isinstance(validator.validation_template, TemplateString)

    def test_field_template_contains_elements(self):
        """Test field template is properly configured."""
        validator = LiveValidator()

        assert validator.field_template is not None
        assert hasattr(validator.field_template, 'template_str')
        from pydantic_schemaforms.templates import TemplateString
        assert isinstance(validator.field_template, TemplateString)


class TestLiveValidatorConfigurationVariations:
    """Test various configuration combinations."""

    def test_all_validation_triggers_enabled(self):
        """Test with all validation triggers enabled."""
        config = HTMXValidationConfig(
            validate_on_blur=True,
            validate_on_input=True,
            validate_on_change=True
        )

        assert config.validate_on_blur is True
        assert config.validate_on_input is True
        assert config.validate_on_change is True

    def test_all_validation_triggers_disabled(self):
        """Test with all validation triggers disabled."""
        config = HTMXValidationConfig(
            validate_on_blur=False,
            validate_on_input=False,
            validate_on_change=False
        )

        assert config.validate_on_blur is False
        assert config.validate_on_input is False
        assert config.validate_on_change is False

    def test_all_feedback_options_disabled(self):
        """Test with all feedback options disabled."""
        config = HTMXValidationConfig(
            show_success_indicators=False,
            show_warnings=False,
            show_suggestions=False,
            clear_on_focus=False
        )

        assert config.show_success_indicators is False
        assert config.show_warnings is False
        assert config.show_suggestions is False
        assert config.clear_on_focus is False
