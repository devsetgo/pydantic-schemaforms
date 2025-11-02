#!/usr/bin/env python3
"""
Flask Example using Pydantic Forms with Unified Templates

A clean Flask demonstration focusing on the core functionality:
- User and pet registration forms using pydantic-forms library
- Unified template system shared with FastAPI
- Bootstrap and Material Design themes
- Form validation and error handling
- Proper use of pydantic-forms library for HTML generation

Run with:
    python flask_example.py

Then visit:
    - http://localhost:5000/ (main page)
    - http://localhost:5000/user (user registration)
    - http://localhost:5000/pets (pet registration)
    - http://localhost:5000/dynamic (dynamic form demo)
"""

import os
from flask import Flask, request, render_template, redirect, url_for, flash

# Import shared models
from shared_models import (
    PetModel, PetOwnerForm, MinimalLoginForm, UserRegistrationForm, PetRegistrationForm,
    CompleteShowcaseForm, EmergencyContactModel, handle_form_submission
)

# Import pydantic-forms components
from pydantic_forms.form_layouts import ListLayout, SectionDesign
from pydantic_forms.enhanced_renderer import render_form_html, EnhancedFormRenderer
from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer

app = Flask(__name__)
app.secret_key = "demo-secret-key-change-in-production"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_form_with_icons(form_class, framework='bootstrap', errors=None):
    """
    Render a form with appropriate icons for the specified framework.
    
    Args:
        form_class: The Pydantic form model class
        framework: 'bootstrap' or 'material'
        errors: Optional validation errors
        
    Returns:
        Rendered HTML form with framework-appropriate icons
    """
    return render_form_html(form_class, framework=framework, errors=errors)

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

@app.route('/user', methods=['GET', 'POST'])
def user_registration():
    """User registration form."""
    style = request.args.get('style', 'bootstrap')
    framework_type = "material" if style == "material" else "bootstrap"
    
    if request.method == 'POST':
        result = handle_form_submission(UserRegistrationForm, request.form.to_dict())
        
        if result['success']:
            flash('User registration successful!', 'success')
            return render_template('user.html',
                                 title="Registration Success",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=True,
                                 user_data=result['data'])
        else:
            flash('Please correct the errors below.', 'error')
            form_html = render_form_with_icons(UserRegistrationForm, framework=style, errors=result['errors'])
            return render_template('user.html',
                                 title="User Registration",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_with_icons(UserRegistrationForm, framework=style)
        return render_template('user.html',
                             title="User Registration",
                             framework="flask",
                             framework_name="Flask",
                             framework_type=framework_type,
                             success=False,
                             form_html=form_html)

@app.route('/pets', methods=['GET', 'POST'])
def pet_registration():
    """Pet registration form with ListLayout."""
    style = request.args.get('style', 'bootstrap')
    framework_type = "material" if style == "material" else "bootstrap"
    
    if request.method == 'POST':
        result = handle_form_submission(PetRegistrationForm, request.form.to_dict())
        
        if result['success']:
            flash('Pet registration successful!', 'success')
            return render_template('pets.html',
                                 title="Pet Registration Success",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=True,
                                 form_data=result['data'])
        else:
            flash('Please correct the errors below.', 'error')
            form_html = render_form_with_icons(PetRegistrationForm, framework=style, errors=result['errors'])
            return render_template('pets.html',
                                 title="Pet Registration Form",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_with_icons(PetRegistrationForm, framework=style)
        return render_template('pets.html',
                             title="Pet Registration Form",
                             framework="flask",
                             framework_name="Flask",
                             framework_type=framework_type,
                             success=False,
                             form_html=form_html)

@app.route('/dynamic', methods=['GET', 'POST'])
def dynamic_form():
    """Dynamic form demo."""
    style = request.args.get('style', 'bootstrap')
    framework_type = "material" if style == "material" else "bootstrap"
    
    if request.method == 'POST':
        return render_template('dynamic.html',
                             title="Dynamic Form Success",
                             framework="flask",
                             framework_name="Flask",
                             framework_type=framework_type,
                             success=True,
                             form_data=dict(request.form))
    else:
        # Use the contact form for dynamic demo
        from shared_models import MediumContactForm
        form_html = render_form_with_icons(MediumContactForm, framework=style)
        return render_template('dynamic.html',
                             title="Dynamic Form Demo",
                             framework="flask",
                             framework_name="Flask",
                             framework_type=framework_type,
                             success=False,
                             form_html=form_html)

@app.route('/showcase', methods=['GET', 'POST'])
def showcase_form():
    """Complete showcase form with all pydantic-forms capabilities."""
    style = request.args.get('style', 'bootstrap')
    framework_type = "material" if style == "material" else "bootstrap"
    
    if request.method == 'POST':
        result = handle_form_submission(CompleteShowcaseForm, request.form.to_dict())
        
        if result['success']:
            flash('Showcase form submitted successfully!', 'success')
            return render_template('showcase.html',
                                 title="Showcase Success",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=True,
                                 form_data=result['data'])
        else:
            flash('Please correct the errors below.', 'error')
            form_html = render_form_with_icons(CompleteShowcaseForm, framework=style, errors=result['errors'])
            return render_template('showcase.html',
                                 title="Complete Showcase Form",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_with_icons(CompleteShowcaseForm, framework=style)
        return render_template('showcase.html',
                             title="Complete Showcase Form",
                             framework="flask",
                             framework_name="Flask",
                             framework_type=framework_type,
                             success=False,
                             form_html=form_html)

@app.route('/login', methods=['GET', 'POST'])
def login_form():
    """Simple login form."""
    style = request.args.get('style', 'bootstrap')
    framework_type = "material" if style == "material" else "bootstrap"
    
    if request.method == 'POST':
        result = handle_form_submission(MinimalLoginForm, request.form.to_dict())
        
        if result['success']:
            flash('Login successful!', 'success')
            return render_template('login.html',
                                 title="Login Success",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=True,
                                 form_data=result['data'])
        else:
            flash('Please correct the errors below.', 'error')
            form_html = render_form_with_icons(MinimalLoginForm, framework=style, errors=result['errors'])
            return render_template('login.html',
                                 title="Login Form",
                                 framework="flask",
                                 framework_name="Flask",
                                 framework_type=framework_type,
                                 success=False,
                                 form_html=form_html,
                                 errors=result['errors'])
    else:
        form_html = render_form_with_icons(MinimalLoginForm, framework=style)
        return render_template('login.html',
                             title="Login Form",
                             framework="flask",
                             framework_name="Flask",
                             framework_type=framework_type,
                             success=False,
                             form_html=form_html)

@app.route('/test-self-contained')
def test_self_contained():
    """Test self-contained form rendering - demonstrates complete autonomy."""
    # Use the new working Material Design renderer for self-contained test
    material_renderer = SimpleMaterialRenderer()
    my_form = material_renderer.render_form_from_model(UserRegistrationForm)
    
    # Return minimal HTML with just the form
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask Material Design Self-Contained Test</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 800px; margin: 50px auto; padding: 20px; }}
        .form-showcase {{ border: 2px solid #e7e0ec; border-radius: 16px; padding: 20px; background: #fef7ff; }}
        .info-box {{ background: #f3f0ff; padding: 20px; border-radius: 12px; font-family: monospace; margin-top: 30px; }}
        pre {{ background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #e7e0ec; margin: 10px 0; }}
        .nav-link {{ color: #6750a4; text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Flask Material Design Self-Contained Test</h1>
        <p><strong>This demonstrates complete Material Design 3 autonomy.</strong></p>
        <p>The form below includes ALL Material Design dependencies internally:</p>
        
        <!-- ALL FORM CONTENT IS SELF-CONTAINED -->
        <div class="form-showcase">
            {my_form}
        </div>
        
        <hr style="margin: 40px 0; border: 1px solid #e7e0ec;">
        
        <div class="info-box">
            <h3>🎯 What you see above is Material Design 3 from just:</h3>
            <pre>&lt;div&gt;
    {{{{ my_form | safe }}}}
&lt;/div&gt;</pre>
            <p><strong>✅ Zero external dependencies required!</strong></p>
            <ul style="margin: 0; padding-left: 20px;">
                <li>No external CSS files needed</li>
                <li>No external JavaScript files needed</li>
                <li>No Google Fonts or CDN dependencies</li>
                <li>Complete Material Design 3 styling embedded</li>
                <li>Material Design interactions included</li>
                <li>Collapsible lists and dynamic forms work</li>
            </ul>
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <a href="/" class="nav-link">← Back to Flask Home</a>
        </div>
    </div>
</body>
</html>"""

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('404.html',
                         title="Page Not Found",
                         framework="flask",
                         framework_name="Flask",
                         framework_type="bootstrap",
                         error_code=404,
                         error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('500.html',
                         title="Server Error",
                         framework="flask",
                         framework_name="Flask",
                         framework_type="bootstrap",
                         error_code=500,
                         error_message="An internal server error occurred."), 500

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print("🚀 Starting Flask Pydantic Forms Example...")
    print(f"📄 Home page: http://localhost:{port}/")
    print(f"👤 User registration: http://localhost:{port}/user")
    print(f"� Login form: http://localhost:{port}/login")
    print(f"�🐾 Pet registration: http://localhost:{port}/pets")
    print(f"🎨 Complete showcase: http://localhost:{port}/showcase")
    print(f"⚡ Dynamic form: http://localhost:{port}/dynamic")
    print(f"🧪 Self-contained test: http://localhost:{port}/test-self-contained")
    print(f"🎨 Material Design: http://localhost:{port}/user?style=material")
    print(f"🎨 Material Showcase: http://localhost:{port}/showcase?style=material")
    print("⚡ Features: ListLayout, Collapsible Cards, Bootstrap/Material Design, Self-contained forms, Zero dependencies")
    
    app.run(host='0.0.0.0', port=port, debug=True)