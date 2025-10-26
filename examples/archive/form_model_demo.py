"""
Example demonstrating the FormModel abstraction for pure Python form generation.
"""

from typing import Optional
from pydantic import Field
from pydantic_forms.form_model import FormModel

# Example 1: Basic form with auto-detection
class ContactForm(FormModel):
    name: str = Field(..., description="Your full name")
    email: str = Field(..., description="Your email address")
    phone: Optional[str] = Field(None, description="Your phone number")
    website: Optional[str] = Field(None, description="Your website URL")
    bio: str = Field(..., description="Tell us about yourself")
    age: int = Field(..., description="Your age", ge=18, le=120)
    subscribe: bool = Field(False, description="Subscribe to newsletter")

# Example 2: Form with explicit UI widgets
class RegistrationForm(FormModel):
    username: str = Field(..., description="Choose a username", json_schema_extra={"ui_widget": "text"})
    email: str = Field(..., description="Your email", json_schema_extra={"ui_widget": "email"})
    password: str = Field(..., description="Choose a password", json_schema_extra={"ui_widget": "password"})
    confirm_password: str = Field(..., description="Confirm password", json_schema_extra={"ui_widget": "password"})
    birthdate: str = Field(..., description="Your birthdate", json_schema_extra={"ui_widget": "date"})
    bio: Optional[str] = Field(None, description="About yourself", json_schema_extra={"ui_widget": "textarea"})
    terms: bool = Field(..., description="I agree to terms and conditions")

    class UIConfig:
        framework = "bootstrap"
        layout = "vertical"
        username = {"autofocus": True, "minlength": 3}
        password = {"minlength": 8}
        bio = {"rows": 4, "cols": 50}

# Example 3: Form with custom configuration
class PreferencesForm(FormModel):
    theme: str = Field("light", description="Choose your theme")
    language: str = Field("en", description="Select language")
    notifications: bool = Field(True, description="Enable notifications")
    max_items: int = Field(10, description="Items per page", ge=5, le=100)

    class UIConfig:
        framework = "material"
        layout = "grid"
        theme = {
            "widget": "select",
            "options": [
                {"value": "light", "label": "Light Theme"},
                {"value": "dark", "label": "Dark Theme"},
                {"value": "auto", "label": "Auto Theme"}
            ]
        }
        language = {
            "widget": "select", 
            "options": [
                {"value": "en", "label": "English"},
                {"value": "es", "label": "Spanish"},
                {"value": "fr", "label": "French"}
            ]
        }

if __name__ == "__main__":
    # Demo the forms
    print("=== Contact Form ===")
    contact_html = ContactForm.render_form()
    print(contact_html)
    
    print("\n=== Registration Form with Data ===")
    reg_data = {"username": "johndoe", "email": "john@example.com"}
    reg_errors = {"password": "Password too weak"}
    reg_html = RegistrationForm.render_form(data=reg_data, errors=reg_errors)
    print(reg_html)
    
    print("\n=== Example Data ===")
    example_data = ContactForm.get_example_form_data()
    print(example_data)