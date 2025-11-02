#!/usr/bin/env python3
"""
Flask Example using Pydantic Forms with ListLayout

A clean Flask demonstration focusing on the core functionality:
- Pet registration form with dynamic ListLayout  
- Bootstrap and Material Design themes
- Form validation and error handling
- Proper use of pydantic-forms library for HTML generation

Run with:
    python flask_example.py

Then visit:
    - http://localhost:5000/ (main page)
    - http://localhost:5000/bootstrap/login (Bootstrap login demo)
    - http://localhost:5000/bootstrap/pets (Bootstrap pets demo)
    - http://localhost:5000/material/pets (Material Design pets demo)
"""

import os
from flask import Flask, request, render_template, redirect, url_for, flash

# Import shared models
from shared_models import (
    PetModel, PetOwnerForm, MinimalLoginForm, 
    handle_form_submission
)

# Import pydantic-forms components
from pydantic_forms.form_layouts import ListLayout, SectionDesign
from pydantic_forms.enhanced_renderer import render_form_html, EnhancedFormRenderer
from pydantic_forms.material_renderer import MaterialDesign3Renderer

app = Flask(__name__)
app.secret_key = "demo-secret-key-change-in-production"

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Main demo page."""
    return render_template('home.html', 
                         title="Flask Pydantic Forms Demo",
                         framework="flask",
                         framework_name="Flask",
                         framework_type="bootstrap", 
                         renderer_info="Enhanced Bootstrap Renderer")

@app.route('/bootstrap/login', methods=['GET', 'POST'])
def bootstrap_login():
    """Simple login form with Bootstrap styling."""
    if request.method == 'POST':
        result = handle_form_submission(MinimalLoginForm, request.form.to_dict())
        
        if result['success']:
            flash('Login successful!', 'success')
            return render_template('flask_login.html',
                                 title="Login Success",
                                 success=True,
                                 form_data=result['data'])
        else:
            flash('Please correct the errors below.', 'error')
            form_html = render_form_html(MinimalLoginForm, framework="bootstrap", errors=result['errors'])
            return render_template('flask_login.html',
                                 title="Login Form",
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_html(MinimalLoginForm, framework="bootstrap")
        return render_template('flask_login.html',
                             title="Login Form",
                             success=False,
                             form_html=form_html)

@app.route('/bootstrap/pets', methods=['GET', 'POST'])
def bootstrap_pets():
    """Bootstrap form with dynamic pet list using ListLayout."""
    if request.method == 'POST':
        # Handle form submission
        form_data = request.form.to_dict(flat=False)
        
        # Extract owner data
        owner_data = {
            'owner_name': form_data.get('owner_name', [''])[0],
            'email': form_data.get('email', [''])[0],
            'address': form_data.get('address', [''])[0],
            'emergency_contact': form_data.get('emergency_contact', [''])[0]
        }
        
        # Extract pets data
        pets_data = []
        pet_index = 0
        while f'item_{pet_index}_name' in form_data:
            pet_data = {
                'name': form_data.get(f'item_{pet_index}_name', [''])[0],
                'species': form_data.get(f'item_{pet_index}_species', [''])[0],
                'age': form_data.get(f'item_{pet_index}_age', [None])[0],
                'is_vaccinated': f'item_{pet_index}_is_vaccinated' in form_data
            }
            if pet_data['name']:  # Only add pets with names
                pets_data.append(pet_data)
            pet_index += 1
        
        # Validate owner form
        result = handle_form_submission(PetOwnerForm, owner_data)
        
        if result['success']:
            return render_template('flask_pets.html',
                                 title="Pet Registration Success",
                                 framework="bootstrap",
                                 success=True,
                                 owner_data=result['data'],
                                 pets_data=pets_data)
        else:
            # Re-render form with errors using pydantic-forms library
            renderer = EnhancedFormRenderer()
            owner_form_html = renderer.render_form_from_model(
                PetOwnerForm.model_construct(), 
                framework="bootstrap", 
                include_submit_button=False, 
                errors=result.get('errors', {})
            )
            
            # Create pet list layout using pydantic-forms library
            pet_list_layout = ListLayout(
                form_model=PetModel,
                min_items=0,
                max_items=10,
                add_button_text="Add Another Pet",
                remove_button_text="Remove Pet",
                collapsible_items=True,
                items_expanded=True,
                section_design=SectionDesign(
                    section_title="Your Pets",
                    section_description="Add information about each of your pets",
                    icon="pets",
                    collapsible=False
                )
            )
            
            pets_html = pet_list_layout.render(
                data={'items': pets_data},
                framework="bootstrap"
            )
            
            return render_template('flask_pets.html',
                                 title="Pet Registration Form",
                                 framework="bootstrap",
                                 success=False,
                                 owner_form_html=owner_form_html,
                                 pets_html=pets_html,
                                 errors=result.get('errors', {}))
    else:
        # GET request - show initial form using pydantic-forms library
        renderer = EnhancedFormRenderer()
        owner_form_html = renderer.render_form_from_model(
            PetOwnerForm.model_construct(), 
            framework="bootstrap", 
            include_submit_button=False
        )
        
        # Create pet list layout using pydantic-forms library
        pet_list_layout = ListLayout(
            form_model=PetModel,
            min_items=0,
            max_items=10,
            add_button_text="Add Another Pet",
            remove_button_text="Remove Pet",
            collapsible_items=True,
            items_expanded=True,
            section_design=SectionDesign(
                section_title="Your Pets",
                section_description="Add information about each of your pets (optional)",
                icon="pets",
                collapsible=False
            )
        )
        
        # Start with one empty pet form
        pets_html = pet_list_layout.render(
            data={'items': [{}]},
            framework="bootstrap"
        )
        
        return render_template('flask_pets.html',
                             title="Pet Registration Form",
                             framework="bootstrap",
                             success=False,
                             owner_form_html=owner_form_html,
                             pets_html=pets_html)

@app.route('/material/pets', methods=['GET', 'POST'])
def material_pets():
    """Material Design form with dynamic pet list using ListLayout."""
    if request.method == 'POST':
        # Handle form submission (same logic as bootstrap version)
        form_data = request.form.to_dict(flat=False)
        
        # Extract owner data
        owner_data = {
            'owner_name': form_data.get('owner_name', [''])[0],
            'email': form_data.get('email', [''])[0],
            'address': form_data.get('address', [''])[0],
            'emergency_contact': form_data.get('emergency_contact', [''])[0]
        }
        
        # Extract pets data
        pets_data = []
        pet_index = 0
        while f'item_{pet_index}_name' in form_data:
            pet_data = {
                'name': form_data.get(f'item_{pet_index}_name', [''])[0],
                'species': form_data.get(f'item_{pet_index}_species', [''])[0],
                'age': form_data.get(f'item_{pet_index}_age', [None])[0],
                'is_vaccinated': f'item_{pet_index}_is_vaccinated' in form_data
            }
            if pet_data['name']:  # Only add pets with names
                pets_data.append(pet_data)
            pet_index += 1
        
        # Validate owner form
        result = handle_form_submission(PetOwnerForm, owner_data)
        
        if result['success']:
            return render_template('flask_pets.html',
                                 title="Pet Registration Success",
                                 framework="material",
                                 success=True,
                                 owner_data=result['data'],
                                 pets_data=pets_data)
        else:
            # Re-render form with errors using pydantic-forms library
            renderer = MaterialDesign3Renderer()
            owner_form_html = renderer.render_form_from_model(
                PetOwnerForm.model_construct(), 
                include_submit_button=False, 
                errors=result.get('errors', {})
            )
            
            # Create pet list layout using pydantic-forms library
            pet_list_layout = ListLayout(
                form_model=PetModel,
                min_items=0,
                max_items=10,
                add_button_text="Add Another Pet",
                remove_button_text="Remove Pet",
                collapsible_items=True,
                items_expanded=True,
                section_design=SectionDesign(
                    section_title="Your Pets",
                    section_description="Add information about each of your pets",
                    icon="pets",
                    collapsible=False
                )
            )
            
            pets_html = pet_list_layout.render(
                data={'items': pets_data},
                framework="material"
            )
            
            return render_template('flask_pets.html',
                                 title="Pet Registration Form",
                                 framework="material",
                                 success=False,
                                 owner_form_html=owner_form_html,
                                 pets_html=pets_html,
                                 errors=result.get('errors', {}))
    else:
        # GET request - show initial form using pydantic-forms library
        renderer = MaterialDesign3Renderer()
        owner_form_html = renderer.render_form_from_model(
            PetOwnerForm.model_construct(), 
            include_submit_button=False
        )
        
        # Create pet list layout using pydantic-forms library
        pet_list_layout = ListLayout(
            form_model=PetModel,
            min_items=0,
            max_items=10,
            add_button_text="Add Another Pet",
            remove_button_text="Remove Pet",
            collapsible_items=True,
            items_expanded=True,
            section_design=SectionDesign(
                section_title="Your Pets",
                section_description="Add information about each of your pets (optional)",
                icon="pets",
                collapsible=False
            )
        )
        
        # Start with one empty pet form
        pets_html = pet_list_layout.render(
            data={'items': [{}]},
            framework="material"
        )
        
        return render_template('flask_pets.html',
                             title="Pet Registration Form",
                             framework="material",
                             success=False,
                             owner_form_html=owner_form_html,
                             pets_html=pets_html)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('flask_error.html', 
                         title="Page Not Found", 
                         error_code=404,
                         error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    return render_template('flask_error.html', 
                         title="Server Error", 
                         error_code=500,
                         error_message="An internal server error occurred."), 500

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print("🚀 Starting Flask Pydantic Forms Example...")
    print(f"📄 Home page: http://localhost:{port}/")
    print(f"🔐 Login form: http://localhost:{port}/bootstrap/login")
    print(f"🐾 Bootstrap pets: http://localhost:{port}/bootstrap/pets")
    print(f"🐾 Material pets: http://localhost:{port}/material/pets")
    print("⚡ Features: ListLayout, Bootstrap/Material Design, Auto-generated forms")
    
    app.run(debug=True, port=port, host='0.0.0.0')