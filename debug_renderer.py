#!/usr/bin/env python3
"""
Debug script with enhanced logging
"""

import sys
import os
from enum import Enum

# Add the library to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic_forms.schema_form import FormModel
from pydantic_forms.form_field import FormField
from pydantic_forms.enhanced_renderer import EnhancedFormRenderer

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

def debug_renderer():
    """Debug the renderer process."""
    print("=== Debugging Enhanced Renderer ===")
    
    # Create renderer
    renderer = EnhancedFormRenderer(framework="bootstrap")
    
    # Get schema
    schema = TestForm.model_json_schema()
    print("Schema properties:")
    for field_name, field_schema in schema["properties"].items():
        print(f"  {field_name}: {field_schema}")
    
    print(f"\n=== Processing Priority Field ===")
    field_name = "priority"
    field_schema = schema["properties"]["priority"]
    
    # Debug the _render_field method logic
    print(f"Field schema: {field_schema}")
    
    # Check UI info extraction
    ui_info = field_schema.get("ui", {})
    print(f"UI info from 'ui' key: {ui_info}")
    
    if not ui_info:
        ui_info = field_schema
        print(f"UI info from field schema directly: {ui_info}")
    
    # Check UI element detection
    ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")
    print(f"Detected UI element: {ui_element}")
    
    if not ui_element:
        ui_element = renderer._infer_ui_element(field_schema)
        print(f"Inferred UI element: {ui_element}")
    
    # Check options
    options = ui_info.get("options", [])
    print(f"Options found: {options}")
    
    # Test if it goes through select path
    if ui_element in ("select", "radio"):
        print("✅ Will use select/radio rendering path")
    else:
        print("❌ Will NOT use select/radio rendering path")

if __name__ == "__main__":
    debug_renderer()