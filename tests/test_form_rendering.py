#!/usr/bin/env python3
"""
Test script to check form rendering with validation errors and data preservation.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from examples.shared_models import PetRegistrationForm, handle_form_submission, parse_nested_form_data
from pydantic_forms.enhanced_renderer import render_form_html

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

print("🧪 Testing form rendering with validation errors...")
print("=" * 60)

# First, validate and get errors
result = handle_form_submission(PetRegistrationForm, form_data)

print(f"Validation failed as expected: {not result['success']}")
print(f"Errors: {result.get('errors', {})}")

if not result['success']:
    print("\n" + "=" * 60)
    print("Testing form re-rendering with errors and preserved data...")
    
    # Parse the form data like the Flask app would
    parsed_form_data = parse_nested_form_data(form_data)
    print(f"\nParsed form data:")
    for key, value in parsed_form_data.items():
        print(f"  {key}: {value}")
    
    # Try to render the form with errors and preserved data
    try:
        form_html = render_form_html(
            PetRegistrationForm,
            framework="bootstrap",
            form_data=parsed_form_data,
            errors=result['errors'],
            submit_url="/pets"
        )
        
        print(f"\n✅ Form rendered successfully with:")
        print(f"  - {len(result['errors'])} validation error(s)")
        print(f"  - Preserved data for {len(parsed_form_data)} field(s)")
        print(f"  - Form HTML length: {len(form_html)} characters")
        
        # Check if the error message is in the rendered HTML
        if "Must be 0.01 or greater" in form_html:
            print("  ✅ Error message found in rendered HTML")
        else:
            print("  ❌ Error message NOT found in rendered HTML")
            
        # Check if the invalid weight value is preserved in the form
        if "-0.98" in form_html:
            print("  ✅ Invalid weight value (-0.98) preserved in form")
        else:
            print("  ❌ Invalid weight value NOT preserved")
            
        # Save the rendered HTML for inspection
        with open("/workspaces/pydantic-forms/debug_form.html", "w") as f:
            f.write(form_html)
        print("  📄 Form HTML saved to debug_form.html")
        
    except Exception as e:
        print(f"  ❌ Form rendering failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Summary:")
print("If the validation and rendering both work here, but the web form doesn't")
print("show errors, the issue is likely in the Flask app's POST handler routing")