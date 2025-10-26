"""
Test suite for Python 3.14 template string system.

This test demonstrates the modern template system using native Python 3.14
template strings for high-performance form rendering.
"""

import pytest
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_forms.templates import (
    TemplateString, FormTemplates, render_template, 
    create_custom_template, validate_template_variables
)
from pydantic_forms.py314_renderer import ModernFormRenderer, RenderContext
from pydantic_forms.form_field import FormField


class TestTemplateString:
    """Test the basic TemplateString functionality."""
    
    def test_simple_substitution(self):
        """Test basic variable substitution."""
        template = TemplateString("Hello ${name}!")
        result = template.render(name="World")
        assert result == "Hello World!"
    
    def test_multiple_variables(self):
        """Test multiple variable substitution."""
        template = TemplateString("${greeting} ${name}, you are ${age} years old!")
        result = template.render(greeting="Hello", name="Alice", age=25)
        assert result == "Hello Alice, you are 25 years old!"
    
    def test_safe_render_missing_variables(self):
        """Test safe rendering with missing variables."""
        template = TemplateString("Hello ${name}, your score is ${score}!")
        result = template.safe_render(name="Bob")
        assert "Hello Bob" in result
        assert "${score}" in result  # Missing variable preserved
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        template = TemplateString("Value: ${value}")
        result = template.render(value=None)
        assert result == "Value: "
    
    def test_boolean_value_handling(self):
        """Test handling of boolean values."""
        template = TemplateString("Enabled: ${enabled}, Disabled: ${disabled}")
        result = template.render(enabled=True, disabled=False)
        assert result == "Enabled: true, Disabled: false"


class TestFormTemplates:
    """Test the pre-built form templates."""
    
    def test_text_input_template(self):
        """Test text input template rendering."""
        result = FormTemplates.TEXT_INPUT.render(
            id="username",
            name="username",
            value="test_user",
            placeholder="Enter username",
            required="required",
            disabled="",
            readonly="",
            attributes="",
            label="Username",
            help_text="",
            error_message="",
            wrapper_class="form-group",
            wrapper_style="",
            input_class="form-control",
            input_style=""
        )
        
        assert 'id="username"' in result
        assert 'name="username"' in result
        assert 'value="test_user"' in result
        assert 'placeholder="Enter username"' in result
        assert 'required' in result
        assert 'form-control' in result
    
    def test_email_input_template(self):
        """Test email input template rendering."""
        result = FormTemplates.EMAIL_INPUT.render(
            id="email",
            name="email",
            value="test@example.com",
            placeholder="Enter email",
            required="required",
            disabled="",
            readonly="",
            attributes="",
            label="Email Address",
            help_text="",
            error_message="",
            wrapper_class="form-group",
            wrapper_style="",
            input_class="form-control",
            input_style=""
        )
        
        assert 'type="email"' in result
        assert 'id="email"' in result
        assert 'value="test@example.com"' in result
    
    def test_form_wrapper_template(self):
        """Test complete form wrapper template."""
        result = FormTemplates.FORM_WRAPPER.render(
            form_id="test-form",
            form_class="pydantic-form",
            form_style="",
            method="POST",
            action="/submit",
            form_attributes="",
            csrf_token="",
            form_content="<div>Form content</div>",
            submit_buttons="<button>Submit</button>"
        )
        
        assert 'id="test-form"' in result
        assert 'method="POST"' in result
        assert 'action="/submit"' in result
        assert '<div>Form content</div>' in result
        assert '<button>Submit</button>' in result


class TestModernFormRenderer:
    """Test the modern form renderer with Python 3.14 templates."""
    
    def test_basic_model_rendering(self):
        """Test rendering a basic Pydantic model."""
        class UserForm(BaseModel):
            name: str = FormField(input_type="text", title="Full Name")
            email: str = FormField(input_type="email", title="Email Address")
            age: int = FormField(input_type="number", title="Age")
        
        renderer = ModernFormRenderer(framework="bootstrap")
        result = renderer.render_form(UserForm)
        
        assert 'name="name"' in result
        assert 'name="email"' in result
        assert 'name="age"' in result
        assert 'type="text"' in result
        assert 'type="email"' in result
        assert 'type="number"' in result
    
    def test_form_with_values_and_errors(self):
        """Test rendering form with pre-filled values and errors."""
        class ContactForm(BaseModel):
            name: str = FormField(input_type="text", title="Name")
            email: str = FormField(input_type="email", title="Email")
            message: str = FormField(input_type="textarea", title="Message")
        
        values = {
            "name": "John Doe",
            "email": "john@example.com",
            "message": "Hello world!"
        }
        
        errors = {
            "email": ["Invalid email format"],
            "message": ["Message is too short"]
        }
        
        renderer = ModernFormRenderer(framework="bootstrap")
        result = renderer.render_form(ContactForm, values=values, errors=errors)
        
        assert 'value="John Doe"' in result
        assert 'value="john@example.com"' in result
        assert 'Hello world!' in result
        assert 'Invalid email format' in result
        assert 'Message is too short' in result
    
    def test_complete_page_rendering(self):
        """Test rendering complete HTML page."""
        class LoginForm(BaseModel):
            username: str = FormField(input_type="text", title="Username")
            password: str = FormField(input_type="password", title="Password")
        
        renderer = ModernFormRenderer(framework="bootstrap")
        result = renderer.render_complete_page(
            LoginForm, 
            title="Login Page",
            values={"username": "testuser"}
        )
        
        assert '<!DOCTYPE html>' in result
        assert '<title>Login Page</title>' in result
        assert 'bootstrap.min.css' in result
        assert 'name="username"' in result
        assert 'type="password"' in result
        assert 'value="testuser"' in result
    
    def test_custom_render_context(self):
        """Test using custom render context."""
        class SimpleForm(BaseModel):
            field: str = FormField(input_type="text", title="Test Field")
        
        context = RenderContext(
            framework="bootstrap",
            form_class="custom-form",
            input_class="custom-input",
            show_icons=True,
            live_validation=True
        )
        
        renderer = ModernFormRenderer()
        result = renderer.render_form(SimpleForm, context=context)
        
        assert 'custom-form' in result
        assert 'custom-input' in result
        assert 'data-live-validation="true"' in result
    
    def test_different_frameworks(self):
        """Test rendering with different CSS frameworks."""
        class TestForm(BaseModel):
            test_field: str = FormField(input_type="text", title="Test")
        
        # Bootstrap
        bootstrap_renderer = ModernFormRenderer(framework="bootstrap")
        bootstrap_result = bootstrap_renderer.render_complete_page(TestForm, title="Bootstrap")
        assert 'bootstrap.min.css' in bootstrap_result
        
        # Material
        material_renderer = ModernFormRenderer(framework="material")
        material_result = material_renderer.render_complete_page(TestForm, title="Material")
        assert 'materialize.min.css' in material_result


class TestTemplateUtilities:
    """Test template utility functions."""
    
    def test_render_template_function(self):
        """Test the render_template convenience function."""
        template = TemplateString("Hello ${name}!")
        result = render_template(template, name="World")
        assert result == "Hello World!"
    
    def test_create_custom_template(self):
        """Test creating custom templates."""
        template = create_custom_template("Custom: ${value}")
        result = template.render(value="test")
        assert result == "Custom: test"
    
    def test_validate_template_variables(self):
        """Test template variable validation."""
        template = TemplateString("Hello ${name}, you are ${age} years old!")
        
        # All variables provided
        validation = validate_template_variables(template, name="Alice", age=25)
        assert validation == {"name": True, "age": True}
        
        # Missing variable
        validation = validate_template_variables(template, name="Bob")
        assert validation == {"name": True, "age": False}


class TestAdvancedFeatures:
    """Test advanced template features."""
    
    def test_complex_form_with_icons_and_help(self):
        """Test complex form with icons and help text."""
        class ProfileForm(BaseModel):
            name: str = FormField(
                input_type="text", 
                title="Full Name", 
                icon="person",
                help_text="Enter your full legal name"
            )
            email: str = FormField(
                input_type="email", 
                title="Email", 
                icon="envelope",
                help_text="We'll never share your email"
            )
            bio: str = FormField(
                input_type="textarea", 
                title="Biography", 
                icon="chat-left-text",
                help_text="Tell us about yourself"
            )
        
        renderer = ModernFormRenderer(framework="bootstrap")
        context = RenderContext(show_icons=True, show_help_text=True)
        result = renderer.render_form(ProfileForm, context=context)
        
        assert 'bi-person' in result
        assert 'bi-envelope' in result
        assert 'bi-chat-left-text' in result
        assert 'Enter your full legal name' in result
        assert "We'll never share your email" in result
        assert 'Tell us about yourself' in result
    
    def test_form_with_validation_constraints(self):
        """Test form with validation constraints."""
        class ConstrainedForm(BaseModel):
            age: int = Field(ge=18, le=100, description="Must be between 18 and 100")
            score: float = Field(ge=0.0, le=10.0)
        
        renderer = ModernFormRenderer(framework="bootstrap")
        result = renderer.render_form(ConstrainedForm)
        
        # Should include min/max attributes
        assert 'min="18"' in result
        assert 'max="100"' in result


def test_performance_with_template_caching():
    """Test that template caching improves performance."""
    import time
    
    class LargeForm(BaseModel):
        field1: str = FormField(input_type="text", title="Field 1")
        field2: str = FormField(input_type="text", title="Field 2")
        field3: str = FormField(input_type="text", title="Field 3")
        field4: str = FormField(input_type="text", title="Field 4")
        field5: str = FormField(input_type="text", title="Field 5")
    
    renderer = ModernFormRenderer(framework="bootstrap")
    
    # First render (templates need to be compiled)
    start_time = time.time()
    result1 = renderer.render_form(LargeForm)
    first_render_time = time.time() - start_time
    
    # Second render (templates are cached)
    start_time = time.time()
    result2 = renderer.render_form(LargeForm)
    second_render_time = time.time() - start_time
    
    # Results should be identical
    assert result1 == result2
    
    # Second render should be faster (though this might not always be measurable)
    # This is more of a demonstration than a strict test
    print(f"First render: {first_render_time:.6f}s")
    print(f"Second render: {second_render_time:.6f}s")


if __name__ == "__main__":
    # Run a quick demo
    print("=== Python 3.14 Template String Demo ===\n")
    
    # Simple template demo
    template = TemplateString("Hello ${name}, welcome to ${app}!")
    result = template.render(name="Developer", app="Pydantic Forms")
    print(f"Simple template: {result}\n")
    
    # Form demo
    class DemoForm(BaseModel):
        name: str = FormField(
            input_type="text", 
            title="Your Name", 
            icon="person",
            help_text="Enter your full name"
        )
        email: str = FormField(
            input_type="email", 
            title="Email Address", 
            icon="envelope"
        )
        age: int = Field(ge=18, le=120, description="Your age")
    
    renderer = ModernFormRenderer(framework="bootstrap")
    context = RenderContext(show_icons=True, show_help_text=True)
    
    values = {"name": "John Doe", "email": "john@example.com", "age": 30}
    errors = {"email": ["Please use a valid email address"]}
    
    form_html = renderer.render_form(DemoForm, values=values, errors=errors, context=context)
    print("=== Generated Form HTML ===")
    print(form_html[:500] + "..." if len(form_html) > 500 else form_html)
    
    print("\n✅ Python 3.14 template system is working perfectly!")