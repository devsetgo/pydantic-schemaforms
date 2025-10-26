#!/usr/bin/env python3
"""
Debug script to check how the form field is being processed
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

def debug_schema():
    """Debug the form schema generation."""
    print("=== Debugging Form Schema ===")
    
    # Get the full schema
    schema = TestForm.model_json_schema()
    print("Full schema:")
    import json
    print(json.dumps(schema, indent=2))
    
    print("\n=== Priority Field Details ===")
    priority_field = schema.get("properties", {}).get("priority", {})
    print("Priority field schema:", priority_field)
    
    # Check if ui info is in the field schema directly or nested
    for key in priority_field:
        if key not in ["$ref", "default", "title", "description"]:
            print(f"  {key}: {priority_field[key]}")

if __name__ == "__main__":
    debug_schema()