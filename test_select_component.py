#!/usr/bin/env python3
"""
Test SelectInput component directly
"""

import sys
import os

# Add the library to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic_forms.inputs.selection_inputs import SelectInput

def test_select_input():
    """Test SelectInput component directly."""
    print("=== Testing SelectInput Component ===")
    
    # Create SelectInput instance
    select_input = SelectInput()
    
    # Test options
    options = [
        {"value": "low", "label": "Low", "selected": False},
        {"value": "medium", "label": "Medium", "selected": True},
        {"value": "high", "label": "High", "selected": False},
        {"value": "urgent", "label": "Urgent", "selected": False}
    ]
    
    # Test rendering
    try:
        html = select_input.render(
            options=options,
            name="priority",
            id="priority",
            **{"class": "form-control"}
        )
        
        print("✅ SelectInput rendered successfully")
        print("HTML output:")
        print(html)
        
        # Check output
        if '<select' in html:
            print("✅ Contains select tag")
        else:
            print("❌ No select tag found")
            
        if 'name="priority"' in html:
            print("✅ Has correct name attribute")
        else:
            print("❌ Missing name attribute")
            
        if 'value="medium" selected' in html or 'selected' in html:
            print("✅ Has selected option")
        else:
            print("❌ No selected option")
            
    except Exception as e:
        print(f"❌ SelectInput failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_select_input()