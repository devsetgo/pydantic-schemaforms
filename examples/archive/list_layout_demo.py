#!/usr/bin/env python3
"""
Demo of the new ListLayout functionality.
This shows how dynamic lists are now properly implemented as layout types
rather than input types, providing better architecture.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic_forms import (
    FormModel, 
    ListLayout, 
    SectionDesign,
    EnhancedFormRenderer,
    render_form_page
)


class PetModel(FormModel):
    """Simple pet model for demonstration."""
    name: str = Field(
        ..., 
        description="Pet's name",
        ui_type="text",
        ui_label="Pet Name"
    )
    species: str = Field(
        ...,
        description="Type of animal",
        ui_type="select",
        ui_label="Species",
        ui_choices=["Dog", "Cat", "Bird", "Fish", "Rabbit", "Other"]
    )
    age: Optional[int] = Field(
        None,
        description="Pet's age in years",
        ui_type="number",
        ui_label="Age (years)",
        ge=0,
        le=50
    )
    is_vaccinated: bool = Field(
        True,
        description="Has the pet been vaccinated?",
        ui_type="checkbox",
        ui_label="Vaccinated"
    )


class OwnerModel(FormModel):
    """Pet owner model."""
    name: str = Field(
        ...,
        description="Owner's full name",
        ui_type="text",
        ui_label="Full Name"
    )
    email: str = Field(
        ...,
        description="Contact email",
        ui_type="email",
        ui_label="Email Address"
    )
    phone: Optional[str] = Field(
        None,
        description="Phone number",
        ui_type="tel",
        ui_label="Phone Number"
    )


def demo_list_layout():
    """Demonstrate the new ListLayout functionality."""
    
    # Create a ListLayout for pets
    pet_list_layout = ListLayout(
        form_model=PetModel,
        min_items=1,
        max_items=5,
        add_button_text="Add Another Pet",
        remove_button_text="Remove Pet",
        section_design=SectionDesign(
            section_title="Pet Information",
            section_description="Add information for each of your pets",
            icon="pets",  # Material icon
            collapsible=True,
            css_class="pet-list-section"
        )
    )
    
    # Create renderer
    renderer = EnhancedFormRenderer()
    
    # Test with sample data
    sample_pets_data = [
        {
            "name": "Buddy",
            "species": "Dog", 
            "age": 3,
            "is_vaccinated": True
        },
        {
            "name": "Whiskers",
            "species": "Cat",
            "age": 2,
            "is_vaccinated": True
        }
    ]
    
    print("=== Bootstrap ListLayout Demo ===")
    bootstrap_html = pet_list_layout.render(
        data={'items': sample_pets_data},
        framework="bootstrap"
    )
    print(bootstrap_html)
    print("\n" + "="*50 + "\n")
    
    print("=== Material Design ListLayout Demo ===")
    material_html = pet_list_layout.render(
        data={'items': sample_pets_data},
        framework="material"
    )
    print(material_html)
    print("\n" + "="*50 + "\n")
    
    # Demo with empty list (should show minimum items)
    empty_list_layout = ListLayout(
        form_model=OwnerModel,
        min_items=1,
        max_items=3,
        add_button_text="Add Owner",
        section_design=SectionDesign(
            section_title="Pet Owners",
            section_description="Information about pet owners"
        )
    )
    
    print("=== Empty List Demo (min_items=1) ===")
    empty_html = empty_list_layout.render(
        data={'items': []},  # Empty data, but min_items=1 will ensure one item shows
        framework="bootstrap"
    )
    print(empty_html)
    
    return pet_list_layout, bootstrap_html, material_html


def create_full_page_demo():
    """Create a complete HTML page demonstrating the ListLayout."""
    
    # Create owner form
    owner = OwnerModel.model_construct()
    renderer = EnhancedFormRenderer()
    
    # Create pet list layout
    pet_list_layout = ListLayout(
        form_model=PetModel,
        min_items=0,
        max_items=10,
        add_button_text="Add Pet",
        remove_button_text="Remove",
        section_design=SectionDesign(
            section_title="Your Pets",
            section_description="Tell us about your furry, feathered, or finned friends!",
            icon="pets",
            collapsible=False
        )
    )
    
    # Render owner form
    owner_html = renderer.render_form_from_model(owner, framework="bootstrap")
    
    # Render pet list
    pet_list_html = pet_list_layout.render(
        data={'items': [{"name": "", "species": "Dog", "age": None, "is_vaccinated": True}]},
        framework="bootstrap"
    )
    
    # Combine into full form
    full_form_html = f"""
    <div class="container">
        <h1>Pet Registration Form</h1>
        <form method="post" action="/register-pets">
            <div class="row">
                <div class="col-md-6">
                    <h3>Owner Information</h3>
                    {owner_html}
                </div>
                <div class="col-md-6">
                    {pet_list_html}
                </div>
            </div>
            <div class="row mt-4">
                <div class="col-12">
                    <button type="submit" class="btn btn-primary btn-lg">
                        Register Pets
                    </button>
                </div>
            </div>
        </form>
    </div>
    """
    
    # Create complete page
    page_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pet Registration - ListLayout Demo</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body {{ background-color: #f8f9fa; padding: 2rem 0; }}
            .list-layout {{ 
                border: 1px solid #dee2e6; 
                border-radius: 0.5rem; 
                padding: 1rem; 
                background: white;
                margin-bottom: 1rem;
            }}
            .list-item {{ 
                border: 1px solid #e9ecef; 
                border-radius: 0.375rem; 
                padding: 1rem; 
                margin-bottom: 1rem;
                background: #fafafa;
                position: relative;
            }}
            .list-remove-btn {{
                position: absolute;
                top: 0.5rem;
                right: 0.5rem;
            }}
            .list-add-btn {{
                margin-top: 1rem;
            }}
        </style>
    </head>
    <body>
        {full_form_html}
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return page_html


if __name__ == "__main__":
    print("Starting ListLayout Demo...")
    
    # Run basic demo
    pet_list, bootstrap_html, material_html = demo_list_layout()
    
    # Create and save full page demo
    page_html = create_full_page_demo()
    
    # Save to file for testing
    demo_file = "/workspaces/pydantic-forms/examples/list_layout_demo.html"
    with open(demo_file, "w") as f:
        f.write(page_html)
    
    print(f"Full demo page saved to: {demo_file}")
    print("You can open this file in a browser to see the ListLayout in action!")
    
    print("\n=== ListLayout Architecture Benefits ===")
    print("✅ Lists are now proper layout types, not input types")
    print("✅ Any FormModel can be used in a list")
    print("✅ Dynamic add/remove functionality built-in")
    print("✅ Minimum and maximum item constraints")
    print("✅ Consistent with other layout types (Vertical, Horizontal, Tabbed)")
    print("✅ Framework-agnostic rendering (Bootstrap, Material Design)")
    print("✅ Proper separation of concerns - layout vs input")