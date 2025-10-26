#!/usr/bin/env python3
"""
Consolidated Flask Demo for Pydantic Forms with New Design Features
==================================================================

This example demonstrates the complete new design_idea.py implementation including:
- Enhanced FormField with icons, validation, and type safety
- Layout composition system (VerticalLayout, HorizontalLayout, TabbedLayout)
- SectionDesign and FormDesign configuration
- @form_validator decorator
- ValidationResult objects with .validate() and .render_with_errors()
- Flask integration pattern matching design_idea.py

Run with:
    python enhanced_flask_demo.py

Then visit:
    - http://localhost:5000/ (main demo page)
    - http://localhost:5000/design-demo (design_idea.py implementation)
    - http://localhost:5000/forms (individual form examples)
    - http://localhost:5000/layouts (layout composition examples)
"""

import os
import sys
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from flask import Flask, request, render_template_string, jsonify

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new pydantic-forms components
from pydantic_forms.schema_form import FormModel, form_validator, EmailStr, ValidationResult
from pydantic_forms.form_field import FormField, TextField, EmailField, NumberField, SelectField, CheckboxField, DateField, TextAreaField
from pydantic_forms.form_layouts import VerticalLayout, HorizontalLayout, TabbedLayout, SectionDesign, FormDesign
from pydantic_forms.input_types import TEXT_INPUTS, NUMERIC_INPUTS, SELECTION_INPUTS, DATETIME_INPUTS, SPECIALIZED_INPUTS

app = Flask(__name__)
app.secret_key = 'demo-secret-key-change-in-production'

# ============================================================================
# FORM MODELS USING NEW DESIGN
# ============================================================================

class SimpleForm(FormModel):
    """Example from design_idea.py - shows new FormField syntax."""
    title: str = FormField(..., title="Title", input_type="text", placeholder="Enter title here", help_text="The title of the item.", icon="card-text")
    age: int = FormField(..., title="Age", input_type="number", min_value=0, max_value=120, help_text="Your age in years.", icon="person")
    email: EmailStr = FormField(..., title="Email", input_type="email", placeholder="example@example.com", help_text="Your email address.", icon="envelope")
    subscribe: bool = FormField(False, title="Subscribe to newsletter", input_type="checkbox", help_text="Check to receive our newsletter.", icon="newspaper")
    country: str = FormField(..., title="Country", input_type="select", options=["USA", "Canada", "UK", "Australia"], help_text="Select your country of residence.", icon="globe")
    birth_date: date = FormField(..., title="Birth Date", input_type="date", help_text="Your date of birth.", icon="calendar")
    appointment_time: datetime = FormField(None, title="Appointment Time", input_type="datetime", help_text="Preferred time for appointment.", icon="clock")
    credit_card_number: str = FormField(..., title="Credit Card Number", input_type="text", placeholder="1234 5678 9012 3456", help_text="Enter your credit card number.", icon="credit-card")

    @form_validator
    def check_age_and_consent(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Example validation from design_idea.py."""
        age = values.get('age')
        if age is not None and age < 13:
            raise ValueError("Age must be at least 13 years old.")
        return values


class UserProfile(FormModel):
    """User profile form from design_idea.py."""
    bio: str = FormField(None, title="Biography", input_type="textarea", placeholder="Tell us about yourself", help_text="A brief biography.", icon="info-circle")
    profile_picture: str = FormField(None, title="Profile Picture", input_type="file", help_text="Upload your profile picture.", icon="image")


class EnhancedLoginForm(FormModel):
    """Enhanced login form showcasing convenience functions."""
    username: str = TextField(..., title="Username", placeholder="Enter your username", help_text="Your username or email address", icon="person")
    password: str = FormField(..., title="Password", input_type="password", min_length=6, help_text="Must be at least 6 characters", icon="lock")
    remember_me: bool = CheckboxField(False, title="Remember me for 30 days", icon="check-circle")


class ComprehensiveForm(FormModel):
    """Comprehensive form showing all input types and features."""
    
    # Text inputs with different types
    name: str = TextField(..., title="Full Name", placeholder="John Doe", icon="person")
    email: EmailStr = EmailField(..., title="Email Address", icon="envelope")
    phone: Optional[str] = FormField(None, title="Phone Number", input_type="tel", placeholder="+1 (555) 123-4567", icon="telephone")
    website: Optional[str] = FormField(None, title="Website", input_type="url", placeholder="https://example.com", icon="globe")
    
    # Numeric inputs
    age: int = NumberField(..., title="Age", min_value=13, max_value=120, icon="calendar-event")
    salary: float = FormField(..., title="Annual Salary", input_type="number", min_value=0, max_value=1000000, icon="currency-dollar")
    rating: int = FormField(5, title="Experience Rating", input_type="range", min_value=1, max_value=10, icon="star")
    
    # Selection inputs
    role: str = SelectField(..., title="Job Role", options=[
        {"value": "developer", "label": "Software Developer"},
        {"value": "designer", "label": "UI/UX Designer"},
        {"value": "manager", "label": "Project Manager"},
        {"value": "analyst", "label": "Data Analyst"}
    ], icon="briefcase")
    
    skills: List[str] = FormField([], title="Technical Skills", input_type="checkbox_group", options=[
        "Python", "JavaScript", "React", "Django", "Flask", "PostgreSQL", "Docker"
    ], icon="tools")
    
    # Date/time inputs
    start_date: date = DateField(..., title="Start Date", icon="calendar")
    interview_time: Optional[datetime] = FormField(None, title="Interview Date & Time", input_type="datetime", icon="clock")
    
    # Text areas
    bio: str = TextAreaField(..., title="Professional Bio", placeholder="Tell us about your experience...", min_length=50, max_length=1000, rows=4, icon="chat-text")
    notes: Optional[str] = FormField(None, title="Additional Notes", input_type="textarea", rows=2, icon="sticky")
    
    # Specialized inputs
    portfolio_url: Optional[str] = FormField(None, title="Portfolio/GitHub", input_type="url", icon="github")
    profile_color: str = FormField("#3b82f6", title="Profile Color", input_type="color", icon="palette")
    
    # Agreements
    terms_accepted: bool = CheckboxField(..., title="I accept the terms and conditions", icon="check-square")
    newsletter: bool = CheckboxField(False, title="Subscribe to our newsletter", icon="envelope-plus")

    @form_validator
    def validate_comprehensive_form(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive validation example."""
        if not values.get('terms_accepted'):
            raise ValueError("You must accept the terms and conditions")
        
        age = values.get('age')
        salary = values.get('salary')
        if age and salary and age < 18 and salary > 50000:
            raise ValueError("Salary seems unusually high for someone under 18")
        
        return values


# ============================================================================
# LAYOUT COMPOSITION SYSTEM
# ============================================================================

class LayoutOne(VerticalLayout):
    """Vertical layout from design_idea.py."""
    form = SimpleForm
    form_config = SectionDesign(
        section_title="User Profile Section", 
        section_description="Fill out your profile information below.", 
        icon="people",
        collapsible=True
    )


class LayoutTwo(HorizontalLayout):
    """Horizontal layout from design_idea.py."""
    profile = UserProfile
    form_config = SectionDesign(
        section_title="Additional Profile Details", 
        section_description="Provide additional details for your profile.", 
        icon="person-badge",
        collapsible=False
    )


class LoginLayoutVertical(VerticalLayout):
    """Login form in vertical layout."""
    login_form = EnhancedLoginForm
    form_config = SectionDesign(
        section_title="User Authentication",
        section_description="Please log in to access your account.",
        icon="shield-lock",
        collapsible=False
    )


class ComprehensiveLayoutHorizontal(HorizontalLayout):
    """Comprehensive form in horizontal layout."""
    comprehensive_form = ComprehensiveForm
    form_config = SectionDesign(
        section_title="Complete Application Form",
        section_description="Please fill out all sections of this application.",
        icon="clipboard-data",
        collapsible=True
    )


class UserProfileLayout(TabbedLayout):
    """Tabbed layout from design_idea.py."""
    tab_one = LayoutOne()
    tab_two = LayoutTwo()

    form_config = FormDesign(
        ui_theme="bootstrap",
        ui_theme_custom_css=None,
        form_name="User Profile",
        form_enctype="application/x-www-form-urlencoded",
        form_width="800px",
        target_url="/api/endpoint/for/form",
        form_method="post",
        error_notification_style="inline",
        show_debug_info=True
    )


class ApplicationLayout(TabbedLayout):
    """Multi-tab application layout."""
    login_tab = LoginLayoutVertical()
    application_tab = ComprehensiveLayoutHorizontal()
    
    form_config = FormDesign(
        ui_theme="bootstrap",
        form_name="Job Application System",
        form_width="1000px",
        target_url="/submit-application",
        form_method="post",
        error_notification_style="inline",
        show_debug_info=False
    )


# ============================================================================
# HTML TEMPLATES
# ============================================================================

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Enhanced Pydantic Forms</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar { background: rgba(255,255,255,0.95) !important; backdrop-filter: blur(10px); }
        .demo-section { 
            background: white; 
            border-radius: 15px; 
            padding: 2rem; 
            margin: 2rem 0; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
        }
        .result-display { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
            border-radius: 8px; 
            padding: 1rem; 
            margin: 1rem 0; 
        }
        .error-display { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb; 
            border-radius: 8px; 
            padding: 1rem; 
            margin: 1rem 0; 
        }
        .feature-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .feature-card:hover {
            transform: translateY(-2px);
        }
        .code-block {
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        .nav-pills .nav-link.active {
            background: linear-gradient(45deg, #667eea, #764ba2);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light fixed-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="bi bi-magic"></i> Enhanced Pydantic Forms
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="bi bi-house"></i> Home</a>
                <a class="nav-link" href="/design-demo"><i class="bi bi-stars"></i> Design Demo</a>
                <a class="nav-link" href="/forms"><i class="bi bi-ui-checks-grid"></i> Forms</a>
                <a class="nav-link" href="/layouts"><i class="bi bi-layout-three-columns"></i> Layouts</a>
            </div>
        </div>
    </nav>
    
    <div class="container" style="margin-top: 100px;">
        {{ content|safe }}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

def render_page(title, content):
    """Helper function to render a page with the base template."""
    return render_template_string(BASE_TEMPLATE, title=title, content=content)


# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Main demo page showcasing the new features."""
    content = """
    <div class="demo-section">
        <div class="text-center mb-5">
            <h1 class="display-4 fw-bold text-primary mb-3">
                <i class="bi bi-magic"></i> Enhanced Pydantic Forms
            </h1>
            <p class="lead text-muted">
                Experience the new design_idea.py implementation with enhanced FormField, 
                layout composition, and advanced validation.
            </p>
            <div class="d-flex justify-content-center flex-wrap gap-2 mb-4">
                <span class="badge bg-primary px-3 py-2">FormField with Icons</span>
                <span class="badge bg-success px-3 py-2">Layout Composition</span>
                <span class="badge bg-info px-3 py-2">Type Validation</span>
                <span class="badge bg-warning px-3 py-2">@form_validator</span>
                <span class="badge bg-danger px-3 py-2">ValidationResult</span>
            </div>
        </div>

        <div class="row g-4">
            <div class="col-lg-4">
                <div class="feature-card text-center">
                    <div class="text-primary mb-3">
                        <i class="bi bi-stars" style="font-size: 3rem;"></i>
                    </div>
                    <h3>Design Demo</h3>
                    <p class="text-muted">
                        See the complete design_idea.py implementation with tabbed layouts, 
                        FormField syntax, and validation patterns.
                    </p>
                    <a href="/design-demo" class="btn btn-primary">
                        <i class="bi bi-arrow-right"></i> View Design Demo
                    </a>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="feature-card text-center">
                    <div class="text-success mb-3">
                        <i class="bi bi-ui-checks-grid" style="font-size: 3rem;"></i>
                    </div>
                    <h3>Individual Forms</h3>
                    <p class="text-muted">
                        Explore individual forms showcasing FormField enhancements, 
                        input types, validation, and icon integration.
                    </p>
                    <a href="/forms" class="btn btn-success">
                        <i class="bi bi-arrow-right"></i> Explore Forms
                    </a>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="feature-card text-center">
                    <div class="text-info mb-3">
                        <i class="bi bi-layout-three-columns" style="font-size: 3rem;"></i>
                    </div>
                    <h3>Layout System</h3>
                    <p class="text-muted">
                        Experience the layout composition system with VerticalLayout, 
                        HorizontalLayout, and TabbedLayout components.
                    </p>
                    <a href="/layouts" class="btn btn-info">
                        <i class="bi bi-arrow-right"></i> Try Layouts
                    </a>
                </div>
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-12">
                <h2 class="text-center mb-4">New Features Implemented</h2>
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="code-block">
                            <strong>Enhanced FormField:</strong><br>
                            <code>FormField(..., input_type="email", icon="envelope", help_text="Your email")</code>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="code-block">
                            <strong>Layout Composition:</strong><br>
                            <code>class UserLayout(TabbedLayout):<br>&nbsp;&nbsp;tab_one = VerticalLayout()</code>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="code-block">
                            <strong>Form Validator:</strong><br>
                            <code>@form_validator<br>def check_age(cls, values): ...</code>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="code-block">
                            <strong>ValidationResult:</strong><br>
                            <code>result.is_valid<br>result.render_with_errors()</code>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page("Enhanced Demo", content)


@app.route('/design-demo', methods=['GET', 'POST'])
def design_demo():
    """Implementation of the exact design_idea.py pattern."""
    
    if request.method == 'POST':
        # Simulate the Flask endpoint logic from design_idea.py
        layout = UserProfileLayout()
        form_data = request.form.to_dict()
        
        # Handle checkboxes that aren't submitted when unchecked
        if 'subscribe' not in form_data:
            form_data['subscribe'] = False
        
        result = layout.validate(form_data)
        
        if result.is_valid:
            success_html = f"""
            <div class="demo-section">
                <div class="result-display">
                    <h4><i class="bi bi-check-circle"></i> Success!</h4>
                    <p>Form submitted successfully. Here's the validated data:</p>
                    <pre>{result.data}</pre>
                </div>
                <a href="/design-demo" class="btn btn-primary">
                    <i class="bi bi-arrow-left"></i> Try Again
                </a>
            </div>
            """
            return render_page("Success", success_html)
        else:
            # Return form with errors - this is the design_idea.py pattern
            error_form_html = result.render_with_errors()
            return render_page("Form Errors", f"""
            <div class="demo-section">
                <h2><i class="bi bi-stars"></i> Design Demo - With Errors</h2>
                <div class="error-display">
                    <h5><i class="bi bi-exclamation-triangle"></i> Validation Errors</h5>
                    <p>Please correct the errors below and try again.</p>
                    <ul>
                        {''.join([f'<li>{field}: {error}</li>' for field, error in result.errors.items()])}
                    </ul>
                </div>
                {error_form_html}
            </div>
            """)
    
    # GET request - render the layout
    layout = UserProfileLayout()
    form_html = layout.render()
    
    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-stars"></i> Design Demo - Complete Implementation</h1>
        <p class="lead text-muted mb-4">
            This is the exact implementation from design_idea.py showing FormField, 
            layout composition, form validation, and the Flask integration pattern.
        </p>
        
        <div class="alert alert-info">
            <h5><i class="bi bi-info-circle"></i> Pattern Demonstration</h5>
            <p class="mb-0">
                This demonstrates the Flask pattern: <code>layout.render()</code> for GET and 
                <code>layout.validate()</code> with <code>result.render_with_errors()</code> for POST.
            </p>
        </div>
        
        {form_html}
        
        <div class="mt-5">
            <h3>Implementation Code</h3>
            <div class="code-block">
@app.route('/user-profile', methods=['GET', 'POST'])
def user_profile():
    layout = UserProfileLayout()
    
    if request.method == 'GET':
        return layout.render()  # Single call to generate form
    
    elif request.method == 'POST':
        result = layout.validate(request.form.to_dict())  # Single call to validate
        
        if result.is_valid:
            return f"Success! Data: {{result.data}}"
        else:
            return result.render_with_errors()  # Re-render with errors
            </div>
        </div>
    </div>
    """
    
    return render_page("Design Demo", content)


@app.route('/forms')
def forms():
    """Individual form examples."""
    content = """
    <div class="demo-section">
        <h1><i class="bi bi-ui-checks-grid"></i> Individual Forms</h1>
        <p class="lead text-muted mb-4">
            Explore individual forms showcasing the new FormField enhancements.
        </p>
        
        <div class="row g-4">
            <div class="col-lg-6">
                <div class="feature-card">
                    <h3><i class="bi bi-shield-lock"></i> Enhanced Login Form</h3>
                    <p class="text-muted">Login form with TextField and CheckboxField convenience functions.</p>
                    <a href="/forms/login" class="btn btn-primary">View Form</a>
                </div>
            </div>
            
            <div class="col-lg-6">
                <div class="feature-card">
                    <h3><i class="bi bi-clipboard-data"></i> Comprehensive Form</h3>
                    <p class="text-muted">Complete form showcasing all FormField input types and validation.</p>
                    <a href="/forms/comprehensive" class="btn btn-success">View Form</a>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <h3>FormField Syntax Examples</h3>
            <div class="row g-3">
                <div class="col-md-6">
                    <div class="code-block">
                        <strong>Text Field with Icon:</strong><br>
                        <code>name: str = TextField(..., title="Full Name", icon="person")</code>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="code-block">
                        <strong>Email with Validation:</strong><br>
                        <code>email: EmailStr = EmailField(..., title="Email", icon="envelope")</code>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="code-block">
                        <strong>Number with Range:</strong><br>
                        <code>age: int = NumberField(..., min_value=13, max_value=120, icon="calendar")</code>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="code-block">
                        <strong>Select with Options:</strong><br>
                        <code>role: str = SelectField(..., options=["Admin", "User"], icon="briefcase")</code>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page("Individual Forms", content)


@app.route('/forms/login', methods=['GET', 'POST'])
def login_form():
    """Enhanced login form example."""
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()
            if 'remember_me' not in form_data:
                form_data['remember_me'] = False
                
            validated_data = EnhancedLoginForm(**form_data)
            
            success_content = f"""
            <div class="demo-section">
                <div class="result-display">
                    <h4><i class="bi bi-check-circle"></i> Login Successful!</h4>
                    <p>Form validated successfully:</p>
                    <pre>{validated_data.model_dump()}</pre>
                </div>
                <a href="/forms/login" class="btn btn-primary">Try Again</a>
            </div>
            """
            return render_page("Login Success", success_content)
            
        except Exception as e:
            error_message = str(e)
    else:
        error_message = None
    
    form_html = EnhancedLoginForm.render_form(framework="bootstrap")
    
    content = f"""
    <div class="demo-section">
        <h2><i class="bi bi-shield-lock"></i> Enhanced Login Form</h2>
        <p class="text-muted mb-4">Demonstrates TextField, FormField with password type, and CheckboxField.</p>
        
        {f'<div class="error-display"><strong>Error:</strong> {error_message}</div>' if error_message else ''}
        
        <form method="POST" class="needs-validation" novalidate>
            {form_html}
            <div class="d-grid">
                <button type="submit" class="btn btn-primary btn-lg">
                    <i class="bi bi-box-arrow-in-right"></i> Sign In
                </button>
            </div>
        </form>
        
        <div class="mt-4">
            <h4>Code Example</h4>
            <div class="code-block">
class EnhancedLoginForm(FormModel):
    username: str = TextField(..., title="Username", icon="person")
    password: str = FormField(..., input_type="password", min_length=6, icon="lock")
    remember_me: bool = CheckboxField(False, title="Remember me", icon="check-circle")
            </div>
        </div>
    </div>
    """
    
    return render_page("Enhanced Login", content)


@app.route('/forms/comprehensive', methods=['GET', 'POST'])
def comprehensive_form():
    """Comprehensive form showing all features."""
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()
            
            # Handle checkboxes and multi-select fields
            checkbox_fields = ['terms_accepted', 'newsletter']
            for field in checkbox_fields:
                if field not in form_data:
                    form_data[field] = False
            
            # Handle multi-select (skills)
            skills = request.form.getlist('skills')
            if skills:
                form_data['skills'] = skills
            else:
                form_data['skills'] = []
                
            validated_data = ComprehensiveForm(**form_data)
            
            success_content = f"""
            <div class="demo-section">
                <div class="result-display">
                    <h4><i class="bi bi-check-circle"></i> Form Submitted Successfully!</h4>
                    <p>All validation passed. Here's the validated data:</p>
                    <pre>{validated_data.model_dump()}</pre>
                </div>
                <a href="/forms/comprehensive" class="btn btn-primary">Submit Another</a>
            </div>
            """
            return render_page("Form Success", success_content)
            
        except Exception as e:
            error_message = str(e)
    else:
        error_message = None
    
    form_html = ComprehensiveForm.render_form(framework="bootstrap")
    
    content = f"""
    <div class="demo-section">
        <h2><i class="bi bi-clipboard-data"></i> Comprehensive Form</h2>
        <p class="text-muted mb-4">
            Showcases all FormField input types, validation rules, and the @form_validator decorator.
        </p>
        
        {f'<div class="error-display"><strong>Validation Error:</strong> {error_message}</div>' if error_message else ''}
        
        <form method="POST" class="needs-validation" novalidate>
            {form_html}
            <div class="d-grid">
                <button type="submit" class="btn btn-success btn-lg">
                    <i class="bi bi-check-circle"></i> Submit Application
                </button>
            </div>
        </form>
        
        <div class="mt-4">
            <h4>Available Input Types</h4>
            <div class="row g-2">
                <div class="col-md-3"><span class="badge bg-primary">Text Inputs: {len(TEXT_INPUTS)}</span></div>
                <div class="col-md-3"><span class="badge bg-success">Numeric: {len(NUMERIC_INPUTS)}</span></div>
                <div class="col-md-3"><span class="badge bg-info">Selection: {len(SELECTION_INPUTS)}</span></div>
                <div class="col-md-3"><span class="badge bg-warning">DateTime: {len(DATETIME_INPUTS)}</span></div>
            </div>
        </div>
    </div>
    """
    
    return render_page("Comprehensive Form", content)


@app.route('/layouts')
def layouts():
    """Layout composition examples."""
    content = """
    <div class="demo-section">
        <h1><i class="bi bi-layout-three-columns"></i> Layout Composition System</h1>
        <p class="lead text-muted mb-4">
            Experience the new layout composition system with nested forms and layouts.
        </p>
        
        <div class="row g-4">
            <div class="col-lg-4">
                <div class="feature-card text-center">
                    <div class="text-primary mb-3">
                        <i class="bi bi-layout-text-window" style="font-size: 2rem;"></i>
                    </div>
                    <h4>Vertical Layout</h4>
                    <p class="text-muted">Forms stacked vertically with section configuration.</p>
                    <a href="/layouts/vertical" class="btn btn-primary">Try It</a>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="feature-card text-center">
                    <div class="text-success mb-3">
                        <i class="bi bi-layout-sidebar" style="font-size: 2rem;"></i>
                    </div>
                    <h4>Horizontal Layout</h4>
                    <p class="text-muted">Forms arranged side by side with responsive design.</p>
                    <a href="/layouts/horizontal" class="btn btn-success">Try It</a>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="feature-card text-center">
                    <div class="text-info mb-3">
                        <i class="bi bi-layout-three-columns" style="font-size: 2rem;"></i>
                    </div>
                    <h4>Tabbed Layout</h4>
                    <p class="text-muted">Complete tabbed interface with multiple forms.</p>
                    <a href="/layouts/tabbed" class="btn btn-info">Try It</a>
                </div>
            </div>
        </div>
        
        <div class="mt-5">
            <h3>Layout Composition Code</h3>
            <div class="code-block">
class UserProfileLayout(TabbedLayout):
    tab_one = LayoutOne()  # VerticalLayout
    tab_two = LayoutTwo()  # HorizontalLayout
    
    form_config = FormDesign(
        ui_theme="bootstrap",
        form_name="User Profile",
        form_width="800px",
        target_url="/submit"
    )
            </div>
        </div>
    </div>
    """
    return render_page("Layout System", content)


@app.route('/layouts/<layout_type>', methods=['GET', 'POST'])
def layout_demo(layout_type):
    """Demo for specific layout types."""
    layouts = {
        'vertical': (LoginLayoutVertical, "Vertical Layout Demo"),
        'horizontal': (ComprehensiveLayoutHorizontal, "Horizontal Layout Demo"), 
        'tabbed': (ApplicationLayout, "Tabbed Layout Demo")
    }
    
    if layout_type not in layouts:
        return "Layout not found", 404
    
    layout_class, title = layouts[layout_type]
    layout = layout_class()
    
    if request.method == 'POST':
        form_data = request.form.to_dict()
        
        # Handle common checkboxes
        checkbox_fields = ['remember_me', 'terms_accepted', 'newsletter', 'subscribe']
        for field in checkbox_fields:
            if field not in form_data:
                form_data[field] = False
        
        result = layout.validate(form_data)
        
        if result.is_valid:
            success_content = f"""
            <div class="demo-section">
                <div class="result-display">
                    <h4><i class="bi bi-check-circle"></i> {title} - Success!</h4>
                    <p>Layout validation successful:</p>
                    <pre>{result.data}</pre>
                </div>
                <a href="/layouts/{layout_type}" class="btn btn-primary">Try Again</a>
            </div>
            """
            return render_page(f"{title} Success", success_content)
        else:
            error_form_html = result.render_with_errors()
            return render_page(f"{title} - Errors", f"""
            <div class="demo-section">
                <h2>{title}</h2>
                <div class="error-display">
                    <h5><i class="bi bi-exclamation-triangle"></i> Validation Errors</h5>
                    <ul>
                        {''.join([f'<li>{field}: {error}</li>' for field, error in result.errors.items()])}
                    </ul>
                </div>
                {error_form_html}
            </div>
            """)
    
    # GET request
    layout_html = layout.render()
    
    content = f"""
    <div class="demo-section">
        <h2><i class="bi bi-layout-three-columns"></i> {title}</h2>
        <p class="text-muted mb-4">
            Demonstrating the {layout_type} layout with form composition and validation.
        </p>
        
        {layout_html}
        
        <div class="mt-4">
            <a href="/layouts" class="btn btn-outline-secondary">
                <i class="bi bi-arrow-left"></i> Back to Layouts
            </a>
        </div>
    </div>
    """
    
    return render_page(title, content)


if __name__ == '__main__':
    print("🚀 Starting Enhanced Pydantic Forms Demo...")
    print("📄 Main page: http://localhost:5000/")
    print("⭐ Design demo: http://localhost:5000/design-demo")
    print("📝 Forms: http://localhost:5000/forms")
    print("📐 Layouts: http://localhost:5000/layouts")
    
    app.run(debug=True, host='0.0.0.0', port=5000)