#!/usr/bin/env python3
"""
Test script to verify Priority field select bug fix
"""

import sys
import os
from enum import Enum

# Add the library to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic_forms.schema_form import FormModel
from pydantic_forms.form_field import FormField
from pydantic_forms.enhanced_renderer import render_form_html
from pydantic_forms.material_renderer import render_material_form_html

class Priority(str, Enum):
    """Priority levels for testing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TestForm(FormModel):
    """Test form with Priority field."""
    
    priority: Priority = FormField(
        Priority.MEDIUM,
        title="Priority Level",
        input_type="select",
        options=[p.value for p in Priority],
        help_text="Select your priority level",
        icon="bi bi-exclamation-triangle"
    )

def test_bootstrap_select():
    """Test Bootstrap select rendering."""
    print("=== Testing Bootstrap Select Rendering ===")
    html = render_form_html(TestForm, framework="bootstrap")
    
    # Check if it contains select tag and options
    if '<select' in html and 'name="priority"' in html:
        print("✅ Bootstrap select tag found")
        
        # Check for options
        priority_options = ["low", "medium", "high", "urgent"]
        options_found = sum(1 for option in priority_options if f'value="{option}"' in html)
        print(f"✅ Found {options_found}/4 priority options")
        
        # Check for default selection
        if 'selected' in html:
            print("✅ Default selection found")
        else:
            print("⚠️  No default selection found")
            
        # Check if it's NOT a text input
        if 'type="text"' not in html or 'input' not in html.lower():
            print("✅ Not rendered as text input")
        else:
            print("❌ Still rendered as text input")
            
    else:
        print("❌ Bootstrap select tag NOT found")
        print("HTML snippet:", html[:500])
    print()

def test_material_select():
    """Test Material Design select rendering."""
    print("=== Testing Material Design Select Rendering ===")
    html = render_material_form_html(TestForm)
    
    # Check if it contains select tag and options
    if '<select' in html and 'name="priority"' in html:
        print("✅ Material select tag found")
        
        # Check for options
        priority_options = ["low", "medium", "high", "urgent"]
        options_found = sum(1 for option in priority_options if f'value="{option}"' in html)
        print(f"✅ Found {options_found}/4 priority options")
        
        # Check for default selection
        if 'selected' in html:
            print("✅ Default selection found")
        else:
            print("⚠️  No default selection found")
            
        # Check for Material Design classes
        if 'mdc-select' in html:
            print("✅ Material Design classes found")
        else:
            print("⚠️  Material Design classes not found")
            
    else:
        print("❌ Material select tag NOT found")
        print("HTML snippet:", html[:500])
    print()

def test_field_schema():
    """Test that field schema contains correct options."""
    print("=== Testing Field Schema ===")
    schema = TestForm.model_json_schema()
    
    priority_field = schema.get("properties", {}).get("priority", {})
    ui_info = priority_field.get("ui", {}) or priority_field
    
    print("Priority field schema:", priority_field)
    print("UI info:", ui_info)
    
    # Check input_type
    input_type = ui_info.get("input_type")
    if input_type == "select":
        print("✅ Input type is 'select'")
    else:
        print(f"❌ Input type is '{input_type}', expected 'select'")
    
    # Check options
    options = ui_info.get("options", [])
    if options and len(options) == 4:
        print("✅ Found 4 options:", options)
    else:
        print(f"❌ Found {len(options)} options: {options}")
    
    print()

if __name__ == "__main__":
    print("🔧 Testing Priority Field Select Bug Fix\n")
    
    test_field_schema()
    test_bootstrap_select()
    test_material_select()
    
    print("✅ Priority field select bug fix testing completed!")