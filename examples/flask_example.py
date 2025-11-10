#!/usr/bin/env python3
"""
Flask Example - Sync Implementation
==================================

This example demonstrates ALL pydantic-forms capabilities in a synchronous Flask application.
It showcases simple, medium, and complex forms with various layouts.

Forms demonstrated:
- Simple: MinimalLoginForm (basic fields, validation)
- Medium: UserRegistrationForm (multiple field types, icons, validation)
- Complex: CompleteShowcaseForm (model lists, dynamic fields, sections, all input types)

Layouts demonstrated:
- Bootstrap styling with external icons
- Material Design 3 styling with external icons
- Self-contained forms (zero dependencies)
- Dynamic list layouts with add/remove functionality
- Sectioned forms with collapsible sections
- All input types (text, email, password, select, number, date, color, range, etc.)
"""

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_models import (
    # Simple Form
    MinimalLoginForm,
    # Medium Form  
    UserRegistrationForm,
    # Complex Form
    CompleteShowcaseForm,
    # Pet Forms
    PetRegistrationForm,
    # Utility functions
    handle_form_submission
)
from pydantic_forms.enhanced_renderer import render_form_html

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

# ================================
# HOME PAGE - ALL EXAMPLES
# ================================

@app.route("/")
def home():
    """Home page showcasing all form examples."""
    return render_template("home.html", 
                         framework="flask",
                         framework_name="Flask",
                         framework_type="sync")

# ================================
# SIMPLE FORM - LOGIN
# ================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Simple form example - Login with basic validation."""
    if request.method == "POST":
        # Handle form submission (sync)
        result = handle_form_submission(MinimalLoginForm, request.form.to_dict())
        
        if result['success']:
            flash(f"Welcome {result['data'].username}!", "success")
            return render_template("success.html",
                                 title="Login Successful",
                                 message=f"Welcome {result['data'].username}!",
                                 data=result['data'],
                                 framework="flask",
                                 framework_name="Flask (Sync)")
        else:
            flash("Login failed. Please check your credentials.", "error")
            form_html = render_form_html(MinimalLoginForm, 
                                       framework=request.args.get("style", "bootstrap"),
                                       errors=result['errors'])
            return render_template("form.html",
                                 title="Login - Simple Form",
                                 description="Demonstrates basic form fields and validation",
                                 framework="flask",
                                 framework_name="Flask (Sync)",
                                 framework_type=request.args.get("style", "bootstrap"),
                                 form_html=form_html,
                                 errors=result['errors'])
    
    # GET request - show form
    style = request.args.get("style", "bootstrap")
    form_html = render_form_html(MinimalLoginForm, framework=style)
    
    return render_template("form.html", 
                         title="Login - Simple Form",
                         description="Demonstrates basic form fields and validation",
                         framework="flask",
                         framework_name="Flask (Sync)",
                         framework_type=style,
                         form_html=form_html)

# ================================
# MEDIUM FORM - USER REGISTRATION
# ================================

@app.route("/register", methods=["GET", "POST"])
def register():
    """Medium complexity form - User registration with multiple field types."""
    if request.method == "POST":
        # Handle form submission (sync)
        result = handle_form_submission(UserRegistrationForm, request.form.to_dict())
        
        if result['success']:
            flash(f"Registration successful! Welcome {result['data'].username}!", "success")
            return render_template("success.html",
                                 title="Registration Successful",
                                 message=f"Welcome {result['data'].username}! Your account has been created.",
                                 data=result['data'],
                                 framework="flask",
                                 framework_name="Flask (Sync)")
        else:
            flash("Registration failed. Please correct the errors below.", "error")
            form_html = render_form_html(UserRegistrationForm, 
                                       framework=request.args.get("style", "bootstrap"),
                                       errors=result['errors'])
            return render_template("form.html",
                                 title="User Registration - Medium Form",
                                 description="Demonstrates multiple field types, icons, and validation",
                                 framework="flask",
                                 framework_name="Flask (Sync)",
                                 framework_type=request.args.get("style", "bootstrap"),
                                 form_html=form_html,
                                 errors=result['errors'])
    
    # GET request - show form
    style = request.args.get("style", "bootstrap")
    form_html = render_form_html(UserRegistrationForm, framework=style)
    
    return render_template("form.html", 
                         title="User Registration - Medium Form",
                         description="Demonstrates multiple field types, icons, and validation",
                         framework="flask",
                         framework_name="Flask (Sync)",
                         framework_type=style,
                         form_html=form_html)

# ================================
# COMPLEX FORM - COMPLETE SHOWCASE
# ================================

@app.route("/showcase", methods=["GET", "POST"])
def showcase():
    """Complex form example - All features and field types."""
    if request.method == "POST":
        # Handle form submission (sync)
        result = handle_form_submission(CompleteShowcaseForm, request.form.to_dict())
        
        if result['success']:
            flash("Showcase form submitted successfully!", "success")
            return render_template("success.html",
                                 title="Showcase Form Submitted Successfully",
                                 message="All form data processed successfully!",
                                 data=result['data'],
                                 framework="flask",
                                 framework_name="Flask (Sync)")
        else:
            flash("Form submission failed. Please correct the errors below.", "error")
            form_html = render_form_html(CompleteShowcaseForm, 
                                       framework=request.args.get("style", "bootstrap"),
                                       errors=result['errors'])
            return render_template("form.html",
                                 title="Complete Showcase - Complex Form",
                                 description="Demonstrates ALL library features: model lists, sections, all input types",
                                 framework="flask",
                                 framework_name="Flask (Sync)",
                                 framework_type=request.args.get("style", "bootstrap"),
                                 form_html=form_html,
                                 errors=result['errors'])
    
    # GET request - show form
    style = request.args.get("style", "bootstrap")
    form_html = render_form_html(CompleteShowcaseForm, framework=style)
    
    return render_template("form.html", 
                         title="Complete Showcase - Complex Form",
                         description="Demonstrates ALL library features: model lists, sections, all input types",
                         framework="flask",
                         framework_name="Flask (Sync)",
                         framework_type=style,
                         form_html=form_html)

# ================================
# PET REGISTRATION - DYNAMIC LISTS
# ================================

@app.route("/pets", methods=["GET", "POST"])
def pets():
    """Pet registration form - demonstrates dynamic lists and complex models."""
    if request.method == "POST":
        # Handle form submission (sync)
        result = handle_form_submission(PetRegistrationForm, request.form.to_dict(flat=False))
        
        if result['success']:
            return render_template("success.html",
                                 title="Pet Registration Successful",
                                 message=f"Successfully registered pets for {result['data'].owner_name}!",
                                 data=result['data'],
                                 framework="flask",
                                 framework_name="Flask (Sync)")
        else:
            # Re-render form with errors
            style = request.args.get("style", "bootstrap")
            form_html = render_form_html(PetRegistrationForm, 
                                       framework=style,
                                       errors=result['errors'])
            
            return render_template("form.html",
                                 title="Pet Registration - Dynamic Lists",
                                 description="Demonstrates pet registration with dynamic lists and owner information",
                                 framework="flask",
                                 framework_name="Flask (Sync)",
                                 framework_type=style,
                                 form_html=form_html,
                                 errors=result['errors'])
    
    # GET request - show form
    style = request.args.get("style", "bootstrap")
    form_html = render_form_html(PetRegistrationForm, framework=style)
    
    return render_template("form.html", 
                         title="Pet Registration - Dynamic Lists",
                         description="Demonstrates pet registration with dynamic lists and owner information",
                         framework="flask",
                         framework_name="Flask (Sync)",
                         framework_type=style,
                         form_html=form_html)

# Style-specific routes for pets
@app.route("/bootstrap/pets", methods=["GET", "POST"])
def bootstrap_pets():
    """Bootstrap-specific pets demo."""
    if request.method == "POST":
        return pets()
    else:
        request.args = request.args.copy()
        request.args['style'] = 'bootstrap'
        return pets()

@app.route("/material/pets", methods=["GET", "POST"])
def material_pets():
    """Material Design pets demo."""
    if request.method == "POST":
        return pets()
    else:
        request.args = request.args.copy()
        request.args['style'] = 'material'
        return pets()

# ================================
# SPECIAL DEMOS
# ================================

@app.route("/self-contained")
def self_contained():
    """Self-contained form demo - zero external dependencies."""
    from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer
    
    renderer = SimpleMaterialRenderer()
    form_html = renderer.render_form_from_model(UserRegistrationForm)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Self-Contained Form Demo</title>
</head>
<body style="max-width: 600px; margin: 50px auto; padding: 20px; font-family: system-ui;">
    <h1>🎯 Self-Contained Form Demo</h1>
    <p><strong>This form includes ZERO external dependencies!</strong></p>
    <p>Everything needed is embedded in the form HTML below:</p>
    
    <div style="border: 2px solid #dee2e6; border-radius: 8px; padding: 20px; background: #f8f9fa;">
        {form_html}
    </div>
    
    <div style="margin-top: 30px; padding: 20px; background: #e7f3ff; border-radius: 8px;">
        <h3>🔧 What's Included:</h3>
        <ul>
            <li>✅ Complete Material Design 3 CSS</li>
            <li>✅ JavaScript for interactions</li>
            <li>✅ Material Icons font</li>
            <li>✅ Form validation and styling</li>
            <li>✅ No external CDN dependencies</li>
        </ul>
        <p><strong>Template Usage:</strong> <code>&lt;div&gt;{{{{ form_html | safe }}}}&lt;/div&gt;</code></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="/" style="color: #0066cc; text-decoration: none;">← Back to Flask Examples</a>
    </div>
</body>
</html>"""

# ================================
# API ENDPOINTS (JSON RESPONSES)
# ================================

@app.route("/api/forms/<form_type>")
def api_form_schema(form_type):
    """API endpoint to get form schema as JSON."""
    form_mapping = {
        "login": MinimalLoginForm,
        "register": UserRegistrationForm,
        "pets": PetRegistrationForm,
        "showcase": CompleteShowcaseForm
    }
    
    if form_type not in form_mapping:
        return jsonify({"error": "Form type not found"}), 404
    
    form_class = form_mapping[form_type]
    schema = form_class.model_json_schema()
    
    return jsonify({
        "form_type": form_type,
        "schema": schema,
        "framework": "flask"
    })

@app.route("/api/submit/<form_type>", methods=["POST"])
def api_submit_form(form_type):
    """API endpoint for form submission."""
    form_mapping = {
        "login": MinimalLoginForm,
        "register": UserRegistrationForm,
        "pets": PetRegistrationForm,
        "showcase": CompleteShowcaseForm
    }
    
    if form_type not in form_mapping:
        return jsonify({"error": "Form type not found"}), 404
    
    form_class = form_mapping[form_type]
    result = handle_form_submission(form_class, request.get_json())
    
    return jsonify({
        "success": result['success'],
        "data": result['data'].dict() if result['success'] else None,
        "errors": result['errors'],
        "framework": "flask"
    })

# ================================
# ERROR HANDLERS
# ================================

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500

# ================================
# RUN APPLICATION
# ================================

if __name__ == "__main__":
    print("🚀 Starting Flask Example (Sync)")
    print("=" * 60)
    print("📋 Available Examples:")
    print("   • Simple:  http://localhost:5000/login")
    print("   • Medium:  http://localhost:5000/register")
    print("   • Complex: http://localhost:5000/showcase")
    print("")
    print("🎨 Style Variants (add ?style= to any form):")
    print("   • Bootstrap:       ?style=bootstrap")
    print("   • Material Design: ?style=material")
    print("")
    print("🎯 Special Demos:")
    print("   • Self-Contained: http://localhost:5000/self-contained")
    print("   • API Schema:     http://localhost:5000/api/forms/register")
    print("   • Home Page:      http://localhost:5000/")
    print("=" * 60)
    
    app.run(debug=True, port=5000)