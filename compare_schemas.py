#!/usr/bin/env python3
"""
Compare different schema methods
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

def compare_schemas():
    """Compare the different schema methods."""
    print("=== Comparing Schema Methods ===")
    
    # Method 1: model_json_schema() (used by renderer)
    print("1. model_json_schema():")
    schema1 = TestForm.model_json_schema()
    print("Priority field:", schema1["properties"]["priority"])
    
    print("\n" + "="*50 + "\n")
    
    # Method 2: get_json_schema() (FormModel custom method)
    print("2. get_json_schema():")
    schema2 = TestForm.get_json_schema()
    print("Priority field:", schema2["properties"]["priority"])
    
    print("\n" + "="*50 + "\n")
    
    # Method 3: Check what the renderer actually uses
    print("3. What enhanced renderer uses:")
    print("   renderer calls: model_cls.get_json_schema()")
    print("   So it should use method 2, not method 1!")

if __name__ == "__main__":
    compare_schemas()