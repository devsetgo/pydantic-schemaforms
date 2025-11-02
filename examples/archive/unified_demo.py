#!/usr/bin/env python3
"""
Unified Pydantic Forms Demo
===========================

A comprehensive Flask demonstration of pydantic-forms library featuring:
- Minimal, medium, and complex (kitchen sink) forms
- Bootstrap 5 and Material Design 3 themes
- Multiple layouts: vertical (default), horizontal, and tabbed
- Complete form validation and error handling
- Modern Python 3.14+ template strings

Run with:
    python unified_demo.py

Then visit:
    - http://localhost:5000/ (main demo page)
    - http://localhost:5000/bootstrap/minimal (simple login form)
    - http://localhost:5000/bootstrap/medium (contact form)
    - http://localhost:5000/bootstrap/complex (kitchen sink)
    - http://localhost:5000/material/minimal (Material Design login)
    - http://localhost:5000/material/medium (Material Design contact)
    - http://localhost:5000/material/complex (Material Design kitchen sink)
    - http://localhost:5000/layouts (layout demonstrations)
"""

import os
import sys
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel, Field, EmailStr, field_validator
from pydantic_forms.schema_form import FormModel
from pydantic_forms.form_field import FormField
from pydantic_forms.form_layouts import VerticalLayout, HorizontalLayout, TabbedLayout, ListLayout, SectionDesign
from pydantic_forms.enhanced_renderer import render_form_html
from pydantic_forms.material_renderer import render_material_form_html
from pydantic_forms.validation import validate_form_data

app = Flask(__name__)
app.secret_key = "demo-secret-key-change-in-production"

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class Priority(str, Enum):
    """Priority levels for forms."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class Country(str, Enum):
    """Countries for selection."""
    US = "United States"
    CA = "Canada"
    UK = "United Kingdom"
    AU = "Australia"
    DE = "Germany"
    FR = "France"
    JP = "Japan"

# ============================================================================
# PYDANTIC FORM MODELS
# ============================================================================

class PetModel(FormModel):
    """Individual pet model for use in ListLayout."""
    
    name: str = FormField(
        title="Pet's Name",
        input_type="text",
        placeholder="Enter your pet's name",
        help_text="The name of your pet",
        icon="bi bi-card-text",
        min_length=1,
        max_length=50
    )
    
    species: str = FormField(
        title="Species",
        input_type="select",
        options=["Dog", "Cat", "Bird", "Fish", "Rabbit", "Hamster", "Reptile", "Other"],
        help_text="Select the type of animal",
        icon="bi bi-paw"
    )
    
    age: Optional[int] = FormField(
        None,
        title="Age (years)",
        input_type="number",
        placeholder="Pet's age",
        help_text="Age of your pet in years",
        icon="bi bi-calendar",
        min_value=0,
        max_value=50
    )
    
    is_vaccinated: bool = FormField(
        True,
        title="Vaccinated",
        input_type="checkbox",
        help_text="Has this pet been vaccinated?",
        icon="bi bi-shield-check"
    )



class MinimalLoginForm(FormModel):
    """Minimal form example - Simple login form."""
    
    username: str = FormField(
        title="Username",
        input_type="text",
        placeholder="Enter your username",
        help_text="Your username or email address",
        icon="bi bi-person",
        min_length=3,
        max_length=50
    )
    
    password: str = FormField(
        title="Password", 
        input_type="password",
        placeholder="Enter your password",
        help_text="Your account password",
        icon="bi bi-lock",
        min_length=6
    )
    
    remember_me: bool = FormField(
        False,
        title="Remember me",
        input_type="checkbox",
        help_text="Keep me logged in on this device",
        icon="bi bi-check2-square"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()

class PetOwnerForm(FormModel):
    """Form that demonstrates ListLayout for pet management."""
    
    owner_name: str = FormField(
        title="Owner Name",
        input_type="text",
        placeholder="Enter your full name",
        help_text="Your full name as the pet owner",
        icon="bi bi-person",
        min_length=2,
        max_length=100
    )
    
    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="Your contact email address",
        icon="bi bi-envelope"
    )
    
    address: Optional[str] = FormField(
        None,
        title="Address",
        input_type="textarea",
        placeholder="Enter your full address...",
        help_text="Your home address (optional)",
        icon="bi bi-house",
        max_length=500
    )
    
    emergency_contact: Optional[str] = FormField(
        None,
        title="Emergency Contact",
        input_type="text",
        placeholder="Emergency contact name and phone",
        help_text="Someone to contact in case of emergency",
        icon="bi bi-person-exclamation",
        max_length=100
    )

class MediumContactForm(FormModel):
    """Medium complexity form - Contact form with validation."""
    
    # Personal Information
    first_name: str = FormField(
        title="First Name",
        input_type="text",
        placeholder="Enter your first name",
        help_text="Your given name",
        icon="bi bi-person",
        min_length=2,
        max_length=50
    )
    
    last_name: str = FormField(
        title="Last Name",
        input_type="text", 
        placeholder="Enter your last name",
        help_text="Your family name",
        icon="bi bi-person",
        min_length=2,
        max_length=50
    )
    
    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="We'll never share your email",
        icon="bi bi-envelope"
    )
    
    phone: Optional[str] = FormField(
        None,
        title="Phone Number",
        input_type="tel",
        placeholder="+1 (555) 123-4567",
        help_text="Optional phone number",
        icon="bi bi-telephone"
    )
    
    # Message Details
    subject: str = FormField(
        title="Subject",
        input_type="text",
        placeholder="Brief subject line",
        help_text="What is this message about?",
        icon="bi bi-chat-left-text",
        min_length=5,
        max_length=200
    )
    
    message: str = FormField(
        title="Message",
        input_type="textarea",
        placeholder="Enter your detailed message here...",
        help_text="Please provide details about your inquiry",
        icon="bi bi-chat-left-dots",
        min_length=10,
        max_length=2000
    )
    
    priority: Priority = FormField(
        Priority.MEDIUM,
        title="Priority Level",
        input_type="select",
        options=[p.value for p in Priority],
        help_text="How urgent is your request?",
        icon="bi bi-exclamation-triangle"
    )
    
    # Preferences
    subscribe_newsletter: bool = FormField(
        False,
        title="Subscribe to Newsletter",
        input_type="checkbox",
        help_text="Receive updates and news",
        icon="bi bi-newspaper"
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v

class ComplexKitchenSinkForm(FormModel):
    """Complex form example - Kitchen sink with all input types."""
    
    # === TEXT INPUTS ===
    text_field: str = FormField(
        title="Text Input",
        input_type="text",
        placeholder="Enter any text",
        help_text="Basic text input field",
        icon="bi bi-input-cursor-text",
        min_length=1,
        max_length=100
    )
    
    email_field: EmailStr = FormField(
        title="Email Field",
        input_type="email", 
        placeholder="user@example.com",
        help_text="Must be a valid email address",
        icon="bi bi-at"
    )
    
    password_field: str = FormField(
        title="Password Field",
        input_type="password",
        placeholder="Enter secure password",
        help_text="At least 8 characters with mixed case",
        icon="bi bi-shield-lock",
        min_length=8
    )
    
    search_field: str = FormField(
        title="Search Field", 
        input_type="search",
        placeholder="Search for something...",
        help_text="Search input with special styling",
        icon="bi bi-search"
    )
    
    url_field: str = FormField(
        title="URL Field",
        input_type="url",
        placeholder="https://example.com",
        help_text="Must be a valid URL",
        icon="bi bi-link-45deg"
    )
    
    tel_field: str = FormField(
        title="Telephone Field",
        input_type="tel", 
        placeholder="+1-555-123-4567",
        help_text="Phone number input",
        icon="bi bi-telephone"
    )
    
    textarea_field: str = FormField(
        title="Text Area",
        input_type="textarea",
        placeholder="Enter multiple lines of text...",
        help_text="Multi-line text input",
        icon="bi bi-textarea-resize",
        min_length=10,
        max_length=500
    )
    
    # === NUMERIC INPUTS ===
    number_field: int = FormField(
        title="Number Input",
        input_type="number",
        placeholder="42",
        help_text="Integer number input",
        icon="bi bi-123",
        min_value=0,
        max_value=1000
    )
    
    float_field: float = FormField(
        title="Decimal Number",
        input_type="number",
        placeholder="3.14159",
        help_text="Decimal number input",
        icon="bi bi-calculator",
        min_value=0.0,
        max_value=999.99
    )
    
    range_field: int = FormField(
        25,
        title="Range Slider",
        input_type="range",
        help_text="Slide to select value",
        icon="bi bi-sliders",
        min_value=0,
        max_value=100
    )
    
    # === SELECTION INPUTS ===
    select_field: str = FormField(
        title="Select Dropdown",
        input_type="select",
        options=["Option 1", "Option 2", "Option 3", "Option 4"],
        help_text="Choose one option from dropdown",
        icon="bi bi-list"
    )
    
    country_field: Country = FormField(
        Country.US,
        title="Country Selection",
        input_type="select",
        options=[c.value for c in Country],
        help_text="Select your country",
        icon="bi bi-globe"
    )
    
    radio_field: str = FormField(
        "medium",
        title="Radio Button Group",
        input_type="radio",
        options=["small", "medium", "large", "extra-large"],
        help_text="Select one option",
        icon="bi bi-ui-radios"
    )
    
    multiselect_field: List[str] = FormField(
        [],
        title="Multiple Selection",
        input_type="select",
        options=["JavaScript", "Python", "Java", "C++", "Go", "Rust"],
        help_text="Select multiple programming languages",
        icon="bi bi-list-check"
    )
    
    # === BOOLEAN INPUTS ===
    checkbox_field: bool = FormField(
        False,
        title="Checkbox Input",
        input_type="checkbox",
        help_text="Check this box to agree",
        icon="bi bi-check-square"
    )
    
    switch_field: bool = FormField(
        True,
        title="Switch Toggle",
        input_type="checkbox",
        help_text="Toggle this switch",
        icon="bi bi-toggle-on"
    )
    
    # === DATE/TIME INPUTS ===
    date_field: date = FormField(
        title="Date Input",
        input_type="date",
        help_text="Select a date",
        icon="bi bi-calendar-date"
    )
    
    time_field: str = FormField(
        title="Time Input",
        input_type="time",
        help_text="Select a time",
        icon="bi bi-clock"
    )
    
    datetime_field: datetime = FormField(
        title="Date & Time",
        input_type="datetime-local",
        help_text="Select date and time",
        icon="bi bi-calendar-event"
    )
    
    # === SPECIALIZED INPUTS ===
    color_field: str = FormField(
        "#3498db",
        title="Color Picker",
        input_type="color",
        help_text="Choose your favorite color",
        icon="bi bi-palette"
    )
    
    file_field: str = FormField(
        title="File Upload",
        input_type="file",
        help_text="Upload a file (max 10MB)",
        icon="bi bi-cloud-upload"
    )
    
    hidden_field: str = FormField(
        "hidden_value",
        title="Hidden Field",
        input_type="hidden",
        help_text="This field is hidden from users"
    )
    
    # === USER PROFILE SECTION ===
    role: UserRole = FormField(
        UserRole.USER,
        title="User Role",
        input_type="select",
        options=[r.value for r in UserRole],
        help_text="Select your role",
        icon="bi bi-person-badge"
    )
    
    bio: Optional[str] = FormField(
        None,
        title="Biography",
        input_type="textarea",
        placeholder="Tell us about yourself...",
        help_text="Optional personal biography",
        icon="bi bi-person-lines-fill",
        max_length=1000
    )
    
    newsletter: bool = FormField(
        False,
        title="Newsletter Subscription",
        input_type="checkbox", 
        help_text="Receive our weekly newsletter",
        icon="bi bi-envelope-heart"
    )
    
    notifications: bool = FormField(
        True,
        title="Push Notifications",
        input_type="checkbox",
        help_text="Receive push notifications",
        icon="bi bi-bell"
    )

    @field_validator("password_field")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v

# ============================================================================
# LAYOUT CLASSES
# ============================================================================

class VerticalFormLayout(VerticalLayout):
    """Vertical layout - default stacked form layout."""
    form = MinimalLoginForm

class HorizontalFormLayout(HorizontalLayout):
    """Horizontal layout - side-by-side form arrangement."""
    form = MediumContactForm

class TabbedFormLayout(TabbedLayout):
    """Tabbed layout - single form split across multiple tabs."""
    # Split the complex form into logical tabs
    personal_info = VerticalLayout()
    contact_details = VerticalLayout() 
    preferences = VerticalLayout()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def handle_form_submission(form_class, form_data, success_message="Form submitted successfully!"):
    """Handle form submission with validation and error handling."""
    try:
        # Validate the form data using Pydantic
        result = validate_form_data(form_class, form_data)
        
        if result.is_valid:
            # Return success response
            return {
                'success': True,
                'message': success_message,
                'data': result.data
            }
        else:
            # Return validation errors
            return {
                'success': False,
                'errors': result.errors
            }
    except Exception as e:
        # Return unexpected errors
        return {
            'success': False,
            'errors': {'form': str(e)}
        }

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Main demo page with overview."""
    return render_template('home.html', title="Home")

# ============================================================================
# BOOTSTRAP ROUTES
# ============================================================================

@app.route('/bootstrap/minimal', methods=['GET', 'POST'])
def bootstrap_minimal():
    """Bootstrap minimal form example."""
    if request.method == 'POST':
        result = handle_form_submission(MinimalLoginForm, request.form.to_dict())
        
        if result['success']:
            flash('Login successful!', 'success')
            return render_template('bootstrap_minimal.html',
                                 title="Bootstrap Minimal Form",
                                 success=True,
                                 form_data=result['data'])
        else:
            flash('Please correct the errors below.', 'error')
            form_html = render_form_html(MinimalLoginForm, framework="bootstrap", errors=result['errors'])
            return render_template('bootstrap_minimal.html',
                                 title="Bootstrap Minimal Form",
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_html(MinimalLoginForm, framework="bootstrap")
        return render_template('bootstrap_minimal.html',
                             title="Bootstrap Minimal Form",
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
            return render_template('bootstrap_pets.html',
                                 title="Pet Registration Form",
                                 success=True,
                                 owner_data=result['data'],
                                 pets_data=pets_data)
        else:
            # Re-render form with errors
            from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
            
            renderer = EnhancedFormRenderer()
            owner_form_html = renderer.render_form_from_model(PetOwnerForm.model_construct(), framework="bootstrap", include_submit_button=False, errors=result.get('errors', {}))
            
            # Create pet list layout
            pet_list_layout = ListLayout(
                form_model=PetModel,
                min_items=0,
                max_items=10,
                add_button_text="Add Another Pet",
                remove_button_text="Remove Pet",
                section_design=SectionDesign(
                    section_title="Your Pets",
                    section_description="Add information about each of your pets",
                    icon="pets",
                    collapsible=False
                ),
                collapsible_items=True,
                items_expanded_by_default=False
            )
            
            pets_html = pet_list_layout.render(
                data={'items': pets_data},
                framework="bootstrap"
            )
            
            return render_template('bootstrap_pets.html',
                                 title="Pet Registration Form",
                                 success=False,
                                 owner_form_html=owner_form_html,
                                 pets_html=pets_html,
                                 errors=result.get('errors', {}))
    else:
        # GET request - show initial form
        from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
        
        renderer = EnhancedFormRenderer()
        owner_form_html = renderer.render_form_from_model(PetOwnerForm.model_construct(), framework="bootstrap", include_submit_button=False)
        
        # Create pet list layout with sample data
        pet_list_layout = ListLayout(
            form_model=PetModel,
            min_items=0,
            max_items=10,
            add_button_text="Add Another Pet",
            remove_button_text="Remove Pet",
            section_design=SectionDesign(
                section_title="Your Pets",
                section_description="Add information about each of your pets (optional)",
                icon="pets",
                collapsible=False
            ),
            collapsible_items=True,
            items_expanded_by_default=False
        )
        
        # Start with one empty pet form
        pets_html = pet_list_layout.render(
            data={'items': [{}]},
            framework="bootstrap"
        )
        
        return render_template('bootstrap_pets.html',
                             title="Pet Registration Form",
                             success=False,
                             owner_form_html=owner_form_html,
                             pets_html=pets_html)

@app.route('/bootstrap/medium', methods=['GET', 'POST'])
def bootstrap_medium():
    """Bootstrap medium complexity form example."""
    if request.method == 'POST':
        result = handle_form_submission(MediumContactForm, request.form.to_dict())
        
        if result['success']:
            return render_template('bootstrap_medium.html',
                                 title="Bootstrap Medium Form",
                                 success=True,
                                 form_data=result['data'])
        else:
            form_html = render_form_html(MediumContactForm, framework="bootstrap", errors=result['errors'])
            return render_template('bootstrap_medium.html',
                                 title="Bootstrap Medium Form",
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_html(MediumContactForm, framework="bootstrap")
        return render_template('bootstrap_medium.html',
                             title="Bootstrap Medium Form",
                             success=False,
                             form_html=form_html)

@app.route('/bootstrap/complex', methods=['GET', 'POST'])
def bootstrap_complex():
    """Bootstrap complex form example - kitchen sink."""
    if request.method == 'POST':
        result = handle_form_submission(ComplexKitchenSinkForm, request.form.to_dict())
        
        if result['success']:
            return render_template('bootstrap_complex.html',
                                 title="Bootstrap Complex Form",
                                 success=True,
                                 form_data=result['data'])
        else:
            form_html = render_form_html(ComplexKitchenSinkForm, framework="bootstrap", errors=result['errors'])
            return render_template('bootstrap_complex.html',
                                 title="Bootstrap Complex Form",
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_html(ComplexKitchenSinkForm, framework="bootstrap")
        return render_template('bootstrap_complex.html',
                             title="Bootstrap Complex Form",
                             success=False,
                             form_html=form_html)

# ============================================================================
# MATERIAL DESIGN ROUTES
# ============================================================================

@app.route('/material/minimal', methods=['GET', 'POST'])
def material_minimal():
    """Material Design minimal form example."""
    if request.method == 'POST':
        result = handle_form_submission(MinimalLoginForm, request.form.to_dict())
        
        if result['success']:
            return render_template('material_minimal.html',
                                 title="Material Design Minimal Form",
                                 theme="material",
                                 success=True,
                                 form_data=result['data'])
        else:
            form_html = render_material_form_html(MinimalLoginForm, errors=result['errors'])
            return render_template('material_minimal.html',
                                 title="Material Design Minimal Form",
                                 theme="material",
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_material_form_html(MinimalLoginForm)
        return render_template('material_minimal.html',
                             title="Material Design Minimal Form",
                             theme="material",
                             success=False,
                             form_html=form_html)

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
            return render_template('material_pets.html',
                                 title="Pet Registration Form",
                                 theme="material",
                                 success=True,
                                 owner_data=result['data'],
                                 pets_data=pets_data)
        else:
            # Re-render form with errors
            from pydantic_forms.material_renderer import MaterialDesign3Renderer
            
            renderer = MaterialDesign3Renderer()
            owner_form_html = renderer.render_form_from_model(PetOwnerForm.model_construct(), include_submit_button=False, errors=result.get('errors', {}))
            
            # Create pet list layout
            pet_list_layout = ListLayout(
                form_model=PetModel,
                min_items=0,
                max_items=10,
                add_button_text="Add Another Pet",
                remove_button_text="Remove Pet",
                section_design=SectionDesign(
                    section_title="Your Pets",
                    section_description="Add information about each of your pets",
                    icon="pets",
                    collapsible=False
                ),
                collapsible_items=True,
                items_expanded_by_default=False
            )
            
            pets_html = pet_list_layout.render(
                data={'items': pets_data},
                framework="material"
            )
            
            return render_template('material_pets.html',
                                 title="Pet Registration Form",
                                 theme="material",
                                 success=False,
                                 owner_form_html=owner_form_html,
                                 pets_html=pets_html,
                                 errors=result.get('errors', {}))
    else:
        # GET request - show initial form
        from pydantic_forms.material_renderer import MaterialDesign3Renderer
        
        renderer = MaterialDesign3Renderer()
        owner_form_html = renderer.render_form_from_model(PetOwnerForm.model_construct(), include_submit_button=False)
        
        # Create pet list layout with sample data
        pet_list_layout = ListLayout(
            form_model=PetModel,
            min_items=0,
            max_items=10,
            add_button_text="Add Another Pet",
            remove_button_text="Remove Pet",
            section_design=SectionDesign(
                section_title="Your Pets",
                section_description="Add information about each of your pets (optional)",
                icon="pets",
                collapsible=False
            ),
            collapsible_items=True,
            items_expanded_by_default=False
        )
        
        # Start with one empty pet form
        pets_html = pet_list_layout.render(
            data={'items': [{}]},
            framework="material"
        )
        
        return render_template('material_pets.html',
                             title="Pet Registration Form",
                             theme="material",
                             success=False,
                             owner_form_html=owner_form_html,
                             pets_html=pets_html)

@app.route('/material/medium', methods=['GET', 'POST'])
def material_medium():
    """Material Design medium complexity form example."""
    if request.method == 'POST':
        result = handle_form_submission(MediumContactForm, request.form.to_dict())
        
        if result['success']:
            return render_template('material_medium.html',
                                 title="Material Design Medium Form",
                                 theme="material",
                                 success=True,
                                 form_data=result['data'])
        else:
            form_html = render_material_form_html(MediumContactForm, errors=result['errors'])
            return render_template('material_medium.html',
                                 title="Material Design Medium Form",
                                 theme="material",
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_material_form_html(MediumContactForm)
        return render_template('material_medium.html',
                             title="Material Design Medium Form",
                             theme="material",
                             success=False,
                             form_html=form_html)

@app.route('/material/complex', methods=['GET', 'POST'])
def material_complex():
    """Material Design complex form example - kitchen sink."""
    if request.method == 'POST':
        result = handle_form_submission(ComplexKitchenSinkForm, request.form.to_dict())
        
        if result['success']:
            return render_template('material_complex.html',
                                 title="Material Design Complex Form",
                                 theme="material",
                                 success=True,
                                 form_data=result['data'])
        else:
            form_html = render_material_form_html(ComplexKitchenSinkForm, errors=result['errors'])
            return render_template('material_complex.html',
                                 title="Material Design Complex Form",
                                 theme="material",
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_material_form_html(ComplexKitchenSinkForm)
        return render_template('material_complex.html',
                             title="Material Design Complex Form",
                             theme="material",
                             success=False,
                             form_html=form_html)

# ============================================================================
# LAYOUT DEMONSTRATION ROUTES
# ============================================================================

@app.route('/layouts')
def layouts_demo():
    """Demonstrate different layout systems using pydantic-forms library."""
    
    # Vertical Layout (Default) - rendered by pydantic-forms
    vertical_form_html = render_form_html(MinimalLoginForm, framework="bootstrap", layout="vertical")
    
    # Horizontal Layout - using library's horizontal layout
    horizontal_form_html = render_form_html(MinimalLoginForm, framework="bootstrap", layout="horizontal")
    
    # Side-by-Side Layout - using library's new side-by-side layout
    side_by_side_form_html = render_form_html(MediumContactForm, framework="bootstrap", layout="side-by-side")
    
    # Tabbed Layout - using library's tabbed layout with a more complex form
    tabbed_form_html = render_form_html(MediumContactForm, framework="bootstrap", layout="tabbed")
    
    return render_template('layouts.html',
                         title="Layout Demonstrations",
                         vertical_form_html=vertical_form_html,
                         horizontal_form_html=horizontal_form_html,
                         side_by_side_form_html=side_by_side_form_html,
                         tabbed_form_html=tabbed_form_html)

@app.route('/material/layouts')
def material_layouts_demo():
    """Demonstrate different layout systems using Material Design renderer."""
    
    # Vertical Layout (Default) - rendered by pydantic-forms Material Design
    vertical_form_html = render_material_form_html(MinimalLoginForm, layout="vertical")
    
    # Horizontal Layout - using Material Design horizontal layout
    horizontal_form_html = render_material_form_html(MinimalLoginForm, layout="horizontal")
    
    # Side-by-Side Layout - using Material Design side-by-side layout
    side_by_side_form_html = render_material_form_html(MediumContactForm, layout="side-by-side")
    
    # Tabbed Layout - using Material Design tabbed layout
    tabbed_form_html = render_material_form_html(MediumContactForm, layout="tabbed")
    
    return render_template('material_layouts.html',
                         title="Material Design Layout Demonstrations",
                         theme="material",
                         vertical_form_html=vertical_form_html,
                         horizontal_form_html=horizontal_form_html,
                         side_by_side_form_html=side_by_side_form_html,
                         tabbed_form_html=tabbed_form_html)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html', title="Page Not Found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    return render_template('500.html', title="Server Error"), 500

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print("🚀 Starting Unified Pydantic Forms Demo...")
    print(f"📄 Home page: http://localhost:{port}/")
    print(f"🎨 Bootstrap examples: http://localhost:{port}/bootstrap/")
    print(f"🐾 Pet registration (ListLayout): http://localhost:{port}/bootstrap/pets")
    print(f"🎨 Material examples: http://localhost:{port}/material/")
    print(f"� Material pets (ListLayout): http://localhost:{port}/material/pets")
    print(f"�📐 Layout examples: http://localhost:{port}/layouts")
    print("⚡ Features: Python 3.14+ templates, multiple themes, ListLayout, all layouts")
    
    app.run(debug=True, port=port, host='0.0.0.0')