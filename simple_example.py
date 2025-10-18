#!/usr/bin/env python3
"""
Simple Flask Example - Pydantic Forms with Python 3.14 Template Strings
========================================================================

A Flask web application demonstrating the modernized pydantic-forms library:
- Python 3.14 native template strings
- Form builder with fluent API
- Auto-generation from Pydantic models
- Multiple framework support (Bootstrap, Material, etc.)
- Real-time validation

Run this script and visit http://localhost:5000 to see the forms in action.
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, ValidationError

# Import the modernized pydantic-forms components
from pydantic_forms import (
    FormBuilder, 
    create_form_from_model,
    create_login_form,
    create_contact_form
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Define Pydantic models for demonstration
class UserProfile(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50, description="Your first name")
    last_name: str = Field(..., min_length=2, max_length=50, description="Your last name")
    email: str = Field(..., description="Your email address")
    age: int = Field(..., ge=18, le=120, description="Your age")
    phone: Optional[str] = Field(None, description="Your phone number")
    birth_date: Optional[date] = Field(None, description="Your birth date")
    bio: Optional[str] = Field(None, max_length=500, description="Brief bio")
    newsletter: bool = Field(False, description="Subscribe to newsletter")

class ContactMessage(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(...)
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=1000)


# Base HTML template
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Pydantic Forms Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .demo-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        .form-demo {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .alert {
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="demo-header">
        <div class="container">
            <h1 class="text-center">
                <i class="fas fa-magic"></i> 
                Pydantic Forms - Python 3.14 Template Strings
            </h1>
            <p class="text-center lead">Modern form generation with native template strings</p>
        </div>
    </div>
    
    <div class="container">
        {% if get_flashed_messages() %}
            {% for message in get_flashed_messages() %}
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}
        
        {{ content | safe }}
        
        <div class="text-center mt-4">
            <a href="/" class="btn btn-secondary">
                <i class="fas fa-home"></i> Back to Examples
            </a>
        </div>
    </div>
    
    <footer class="mt-5 py-4 bg-dark text-light">
        <div class="container text-center">
            <p>&copy; 2025 Pydantic Forms - Built with Python 3.14 Template Strings</p>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


@app.route("/")
def index():
    """Main index page with links to different form examples."""
    content = """
    <div class="row">
        <div class="col-md-8 mx-auto">
            <h2 class="text-center mb-4">
                <i class="fas fa-rocket"></i> 
                Choose a Form Example
            </h2>
            <p class="text-center mb-4">
                Explore different ways to generate forms with the modernized pydantic-forms library
            </p>
            
            <div class="row g-4">
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-tools text-primary"></i> 
                                Form Builder
                            </h5>
                            <p class="card-text">
                                Build forms using the fluent API with method chaining
                            </p>
                            <a href="/form-builder" class="btn btn-primary">Try Form Builder</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-robot text-success"></i> 
                                Auto-Generated
                            </h5>
                            <p class="card-text">
                                Automatically generate forms from Pydantic models
                            </p>
                            <a href="/auto-form" class="btn btn-success">Try Auto-Generated</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-sign-in-alt text-info"></i> 
                                Login Form
                            </h5>
                            <p class="card-text">
                                Pre-built login form template
                            </p>
                            <a href="/login" class="btn btn-info">Try Login Form</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-envelope text-warning"></i> 
                                Contact Form
                            </h5>
                            <p class="card-text">
                                Pre-built contact form template
                            </p>
                            <a href="/contact" class="btn btn-warning">Try Contact Form</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-5 p-4 bg-light rounded">
                <h4><i class="fas fa-info-circle text-info"></i> About This Demo</h4>
                <ul class="list-unstyled">
                    <li><i class="fas fa-check text-success"></i> Python 3.14 native template strings</li>
                    <li><i class="fas fa-check text-success"></i> Real-time form validation</li>
                    <li><i class="fas fa-check text-success"></i> Bootstrap 5 styling</li>
                    <li><i class="fas fa-check text-success"></i> Pydantic model integration</li>
                </ul>
            </div>
        </div>
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, title="Home", content=content)


@app.route("/form-builder", methods=["GET", "POST"])
def form_builder_demo():
    """Demonstrate FormBuilder with fluent API."""
    if request.method == "POST":
        # Process form submission
        form_data = request.form.to_dict()
        
        # Create the same form for validation
        form = (FormBuilder(framework="bootstrap")
                .text_input("first_name", "First Name")
                .text_input("last_name", "Last Name") 
                .email_input("email", "Email Address")
                .password_input("password", "Password")
                .number_input("age", "Age", min_val=18, max_val=120)
                .select_input("country", [
                    {"value": "us", "text": "United States"},
                    {"value": "ca", "text": "Canada"},
                    {"value": "uk", "text": "United Kingdom"},
                    {"value": "de", "text": "Germany"}
                ], "Country")
                .textarea_input("message", "Message", rows=4)
                .checkbox_input("newsletter", "Subscribe to newsletter")
                .required("first_name")
                .required("last_name")
                .required("email")
                .required("password")
                .min_length("password", 8))
        
        is_valid, errors = form.validate_data(form_data)
        
        if is_valid:
            flash("Form submitted successfully! All validation passed.")
            return redirect(url_for('form_builder_demo'))
        else:
            flash(f"Validation errors: {', '.join([f'{k}: {v[0]}' for k, v in errors.items()])}")
    
    # Build the form
    form = (FormBuilder(framework="bootstrap")
            .text_input("first_name", "First Name")
            .text_input("last_name", "Last Name") 
            .email_input("email", "Email Address")
            .password_input("password", "Password")
            .number_input("age", "Age", min_val=18, max_val=120)
            .select_input("country", [
                {"value": "us", "text": "United States"},
                {"value": "ca", "text": "Canada"},
                {"value": "uk", "text": "United Kingdom"},
                {"value": "de", "text": "Germany"}
            ], "Country")
            .textarea_input("message", "Message", rows=4)
            .checkbox_input("newsletter", "Subscribe to newsletter")
            .required("first_name")
            .required("last_name")
            .required("email")
            .required("password")
            .min_length("password", 8))
    
    try:
        form_html = form.render()
        
        content = f"""
        <div class="form-demo">
            <h2><i class="fas fa-tools text-primary"></i> Form Builder Demo</h2>
            <p class="text-muted">Built using FormBuilder with fluent API and Python 3.14 template strings</p>
            
            <div class="row">
                <div class="col-md-8">
                    {form_html}
                </div>
                <div class="col-md-4">
                    <div class="bg-light p-3 rounded">
                        <h5>Features:</h5>
                        <ul class="small">
                            <li>Fluent API with method chaining</li>
                            <li>Built-in validation rules</li>
                            <li>Bootstrap 5 styling</li>
                            <li>Python 3.14 template strings</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """
        
    except Exception as e:
        content = f"""
        <div class="alert alert-danger">
            <h4>Error rendering form:</h4>
            <p>{str(e)}</p>
        </div>
        """
    
    return render_template_string(BASE_TEMPLATE, title="Form Builder", content=content)


@app.route("/auto-form", methods=["GET", "POST"])
def auto_form_demo():
    """Demonstrate auto-generated form from Pydantic model."""
    if request.method == "POST":
        try:
            # Convert form data to match Pydantic model
            form_data = request.form.to_dict()
            
            # Handle checkbox
            if 'newsletter' not in form_data:
                form_data['newsletter'] = False
            else:
                form_data['newsletter'] = True
            
            # Convert age to int
            if 'age' in form_data:
                form_data['age'] = int(form_data['age'])
            
            # Validate with Pydantic model
            user_profile = UserProfile(**form_data)
            flash(f"User profile created successfully for {user_profile.first_name} {user_profile.last_name}!")
            return redirect(url_for('auto_form_demo'))
            
        except ValidationError as e:
            flash(f"Validation errors: {', '.join([f'{err['loc'][0]}: {err['msg']}' for err in e.errors()])}")
        except ValueError as e:
            flash(f"Data conversion error: {str(e)}")
    
    try:
        # Auto-generate form from Pydantic model
        form = create_form_from_model(UserProfile, framework="bootstrap")
        form.min_length("first_name", 2)
        form.min_length("last_name", 2)
        
        form_html = form.render()
        
        content = f"""
        <div class="form-demo">
            <h2><i class="fas fa-robot text-success"></i> Auto-Generated Form Demo</h2>
            <p class="text-muted">Automatically generated from Pydantic model using Python 3.14 template strings</p>
            
            <div class="row">
                <div class="col-md-8">
                    {form_html}
                </div>
                <div class="col-md-4">
                    <div class="bg-light p-3 rounded">
                        <h5>Pydantic Model:</h5>
                        <pre class="small"><code>class UserProfile(BaseModel):
    first_name: str
    last_name: str
    email: str
    age: int (18-120)
    phone: Optional[str]
    birth_date: Optional[date]
    bio: Optional[str]
    newsletter: bool</code></pre>
                    </div>
                </div>
            </div>
        </div>
        """
        
    except Exception as e:
        content = f"""
        <div class="alert alert-danger">
            <h4>Error generating auto-form:</h4>
            <p>{str(e)}</p>
        </div>
        """
    
    return render_template_string(BASE_TEMPLATE, title="Auto-Generated Form", content=content)


@app.route("/login", methods=["GET", "POST"])
def login_demo():
    """Demonstrate pre-built login form."""
    if request.method == "POST":
        form_data = request.form.to_dict()
        
        # Create login form for validation
        login_form = create_login_form()
        is_valid, errors = login_form.validate_data(form_data)
        
        if is_valid:
            flash(f"Login successful for {form_data.get('email', 'user')}!")
            return redirect(url_for('login_demo'))
        else:
            flash(f"Login validation errors: {', '.join([f'{k}: {v[0]}' for k, v in errors.items()])}")
    
    try:
        login_form = create_login_form()
        form_html = login_form.render()
        
        content = f"""
        <div class="form-demo">
            <h2><i class="fas fa-sign-in-alt text-info"></i> Pre-built Login Form</h2>
            <p class="text-muted">Ready-to-use login form template with Python 3.14 template strings</p>
            
            <div class="row justify-content-center">
                <div class="col-md-6">
                    {form_html}
                </div>
                <div class="col-md-6">
                    <div class="bg-light p-3 rounded">
                        <h5>Features:</h5>
                        <ul class="small">
                            <li>Email validation</li>
                            <li>Password security</li>
                            <li>Ready-to-use template</li>
                            <li>Bootstrap styling</li>
                        </ul>
                        
                        <h6 class="mt-3">Test Credentials:</h6>
                        <p class="small">
                            Email: test@example.com<br>
                            Password: testpassword123
                        </p>
                    </div>
                </div>
            </div>
        </div>
        """
        
    except Exception as e:
        content = f"""
        <div class="alert alert-danger">
            <h4>Error creating login form:</h4>
            <p>{str(e)}</p>
        </div>
        """
    
    return render_template_string(BASE_TEMPLATE, title="Login Form", content=content)


@app.route("/contact", methods=["GET", "POST"])
def contact_demo():
    """Demonstrate pre-built contact form."""
    if request.method == "POST":
        try:
            form_data = request.form.to_dict()
            
            # Validate with Pydantic model
            contact_message = ContactMessage(**form_data)
            flash(f"Message received from {contact_message.name}! Subject: {contact_message.subject}")
            return redirect(url_for('contact_demo'))
            
        except ValidationError as e:
            flash(f"Validation errors: {', '.join([f'{err['loc'][0]}: {err['msg']}' for err in e.errors()])}")
    
    try:
        contact_form = create_contact_form()
        form_html = contact_form.render()
        
        content = f"""
        <div class="form-demo">
            <h2><i class="fas fa-envelope text-warning"></i> Pre-built Contact Form</h2>
            <p class="text-muted">Ready-to-use contact form template with Python 3.14 template strings</p>
            
            <div class="row">
                <div class="col-md-8">
                    {form_html}
                </div>
                <div class="col-md-4">
                    <div class="bg-light p-3 rounded">
                        <h5>Validation Rules:</h5>
                        <ul class="small">
                            <li>Name: 2-100 characters</li>
                            <li>Email: Valid email format</li>
                            <li>Subject: 5-200 characters</li>
                            <li>Message: 10-1000 characters</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """
        
    except Exception as e:
        content = f"""
        <div class="alert alert-danger">
            <h4>Error creating contact form:</h4>
            <p>{str(e)}</p>
        </div>
        """
    
    return render_template_string(BASE_TEMPLATE, title="Contact Form", content=content)


@app.route("/api/validate", methods=["POST"])
def api_validate():
    """API endpoint for real-time validation."""
    try:
        data = request.get_json()
        form_type = data.get('form_type')
        form_data = data.get('data', {})
        
        if form_type == 'user_profile':
            user_profile = UserProfile(**form_data)
            return jsonify({"valid": True, "message": "Validation passed"})
        elif form_type == 'contact':
            contact_message = ContactMessage(**form_data)
            return jsonify({"valid": True, "message": "Validation passed"})
        else:
            return jsonify({"valid": False, "message": "Unknown form type"})
            
    except ValidationError as e:
        errors = {err['loc'][0]: err['msg'] for err in e.errors()}
        return jsonify({"valid": False, "errors": errors})
    except Exception as e:
        return jsonify({"valid": False, "message": str(e)})


if __name__ == "__main__":
    print("🚀 Starting Pydantic Forms Flask Demo")
    print("📱 Visit http://localhost:5000 to see the forms in action")
    print("🔥 Powered by Python 3.14 template strings!")
    app.run(debug=True, host='0.0.0.0', port=5000)
