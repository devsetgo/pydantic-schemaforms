"""
Simple Examples for Pydantic Forms

This demonstrates basic usage of the pydantic-forms library
without framework dependencies. Shows how to generate HTML forms
from Pydantic models with minimal setup.
"""

from pydantic_forms.schema_form import FormModel, Field
from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
from typing import Optional
from datetime import date

# Example 1: Basic User Form
class UserForm(FormModel):
    """Simple user registration form."""
    name: str = Field(
        ..., 
        min_length=2, 
        description="Your full name",
        ui_autofocus=True
    )
    email: str = Field(
        ..., 
        description="Your email address",
        ui_element="email"
    )
    age: int = Field(
        ..., 
        ge=18, 
        le=120, 
        description="Your age",
        ui_element="number"
    )
    newsletter: bool = Field(
        False, 
        description="Subscribe to newsletter",
        ui_element="checkbox"
    )

# Example 2: Contact Form with More Field Types
class ContactForm(FormModel):
    """Contact form with various input types."""
    name: str = Field(
        ..., 
        description="Your name",
        ui_autofocus=True
    )
    email: str = Field(
        ..., 
        description="Email address",
        ui_element="email"
    )
    phone: Optional[str] = Field(
        None, 
        description="Phone number",
        ui_element="tel"
    )
    website: Optional[str] = Field(
        None, 
        description="Your website",
        ui_element="url"
    )
    birth_date: Optional[date] = Field(
        None, 
        description="Birth date",
        ui_element="date"
    )
    message: str = Field(
        ..., 
        min_length=10, 
        max_length=500, 
        description="Your message",
        ui_element="textarea",
        ui_options={"rows": 4}
    )

# Example 3: Event Form with Advanced Fields
class EventForm(FormModel):
    """Event creation form with advanced input types."""
    event_name: str = Field(
        ..., 
        description="Event name",
        ui_autofocus=True
    )
    event_datetime: str = Field(
        ..., 
        description="Event date and time",
        ui_element="datetime-local"
    )
    duration: int = Field(
        ..., 
        ge=30, 
        le=480, 
        description="Duration in minutes",
        ui_element="number"
    )
    max_attendees: int = Field(
        ..., 
        ge=1, 
        le=1000, 
        description="Maximum attendees",
        ui_element="number"
    )
    event_color: str = Field(
        "#3498db", 
        description="Event color",
        ui_element="color"
    )
    description: str = Field(
        ..., 
        min_length=20, 
        max_length=1000, 
        description="Event description",
        ui_element="textarea",
        ui_options={"rows": 5}
    )
    is_public: bool = Field(
        True, 
        description="Make event public",
        ui_element="checkbox"
    )

def demo_forms():
    """Demonstrate different forms with various frameworks."""
    
    print("=== Pydantic Forms - Simple Examples ===\n")
    
    # Demo 1: Bootstrap User Form
    print("1. Bootstrap User Form:")
    print("-" * 40)
    user_form_html = UserForm.render_form(framework="bootstrap", submit_url="/submit-user")
    print(user_form_html[:200] + "..." if len(user_form_html) > 200 else user_form_html)
    print()
    
    # Demo 2: Material Design Contact Form
    print("2. Material Design Contact Form:")
    print("-" * 40)
    contact_form_html = ContactForm.render_form(framework="material", submit_url="/submit-contact")
    print(contact_form_html[:200] + "..." if len(contact_form_html) > 200 else contact_form_html)
    print()
    
    # Demo 3: Plain HTML Event Form
    print("3. Plain HTML Event Form:")
    print("-" * 40)
    event_form_html = EventForm.render_form(framework="none", submit_url="/submit-event")
    print(event_form_html[:200] + "..." if len(event_form_html) > 200 else event_form_html)
    print()

def demo_validation():
    """Demonstrate form validation."""
    
    print("=== Form Validation Demo ===\n")
    
    # Test valid data
    print("Testing valid user data:")
    try:
        user = UserForm(
            name="John Doe",
            email="john@example.com", 
            age=25,
            newsletter=True
        )
        print(f"✓ Valid user created: {user.name}, {user.email}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
    
    print()
    
    # Test invalid data
    print("Testing invalid user data:")
    try:
        user = UserForm(
            name="J",  # Too short
            email="invalid-email",  # Invalid format
            age=15,  # Too young
            newsletter=True
        )
        print(f"✓ User created: {user.name}")
    except Exception as e:
        print(f"✗ Validation failed (expected): {e}")
    
    print()

def write_example_html():
    """Write complete HTML examples to files."""
    
    print("=== Writing HTML Examples ===\n")
    
    # Bootstrap example
    bootstrap_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Bootstrap User Form</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container my-5">
            <h1>User Registration</h1>
            {UserForm.render_form(framework="bootstrap", submit_url="/submit")}
        </div>
    </body>
    </html>
    """
    
    with open("/workspaces/pydantic-forms/example_bootstrap.html", "w") as f:
        f.write(bootstrap_html)
    print("✓ Created example_bootstrap.html")
    
    # Material Design example
    material_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Material Contact Form</title>
        <link href="https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <h1>Contact Us</h1>
            {ContactForm.render_form(framework="material", submit_url="/contact")}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js"></script>
    </body>
    </html>
    """
    
    with open("/workspaces/pydantic-forms/example_material.html", "w") as f:
        f.write(material_html)
    print("✓ Created example_material.html")
    
    # Plain HTML example
    plain_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Event Creation Form</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, textarea, select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <h1>Create Event</h1>
        {EventForm.render_form(framework="none", submit_url="/create-event")}
    </body>
    </html>
    """
    
    with open("/workspaces/pydantic-forms/example_plain.html", "w") as f:
        f.write(plain_html)
    print("✓ Created example_plain.html")
    
    print("\nHTML examples written! You can open these files in a browser to see the forms.")

if __name__ == "__main__":
    demo_forms()
    demo_validation()
    write_example_html()
    
    print("\n=== Summary ===")
    print("This demonstrates the pydantic-forms library with:")
    print("• Pydantic 2.x+ models with UI element specifications")
    print("• Multiple CSS frameworks (Bootstrap, Material Design, Plain HTML)")
    print("• Form validation using Pydantic's built-in validation")
    print("• React JSON Schema Forms compatible UI element syntax")
    print("• Automatic HTML form generation")
    print("\nCheck the generated .html files to see the complete forms!")
