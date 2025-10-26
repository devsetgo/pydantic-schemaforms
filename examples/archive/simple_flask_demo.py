#!/usr/bin/env python3
"""
Simple Flask Demo for Pydantic Forms
====================================

A standalone Flask application demonstrating form creation and validation
using Pydantic models with minimal dependencies.

Run with:
    python simple_flask_demo.py

Then visit:
    - http://localhost:5000/ (main demo page)
    - http://localhost:5000/minimal (login form)
    - http://localhost:5000/medium (contact form)
    - http://localhost:5000/kitchen (all features)
"""

import os
import sys
from datetime import date
from typing import Optional
from flask import Flask, request, render_template_string
from pydantic import BaseModel, Field, field_validator, EmailStr

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)


# Pydantic Models for form validation
class LoginModel(BaseModel):
    """Simple login form model."""

    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=6, description="Password")
    remember_me: bool = Field(default=False, description="Remember me")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return v


class ContactModel(BaseModel):
    """Contact form model with more fields."""

    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    subject: str = Field(..., min_length=5, max_length=200, description="Subject")
    message: str = Field(..., min_length=10, max_length=2000, description="Message")
    priority: str = Field(default="medium", description="Priority level")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v


class KitchenSinkModel(BaseModel):
    """Kitchen sink model with all field types."""

    text_field: str = Field(..., min_length=1, description="Text input")
    email_field: EmailStr = Field(..., description="Email input")
    password_field: str = Field(..., min_length=6, description="Password")
    integer_field: int = Field(..., ge=1, le=100, description="Integer between 1-100")
    float_field: float = Field(..., ge=0, le=1000, description="Decimal number")
    textarea_field: str = Field(..., min_length=10, description="Text area")
    select_field: str = Field(..., description="Select dropdown")
    radio_field: str = Field(..., description="Radio selection")
    date_field: date = Field(..., description="Date picker")
    checkbox_field: bool = Field(default=False, description="Checkbox option")
    terms_accepted: bool = Field(default=False, description="Terms acceptance")

    @field_validator("terms_accepted")
    @classmethod
    def validate_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v


# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Pydantic Forms Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; }
        .demo-section { background: white; border-radius: 15px; padding: 2rem; margin: 2rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .form-container { background: white; border-radius: 10px; padding: 2rem; margin: 1rem 0; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .navbar { background: rgba(255,255,255,0.95) !important; backdrop-filter: blur(10px); }
        .result-display { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 5px; padding: 1rem; margin: 1rem 0; }
        .error-display { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 5px; padding: 1rem; margin: 1rem 0; }
        .card { border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card-header { background: linear-gradient(45deg, #667eea, #764ba2); color: white; }
        .btn-primary { background: linear-gradient(45deg, #667eea, #764ba2); border: none; }
        .btn-success { background: linear-gradient(45deg, #56ab2f, #a8e6cf); border: none; }
        .btn-warning { background: linear-gradient(45deg, #f093fb, #f5576c); border: none; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light fixed-top">
        <div class="container">
            <a class="navbar-brand" href="/"><strong><i class="bi bi-magic"></i> Pydantic Forms</strong></a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="bi bi-house"></i> Home</a>
                <a class="nav-link" href="/minimal"><i class="bi bi-person"></i> Login</a>
                <a class="nav-link" href="/medium"><i class="bi bi-envelope"></i> Contact</a>
                <a class="nav-link" href="/kitchen"><i class="bi bi-stars"></i> Kitchen Sink</a>
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


def handle_form_submission(model_class, success_message):
    """Generic form submission handler."""
    try:
        # Convert form data to dict (handle checkboxes properly)
        form_data = request.form.to_dict()

        # Handle checkboxes (they're not submitted if unchecked)
        for field_name in ["remember_me", "checkbox_field", "terms_accepted"]:
            if field_name not in form_data:
                form_data[field_name] = False
            else:
                form_data[field_name] = True

        # Handle date fields
        if "date_field" in form_data and form_data["date_field"]:
            from datetime import datetime

            form_data["date_field"] = datetime.strptime(form_data["date_field"], "%Y-%m-%d").date()

        # Validate with Pydantic
        validated_data = model_class(**form_data)

        return {"success": True, "message": success_message, "data": validated_data.model_dump()}
    except Exception as e:
        return {"success": False, "message": str(e), "data": form_data}


@app.route("/")
def index():
    """Main demo page."""
    content = """
    <div class="demo-section text-center">
        <h1><i class="bi bi-magic"></i> Pydantic Forms Demo</h1>
        <p class="lead">Beautiful, validated forms using Pydantic models and Flask</p>
        <p class="text-muted">This demo showcases three different complexity levels of forms, all using Pydantic for validation.</p>
    </div>

    <div class="row g-4">
        <div class="col-md-4">
            <div class="card h-100">
                <div class="card-header text-center">
                    <h5><i class="bi bi-person"></i> Minimal Form</h5>
                </div>
                <div class="card-body">
                    <p>Simple login form with basic validation:</p>
                    <ul>
                        <li>Username/email field</li>
                        <li>Password field</li>
                        <li>Remember me checkbox</li>
                        <li>Basic Pydantic validation</li>
                    </ul>
                </div>
                <div class="card-footer">
                    <a href="/minimal" class="btn btn-primary w-100">
                        <i class="bi bi-arrow-right"></i> Try Login Form
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card h-100">
                <div class="card-header text-center">
                    <h5><i class="bi bi-envelope"></i> Medium Form</h5>
                </div>
                <div class="card-body">
                    <p>Contact form with more complexity:</p>
                    <ul>
                        <li>Multiple text inputs</li>
                        <li>Email validation</li>
                        <li>Phone number validation</li>
                        <li>Dropdown selections</li>
                        <li>Textarea for messages</li>
                    </ul>
                </div>
                <div class="card-footer">
                    <a href="/medium" class="btn btn-success w-100">
                        <i class="bi bi-arrow-right"></i> Try Contact Form
                    </a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card h-100">
                <div class="card-header text-center">
                    <h5><i class="bi bi-stars"></i> Kitchen Sink</h5>
                </div>
                <div class="card-body">
                    <p>Complete showcase of all features:</p>
                    <ul>
                        <li>Every input type</li>
                        <li>Advanced validation</li>
                        <li>File uploads</li>
                        <li>Date pickers</li>
                        <li>Complex layout options</li>
                    </ul>
                </div>
                <div class="card-footer">
                    <a href="/kitchen" class="btn btn-warning w-100">
                        <i class="bi bi-arrow-right"></i> Try Kitchen Sink
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="demo-section">
        <h3>Features Demonstrated</h3>
        <div class="row g-3">
            <div class="col-md-6">
                <h5><i class="bi bi-shield-check text-success"></i> Pydantic Validation</h5>
                <ul>
                    <li>Type checking and conversion</li>
                    <li>Field validation with custom validators</li>
                    <li>Error handling and display</li>
                    <li>Data sanitization</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h5><i class="bi bi-palette text-primary"></i> Bootstrap Integration</h5>
                <ul>
                    <li>Responsive form layouts</li>
                    <li>Beautiful styling</li>
                    <li>Card-based organization</li>
                    <li>Modern UI components</li>
                </ul>
            </div>
        </div>
    </div>
    """

    return render_page("Home", content)


@app.route("/minimal", methods=["GET", "POST"])
def minimal():
    """Minimal form example."""

    # Handle form submission
    login_result = None

    if request.method == "POST":
        login_result = handle_form_submission(LoginModel, "Login successful!")

    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-person"></i> Minimal Form Example</h1>
        <p class="lead">Simple login form demonstrating basic Pydantic validation.</p>
    </div>

    <div class="form-container">
        <h3><i class="bi bi-box-arrow-in-right"></i> User Login</h3>
        
        {'<div class="result-display"><strong>Success!</strong> ' + str(login_result) + '</div>' if login_result and login_result.get('success') else ''}
        {'<div class="error-display"><strong>Error:</strong> ' + str(login_result.get('message', '')) + '</div>' if login_result and not login_result.get('success') else ''}
        
        <form method="POST" class="needs-validation" novalidate>
            <div class="mb-3">
                <label for="username" class="form-label">Username <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="username" name="username" placeholder="Enter username or email" required>
                <div class="form-text">Must be at least 3 characters long.</div>
            </div>
            
            <div class="mb-3">
                <label for="password" class="form-label">Password <span class="text-danger">*</span></label>
                <input type="password" class="form-control" id="password" name="password" placeholder="Enter password" required>
                <div class="form-text">Must be at least 6 characters long.</div>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="remember_me" name="remember_me" value="true">
                <label class="form-check-label" for="remember_me">
                    Remember me
                </label>
            </div>
            
            <input type="hidden" name="login_submit" value="1">
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-box-arrow-in-right"></i> Sign In
                </button>
            </div>
        </form>
    </div>

    <div class="form-container">
        <h4>Form Features</h4>
        <ul>
            <li><strong>Username validation:</strong> Minimum 3 characters</li>
            <li><strong>Password validation:</strong> Minimum 6 characters</li>
            <li><strong>Optional checkbox:</strong> Remember me functionality</li>
            <li><strong>Error handling:</strong> Clear validation messages</li>
        </ul>
    </div>
    """

    return render_page("Login", content)


@app.route("/medium", methods=["GET", "POST"])
def medium():
    """Medium complexity form example."""

    # Handle form submission
    contact_result = None

    if request.method == "POST":
        contact_result = handle_form_submission(
            ContactModel, "Contact form submitted successfully!"
        )

    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-envelope"></i> Medium Complexity Form</h1>
        <p class="lead">Contact form with more fields and validation options.</p>
    </div>

    <div class="form-container">
        <h3><i class="bi bi-chat-dots"></i> Contact Us</h3>
        <p class="text-muted">Get in touch with us using the form below.</p>
        
        {'<div class="result-display"><strong>Success!</strong> ' + str(contact_result) + '</div>' if contact_result and contact_result.get('success') else ''}
        {'<div class="error-display"><strong>Error:</strong> ' + str(contact_result.get('message', '')) + '</div>' if contact_result and not contact_result.get('success') else ''}
        
        <form method="POST" class="needs-validation" novalidate>
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="name" class="form-label">Full Name <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="name" name="name" placeholder="Enter your full name" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="email" class="form-label">Email Address <span class="text-danger">*</span></label>
                        <input type="email" class="form-control" id="email" name="email" placeholder="Enter your email" required>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="phone" class="form-label">Phone Number</label>
                        <input type="tel" class="form-control" id="phone" name="phone" placeholder="Enter your phone number">
                        <div class="form-text">Optional, but must be at least 10 digits if provided.</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="priority" class="form-label">Priority</label>
                        <select class="form-select" id="priority" name="priority">
                            <option value="low">Low</option>
                            <option value="medium" selected>Medium</option>
                            <option value="high">High</option>
                            <option value="urgent">Urgent</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <label for="subject" class="form-label">Subject <span class="text-danger">*</span></label>
                <input type="text" class="form-control" id="subject" name="subject" placeholder="Enter message subject" required>
                <div class="form-text">Minimum 5 characters, maximum 200.</div>
            </div>
            
            <div class="mb-3">
                <label for="message" class="form-label">Message <span class="text-danger">*</span></label>
                <textarea class="form-control" id="message" name="message" rows="4" placeholder="Enter your message" required></textarea>
                <div class="form-text">Minimum 10 characters, maximum 2000.</div>
            </div>
            
            <input type="hidden" name="contact_submit" value="1">
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-success">
                    <i class="bi bi-send"></i> Send Message
                </button>
            </div>
        </form>
    </div>

    <div class="form-container">
        <h4>Form Features</h4>
        <div class="row">
            <div class="col-md-6">
                <ul>
                    <li><strong>Email validation:</strong> Built-in Pydantic EmailStr</li>
                    <li><strong>Phone validation:</strong> Custom validator for phone numbers</li>
                    <li><strong>Text length validation:</strong> Min/max constraints</li>
                </ul>
            </div>
            <div class="col-md-6">
                <ul>
                    <li><strong>Responsive layout:</strong> Two-column design</li>
                    <li><strong>Dropdown selection:</strong> Priority levels</li>
                    <li><strong>Optional fields:</strong> Phone number is optional</li>
                </ul>
            </div>
        </div>
    </div>
    """

    return render_page("Contact", content)


@app.route("/kitchen", methods=["GET", "POST"])
def kitchen_sink():
    """Kitchen sink form - showcasing all features."""

    # Handle form submission
    kitchen_result = None

    if request.method == "POST":
        kitchen_result = handle_form_submission(
            KitchenSinkModel, "Kitchen sink form submitted successfully!"
        )

    content = f"""
    <div class="demo-section">
        <h1><i class="bi bi-stars"></i> Kitchen Sink Form</h1>
        <p class="lead">Complete showcase of every input type, layout option, and advanced feature.</p>
    </div>

    <div class="form-container">
        <h3><i class="bi bi-collection"></i> All Input Types</h3>
        <p class="text-muted">This form demonstrates every available input type and feature.</p>
        
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


if __name__ == "__main__":
    print("🚀 Starting Pydantic Forms Demo...")
    print("📄 Visit: http://localhost:5000/")
    print("🔐 Login form: http://localhost:5000/minimal")
    print("📧 Contact form: http://localhost:5000/medium")
    print("🏪 Kitchen sink: http://localhost:5000/kitchen")

    app.run(debug=True, host="0.0.0.0", port=5000)
