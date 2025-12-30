"""Comprehensive tests for integration/builder.py to improve coverage."""

import pytest
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

from pydantic_forms.integration.builder import (
    FormBuilder,
    AutoFormBuilder,
    create_login_form,
    create_registration_form,
    create_contact_form,
    create_form_from_model,
)
from pydantic_forms.modern_renderer import FormField


# Test models
class UserModel(BaseModel):
    """Test user model."""
    username: str
    email: str
    age: int
    is_active: bool = True
    birth_date: date


class ProfileModel(BaseModel):
    """Test profile model with various field types."""
    full_name: str
    email_address: str
    password_field: str
    phone_number: str
    website_url: str
    description: str
    comment: str
    notes: str
    bio: str
    score: float
    registered_date: datetime
    optional_field: Optional[str] = None


class TestFormBuilderInputMethods:
    """Test FormBuilder input method additions."""
    
    def test_select_input(self):
        """Test select_input adds select field."""
        builder = FormBuilder()
        options = [{"value": "1", "label": "One"}, {"value": "2", "label": "Two"}]
        
        result = builder.select_input("country", options, label="Country")
        
        assert result is builder  # Chaining
        assert len(builder.fields) == 1
        assert builder.fields[0].name == "country"
        assert builder.fields[0].field_type == "select"
        assert builder.fields[0].options == options
    
    def test_checkbox_input(self):
        """Test checkbox_input adds checkbox field."""
        builder = FormBuilder()
        
        result = builder.checkbox_input("terms", label="Accept Terms")
        
        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == "terms"
        assert builder.fields[0].field_type == "checkbox"
        assert builder.fields[0].label == "Accept Terms"
    
    def test_textarea_input(self):
        """Test textarea_input adds textarea field."""
        builder = FormBuilder()
        
        result = builder.textarea_input("comments", rows=6)
        
        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == "comments"
        assert builder.fields[0].field_type == "textarea"
        assert builder.fields[0].attributes["rows"] == "6"
    
    def test_textarea_input_default_rows(self):
        """Test textarea_input with default rows."""
        builder = FormBuilder()
        
        builder.textarea_input("message")
        
        assert builder.fields[0].attributes["rows"] == "4"
    
    def test_date_input(self):
        """Test date_input adds date field."""
        builder = FormBuilder()
        
        result = builder.date_input("birth_date", label="Date of Birth")
        
        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == "birth_date"
        assert builder.fields[0].field_type == "date"
    
    def test_file_input(self):
        """Test file_input adds file field."""
        builder = FormBuilder()
        
        result = builder.file_input("document", label="Upload Document")
        
        assert result is builder
        assert len(builder.fields) == 1
        assert builder.fields[0].name == "document"
        assert builder.fields[0].field_type == "file"
    
    def test_file_input_with_accept(self):
        """Test file_input with accept attribute."""
        builder = FormBuilder()
        
        builder.file_input("image", accept="image/*")
        
        assert builder.fields[0].attributes["accept"] == "image/*"


class TestFormBuilderValidation:
    """Test FormBuilder validation methods."""
    
    def test_required(self):
        """Test required validation."""
        builder = FormBuilder()
        builder.text_input("name")
        
        result = builder.required("name", "Name is required")
        
        assert result is builder
        # Validator should have the rule added
    
    def test_min_length(self):
        """Test min_length validation."""
        builder = FormBuilder()
        builder.text_input("password")
        
        result = builder.min_length("password", 8, "Min 8 chars")
        
        assert result is builder
    
    def test_max_length(self):
        """Test max_length validation."""
        builder = FormBuilder()
        builder.text_input("username")
        
        result = builder.max_length("username", 20, "Max 20 chars")
        
        assert result is builder


class TestFormBuilderConfiguration:
    """Test FormBuilder configuration methods."""
    
    def test_set_layout(self):
        """Test set_layout changes layout type."""
        builder = FormBuilder()
        
        result = builder.set_layout("horizontal")
        
        assert result is builder
        assert builder.layout_type == "horizontal"
    
    def test_set_form_attributes(self):
        """Test set_form_attributes updates attributes."""
        builder = FormBuilder()
        
        result = builder.set_form_attributes(id="my-form", class_="custom-form")
        
        assert result is builder
        assert builder.form_attrs["id"] == "my-form"
        assert builder.form_attrs["class_"] == "custom-form"
    
    def test_disable_csrf(self):
        """Test disable_csrf disables CSRF protection."""
        builder = FormBuilder()
        
        result = builder.disable_csrf()
        
        assert result is builder
        assert builder.csrf_enabled is False
    
    def test_disable_honeypot(self):
        """Test disable_honeypot disables honeypot."""
        builder = FormBuilder()
        
        result = builder.disable_honeypot()
        
        assert result is builder
        assert builder.honeypot_enabled is False


class TestFormBuilderBuildValidate:
    """Test FormBuilder build and validation."""
    
    def test_validate_data_with_model(self):
        """Test validate_data with Pydantic model."""
        builder = FormBuilder(model=UserModel)
        
        data = {
            "username": "john",
            "email": "john@example.com",
            "age": 30,
            "is_active": True,
            "birth_date": "2000-01-01"
        }
        
        is_valid, errors = builder.validate_data(data)
        
        # Should delegate to validator
        assert isinstance(is_valid, bool)
        assert isinstance(errors, dict)
    
    def test_validate_data_without_model(self):
        """Test validate_data without model."""
        builder = FormBuilder()
        builder.text_input("name").required("name")
        
        is_valid, errors = builder.validate_data({"name": "John"})
        
        assert isinstance(is_valid, bool)
        assert isinstance(errors, dict)
    
    def test_get_validation_script(self):
        """Test get_validation_script returns JavaScript."""
        builder = FormBuilder()
        builder.text_input("email").email_input()
        
        script = builder.get_validation_script()
        
        assert isinstance(script, str)


class TestAutoFormBuilder:
    """Test AutoFormBuilder automatic form generation."""
    
    def test_build_from_model_basic_types(self):
        """Test _build_from_model with basic field types."""
        builder = AutoFormBuilder(UserModel)
        
        assert len(builder.fields) == 5
        
        # Check field names
        field_names = [f.name for f in builder.fields]
        assert "username" in field_names
        assert "email" in field_names
        assert "age" in field_names
        assert "is_active" in field_names
        assert "birth_date" in field_names
    
    def test_build_from_model_input_types(self):
        """Test _build_from_model assigns correct input types."""
        builder = AutoFormBuilder(UserModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["username"].field_type == "text"
        assert field_map["age"].field_type == "number"
        assert field_map["is_active"].field_type == "checkbox"
        assert field_map["birth_date"].field_type == "date"
    
    def test_get_input_type_for_field_email(self):
        """Test _get_input_type_for_field detects email fields."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["email_address"].field_type == "email"
    
    def test_get_input_type_for_field_password(self):
        """Test _get_input_type_for_field detects password fields."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["password_field"].field_type == "password"
    
    def test_get_input_type_for_field_phone(self):
        """Test _get_input_type_for_field detects phone fields."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["phone_number"].field_type == "tel"
    
    def test_get_input_type_for_field_url(self):
        """Test _get_input_type_for_field detects URL fields."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["website_url"].field_type == "url"
    
    def test_get_input_type_for_field_textarea_fields(self):
        """Test _get_input_type_for_field detects textarea fields."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["description"].field_type == "textarea"
        assert field_map["comment"].field_type == "textarea"
        assert field_map["notes"].field_type == "textarea"
        assert field_map["bio"].field_type == "textarea"
    
    def test_get_input_type_for_field_number(self):
        """Test _get_input_type_for_field handles int and float."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["score"].field_type == "number"
    
    def test_get_input_type_for_field_datetime(self):
        """Test _get_input_type_for_field handles datetime."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["registered_date"].field_type == "date"
    
    def test_get_input_type_for_field_optional(self):
        """Test _get_input_type_for_field handles Optional fields."""
        builder = AutoFormBuilder(ProfileModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        # Should handle Optional[str] -> str -> text
        assert field_map["optional_field"].field_type == "text"
    
    def test_add_field_validation_required(self):
        """Test _add_field_validation adds required validation."""
        class RequiredModel(BaseModel):
            required_field: str
            optional_field: str = "default"
        
        builder = AutoFormBuilder(RequiredModel)
        
        field_map = {f.name: f for f in builder.fields}
        
        assert field_map["required_field"].required is True
        assert field_map["optional_field"].required is False


class TestBuilderFactoryFunctions:
    """Test factory functions for common forms."""
    
    def test_create_login_form(self):
        """Test create_login_form creates login form."""
        builder = create_login_form()
        
        assert isinstance(builder, FormBuilder)
        assert len(builder.fields) >= 2
        
        field_names = [f.name for f in builder.fields]
        assert "email" in field_names
        assert "password" in field_names
    
    def test_create_login_form_framework(self):
        """Test create_login_form with custom framework."""
        builder = create_login_form(framework="material")
        
        assert builder.framework == "material"
    
    def test_create_registration_form(self):
        """Test create_registration_form creates registration form."""
        builder = create_registration_form()
        
        assert isinstance(builder, FormBuilder)
        assert len(builder.fields) >= 5
        
        field_names = [f.name for f in builder.fields]
        assert "first_name" in field_names
        assert "last_name" in field_names
        assert "email" in field_names
        assert "password" in field_names
        assert "confirm_password" in field_names
    
    def test_create_registration_form_framework(self):
        """Test create_registration_form with custom framework."""
        builder = create_registration_form(framework="material")
        
        assert builder.framework == "material"
    
    def test_create_contact_form(self):
        """Test create_contact_form creates contact form."""
        builder = create_contact_form()
        
        assert isinstance(builder, FormBuilder)
        assert len(builder.fields) >= 4
        
        field_names = [f.name for f in builder.fields]
        assert "name" in field_names
        assert "email" in field_names
        assert "subject" in field_names
        assert "message" in field_names
    
    def test_create_contact_form_framework(self):
        """Test create_contact_form with custom framework."""
        builder = create_contact_form(framework="tailwind")
        
        assert builder.framework == "tailwind"
    
    def test_create_form_from_model(self):
        """Test create_form_from_model creates AutoFormBuilder."""
        builder = create_form_from_model(UserModel)
        
        assert isinstance(builder, AutoFormBuilder)
        assert builder.model is UserModel
    
    def test_create_form_from_model_with_kwargs(self):
        """Test create_form_from_model passes kwargs."""
        builder = create_form_from_model(
            UserModel,
            framework="material",
            theme="dark"
        )
        
        assert builder.framework == "material"
        assert builder.theme == "dark"
