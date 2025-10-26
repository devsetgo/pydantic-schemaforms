"""
Comprehensive Flask Examples for Pydantic Forms

This file demonstrates the full capabilities of the pydantic-forms library
with Flask integration. It includes:

1. Minimal Forms (Login, Contact)
2. Medium Complexity Forms (User Registration, Profile)
3. Kitchen Sink Forms (All input types and features)
4. Different Layout Systems (Vertical, Horizontal, Grid, Tabs, Cards)
5. Validation Examples (Client & Server-side)
6. Advanced Features (CSRF, Honeypot, File uploads)

Run this example:
    python flask_examples.py

Then visit:
    http://localhost:5001/          - Overview page
    http://localhost:5001/minimal   - Minimal forms
    http://localhost:5001/medium    - Medium complexity
    http://localhost:5001/kitchen   - Kitchen sink
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum

# Import pydantic-forms components
from pydantic_forms.integration import (
    FormBuilder, AutoFormBuilder, create_login_form, create_contact_form,
    create_registration_form, render_form_page, FormIntegration
)
from pydantic_forms.modern_renderer import FormField, FormSection, FormDefinition
from pydantic_forms.layouts import (
    Layout, HorizontalLayout, VerticalLayout, GridLayout, 
    TabLayout, CardLayout, ResponsiveGridLayout
)

app = Flask(__name__)
app.secret_key = 'demo-secret-key-change-in-production'

# ============================================================================
# PYDANTIC MODELS FOR FORMS
# ============================================================================

class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"

class LoginModel(BaseModel):
    """Simple login model."""
    email: EmailStr = Field(..., description="Your email address")
    password: str = Field(..., min_length=6, description="Your password")
    remember_me: bool = Field(False, description="Keep me logged in")

class ContactModel(BaseModel):
    """Contact form model."""
    name: str = Field(..., min_length=2, max_length=100, description="Your full name")
    email: EmailStr = Field(..., description="Your email address")
    subject: str = Field(..., min_length=5, max_length=200, description="Subject of your message")
    message: str = Field(..., min_length=10, max_length=2000, description="Your message")
    urgency: str = Field("medium", description="How urgent is this?")
    subscribe: bool = Field(False, description="Subscribe to newsletter")

class UserProfileModel(BaseModel):
    """Medium complexity user profile model."""
    # Personal Information
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(...)
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    
    # Account Settings
    username: str = Field(..., min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$')
    role: UserRole = Field(UserRole.USER)
    bio: Optional[str] = Field(None, max_length=500)
    
    # Preferences
    birth_date: Optional[date] = Field(None)
    newsletter: bool = Field(False)
    notifications: bool = Field(True)
    
    # Location
    country: str = Field(..., description="Your country")
    timezone: str = Field("UTC", description="Your timezone")

class KitchenSinkModel(BaseModel):
    """Comprehensive model showcasing all input types and features."""
    
    # === TEXT INPUTS ===
    text_field: str = Field(..., min_length=2, max_length=100, description="Basic text input")
    email_field: EmailStr = Field(..., description="Email with validation")
    password_field: str = Field(..., min_length=8, description="Password field")
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
    checkbox_field: bool = Field(False, description="Single checkbox")
    multiselect_field: List[str] = Field(default_factory=list, description="Multiple selection")
    
    # === DATE/TIME INPUTS ===
    date_field: date = Field(..., description="Date picker")
    datetime_field: datetime = Field(..., description="Date and time picker")
    time_field: Optional[str] = Field(None, description="Time picker")
    month_field: Optional[str] = Field(None, description="Month picker")
    week_field: Optional[str] = Field(None, description="Week picker")
    
    # === TEXT AREAS ===
    textarea_field: str = Field(..., min_length=10, max_length=1000, description="Large text area")
    code_field: Optional[str] = Field(None, description="Code input area")
    
    # === SPECIALIZED INPUTS ===
    color_field: str = Field("#ff0000", description="Color picker")
    file_field: Optional[str] = Field(None, description="File upload")
    image_field: Optional[str] = Field(None, description="Image upload")
    hidden_field: str = Field("hidden_value", description="Hidden field")
    
    # === ADVANCED VALIDATIONS ===
    confirm_password: str = Field(..., description="Confirm password")
    terms_accepted: bool = Field(..., description="Accept terms and conditions")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password_field' in info.data and v != info.data['password_field']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('terms_accepted')
    @classmethod
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_base_template():
    """Get the base HTML template with Bootstrap and navigation."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Pydantic Forms Flask Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .navbar { box-shadow: 0 2px 4px rgba(0,0,0,.1); }
        .form-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,.1);
            padding: 2rem;
            margin: 2rem 0;
        }
        .demo-section {
            border-left: 4px solid #0d6efd;
            padding-left: 1rem;
            margin: 2rem 0;
        }
        .code-preview {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .layout-tabs .nav-link {
            border-radius: 8px 8px 0 0;
        }
        .feature-badge {
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
        }
        .result-display {
            background: #e7f3ff;
            border: 1px solid #b6d7ff;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
        .error-display {
            background: #ffe7e7;
            border: 1px solid #ffb6b6;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="bi bi-form"></i> Pydantic Forms Demo
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Overview</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/minimal">Minimal Forms</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/medium">Medium Complexity</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/kitchen">Kitchen Sink</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/layouts">Layout Examples</a>
                    </li>
                </ul>
                <span class="navbar-text">
                    <i class="bi bi-github"></i> Pydantic Forms v25.4.1b1
                </span>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container">
        {{ content|safe }}
    </div>

    <!-- Footer -->
    <footer class="mt-5 py-4 bg-light border-top">
        <div class="container text-center text-muted">
            <p>Pydantic Forms Flask Demo - Showcasing form generation with Python 3.14+ template strings</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Enhanced form validation and UX
        document.addEventListener('DOMContentLoaded', function() {
            // Add form submission handling
            document.querySelectorAll('form').forEach(form => {
                form.addEventListener('submit', function(e) {
                    // Add loading state
                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing...';
                        submitBtn.disabled = true;
                    }
                });
            });
            
            // Add real-time validation feedback
            document.querySelectorAll('input, select, textarea').forEach(input => {
                input.addEventListener('blur', function() {
                    if (this.checkValidity()) {
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                    } else {
                        this.classList.remove('is-valid');
                        this.classList.add('is-invalid');
                    }
                });
            });
        });
    </script>
</body>
</html>
    """

def render_page(title, content):
    """Render a page with the base template."""
    template = get_base_template()
    from markupsafe import Markup
    return render_template_string(template, title=title, content=Markup(content))

def handle_form_submission(form_model, success_message="Form submitted successfully!"):
    """Handle form submission with validation and feedback."""
    if request.method == 'POST':
        try:
            # Get form data
            form_data = request.form.to_dict()
            
            # Handle checkboxes (they don't appear in form data if unchecked)
            for field_name, field_info in form_model.model_fields.items():
                if field_info.annotation == bool and field_name not in form_data:
                    form_data[field_name] = False
                elif field_info.annotation == bool and form_data.get(field_name) == 'on':
                    form_data[field_name] = True
            
            # Handle multiselect fields
            for key in request.form.keys():
                if len(request.form.getlist(key)) > 1:
                    form_data[key] = request.form.getlist(key)
            
            # Validate with Pydantic model
            validated_data = form_model(**form_data)
            
            flash(success_message, 'success')
            return {
                'success': True,
                'data': validated_data.dict(),
                'message': success_message
            }
            
        except Exception as e:
            error_msg = str(e)
            flash(f'Form validation failed: {error_msg}', 'error')
            return {
                'success': False,
                'data': form_data,
                'errors': {'general': [error_msg]},
                'message': error_msg
            }
    
    return None

def create_simple_form_html(fields_data):
    """Create simple HTML form from field data."""
    html_parts = []
    
    for field in fields_data:
        field_html = f"""
        <div class="mb-3">
            <label for="{field['name']}" class="form-label">
                {field['label']}
                {'<span class="text-danger">*</span>' if field.get('required') else ''}
            </label>
        """
        
        if field['type'] == 'text':
            field_html += f'<input type="text" class="form-control" id="{field["name"]}" name="{field["name"]}" placeholder="{field.get("placeholder", "")}" {"required" if field.get("required") else ""}>'
        elif field['type'] == 'email':
            field_html += f'<input type="email" class="form-control" id="{field["name"]}" name="{field["name"]}" placeholder="{field.get("placeholder", "")}" {"required" if field.get("required") else ""}>'
        elif field['type'] == 'password':
            field_html += f'<input type="password" class="form-control" id="{field["name"]}" name="{field["name"]}" placeholder="{field.get("placeholder", "")}" {"required" if field.get("required") else ""}>'
        elif field['type'] == 'textarea':
            rows = field.get('rows', 3)
            field_html += f'<textarea class="form-control" id="{field["name"]}" name="{field["name"]}" rows="{rows}" placeholder="{field.get("placeholder", "")}" {"required" if field.get("required") else ""}></textarea>'
        elif field['type'] == 'select':
            field_html += f'<select class="form-select" id="{field["name"]}" name="{field["name"]}" {"required" if field.get("required") else ""}>'
            for option in field.get('options', []):
                selected = 'selected' if option.get('selected') else ''
                field_html += f'<option value="{option["value"]}" {selected}>{option["label"]}</option>'
            field_html += '</select>'
        elif field['type'] == 'checkbox':
            field_html += f"""
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="{field["name"]}" name="{field["name"]}" value="true">
                <label class="form-check-label" for="{field["name"]}">
                    {field['label']}
                </label>
            </div>"""
            continue  # Skip the closing div since checkbox has its own structure
        elif field['type'] == 'file':
            accept = f'accept="{field["accept"]}"' if field.get('accept') else ''
            field_html += f'<input type="file" class="form-control" id="{field["name"]}" name="{field["name"]}" {accept} {"required" if field.get("required") else ""}>'
        elif field['type'] == 'number':
            min_attr = f'min="{field["min"]}"' if field.get('min') is not None else ''
            max_attr = f'max="{field["max"]}"' if field.get('max') is not None else ''
            field_html += f'<input type="number" class="form-control" id="{field["name"]}" name="{field["name"]}" {min_attr} {max_attr} placeholder="{field.get("placeholder", "")}" {"required" if field.get("required") else ""}>'
        elif field['type'] == 'date':
            field_html += f'<input type="date" class="form-control" id="{field["name"]}" name="{field["name"]}" {"required" if field.get("required") else ""}>'
        else:
            field_html += f'<input type="text" class="form-control" id="{field["name"]}" name="{field["name"]}" placeholder="{field.get("placeholder", "")}" {"required" if field.get("required") else ""}>'
        
        if field['type'] != 'checkbox':
            field_html += '</div>'
        
        html_parts.append(field_html)
    
    return '\n'.join(html_parts)
    """Handle form submission with validation and feedback."""
    if request.method == 'POST':
        try:
            # Get form data
            form_data = request.form.to_dict()
            
            # Handle checkboxes (they don't appear in form data if unchecked)
            for field_name, field_info in form_model.model_fields.items():
                if field_info.annotation == bool and field_name not in form_data:
                    form_data[field_name] = False
                elif field_info.annotation == bool and form_data.get(field_name) == 'on':
                    form_data[field_name] = True
            
            # Handle multiselect fields
            for key in request.form.keys():
                if len(request.form.getlist(key)) > 1:
                    form_data[key] = request.form.getlist(key)
            
            # Validate with Pydantic model
            validated_data = form_model(**form_data)
            
            flash(success_message, 'success')
            return {
                'success': True,
                'data': validated_data.dict(),
                'message': success_message
            }
            
        except Exception as e:
            error_msg = str(e)
            flash(f'Form validation failed: {error_msg}', 'error')
            return {
                'success': False,
                'data': form_data,
                'errors': {'general': [error_msg]},
                'message': error_msg
            }
    
    return None

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Main overview page showcasing all examples."""
    content = """
    <div class="row">
        <div class="col-12">
            <div class="text-center mb-5">
                <h1 class="display-4 fw-bold text-primary">
                    <i class="bi bi-form"></i> Pydantic Forms Flask Demo
                </h1>
                <p class="lead">Comprehensive examples of form generation using Python 3.14+ template strings</p>
                <div class="d-flex justify-content-center gap-2">
                    <span class="badge bg-primary feature-badge">Python 3.14+</span>
                    <span class="badge bg-success feature-badge">Type-Safe</span>
                    <span class="badge bg-info feature-badge">Auto-Generated</span>
                    <span class="badge bg-warning feature-badge">Multi-Framework</span>
                </div>
            </div>
        </div>
    </div>

    <div class="row g-4">
        <!-- Minimal Forms -->
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="bi bi-lightning-charge fs-3 text-success me-2"></i>
                        <h5 class="card-title mb-0">Minimal Forms</h5>
                    </div>
                    <p class="card-text">Simple, essential forms like login and contact. Perfect for getting started quickly.</p>
                    <ul class="list-unstyled small text-muted">
                        <li><i class="bi bi-check2"></i> Login form</li>
                        <li><i class="bi bi-check2"></i> Contact form</li>
                        <li><i class="bi bi-check2"></i> Basic validation</li>
                        <li><i class="bi bi-check2"></i> Clean layouts</li>
                    </ul>
                    <a href="/minimal" class="btn btn-success">
                        <i class="bi bi-arrow-right"></i> View Examples
                    </a>
                </div>
            </div>
        </div>

        <!-- Medium Complexity -->
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="bi bi-gear fs-3 text-primary me-2"></i>
                        <h5 class="card-title mb-0">Medium Complexity</h5>
                    </div>
                    <p class="card-text">User registration and profile forms with advanced validation and multiple field types.</p>
                    <ul class="list-unstyled small text-muted">
                        <li><i class="bi bi-check2"></i> User profiles</li>
                        <li><i class="bi bi-check2"></i> Multiple sections</li>
                        <li><i class="bi bi-check2"></i> Advanced validation</li>
                        <li><i class="bi bi-check2"></i> File uploads</li>
                    </ul>
                    <a href="/medium" class="btn btn-primary">
                        <i class="bi bi-arrow-right"></i> View Examples
                    </a>
                </div>
            </div>
        </div>

        <!-- Kitchen Sink -->
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="bi bi-stars fs-3 text-warning me-2"></i>
                        <h5 class="card-title mb-0">Kitchen Sink</h5>
                    </div>
                    <p class="card-text">Complete showcase of every input type, layout option, and advanced feature available.</p>
                    <ul class="list-unstyled small text-muted">
                        <li><i class="bi bi-check2"></i> All input types</li>
                        <li><i class="bi bi-check2"></i> Every layout</li>
                        <li><i class="bi bi-check2"></i> CSRF protection</li>
                        <li><i class="bi bi-check2"></i> Advanced features</li>
                    </ul>
                    <a href="/kitchen" class="btn btn-warning">
                        <i class="bi bi-arrow-right"></i> View Examples
                    </a>
                </div>
            </div>
        </div>

        <!-- Layout Showcase -->
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="bi bi-grid-3x3 fs-3 text-info me-2"></i>
                        <h5 class="card-title mb-0">Layout Systems</h5>
                    </div>
                    <p class="card-text">Explore different layout options: vertical, horizontal, grid, tabs, and cards.</p>
                    <ul class="list-unstyled small text-muted">
                        <li><i class="bi bi-check2"></i> Responsive grids</li>
                        <li><i class="bi bi-check2"></i> Tab layouts</li>
                        <li><i class="bi bi-check2"></i> Card layouts</li>
                        <li><i class="bi bi-check2"></i> Custom layouts</li>
                    </ul>
                    <a href="/layouts" class="btn btn-info">
                        <i class="bi bi-arrow-right"></i> View Examples
                    </a>
                </div>
            </div>
        </div>

        <!-- Documentation -->
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="bi bi-book fs-3 text-secondary me-2"></i>
                        <h5 class="card-title mb-0">Documentation</h5>
                    </div>
                    <p class="card-text">Complete API documentation and integration guides for production use.</p>
                    <ul class="list-unstyled small text-muted">
                        <li><i class="bi bi-check2"></i> API Reference</li>
                        <li><i class="bi bi-check2"></i> Integration guides</li>
                        <li><i class="bi bi-check2"></i> Best practices</li>
                        <li><i class="bi bi-check2"></i> Examples</li>
                    </ul>
                    <a href="/docs" class="btn btn-secondary">
                        <i class="bi bi-arrow-right"></i> View Docs
                    </a>
                </div>
            </div>
        </div>

        <!-- Code Examples -->
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <i class="bi bi-code-slash fs-3 text-dark me-2"></i>
                        <h5 class="card-title mb-0">Source Code</h5>
                    </div>
                    <p class="card-text">View the source code for all examples and learn how to implement them.</p>
                    <ul class="list-unstyled small text-muted">
                        <li><i class="bi bi-check2"></i> Flask integration</li>
                        <li><i class="bi bi-check2"></i> Pydantic models</li>
                        <li><i class="bi bi-check2"></i> Form builders</li>
                        <li><i class="bi bi-check2"></i> Validation</li>
                    </ul>
                    <a href="https://github.com/devsetgo/pydantic-forms" class="btn btn-dark" target="_blank">
                        <i class="bi bi-github"></i> View on GitHub
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- Features Overview -->
    <div class="row mt-5">
        <div class="col-12">
            <div class="form-container">
                <h2 class="text-center mb-4">Key Features</h2>
                <div class="row g-4">
                    <div class="col-md-4 text-center">
                        <i class="bi bi-lightning-charge fs-1 text-success"></i>
                        <h5 class="mt-2">Type-Safe</h5>
                        <p class="text-muted">Built on Pydantic for automatic validation and type safety</p>
                    </div>
                    <div class="col-md-4 text-center">
                        <i class="bi bi-palette fs-1 text-primary"></i>
                        <h5 class="mt-2">Multi-Framework</h5>
                        <p class="text-muted">Works with Bootstrap, Material, Tailwind, and custom themes</p>
                    </div>
                    <div class="col-md-4 text-center">
                        <i class="bi bi-shield-check fs-1 text-warning"></i>
                        <h5 class="mt-2">Security</h5>
                        <p class="text-muted">Built-in CSRF protection, honeypot fields, and input sanitization</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    
    return render_page("Home", content)

@app.route('/minimal', methods=['GET', 'POST'])
def minimal_forms():
    """Minimal forms examples - login and contact."""
    
    # Handle form submissions
    login_result = None
    contact_result = None
    
    if request.method == 'POST':
        if 'login_submit' in request.form:
            login_result = handle_form_submission(LoginModel, "Login successful!")
        elif 'contact_submit' in request.form:
            contact_result = handle_form_submission(ContactModel, "Message sent successfully!")
    
    # Define login form fields
    login_fields = [
        {'name': 'email', 'label': 'Email Address', 'type': 'email', 'required': True, 'placeholder': 'Enter your email'},
        {'name': 'password', 'label': 'Password', 'type': 'password', 'required': True, 'placeholder': 'Enter your password'},
        {'name': 'remember_me', 'label': 'Remember Me', 'type': 'checkbox'}
    ]
    
    # Define contact form fields
    contact_fields = [
        {'name': 'name', 'label': 'Full Name', 'type': 'text', 'required': True, 'placeholder': 'Enter your full name'},
        {'name': 'email', 'label': 'Email Address', 'type': 'email', 'required': True, 'placeholder': 'Enter your email'},
        {'name': 'subject', 'label': 'Subject', 'type': 'text', 'required': True, 'placeholder': 'Subject of your message'},
        {'name': 'urgency', 'label': 'Urgency Level', 'type': 'select', 'required': True, 'options': [
            {'value': 'low', 'label': 'Low'},
            {'value': 'medium', 'label': 'Medium', 'selected': True},
            {'value': 'high', 'label': 'High'},
            {'value': 'urgent', 'label': 'Urgent'}
        ]},
        {'name': 'message', 'label': 'Message', 'type': 'textarea', 'required': True, 'rows': 4, 'placeholder': 'Your message'},
        {'name': 'subscribe', 'label': 'Subscribe to newsletter', 'type': 'checkbox'}
    ]
    
    login_form_html = create_simple_form_html(login_fields)
    contact_form_html = create_simple_form_html(contact_fields)
    
    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-lightning-charge"></i> Minimal Forms</h1>
        <p class="lead">Simple, essential forms that get the job done quickly and efficiently.</p>
    </div>

    <div class="row">
        <!-- Login Form -->
        <div class="col-lg-6">
            <div class="form-container">
                <h3><i class="bi bi-person-lock"></i> Login Form</h3>
                <p class="text-muted">Essential authentication form with email and password.</p>
                
                {'<div class="result-display"><strong>Success!</strong> ' + str(login_result) + '</div>' if login_result and login_result.get('success') else ''}
                {'<div class="error-display"><strong>Error:</strong> ' + str(login_result.get('message', '')) + '</div>' if login_result and not login_result.get('success') else ''}
                
                <form method="POST" class="needs-validation" novalidate>
                    {login_form_html}
                    <input type="hidden" name="login_submit" value="1">
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-box-arrow-in-right"></i> Sign In
                        </button>
                    </div>
                </form>
                
                <div class="code-preview mt-4">
                    <h6><i class="bi bi-code"></i> Code Example:</h6>
                    <pre><code># Define form fields
login_fields = [
    {{'name': 'email', 'label': 'Email', 'type': 'email', 'required': True}},
    {{'name': 'password', 'label': 'Password', 'type': 'password', 'required': True}},
    {{'name': 'remember_me', 'label': 'Remember Me', 'type': 'checkbox'}}
]

# Render HTML
html = create_simple_form_html(login_fields)</code></pre>
                </div>
            </div>
        </div>

        <!-- Contact Form -->
        <div class="col-lg-6">
            <div class="form-container">
                <h3><i class="bi bi-envelope"></i> Contact Form</h3>
                <p class="text-muted">Standard contact form with subject and message fields.</p>
                
                {'<div class="result-display"><strong>Success!</strong> ' + str(contact_result) + '</div>' if contact_result and contact_result.get('success') else ''}
                {'<div class="error-display"><strong>Error:</strong> ' + str(contact_result.get('message', '')) + '</div>' if contact_result and not contact_result.get('success') else ''}
                
                <form method="POST" class="needs-validation" novalidate>
                    {contact_form_html}
                    <input type="hidden" name="contact_submit" value="1">
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-success">
                            <i class="bi bi-send"></i> Send Message
                        </button>
                    </div>
                </form>
                
                <div class="code-preview mt-4">
                    <h6><i class="bi bi-code"></i> Code Example:</h6>
                    <pre><code># Define contact form fields
contact_fields = [
    {{'name': 'name', 'label': 'Full Name', 'type': 'text', 'required': True}},
    {{'name': 'email', 'label': 'Email', 'type': 'email', 'required': True}},
    {{'name': 'subject', 'label': 'Subject', 'type': 'text', 'required': True}},
    {{'name': 'message', 'label': 'Message', 'type': 'textarea', 'required': True}},
    {{'name': 'urgency', 'label': 'Urgency', 'type': 'select', 'options': [...]}}
]

# Render form
html = create_simple_form_html(contact_fields)</code></pre>
                </div>
            </div>
        </div>
    </div>

    <!-- Features Overview -->
    <div class="row mt-4">
        <div class="col-12">
            <div class="form-container">
                <h4>Minimal Form Features</h4>
                <div class="row">
                    <div class="col-md-3">
                        <h6><i class="bi bi-check-circle text-success"></i> Clean Design</h6>
                        <p class="small text-muted">Simple, focused forms without clutter</p>
                    </div>
                    <div class="col-md-3">
                        <h6><i class="bi bi-shield-check text-success"></i> Built-in Validation</h6>
                        <p class="small text-muted">Automatic client and server-side validation</p>
                    </div>
                    <div class="col-md-3">
                        <h6><i class="bi bi-speedometer text-success"></i> Fast Setup</h6>
                        <p class="small text-muted">Create forms with just a few lines of code</p>
                    </div>
                    <div class="col-md-3">
                        <h6><i class="bi bi-phone text-success"></i> Responsive</h6>
                        <p class="small text-muted">Works perfectly on all device sizes</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    
    return render_page("Minimal Forms", content)

@app.route('/medium', methods=['GET', 'POST'])
def medium_forms():
    """Medium complexity forms - user registration and profiles."""
    
    # Handle form submissions
    profile_result = None
    
    if request.method == 'POST':
        if 'profile_submit' in request.form:
            profile_result = handle_form_submission(UserProfileModel, "Profile updated successfully!")
    
    # Define profile form fields
    profile_fields = [
        {'name': 'first_name', 'label': 'First Name', 'type': 'text', 'required': True, 'placeholder': 'Enter your first name'},
        {'name': 'last_name', 'label': 'Last Name', 'type': 'text', 'required': True, 'placeholder': 'Enter your last name'},
        {'name': 'email', 'label': 'Email Address', 'type': 'email', 'required': True, 'placeholder': 'Enter your email'},
        {'name': 'phone', 'label': 'Phone Number', 'type': 'text', 'placeholder': 'Enter your phone number'},
        {'name': 'username', 'label': 'Username', 'type': 'text', 'required': True, 'placeholder': 'Choose a username'},
        {'name': 'role', 'label': 'Role', 'type': 'select', 'required': True, 'options': [
            {'value': 'user', 'label': 'User', 'selected': True},
            {'value': 'admin', 'label': 'Administrator'},
            {'value': 'moderator', 'label': 'Moderator'},
            {'value': 'guest', 'label': 'Guest'}
        ]},
        {'name': 'bio', 'label': 'Biography', 'type': 'textarea', 'rows': 4, 'placeholder': 'Tell us about yourself'},
        {'name': 'birth_date', 'label': 'Birth Date', 'type': 'date'},
        {'name': 'country', 'label': 'Country', 'type': 'select', 'required': True, 'options': [
            {'value': 'us', 'label': 'United States'},
            {'value': 'ca', 'label': 'Canada'},
            {'value': 'uk', 'label': 'United Kingdom'},
            {'value': 'au', 'label': 'Australia'}
        ]},
        {'name': 'newsletter', 'label': 'Subscribe to Newsletter', 'type': 'checkbox'},
        {'name': 'notifications', 'label': 'Enable Notifications', 'type': 'checkbox'}
    ]
    
    profile_form_html = create_simple_form_html(profile_fields)
    
    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-gear"></i> Medium Complexity Forms</h1>
        <p class="lead">User profile form with advanced validation and multiple field types.</p>
    </div>

    <!-- Profile Form -->
    <div class="form-container">
        <h3><i class="bi bi-person-gear"></i> User Profile Form</h3>
        <p class="text-muted">Complete user profile with personal details, account settings, and preferences.</p>
        
        {'<div class="result-display"><strong>Success!</strong> ' + str(profile_result) + '</div>' if profile_result and profile_result.get('success') else ''}
        {'<div class="error-display"><strong>Error:</strong> ' + str(profile_result.get('message', '')) + '</div>' if profile_result and not profile_result.get('success') else ''}
        
        <form method="POST" class="needs-validation" novalidate>
            <!-- Personal Information Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-person"></i> Personal Information</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="first_name" class="form-label">First Name <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="first_name" name="first_name" placeholder="Enter your first name" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="last_name" class="form-label">Last Name <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="last_name" name="last_name" placeholder="Enter your last name" required>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email Address <span class="text-danger">*</span></label>
                                <input type="email" class="form-control" id="email" name="email" placeholder="Enter your email" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="phone" class="form-label">Phone Number</label>
                                <input type="text" class="form-control" id="phone" name="phone" placeholder="Enter your phone number">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Account Settings Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-gear"></i> Account Settings</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="username" name="username" placeholder="Choose a username" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="role" class="form-label">Role <span class="text-danger">*</span></label>
                                <select class="form-select" id="role" name="role" required>
                                    <option value="user" selected>User</option>
                                    <option value="admin">Administrator</option>
                                    <option value="moderator">Moderator</option>
                                    <option value="guest">Guest</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="bio" class="form-label">Biography</label>
                        <textarea class="form-control" id="bio" name="bio" rows="4" placeholder="Tell us about yourself"></textarea>
                    </div>
                </div>
            </div>
            
            <!-- Preferences Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-sliders"></i> Preferences</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="birth_date" class="form-label">Birth Date</label>
                                <input type="date" class="form-control" id="birth_date" name="birth_date">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="country" class="form-label">Country <span class="text-danger">*</span></label>
                                <select class="form-select" id="country" name="country" required>
                                    <option value="us">United States</option>
                                    <option value="ca">Canada</option>
                                    <option value="uk">United Kingdom</option>
                                    <option value="au">Australia</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="newsletter" name="newsletter" value="true">
                                <label class="form-check-label" for="newsletter">
                                    Subscribe to Newsletter
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="notifications" name="notifications" value="true">
                                <label class="form-check-label" for="notifications">
                                    Enable Notifications
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <input type="hidden" name="profile_submit" value="1">
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-success">
                    <i class="bi bi-check-lg"></i> Update Profile
                </button>
            </div>
        </form>
        
        <div class="code-preview mt-4">
            <h6><i class="bi bi-code"></i> Sectioned Form Code:</h6>
            <pre><code># Organize form into logical sections with cards
&lt;div class="card"&gt;
    &lt;div class="card-header"&gt;
        &lt;h5&gt;Personal Information&lt;/h5&gt;
    &lt;/div&gt;
    &lt;div class="card-body"&gt;
        {{{{ form_fields }}}}
    &lt;/div&gt;
&lt;/div&gt;</code></pre>
        </div>
    </div>
    """
    
    return render_page("Medium Complexity", content)

@app.route('/kitchen', methods=['GET', 'POST'])
def kitchen_sink():
    """Kitchen sink form - showcasing all features."""
    
    # Handle form submission
    kitchen_result = None
    
    if request.method == 'POST':
        kitchen_result = handle_form_submission(KitchenSinkModel, "Kitchen sink form submitted successfully!")
    
    # Define comprehensive form fields
    kitchen_fields = [
        {'name': 'text_field', 'label': 'Text Input', 'type': 'text', 'required': True, 'placeholder': 'Enter some text'},
        {'name': 'email_field', 'label': 'Email Input', 'type': 'email', 'required': True, 'placeholder': 'Enter your email'},
        {'name': 'password_field', 'label': 'Password', 'type': 'password', 'required': True, 'placeholder': 'Enter password'},
        {'name': 'integer_field', 'label': 'Integer (1-100)', 'type': 'number', 'required': True, 'min': 1, 'max': 100, 'placeholder': 'Enter a number'},
        {'name': 'float_field', 'label': 'Decimal Number', 'type': 'number', 'required': True, 'min': 0, 'max': 1000, 'placeholder': 'Enter decimal'},
        {'name': 'textarea_field', 'label': 'Text Area', 'type': 'textarea', 'required': True, 'rows': 4, 'placeholder': 'Enter your message'},
        {'name': 'select_field', 'label': 'Select Dropdown', 'type': 'select', 'required': True, 'options': [
            {'value': 'option1', 'label': 'Option 1'},
            {'value': 'option2', 'label': 'Option 2'},
            {'value': 'option3', 'label': 'Option 3'}
        ]},
        {'name': 'radio_field', 'label': 'Radio Group', 'type': 'select', 'required': True, 'options': [
            {'value': 'red', 'label': 'Red'},
            {'value': 'green', 'label': 'Green'},
            {'value': 'blue', 'label': 'Blue'}
        ]},
        {'name': 'date_field', 'label': 'Date Picker', 'type': 'date', 'required': True},
        {'name': 'file_field', 'label': 'File Upload', 'type': 'file', 'accept': '.pdf,.jpg,.png'},
        {'name': 'checkbox_field', 'label': 'Checkbox Option', 'type': 'checkbox'},
        {'name': 'terms_accepted', 'label': 'I accept the terms and conditions', 'type': 'checkbox'}
    ]
    
    kitchen_form_html = create_simple_form_html(kitchen_fields)
    
    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-stars"></i> Kitchen Sink Form</h1>
        <p class="lead">Complete showcase of every input type, layout option, and advanced feature.</p>
    </div>

    <div class="form-container">
        <h3><i class="bi bi-collection"></i> All Input Types</h3>
        <p class="text-muted">This form demonstrates every available input type and feature in pydantic-forms.</p>
        
        {'<div class="result-display"><strong>Success!</strong> ' + str(kitchen_result) + '</div>' if kitchen_result and kitchen_result.get('success') else ''}
        {'<div class="error-display"><strong>Error:</strong> ' + str(kitchen_result.get('message', '')) + '</div>' if kitchen_result and not kitchen_result.get('success') else ''}
        
        <form method="POST" class="needs-validation" novalidate enctype="multipart/form-data">
            <!-- Text Inputs Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-input-cursor"></i> Text Inputs</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="text_field" class="form-label">Text Input <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="text_field" name="text_field" placeholder="Enter some text" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="email_field" class="form-label">Email Input <span class="text-danger">*</span></label>
                                <input type="email" class="form-control" id="email_field" name="email_field" placeholder="Enter your email" required>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="password_field" class="form-label">Password <span class="text-danger">*</span></label>
                                <input type="password" class="form-control" id="password_field" name="password_field" placeholder="Enter password" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="textarea_field" class="form-label">Text Area <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="textarea_field" name="textarea_field" rows="3" placeholder="Enter your message" required></textarea>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Numeric Inputs Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-123"></i> Numeric Inputs</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="integer_field" class="form-label">Integer (1-100) <span class="text-danger">*</span></label>
                                <input type="number" class="form-control" id="integer_field" name="integer_field" min="1" max="100" placeholder="Enter a number" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="float_field" class="form-label">Decimal Number <span class="text-danger">*</span></label>
                                <input type="number" class="form-control" id="float_field" name="float_field" min="0" max="1000" step="0.01" placeholder="Enter decimal" required>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Selection Inputs Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-ui-checks"></i> Selection Inputs</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="select_field" class="form-label">Select Dropdown <span class="text-danger">*</span></label>
                                <select class="form-select" id="select_field" name="select_field" required>
                                    <option value="">Choose an option...</option>
                                    <option value="option1">Option 1</option>
                                    <option value="option2">Option 2</option>
                                    <option value="option3">Option 3</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="radio_field" class="form-label">Color Choice <span class="text-danger">*</span></label>
                                <select class="form-select" id="radio_field" name="radio_field" required>
                                    <option value="">Choose a color...</option>
                                    <option value="red">Red</option>
                                    <option value="green">Green</option>
                                    <option value="blue">Blue</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Date and File Inputs Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-calendar3"></i> Date & File Inputs</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="date_field" class="form-label">Date Picker <span class="text-danger">*</span></label>
                                <input type="date" class="form-control" id="date_field" name="date_field" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="file_field" class="form-label">File Upload</label>
                                <input type="file" class="form-control" id="file_field" name="file_field" accept=".pdf,.jpg,.png">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Checkboxes Section -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0"><i class="bi bi-check-square"></i> Checkboxes</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="checkbox_field" name="checkbox_field" value="true">
                                <label class="form-check-label" for="checkbox_field">
                                    Checkbox Option
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="terms_accepted" name="terms_accepted" value="true">
                                <label class="form-check-label" for="terms_accepted">
                                    I accept the terms and conditions <span class="text-danger">*</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <input type="hidden" name="kitchen_submit" value="1">
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-warning">
                    <i class="bi bi-rocket"></i> Submit Kitchen Sink
                </button>
            </div>
        </form>
    </div>

    <!-- Features Overview -->
    <div class="form-container">
        <h4>Kitchen Sink Features</h4>
        <div class="row g-3">
            <div class="col-md-4">
                <h6><i class="bi bi-input-cursor text-primary"></i> Text Inputs</h6>
                <ul class="small">
                    <li>Text, Email, Password</li>
                    <li>URL, Phone, Search</li>
                    <li>Textarea with resizing</li>
                </ul>
            </div>
            <div class="col-md-4">
                <h6><i class="bi bi-123 text-success"></i> Numeric Inputs</h6>
                <ul class="small">
                    <li>Integer and Float</li>
                    <li>Range sliders</li>
                    <li>Min/Max validation</li>
                </ul>
            </div>
            <div class="col-md-4">
                <h6><i class="bi bi-ui-checks text-info"></i> Selection Inputs</h6>
                <ul class="small">
                    <li>Dropdowns and Multi-select</li>
                    <li>Radio buttons</li>
                    <li>Checkboxes</li>
                </ul>
            </div>
            <div class="col-md-4">
                <h6><i class="bi bi-calendar3 text-warning"></i> Date & Time</h6>
                <ul class="small">
                    <li>Date and DateTime pickers</li>
                    <li>Time input</li>
                    <li>Month/Week selectors</li>
                </ul>
            </div>
            <div class="col-md-4">
                <h6><i class="bi bi-file-earmark text-danger"></i> File Uploads</h6>
                <ul class="small">
                    <li>Single and Multiple files</li>
                    <li>Type restrictions</li>
                    <li>Image previews</li>
                </ul>
            </div>
            <div class="col-md-4">
                <h6><i class="bi bi-palette text-secondary"></i> Specialized</h6>
                <ul class="small">
                    <li>Color picker</li>
                    <li>Hidden fields</li>
                    <li>Custom components</li>
                </ul>
            </div>
        </div>
    </div>
    """
    
    return render_page("Kitchen Sink", content)

@app.route('/layouts')
def layout_examples():
    """Showcase different layout systems."""
    
    # Create sample form for layout demonstrations
    sample_form = FormBuilder(framework="bootstrap")
    sample_form.text_input("name", "Full Name")
    sample_form.email_input("email", "Email")
    sample_form.textarea_input("message", "Message", rows=3)
    
    # Render form with different layouts
    vertical_layout = sample_form.render()
    
    # Simple horizontal layout using CSS classes
    horizontal_layout_form = FormBuilder(framework="bootstrap")
    horizontal_layout_form.text_input("name", "Full Name")
    horizontal_layout_form.email_input("email", "Email")
    horizontal_layout_form.textarea_input("message", "Message", rows=3)
    
    horizontal_layout = f"""
    <div class="row">
        <div class="col-md-4">
            <div class="mb-3">
                <label class="form-label">Full Name</label>
                <input type="text" class="form-control" name="name" placeholder="Full Name">
            </div>
        </div>
        <div class="col-md-4">
            <div class="mb-3">
                <label class="form-label">Email</label>
                <input type="email" class="form-control" name="email" placeholder="Email">
            </div>
        </div>
        <div class="col-md-4">
            <div class="mb-3">
                <label class="form-label">Message</label>
                <textarea class="form-control" name="message" rows="3" placeholder="Message"></textarea>
            </div>
        </div>
    </div>
    """
    
    # Grid layout using Bootstrap grid
    grid_layout = f"""
    <div class="row g-3">
        <div class="col-md-6">
            <div class="mb-3">
                <label class="form-label">Full Name</label>
                <input type="text" class="form-control" name="name" placeholder="Full Name">
            </div>
        </div>
        <div class="col-md-6">
            <div class="mb-3">
                <label class="form-label">Email</label>
                <input type="email" class="form-control" name="email" placeholder="Email">
            </div>
        </div>
        <div class="col-12">
            <div class="mb-3">
                <label class="form-label">Message</label>
                <textarea class="form-control" name="message" rows="3" placeholder="Message"></textarea>
            </div>
        </div>
    </div>
    """
    
    # Tab layout using Bootstrap tabs
    tab_layout = f"""
    <ul class="nav nav-tabs" id="formTabs" role="tablist">
        <li class="nav-item" role="presentation">
            <button class="nav-link active" id="personal-tab" data-bs-toggle="tab" data-bs-target="#personal" type="button">
                Personal
            </button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="contact-tab" data-bs-toggle="tab" data-bs-target="#contact" type="button">
                Contact
            </button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="message-tab" data-bs-toggle="tab" data-bs-target="#message" type="button">
                Message
            </button>
        </li>
    </ul>
    <div class="tab-content" id="formTabContent">
        <div class="tab-pane fade show active" id="personal" role="tabpanel">
            <div class="p-3">
                <div class="mb-3">
                    <label class="form-label">Full Name</label>
                    <input type="text" class="form-control" name="name" placeholder="Full Name">
                </div>
            </div>
        </div>
        <div class="tab-pane fade" id="contact" role="tabpanel">
            <div class="p-3">
                <div class="mb-3">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-control" name="email" placeholder="Email">
                </div>
            </div>
        </div>
        <div class="tab-pane fade" id="message" role="tabpanel">
            <div class="p-3">
                <div class="mb-3">
                    <label class="form-label">Message</label>
                    <textarea class="form-control" name="message" rows="3" placeholder="Message"></textarea>
                </div>
            </div>
        </div>
    </div>
    """
    
    # Card layout
    card_layout = f"""
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Contact Form</h5>
            <p class="mb-0 text-muted">Get in touch with us</p>
        </div>
        <div class="card-body">
            {sample_form.render()}
        </div>
    </div>
    """
    
    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-grid-3x3"></i> Layout Systems</h1>
        <p class="lead">Explore different layout options for organizing your forms.</p>
    </div>

    <!-- Layout Tabs -->
    <div class="form-container">
        <ul class="nav nav-tabs layout-tabs" id="layoutTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="vertical-tab" data-bs-toggle="tab" data-bs-target="#vertical" type="button">
                    <i class="bi bi-arrow-down"></i> Vertical Layout
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="horizontal-tab" data-bs-toggle="tab" data-bs-target="#horizontal" type="button">
                    <i class="bi bi-arrow-right"></i> Horizontal Layout
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="grid-tab" data-bs-toggle="tab" data-bs-target="#grid" type="button">
                    <i class="bi bi-grid"></i> Grid Layout
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="tabs-tab" data-bs-toggle="tab" data-bs-target="#tabs" type="button">
                    <i class="bi bi-folder"></i> Tab Layout
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="cards-tab" data-bs-toggle="tab" data-bs-target="#cards" type="button">
                    <i class="bi bi-card-text"></i> Card Layout
                </button>
            </li>
        </ul>

        <div class="tab-content" id="layoutTabContent">
            <!-- Vertical Layout -->
            <div class="tab-pane fade show active" id="vertical" role="tabpanel">
                <div class="p-4">
                    <h5>Vertical Layout (Default)</h5>
                    <p class="text-muted">Standard form layout with fields stacked vertically.</p>
                    {vertical_layout}
                    <div class="code-preview mt-3">
                        <h6><i class="bi bi-code"></i> Code:</h6>
                        <pre><code>form = FormBuilder()
form.text_input("name", "Full Name")
form.email_input("email", "Email")
html = form.render()  # Default vertical layout</code></pre>
                    </div>
                </div>
            </div>

            <!-- Horizontal Layout -->
            <div class="tab-pane fade" id="horizontal" role="tabpanel">
                <div class="p-4">
                    <h5>Horizontal Layout</h5>
                    <p class="text-muted">Labels and inputs arranged horizontally for compact forms.</p>
                    <form class="needs-validation" novalidate>
                        {horizontal_layout}
                    </form>
                    <div class="code-preview mt-3">
                        <h6><i class="bi bi-code"></i> Code:</h6>
                        <pre><code># Using Bootstrap grid for horizontal layout
&lt;div class="row"&gt;
    &lt;div class="col-md-4"&gt;{{{{ field1 }}}}&lt;/div&gt;
    &lt;div class="col-md-4"&gt;{{{{ field2 }}}}&lt;/div&gt;
    &lt;div class="col-md-4"&gt;{{{{ field3 }}}}&lt;/div&gt;
&lt;/div&gt;</code></pre>
                    </div>
                </div>
            </div>

            <!-- Grid Layout -->
            <div class="tab-pane fade" id="grid" role="tabpanel">
                <div class="p-4">
                    <h5>Grid Layout</h5>
                    <p class="text-muted">Responsive grid system for multi-column forms.</p>
                    <form class="needs-validation" novalidate>
                        {grid_layout}
                    </form>
                    <div class="code-preview mt-3">
                        <h6><i class="bi bi-code"></i> Code:</h6>
                        <pre><code># Responsive grid layout
&lt;div class="row g-3"&gt;
    &lt;div class="col-md-6"&gt;{{{{ field1 }}}}&lt;/div&gt;
    &lt;div class="col-md-6"&gt;{{{{ field2 }}}}&lt;/div&gt;
    &lt;div class="col-12"&gt;{{{{ field3 }}}}&lt;/div&gt;
&lt;/div&gt;</code></pre>
                    </div>
                </div>
            </div>

            <!-- Tab Layout -->
            <div class="tab-pane fade" id="tabs" role="tabpanel">
                <div class="p-4">
                    <h5>Tab Layout</h5>
                    <p class="text-muted">Organize complex forms into tabbed sections.</p>
                    <form class="needs-validation" novalidate>
                        {tab_layout}
                    </form>
                    <div class="code-preview mt-3">
                        <h6><i class="bi bi-code"></i> Code:</h6>
                        <pre><code># Bootstrap tab layout
&lt;ul class="nav nav-tabs"&gt;
    &lt;li class="nav-item"&gt;
        &lt;button class="nav-link active" data-bs-toggle="tab"&gt;
            Personal
        &lt;/button&gt;
    &lt;/li&gt;
&lt;/ul&gt;
&lt;div class="tab-content"&gt;
    &lt;div class="tab-pane active"&gt;{{{{ content }}}}&lt;/div&gt;
&lt;/div&gt;</code></pre>
                    </div>
                </div>
            </div>

            <!-- Card Layout -->
            <div class="tab-pane fade" id="cards" role="tabpanel">
                <div class="p-4">
                    <h5>Card Layout</h5>
                    <p class="text-muted">Forms wrapped in attractive card containers.</p>
                    {card_layout}
                    <div class="code-preview mt-3">
                        <h6><i class="bi bi-code"></i> Code:</h6>
                        <pre><code># Bootstrap card layout
&lt;div class="card"&gt;
    &lt;div class="card-header"&gt;
        &lt;h5&gt;Contact Form&lt;/h5&gt;
    &lt;/div&gt;
    &lt;div class="card-body"&gt;
        {{{{ form_content }}}}
    &lt;/div&gt;
&lt;/div&gt;</code></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Layout Features -->
    <div class="form-container">
        <h4>Layout System Features</h4>
        <div class="row g-3">
            <div class="col-md-6">
                <h6><i class="bi bi-phone text-success"></i> Responsive Design</h6>
                <p class="small text-muted">All layouts automatically adapt to different screen sizes and devices.</p>
            </div>
            <div class="col-md-6">
                <h6><i class="bi bi-puzzle text-primary"></i> Composable</h6>
                <p class="small text-muted">Mix and match different layout components to create complex forms.</p>
            </div>
            <div class="col-md-6">
                <h6><i class="bi bi-brush text-info"></i> Themeable</h6>
                <p class="small text-muted">Works with Bootstrap, Material Design, Tailwind, and custom themes.</p>
            </div>
            <div class="col-md-6">
                <h6><i class="bi bi-code-slash text-warning"></i> Easy Integration</h6>
                <p class="small text-muted">Simple API for applying layouts to any form builder instance.</p>
            </div>
        </div>
    </div>
    """
    
    return render_page("Layout Examples", content)

@app.route('/docs')
def documentation():
    """Documentation and API reference."""
    content = """
    <div class="demo-section">
        <h1><i class="bi bi-book"></i> Documentation</h1>
        <p class="lead">Complete API documentation and integration guides.</p>
    </div>

    <div class="form-container">
        <div class="text-center">
            <i class="bi bi-tools fs-1 text-muted"></i>
            <h3>Documentation Coming Soon</h3>
            <p class="text-muted">Complete API documentation and tutorials are being prepared.</p>
            <p>For now, explore the source code examples in this demo.</p>
            <a href="https://github.com/devsetgo/pydantic-forms" class="btn btn-primary" target="_blank">
                <i class="bi bi-github"></i> View on GitHub
            </a>
        </div>
    </div>
    """
    return render_page("Documentation", content)

if __name__ == '__main__':
    print("🚀 Starting Pydantic Forms Flask Demo")
    print("📱 Visit http://localhost:5001 to see the examples")
    print("🔧 This demonstrates comprehensive Flask integration")
    app.run(debug=True, host='0.0.0.0', port=5001)