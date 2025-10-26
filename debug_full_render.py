#!/usr/bin/env python3
"""
Test the full renderer chain with debugging
"""

import sys
import os
from enum import Enum

# Add the library to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic_forms.schema_form import FormModel
from pydantic_forms.form_field import FormField

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

# Import after creating the form to avoid circular imports
from pydantic_forms.enhanced_renderer import EnhancedFormRenderer

def debug_full_rendering():
    """Debug the full rendering process."""
    print("=== Full Rendering Debug ===")
    
    # Monkey patch the renderer to add debugging
    original_render_field = EnhancedFormRenderer._render_field
    
    def debug_render_field(self, field_name, field_schema, value=None, error=None, required_fields=None):
        print(f"\n--- Rendering field: {field_name} ---")
        print(f"Field schema: {field_schema}")
        
        # Check UI info extraction
        ui_info = field_schema.get("ui", {})
        if not ui_info:
            ui_info = field_schema
        print(f"UI info: {ui_info}")
        
        # Check UI element detection
        ui_element = ui_info.get("element") or ui_info.get("widget") or ui_info.get("input_type")
        if not ui_element:
            ui_element = self._infer_ui_element(field_schema)
        print(f"UI element: {ui_element}")
        
        # Get input component
        input_component = self.UI_ELEMENT_MAPPING.get(ui_element)
        print(f"Input component: {input_component}")
        
        # Check rendering path
        if ui_element in ("select", "radio"):
            print("✅ Taking select/radio path")
            ui_options_list = ui_info.get("options", [])
            print(f"Options: {ui_options_list}")
        else:
            print("❌ Taking regular input path")
        
        # Call original method
        result = original_render_field(self, field_name, field_schema, value, error, required_fields)
        print(f"Rendered result: {result}")
        return result
    
    # Apply monkey patch
    EnhancedFormRenderer._render_field = debug_render_field
    
    try:
        # Create renderer and render form
        renderer = EnhancedFormRenderer(framework="bootstrap")
        html = renderer.render_form_from_model(TestForm)
        
        print("\n=== Final HTML ===")
        print(html)
        
    finally:
        # Restore original method
        EnhancedFormRenderer._render_field = original_render_field

if __name__ == "__main__":
    debug_full_rendering()