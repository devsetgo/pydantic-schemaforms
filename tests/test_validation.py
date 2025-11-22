#!/usr/bin/env python3
"""
Test script to debug validation issues with pet weight field.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from examples.shared_models import PetRegistrationForm, handle_form_submission

# Test the problematic form data you provided
form_data = {
    "owner_name": "Sarah Thompson",
    "email": "sarah.thompson@email.com", 
    "address": "5 Marine Parade, ",
    "emergency_contact": "Mike Thompson - (555) 123-4567",
    "pets[0].name": "Tweety",
    "pets[0].species": "Dog",
    "pets[0].age": "2",
    "pets[0].weight": "-0.98",  # This should trigger validation error
    "pets[0].breed": "Canary",
    "pets[0].color": "#000000",
    "pets[0].last_vet_visit": "2024-11-01",
    "pets[0].special_needs": "Requires daily singing practice and fresh seed mix"
}

print("🧪 Testing form validation with problematic data...")
print("=" * 60)

print("Form data:")
for key, value in form_data.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("Testing validation...")

# Test the form submission handler
result = handle_form_submission(PetRegistrationForm, form_data)

print(f"\nValidation result:")
print(f"  Success: {result['success']}")

if result['success']:
    print("  ✅ Form validation passed")
    print("  Data:", result.get('data', {}))
else:
    print("  ❌ Form validation failed")
    print("  Errors:")
    for field, error in result.get('errors', {}).items():
        print(f"    {field}: {error}")

print("\n" + "=" * 60)
print("Expected behavior:")
print("  - Validation should fail due to negative weight (-0.98)")
print("  - Error should show: 'pets[0].weight: Must be 0.01 or greater'")
print("  - Form data should be preserved for user to fix")