#!/usr/bin/env python3
"""
Comprehensive Flask Demo for Pydantic Forms
===========================================

A complete Flask application demonstrating all features of the pydantic-forms library
with proper template structure and multiple theme support.

Features:
- Bootstrap 5.3.8 and Material Design v3 themes
- Complete form examples (minimal, medium, kitchen sink)
- Proper Jinja2 template structure
- CDN-based assets
- Form validation and error handling
- Multiple layout systems

Run with:
    python comprehensive_flask_demo.py

Then visit:
    - http://localhost:5000/ (main demo page)
    - http://localhost:5000/bootstrap/ (Bootstrap version)
    - http://localhost:5000/material/ (Material Design version)
"""

import os
import sys
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from flask import Flask, request, render_template, redirect, url_for, flash, session
from pydantic import BaseModel, Field, field_validator, EmailStr

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.secret_key = 'demo-secret-key-change-in-production'

# Configure template and static folders
app.template_folder = 'templates'
app.static_folder = 'static'

# ============================================================================
# PYDANTIC MODELS FOR FORMS
# ============================================================================

class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"

class Priority(str, Enum):
    """Priority level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class LoginModel(BaseModel):
    """Simple login form model."""
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=6, description="Password")
    remember_me: bool = Field(default=False, description="Remember me")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v

class ContactModel(BaseModel):
    """Contact form model with validation."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    subject: str = Field(..., min_length=5, max_length=200, description="Subject")
    message: str = Field(..., min_length=10, max_length=2000, description="Message")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    subscribe: bool = Field(default=False, description="Subscribe to newsletter")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v

class UserProfileModel(BaseModel):
    """Medium complexity user profile model."""
    # Personal Information
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$', description="Phone number")
    
    # Account Settings
    username: str = Field(..., min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$', description="Username")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    bio: Optional[str] = Field(None, max_length=500, description="Biography")
    
    # Preferences
    birth_date: Optional[date] = Field(None, description="Date of birth")
    newsletter: bool = Field(default=False, description="Newsletter subscription")
    notifications: bool = Field(default=True, description="Email notifications")
    
    # Location
    country: str = Field(..., description="Country")
    timezone: str = Field(default="UTC", description="Timezone")

class KitchenSinkModel(BaseModel):
    """Comprehensive model showcasing all input types and features."""
    
    # === TEXT INPUTS ===
    text_field: str = Field(..., min_length=1, description="Text input")
    email_field: EmailStr = Field(..., description="Email input")
    password_field: str = Field(..., min_length=6, description="Password")
    url_field: Optional[str] = Field(None, pattern=r'^https?://.+', description="Website URL")
    search_field: Optional[str] = Field(None, description="Search input")
    tel_field: Optional[str] = Field(None, description="Phone number")
    
    # === NUMERIC INPUTS ===
    integer_field: int = Field(..., ge=1, le=100, description="Integer between 1-100")
    float_field: float = Field(..., ge=0.0, le=1000.0, description="Decimal number")
    range_field: int = Field(50, ge=0, le=100, description="Range slider")
    
    # === SELECTION INPUTS ===
    select_field: str = Field(..., description="Dropdown selection")
    radio_field: str = Field(..., description="Radio button group")
    checkbox_field: bool = Field(default=False, description="Single checkbox")
    multiselect_field: Optional[List[str]] = Field(default=None, description="Multiple selection")
    
    # === DATE/TIME INPUTS ===
    date_field: date = Field(..., description="Date picker")
    datetime_field: Optional[datetime] = Field(None, description="Date and time picker")
    time_field: Optional[str] = Field(None, description="Time picker")
    
    # === TEXT AREAS ===
    textarea_field: str = Field(..., min_length=10, max_length=1000, description="Large text area")
    
    # === SPECIALIZED INPUTS ===
    color_field: str = Field("#ff0000", description="Color picker")
    file_field: Optional[str] = Field(None, description="File upload")
    hidden_field: str = Field("hidden_value", description="Hidden field")
    
    # === VALIDATION REQUIREMENTS ===
    terms_accepted: bool = Field(..., description="Accept terms and conditions")

    @field_validator('terms_accepted')
    @classmethod
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def handle_form_submission(form_model, success_message="Form submitted successfully!"):
    """Generic form submission handler with validation."""
    try:
        # Convert form data to dict (handle checkboxes properly)
        form_data = request.form.to_dict()
        
        # Handle checkboxes (they're not submitted if unchecked)
        checkbox_fields = ['remember_me', 'subscribe', 'newsletter', 'notifications', 
                          'checkbox_field', 'terms_accepted']
        for field_name in checkbox_fields:
            if field_name not in form_data:
                form_data[field_name] = False
            else:
                form_data[field_name] = True
        
        # Handle date fields
        date_fields = ['date_field', 'birth_date']
        for field_name in date_fields:
            if field_name in form_data and form_data[field_name]:
                form_data[field_name] = datetime.strptime(form_data[field_name], '%Y-%m-%d').date()
        
        # Handle datetime fields
        if 'datetime_field' in form_data and form_data['datetime_field']:
            form_data['datetime_field'] = datetime.strptime(form_data['datetime_field'], '%Y-%m-%dT%H:%M')
        
        # Handle multiselect fields
        if 'multiselect_field' in form_data:
            multiselect_values = request.form.getlist('multiselect_field')
            form_data['multiselect_field'] = multiselect_values if multiselect_values else None
        
        # Validate with Pydantic
        validated_data = form_model(**form_data)
        
        return {
            'success': True,
            'message': success_message,
            'data': validated_data.model_dump()
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e),
            'data': form_data
        }

def get_form_field_config():
    """Get form field configurations for different forms."""
    return {
        'login': [
            {'name': 'username', 'label': 'Username or Email', 'type': 'text', 'required': True, 
             'placeholder': 'Enter username or email', 'help': 'Must be at least 3 characters long'},
            {'name': 'password', 'label': 'Password', 'type': 'password', 'required': True, 
             'placeholder': 'Enter password', 'help': 'Must be at least 6 characters long'},
            {'name': 'remember_me', 'label': 'Remember Me', 'type': 'checkbox', 'help': 'Keep me logged in'}
        ],
        'contact': [
            {'name': 'name', 'label': 'Full Name', 'type': 'text', 'required': True, 'placeholder': 'Enter your full name'},
            {'name': 'email', 'label': 'Email Address', 'type': 'email', 'required': True, 'placeholder': 'Enter your email'},
            {'name': 'phone', 'label': 'Phone Number', 'type': 'tel', 'placeholder': 'Enter your phone number (optional)', 
             'help': 'Optional, but must be at least 10 digits if provided'},
            {'name': 'subject', 'label': 'Subject', 'type': 'text', 'required': True, 'placeholder': 'Subject of your message'},
            {'name': 'priority', 'label': 'Priority Level', 'type': 'select', 'required': True, 'options': [
                {'value': 'low', 'label': 'Low'},
                {'value': 'medium', 'label': 'Medium', 'selected': True},
                {'value': 'high', 'label': 'High'},
                {'value': 'urgent', 'label': 'Urgent'}
            ]},
            {'name': 'message', 'label': 'Message', 'type': 'textarea', 'required': True, 'rows': 4, 
             'placeholder': 'Your message', 'help': 'Minimum 10 characters, maximum 2000'},
            {'name': 'subscribe', 'label': 'Subscribe to newsletter', 'type': 'checkbox'}
        ],
        'profile': [
            {'name': 'first_name', 'label': 'First Name', 'type': 'text', 'required': True, 'placeholder': 'Enter your first name'},
            {'name': 'last_name', 'label': 'Last Name', 'type': 'text', 'required': True, 'placeholder': 'Enter your last name'},
            {'name': 'email', 'label': 'Email Address', 'type': 'email', 'required': True, 'placeholder': 'Enter your email'},
            {'name': 'phone', 'label': 'Phone Number', 'type': 'tel', 'placeholder': 'Enter your phone number'},
            {'name': 'username', 'label': 'Username', 'type': 'text', 'required': True, 'placeholder': 'Choose a username', 
             'help': 'Letters, numbers, and underscores only'},
            {'name': 'role', 'label': 'Role', 'type': 'select', 'required': True, 'options': [
                {'value': 'user', 'label': 'User', 'selected': True},
                {'value': 'admin', 'label': 'Administrator'},
                {'value': 'moderator', 'label': 'Moderator'},
                {'value': 'guest', 'label': 'Guest'}
            ]},
            {'name': 'bio', 'label': 'Biography', 'type': 'textarea', 'rows': 4, 'placeholder': 'Tell us about yourself',
             'help': 'Maximum 500 characters'},
            {'name': 'birth_date', 'label': 'Birth Date', 'type': 'date'},
            {'name': 'country', 'label': 'Country', 'type': 'select', 'required': True, 'options': [
                {'value': '', 'label': 'Select your country'},
                {'value': 'us', 'label': 'United States'},
                {'value': 'ca', 'label': 'Canada'},
                {'value': 'uk', 'label': 'United Kingdom'},
                {'value': 'au', 'label': 'Australia'},
                {'value': 'de', 'label': 'Germany'},
                {'value': 'fr', 'label': 'France'},
                {'value': 'jp', 'label': 'Japan'}
            ]},
            {'name': 'timezone', 'label': 'Timezone', 'type': 'select', 'options': [
                {'value': 'UTC', 'label': 'UTC (Coordinated Universal Time)', 'selected': True},
                {'value': 'EST', 'label': 'EST (Eastern Standard Time)'},
                {'value': 'PST', 'label': 'PST (Pacific Standard Time)'},
                {'value': 'GMT', 'label': 'GMT (Greenwich Mean Time)'},
                {'value': 'CET', 'label': 'CET (Central European Time)'}
            ]},
            {'name': 'newsletter', 'label': 'Subscribe to Newsletter', 'type': 'checkbox'},
            {'name': 'notifications', 'label': 'Enable Email Notifications', 'type': 'checkbox', 'checked': True}
        ],
        'kitchen_sink': [
            # Text inputs
            {'name': 'text_field', 'label': 'Text Input', 'type': 'text', 'required': True, 'placeholder': 'Enter some text'},
            {'name': 'email_field', 'label': 'Email Input', 'type': 'email', 'required': True, 'placeholder': 'Enter your email'},
            {'name': 'password_field', 'label': 'Password', 'type': 'password', 'required': True, 'placeholder': 'Enter password'},
            {'name': 'url_field', 'label': 'URL Input', 'type': 'url', 'placeholder': 'https://example.com'},
            {'name': 'search_field', 'label': 'Search Input', 'type': 'search', 'placeholder': 'Search...'},
            {'name': 'tel_field', 'label': 'Phone Input', 'type': 'tel', 'placeholder': '+1-555-123-4567'},
            
            # Numeric inputs
            {'name': 'integer_field', 'label': 'Integer (1-100)', 'type': 'number', 'required': True, 'min': 1, 'max': 100},
            {'name': 'float_field', 'label': 'Decimal Number', 'type': 'number', 'required': True, 'min': 0, 'max': 1000, 'step': 0.01},
            {'name': 'range_field', 'label': 'Range Slider', 'type': 'range', 'min': 0, 'max': 100, 'value': 50},
            
            # Selection inputs
            {'name': 'select_field', 'label': 'Select Dropdown', 'type': 'select', 'required': True, 'options': [
                {'value': '', 'label': 'Choose an option...'},
                {'value': 'option1', 'label': 'Option 1'},
                {'value': 'option2', 'label': 'Option 2'},
                {'value': 'option3', 'label': 'Option 3'}
            ]},
            {'name': 'radio_field', 'label': 'Radio Group', 'type': 'radio', 'required': True, 'options': [
                {'value': 'red', 'label': 'Red'},
                {'value': 'green', 'label': 'Green'},
                {'value': 'blue', 'label': 'Blue'}
            ]},
            {'name': 'multiselect_field', 'label': 'Multiple Select', 'type': 'multiselect', 'options': [
                {'value': 'tag1', 'label': 'Tag 1'},
                {'value': 'tag2', 'label': 'Tag 2'},
                {'value': 'tag3', 'label': 'Tag 3'},
                {'value': 'tag4', 'label': 'Tag 4'}
            ]},
            
            # Date/time inputs
            {'name': 'date_field', 'label': 'Date Picker', 'type': 'date', 'required': True},
            {'name': 'datetime_field', 'label': 'Date & Time', 'type': 'datetime-local'},
            {'name': 'time_field', 'label': 'Time Picker', 'type': 'time'},
            
            # Text areas
            {'name': 'textarea_field', 'label': 'Text Area', 'type': 'textarea', 'required': True, 'rows': 4, 
             'placeholder': 'Enter your message'},
            
            # Specialized inputs
            {'name': 'color_field', 'label': 'Color Picker', 'type': 'color', 'value': '#ff0000'},
            {'name': 'file_field', 'label': 'File Upload', 'type': 'file', 'accept': '.pdf,.jpg,.png,.doc,.docx'},
            
            # Checkboxes
            {'name': 'checkbox_field', 'label': 'Checkbox Option', 'type': 'checkbox'},
            {'name': 'terms_accepted', 'label': 'I accept the terms and conditions', 'type': 'checkbox', 'required': True}
        ]
    }

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Main overview page."""
    return render_template('index.html')

@app.route('/bootstrap/')
def bootstrap_index():
    """Bootstrap version main page."""
    return render_template('bootstrap/index.html', theme='bootstrap')

@app.route('/material/')
def material_index():
    """Material Design version main page."""
    return render_template('material/index.html', theme='material')

# Bootstrap Routes
@app.route('/bootstrap/minimal', methods=['GET', 'POST'])
def bootstrap_minimal():
    """Bootstrap minimal forms."""
    login_result = None
    contact_result = None
    
    if request.method == 'POST':
        if 'login_submit' in request.form:
            login_result = handle_form_submission(LoginModel, "Login successful!")
        elif 'contact_submit' in request.form:
            contact_result = handle_form_submission(ContactModel, "Contact form submitted successfully!")
    
    form_configs = get_form_field_config()
    return render_template('bootstrap/minimal.html', 
                         theme='bootstrap',
                         login_fields=form_configs['login'],
                         contact_fields=form_configs['contact'],
                         login_result=login_result,
                         contact_result=contact_result)

@app.route('/bootstrap/medium', methods=['GET', 'POST'])
def bootstrap_medium():
    """Bootstrap medium complexity forms."""
    profile_result = None
    
    if request.method == 'POST':
        profile_result = handle_form_submission(UserProfileModel, "Profile updated successfully!")
    
    form_configs = get_form_field_config()
    return render_template('bootstrap/medium.html', 
                         theme='bootstrap',
                         profile_fields=form_configs['profile'],
                         profile_result=profile_result)

@app.route('/bootstrap/kitchen', methods=['GET', 'POST'])
def bootstrap_kitchen():
    """Bootstrap kitchen sink forms."""
    kitchen_result = None
    
    if request.method == 'POST':
        kitchen_result = handle_form_submission(KitchenSinkModel, "Kitchen sink form submitted successfully!")
    
    form_configs = get_form_field_config()
    return render_template('bootstrap/kitchen.html', 
                         theme='bootstrap',
                         kitchen_fields=form_configs['kitchen_sink'],
                         kitchen_result=kitchen_result)

# Material Design Routes
@app.route('/material/minimal', methods=['GET', 'POST'])
def material_minimal():
    """Material Design minimal forms."""
    login_result = None
    contact_result = None
    
    if request.method == 'POST':
        if 'login_submit' in request.form:
            login_result = handle_form_submission(LoginModel, "Login successful!")
        elif 'contact_submit' in request.form:
            contact_result = handle_form_submission(ContactModel, "Contact form submitted successfully!")
    
    form_configs = get_form_field_config()
    return render_template('material/minimal.html', 
                         theme='material',
                         login_fields=form_configs['login'],
                         contact_fields=form_configs['contact'],
                         login_result=login_result,
                         contact_result=contact_result)

@app.route('/material/medium', methods=['GET', 'POST'])
def material_medium():
    """Material Design medium complexity forms."""
    profile_result = None
    
    if request.method == 'POST':
        profile_result = handle_form_submission(UserProfileModel, "Profile updated successfully!")
    
    form_configs = get_form_field_config()
    return render_template('material/medium.html', 
                         theme='material',
                         profile_fields=form_configs['profile'],
                         profile_result=profile_result)

@app.route('/material/kitchen', methods=['GET', 'POST'])
def material_kitchen():
    """Material Design kitchen sink forms."""
    kitchen_result = None
    
    if request.method == 'POST':
        kitchen_result = handle_form_submission(KitchenSinkModel, "Kitchen sink form submitted successfully!")
    
    form_configs = get_form_field_config()
    return render_template('material/kitchen.html', 
                         theme='material',
                         kitchen_fields=form_configs['kitchen_sink'],
                         kitchen_result=kitchen_result)

if __name__ == '__main__':
    print("🚀 Starting Comprehensive Pydantic Forms Demo...")
    print("📄 Visit: http://localhost:5000/")
    print("🎨 Bootstrap: http://localhost:5000/bootstrap/")
    print("🎨 Material: http://localhost:5000/material/")
    
    app.run(debug=True, host='0.0.0.0', port=5000)