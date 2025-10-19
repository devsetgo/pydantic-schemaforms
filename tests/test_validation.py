"""
Tests for validation module - form validation and error handling.
"""

import pytest
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import ValidationError, validator, field_validator, EmailStr
from pydantic_forms.schema_form import FormModel, Field
from pydantic_forms.validation import validate_form_data, ValidationResult


class TestValidationBasics:
    """Test basic validation functionality."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        # Test successful validation
        result = ValidationResult(is_valid=True, data={"name": "John"})
        assert result.is_valid is True
        assert result.data == {"name": "John"}
        assert result.errors == {}
        
        # Test failed validation
        errors = {"email": "Invalid email format"}
        result = ValidationResult(is_valid=False, errors=errors)
        assert result.is_valid is False
        assert result.errors == errors
        assert result.data == {}
    
    def test_validate_form_data_success(self, simple_form_model, sample_form_data):
        """Test successful form data validation."""
        result = validate_form_data(simple_form_model, sample_form_data)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.errors == {}
        assert result.data is not None
        
        # Check that data contains expected fields
        assert "name" in result.data
        assert "email" in result.data
        assert result.data["name"] == sample_form_data["name"]
    
    def test_validate_form_data_failure(self, simple_form_model):
        """Test form data validation failure."""
        invalid_data = {
            "name": "",  # Required field empty
            "email": "invalid-email",  # Invalid email format
            "age": 15  # Below minimum age
        }
        
        result = validate_form_data(simple_form_model, invalid_data)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.data == {}
        
        # Should have errors for multiple fields
        error_fields = list(result.errors.keys())
        assert "name" in error_fields or "email" in error_fields or "age" in error_fields
    
    def test_validate_form_data_partial_failure(self, simple_form_model):
        """Test form data validation with some valid, some invalid fields."""
        mixed_data = {
            "name": "John Doe",  # Valid
            "email": "invalid-email",  # Invalid
            "age": 25,  # Valid
            "newsletter": True  # Valid
        }
        
        result = validate_form_data(simple_form_model, mixed_data)
        
        assert result.is_valid is False
        assert "email" in result.errors
        assert len(result.errors) == 1  # Only email should fail


class TestFormModelValidation:
    """Test validation features built into FormModel."""
    
    def test_required_field_validation(self):
        """Test validation of required fields."""
        class TestForm(FormModel):
            name: str = Field(..., description="Required name field")
            email: str = Field(..., ui_element="email")
            optional_field: str = Field("", description="Optional field")
        
        # Test missing required field
        with pytest.raises(ValidationError) as exc_info:
            TestForm(email="test@example.com", optional_field="test")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("name",) for err in errors)
        
        # Test with all required fields
        form = TestForm(name="John", email="test@example.com")
        assert form.name == "John"
        assert form.email == "test@example.com"
        assert form.optional_field == ""
    
    def test_email_field_validation(self):
        """Test email field validation."""
        class EmailForm(FormModel):
            email: EmailStr = Field(..., ui_element="email")
        
        # Test valid email
        form = EmailForm(email="user@example.com")
        assert form.email == "user@example.com"
        
        # Test invalid email
        with pytest.raises(ValidationError) as exc_info:
            EmailForm(email="invalid-email")
        
        errors = exc_info.value.errors()
        assert any("email" in str(err).lower() for err in errors)
    
    def test_numeric_field_validation(self):
        """Test numeric field validation with constraints."""
        class NumericForm(FormModel):
            age: int = Field(..., ge=18, le=120, description="Age between 18 and 120")
            rating: float = Field(..., ge=0.0, le=5.0, description="Rating 0-5")
            count: int = Field(..., gt=0, description="Positive count")
        
        # Test valid values
        form = NumericForm(age=25, rating=4.5, count=10)
        assert form.age == 25
        assert form.rating == 4.5
        assert form.count == 10
        
        # Test age too low
        with pytest.raises(ValidationError):
            NumericForm(age=15, rating=4.5, count=10)
        
        # Test age too high
        with pytest.raises(ValidationError):
            NumericForm(age=150, rating=4.5, count=10)
        
        # Test rating out of range
        with pytest.raises(ValidationError):
            NumericForm(age=25, rating=6.0, count=10)
        
        # Test count not positive
        with pytest.raises(ValidationError):
            NumericForm(age=25, rating=4.5, count=0)
    
    def test_string_length_validation(self):
        """Test string length validation."""
        class StringForm(FormModel):
            short_text: str = Field(..., min_length=2, max_length=10)
            long_text: str = Field(..., min_length=10)
        
        # Test valid strings
        form = StringForm(short_text="hello", long_text="this is a long text field")
        assert form.short_text == "hello"
        
        # Test short_text too short
        with pytest.raises(ValidationError):
            StringForm(short_text="a", long_text="this is long enough")
        
        # Test short_text too long
        with pytest.raises(ValidationError):
            StringForm(short_text="this is way too long", long_text="this is long enough")
        
        # Test long_text too short
        with pytest.raises(ValidationError):
            StringForm(short_text="hello", long_text="short")
    
    def test_custom_validator_functions(self):
        """Test custom validator functions."""
        class CustomValidationForm(FormModel):
            username: str = Field(..., description="Username")
            password: str = Field(..., ui_element="password")
            confirm_password: str = Field(..., ui_element="password")
            
            @field_validator('username')
            @classmethod
            def validate_username(cls, v):
                if len(v) < 3:
                    raise ValueError("Username must be at least 3 characters")
                if not v.isalnum():
                    raise ValueError("Username must contain only letters and numbers")
                return v
            
            @field_validator('password')
            @classmethod
            def validate_password(cls, v):
                if len(v) < 8:
                    raise ValueError("Password must be at least 8 characters")
                if not any(c.isupper() for c in v):
                    raise ValueError("Password must contain at least one uppercase letter")
                if not any(c.isdigit() for c in v):
                    raise ValueError("Password must contain at least one digit")
                return v
            
            def validate_passwords_match(self):
                """Custom method to validate password confirmation."""
                if self.password != self.confirm_password:
                    raise ValueError("Passwords do not match")
                return self
        
        # Test valid data
        form = CustomValidationForm(
            username="user123",
            password="Password123",
            confirm_password="Password123"
        )
        assert form.username == "user123"
        
        # Test invalid username (too short)
        with pytest.raises(ValidationError):
            CustomValidationForm(
                username="ab",
                password="Password123",
                confirm_password="Password123"
            )
        
        # Test invalid username (special characters)
        with pytest.raises(ValidationError):
            CustomValidationForm(
                username="user@123",
                password="Password123",
                confirm_password="Password123"
            )
        
        # Test invalid password (too short)
        with pytest.raises(ValidationError):
            CustomValidationForm(
                username="user123",
                password="Pass1",
                confirm_password="Pass1"
            )
        
        # Test invalid password (no uppercase)
        with pytest.raises(ValidationError):
            CustomValidationForm(
                username="user123",
                password="password123",
                confirm_password="password123"
            )
        
        # Test invalid password (no digit)
        with pytest.raises(ValidationError):
            CustomValidationForm(
                username="user123",
                password="Password",
                confirm_password="Password"
            )


class TestValidationErrorHandling:
    """Test validation error handling and formatting."""
    
    def test_validation_error_extraction(self, simple_form_model):
        """Test extraction of validation errors from Pydantic ValidationError."""
        invalid_data = {
            "name": "",
            "email": "invalid-email",
            "age": 15
        }
        
        result = validate_form_data(simple_form_model, invalid_data)
        
        assert not result.is_valid
        assert isinstance(result.errors, dict)
        
        # Errors should be field-name keyed
        for field_name, error_message in result.errors.items():
            assert isinstance(field_name, str)
            assert isinstance(error_message, str)
            assert len(error_message) > 0
    
    def test_multiple_errors_same_field(self):
        """Test handling multiple validation errors for the same field."""
        class MultiErrorForm(FormModel):
            text: str = Field(..., min_length=5, max_length=10)
        
        # This should violate min_length
        result = validate_form_data(MultiErrorForm, {"text": "ab"})
        
        assert not result.is_valid
        assert "text" in result.errors
        assert "at least" in result.errors["text"] or "minimum" in result.errors["text"]
    
    def test_nested_validation_errors(self):
        """Test validation errors with nested data structures."""
        class NestedForm(FormModel):
            user_info: dict = Field(..., description="User information")
            tags: List[str] = Field([], description="User tags")
        
        invalid_data = {
            "user_info": "not a dict",  # Should be dict
            "tags": "not a list"       # Should be list
        }
        
        result = validate_form_data(NestedForm, invalid_data)
        
        assert not result.is_valid
        # Should have errors for type mismatches
        assert len(result.errors) > 0
    
    def test_error_message_formatting(self, simple_form_model):
        """Test that error messages are properly formatted."""
        invalid_data = {"name": "", "email": "bad-email", "age": 200}
        
        result = validate_form_data(simple_form_model, invalid_data)
        
        for field_name, error_message in result.errors.items():
            # Error messages should be human-readable
            assert len(error_message) > 10
            assert not error_message.startswith("ValidationError")
            # Should not contain internal Pydantic error codes
            assert "type=" not in error_message


class TestValidationIntegration:
    """Test validation integration with the broader system."""
    
    def test_validation_with_form_rendering(self, simple_form_model, enhanced_renderer):
        """Test validation integration with form rendering."""
        invalid_data = {"name": "", "email": "invalid"}
        result = validate_form_data(simple_form_model, invalid_data)
        
        # Render form with validation errors
        html = enhanced_renderer.render_form_from_model(
            simple_form_model,
            errors=result.errors
        )
        
        # Should contain error messages in rendered HTML
        for error_message in result.errors.values():
            assert error_message in html
    
    def test_validation_with_complex_form(self, complex_form_model):
        """Test validation with complex form model."""
        # Test with missing required fields
        incomplete_data = {
            "first_name": "John",
            "email": "john@example.com"
            # Missing required fields: last_name, age, rating, terms
        }
        
        result = validate_form_data(complex_form_model, incomplete_data)
        
        assert not result.is_valid
        assert len(result.errors) >= 4  # At least 4 missing required fields
        
        # Check specific required field errors
        required_fields = ["last_name", "age", "rating", "terms"]
        error_fields = list(result.errors.keys())
        
        for field in required_fields:
            assert field in error_fields
    
    def test_validation_preserves_valid_data(self, simple_form_model):
        """Test that validation preserves valid data even when some fields fail."""
        mixed_data = {
            "name": "John Doe",  # Valid
            "email": "invalid-email",  # Invalid
            "age": 25,  # Valid
            "newsletter": True  # Valid
        }
        
        # Even though validation fails, we should be able to get the valid data
        try:
            form = simple_form_model(**mixed_data)
        except ValidationError as e:
            # The valid fields should be identifiable
            assert len(e.errors()) == 1  # Only email should fail
            
            # Extract the one error
            error = e.errors()[0]
            assert error["loc"] == ("email",)
    
    def test_validation_with_default_values(self):
        """Test validation behavior with default values."""
        class DefaultForm(FormModel):
            name: str = Field(..., description="Required name")
            email: str = Field("", ui_element="email")
            newsletter: bool = Field(False, description="Newsletter subscription")
            rating: int = Field(5, ge=1, le=5, description="Default rating")
        
        # Test with minimal data (using defaults)
        minimal_data = {"name": "John"}
        result = validate_form_data(DefaultForm, minimal_data)
        
        assert result.is_valid
        assert result.data["name"] == "John"
        assert result.data["email"] == ""
        assert result.data["newsletter"] is False
        assert result.data["rating"] == 5
    
    def test_validation_error_recovery(self, simple_form_model):
        """Test that forms can recover from validation errors."""
        # First attempt with invalid data
        invalid_data = {"name": "", "email": "invalid"}
        result1 = validate_form_data(simple_form_model, invalid_data)
        assert not result1.is_valid
        
        # Second attempt with corrected data
        corrected_data = {"name": "John", "email": "john@example.com", "age": 25}
        result2 = validate_form_data(simple_form_model, corrected_data)
        assert result2.is_valid
        assert result2.data["name"] == "John"


class TestValidationPerformance:
    """Test validation performance and edge cases."""
    
    def test_large_form_validation(self):
        """Test validation performance with large forms."""
        # Create a form with many fields
        class LargeForm(FormModel):
            field1: str = Field(..., min_length=1)
            field2: str = Field(..., min_length=1)
            field3: str = Field(..., min_length=1)
            field4: str = Field(..., min_length=1)
            field5: str = Field(..., min_length=1)
            field6: int = Field(..., ge=0)
            field7: int = Field(..., ge=0)
            field8: int = Field(..., ge=0)
            field9: float = Field(..., ge=0.0)
            field10: bool = Field(False)
        
        # Test with valid data
        valid_data = {
            f"field{i}": f"value{i}" if i <= 5 else (i if i <= 8 else (float(i) if i == 9 else True))
            for i in range(1, 11)
        }
        
        result = validate_form_data(LargeForm, valid_data)
        assert result.is_valid
    
    def test_validation_with_empty_data(self, simple_form_model):
        """Test validation with completely empty data."""
        result = validate_form_data(simple_form_model, {})
        
        assert not result.is_valid
        assert len(result.errors) >= 1  # Should have errors for required fields
    
    def test_validation_with_extra_fields(self, simple_form_model):
        """Test validation behavior with extra unexpected fields."""
        data_with_extra = {
            "name": "John",
            "email": "john@example.com",
            "age": 25,
            "newsletter": True,
            "extra_field": "should be ignored"
        }
        
        # Pydantic should ignore extra fields by default
        result = validate_form_data(simple_form_model, data_with_extra)
        assert result.is_valid
        # Extra field should not be in the result
        assert "extra_field" not in result.data