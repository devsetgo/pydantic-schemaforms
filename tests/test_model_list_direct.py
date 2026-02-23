#!/usr/bin/env python3
"""
More detailed debugging script to trace what happens during rendering.
"""

import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from examples.shared_models import PetRegistrationForm

from pydantic_schemaforms.form_data import parse_nested_form_data
from pydantic_schemaforms.validation import validate_form_data

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

print("🔍 Detailed debugging of form rendering...")
print("=" * 60)

# First, validate and get errors
parsed = parse_nested_form_data(form_data)
validation = validate_form_data(PetRegistrationForm, parsed)
print(f"Validation errors: {validation.errors}")

if not validation.is_valid:
    # Parse the form data like the Flask app would
    parsed_form_data = parsed

    print("\n" + "=" * 60)
    print("Testing model list rendering directly...")

    # Import the model list renderer directly
    from examples.shared_models import PetModel

    from pydantic_schemaforms.model_list import ModelListRenderer

    list_renderer = ModelListRenderer(framework="bootstrap")

    # Extract the pet data
    pets_data = parsed_form_data.get('pets', [])
    print(f"Pets data: {pets_data}")

    # Simulate the nested error extraction
    from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
    renderer = EnhancedFormRenderer(framework="bootstrap")

    nested_errors = renderer._extract_nested_errors_for_field('pets', validation.errors)
    print(f"Nested errors: {nested_errors}")

    # Try to render just the model list
    try:
        model_list_html = list_renderer.render_model_list(
            field_name="pets",
            label="Your Pets",
            model_class=PetModel,
            values=pets_data,
            error=None,
            nested_errors=nested_errors,
            help_text="Add information about each of your pets",
            is_required=True,
            min_items=1,
            max_items=10
        )

        print("\n✅ Model list rendered successfully")
        print(f"HTML length: {len(model_list_html)} characters")

        # Check if the error message is in the model list HTML
        if "Must be 0.01 or greater" in model_list_html:
            print("✅ Error message found in model list HTML!")
        else:
            print("❌ Error message NOT found in model list HTML")

        # Save just the model list HTML for inspection
        from pathlib import Path

        out_path = Path(__file__).resolve().parents[1] / "debug_model_list.html"
        out_path.write_text(model_list_html, encoding="utf-8")
        print(f"📄 Model list HTML saved to {out_path}")

    except Exception as e:
        print(f"❌ Model list rendering failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Next step: Check the saved HTML file for error display")
