#!/usr/bin/env python3
"""
Test script for Material Design icons with pydantic-forms

This script demonstrates how to use Material Icons with the SimpleMaterialRenderer.
"""

import os
import sys

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from pydantic_forms.schema_form import FormModel
from pydantic_forms.form_field import FormField
from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer

class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class IconTestForm(FormModel):
    """Test form with Material Design icons."""
    
    name: str = FormField(
        title="Full Name",
        input_type="text",
        placeholder="Enter your full name",
        help_text="Your first and last name",
        icon="person",  # Material Icon
        min_length=2,
        max_length=100
    )
    
    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="Your email address",
        icon="email"  # Material Icon
    )
    
    password: str = FormField(
        title="Password", 
        input_type="password",
        placeholder="Create a secure password",
        help_text="At least 8 characters required",
        icon="lock",  # Material Icon
        min_length=8
    )
    
    phone: Optional[str] = FormField(
        None,
        title="Phone Number",
        input_type="tel",
        placeholder="(555) 123-4567",
        help_text="Your phone number (optional)",
        icon="phone"  # Material Icon
    )
    
    age: Optional[int] = FormField(
        None,
        title="Age",
        input_type="number",
        placeholder="Your age",
        help_text="Must be 18 or older",
        icon="cake",  # Material Icon
        minimum=18,
        maximum=120
    )
    
    role: UserRole = FormField(
        UserRole.USER,
        title="User Role",
        help_text="Select your role",
        icon="admin_panel_settings"  # Material Icon
    )
    
    bio: Optional[str] = FormField(
        None,
        title="Bio",
        input_type="textarea",
        placeholder="Tell us about yourself...",
        help_text="Optional bio (max 500 characters)",
        icon="description",  # Material Icon
        max_length=500
    )

def test_material_icons():
    """Test rendering form with Material Design icons."""
    renderer = SimpleMaterialRenderer()
    
    # Render the form with icons
    form_html = renderer.render_form_from_model(IconTestForm)
    
    # Create complete HTML page
    html_page = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Material Design Icons Test</title>
</head>
<body>
    <div style="max-width: 600px; margin: 40px auto; padding: 20px;">
        <h1 style="text-align: center; color: #6750a4; font-family: Roboto, sans-serif;">
            Material Design Icons Test
        </h1>
        <p style="text-align: center; color: #49454f; font-family: Roboto, sans-serif;">
            This form demonstrates Material Design 3 fields with icons
        </p>
        {form_html}
    </div>
</body>
</html>
"""
    
    # Write to test file
    test_file = os.path.join(os.path.dirname(__file__), "test_icons.html")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(html_page)
    
    print(f"✅ Test file created: {test_file}")
    print("🌐 Open in browser to view Material Design icons")
    
    return form_html

if __name__ == "__main__":
    test_material_icons()