#!/usr/bin/env python3
"""
Debug script to test nested error extraction.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic_forms.enhanced_renderer import EnhancedFormRenderer

# Test error extraction
renderer = EnhancedFormRenderer(framework="bootstrap")

# Test the error extraction method
all_errors = {
    'pets[0].weight': 'Must be 0.01 or greater',
    'pets[1].name': 'Name is required',
    'owner_name': 'Owner name is required'
}

print("🐛 Testing nested error extraction...")
print("=" * 60)

print("All errors:")
for key, value in all_errors.items():
    print(f"  {key}: {value}")

print("\nExtracting nested errors for 'pets' field...")
nested_errors = renderer._extract_nested_errors_for_field('pets', all_errors)

print(f"Extracted nested errors: {nested_errors}")

print("\nExpected result:")
print("  {'0.weight': 'Must be 0.01 or greater', '1.name': 'Name is required'}")

print("\n" + "=" * 60)
print("Testing if extraction works correctly...")
expected = {'0.weight': 'Must be 0.01 or greater', '1.name': 'Name is required'}

if nested_errors == expected:
    print("✅ Error extraction works correctly!")
else:
    print("❌ Error extraction failed!")
    print(f"Expected: {expected}")
    print(f"Got: {nested_errors}")