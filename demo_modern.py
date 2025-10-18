"""
Demo script showcasing the modernized pydantic-forms library with Python 3.14 template strings.
This demonstrates all major features and capabilities.
"""

import asyncio
from datetime import date
from typing import Optional
from pydantic import BaseModel

# Import the modernized pydantic-forms
from pydantic_forms import (
    FormBuilder, AutoFormBuilder, create_form_from_model,
    create_login_form, create_registration_form, create_contact_form,
    render_form_page, Layout, create_validator
)


# Demo 1: Simple form builder
def demo_simple_form():
    """Demonstrate basic form building capabilities."""
    print("=== Demo 1: Simple Form Builder ===")
    
    form = (FormBuilder(framework="bootstrap")
            .text_input("name", "Full Name")
            .email_input("email", "Email Address")
            .password_input("password", "Password")
            .number_input("age", "Age", min_val=18, max_val=120)
            .select_input("country", [
                {"value": "us", "text": "United States"},
                {"value": "ca", "text": "Canada"},
                {"value": "uk", "text": "United Kingdom"}
            ], "Country")
            .textarea_input("bio", "Biography", rows=4)
            .checkbox_input("subscribe", "Subscribe to newsletter")
            .required("name")
            .required("email")
            .required("password")
            .min_length("password", 8))
    
    # Render the form
    html = form.render()
    print("Form HTML generated successfully!")
    print(f"HTML length: {len(html)} characters")
    
    # Test validation
    test_data = {
        "name": "John Doe",
        "email": "john@example.com", 
        "password": "short",  # Invalid - too short
        "age": "25",
        "country": "us"
    }
    
    is_valid, errors = form.validate_data(test_data)
    print(f"Validation result: {'Valid' if is_valid else 'Invalid'}")
    if errors:
        print("Errors:", errors)
    
    return form


# Demo 2: Auto-generated form from Pydantic model
class UserModel(BaseModel):
    first_name: str
    last_name: str
    email: str
    age: int
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    is_active: bool = True
    description: Optional[str] = None


def demo_auto_form():
    """Demonstrate automatic form generation from Pydantic models."""
    print("\n=== Demo 2: Auto-Generated Form from Pydantic Model ===")
    
    form = create_form_from_model(UserModel, framework="bootstrap")
    
    # Add additional validation (that's available on FormBuilder)
    form.min_length("first_name", 2)
    form.min_length("last_name", 2)
    # Note: numeric range validation for 'age' is automatically added from the Pydantic model
    
    html = form.render()
    print("Auto-generated form created successfully!")
    print(f"HTML length: {len(html)} characters")
    
    # Test with valid data
    test_data = {
        "first_name": "Jane",
        "last_name": "Smith", 
        "email": "jane@example.com",
        "age": 30,
        "phone": "+1-555-0123",
        "birth_date": "1993-05-15",
        "is_active": True,
        "description": "Software engineer with 5+ years experience"
    }
    
    is_valid, errors = form.validate_data(test_data)
    print(f"Validation result: {'Valid' if is_valid else 'Invalid'}")
    
    return form


# Demo 3: Pre-built form templates
def demo_prebuilt_forms():
    """Demonstrate pre-built form templates."""
    print("\n=== Demo 3: Pre-built Form Templates ===")
    
    # Login form
    login_form = create_login_form()
    print("Login form created")
    
    # Registration form
    registration_form = create_registration_form()
    print("Registration form created")
    
    # Contact form
    contact_form = create_contact_form()
    print("Contact form created")
    
    # Test login form validation
    login_data = {
        "email": "user@example.com",
        "password": "mypassword123"
    }
    
    is_valid, errors = login_form.validate_data(login_data)
    print(f"Login validation: {'Valid' if is_valid else 'Invalid'}")
    
    return login_form, registration_form, contact_form


# Demo 4: Advanced layouts
def demo_layouts():
    """Demonstrate layout system capabilities."""
    print("\n=== Demo 4: Advanced Layout System ===")
    
    # Create some sample content
    form1 = create_login_form().render()
    form2 = create_contact_form().render()
    
    # Horizontal layout
    horizontal = Layout.horizontal(form1, form2, gap="2rem")
    print("Horizontal layout created")
    
    # Grid layout
    grid = Layout.grid(form1, form2, columns="1fr 1fr", gap="1rem")
    print("Grid layout created")
    
    # Tab layout
    tabs = Layout.tabs([
        {"title": "Login", "content": form1},
        {"title": "Contact", "content": form2}
    ])
    print("Tab layout created")
    
    # Accordion layout
    accordion = Layout.accordion([
        {"title": "User Login", "content": form1},
        {"title": "Contact Us", "content": form2}
    ])
    print("Accordion layout created")
    
    # Modal layout
    modal = Layout.modal("login-modal", "User Login", form1)
    print("Modal layout created")
    
    return {
        "horizontal": horizontal.render(),
        "grid": grid.render(), 
        "tabs": tabs.render(),
        "accordion": accordion.render(),
        "modal": modal.render()
    }


# Demo 5: Complete form page generation
def demo_complete_page():
    """Demonstrate complete HTML page generation."""
    print("\n=== Demo 5: Complete Form Page Generation ===")
    
    # Create a registration form
    form = create_registration_form()
    
    # Generate complete HTML page
    page_html = render_form_page(
        form, 
        title="User Registration",
        data={},  # No pre-filled data
        errors={}  # No errors
    )
    
    print("Complete HTML page generated!")
    print(f"Page HTML length: {len(page_html)} characters")
    
    # Save to file for testing
    with open("/workspaces/pydantic-forms/demo_registration.html", "w") as f:
        f.write(page_html)
    print("Saved to demo_registration.html")
    
    return page_html


# Demo 6: Advanced validation features
def demo_advanced_validation():
    """Demonstrate advanced validation capabilities."""
    print("\n=== Demo 6: Advanced Validation Features ===")
    
    # Create custom validator
    validator = create_validator()
    
    # Add custom validation rule
    def validate_strong_password(password):
        if not password:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain a number"
        
        return True, ""
    
    # Build form with advanced validation
    form = (FormBuilder()
            .text_input("username", "Username")
            .email_input("email", "Email")
            .password_input("password", "Password")
            .password_input("confirm_password", "Confirm Password")
            .required("username")
            .required("email")
            .min_length("username", 3)
            .max_length("username", 20))
    
    # Add custom password validation
    form.validator.field("password").custom(validate_strong_password)
    
    # Add cross-field validation for password confirmation
    from pydantic_forms.validation import CrossFieldRules
    form.validator.add_cross_field_rule(
        CrossFieldRules.password_confirmation("password", "confirm_password")
    )
    
    # Test with various data
    test_cases = [
        {
            "username": "jo",  # Too short
            "email": "invalid-email",  # Invalid email
            "password": "weak",  # Weak password
            "confirm_password": "different"  # Doesn't match
        },
        {
            "username": "johndoe",
            "email": "john@example.com", 
            "password": "StrongPass123",
            "confirm_password": "StrongPass123"
        }
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        is_valid, errors = form.validate_data(test_data)
        print(f"Test case {i}: {'Valid' if is_valid else 'Invalid'}")
        if errors:
            for field, field_errors in errors.items():
                for error in field_errors:
                    print(f"  - {field}: {error}")
    
    # Generate client-side validation script
    js_validation = form.get_validation_script()
    print(f"Client-side validation script generated: {len(js_validation)} characters")
    
    return form


# Async demo
async def demo_async_rendering():
    """Demonstrate async form rendering capabilities."""
    print("\n=== Demo 7: Async Rendering ===")
    
    form = create_registration_form()
    
    # Async rendering
    html = await form.render_async()
    print("Async form rendering completed!")
    print(f"HTML length: {len(html)} characters")
    
    return html


# Main demo runner
def run_all_demos():
    """Run all demonstrations."""
    print("🚀 Pydantic Forms v2.0 - Python 3.14 Demo")
    print("=" * 50)
    
    # Run synchronous demos
    demo_simple_form()
    demo_auto_form()
    demo_prebuilt_forms()
    demo_layouts()
    demo_complete_page()
    demo_advanced_validation()
    
    # Run async demo
    asyncio.run(demo_async_rendering())
    
    print("\n" + "=" * 50)
    print("✅ All demos completed successfully!")
    print("\nFeatures demonstrated:")
    print("- Form building with fluent API")
    print("- Auto-generation from Pydantic models")
    print("- Pre-built form templates")
    print("- Advanced layout system")
    print("- Complete page generation")
    print("- Comprehensive validation")
    print("- Async/sync rendering")
    print("- Python 3.14 template strings")


if __name__ == "__main__":
    run_all_demos()