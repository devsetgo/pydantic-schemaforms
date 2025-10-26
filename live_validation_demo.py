"""
Demonstration of live server-side validation using HTMX.

This demo shows how to implement real-time validation with pydantic-forms
using Python 3.14 template strings and HTMX for seamless user experience.
"""

from flask import Flask, request, render_template_string
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
import re

from pydantic_forms.live_validation import (
    LiveValidator, HTMXValidationConfig, ValidationResponse,
    create_email_validator, create_password_strength_validator
)
from pydantic_forms.form_field import FormField


# Create Flask app
app = Flask(__name__)

# Configure live validation
validation_config = HTMXValidationConfig(
    validate_on_blur=True,
    validate_on_input=False,
    debounce_ms=500,
    show_success_indicators=True,
    show_warnings=True,
    clear_on_focus=True
)

validator_instance = LiveValidator(validation_config)


# Define a complex form model
class UserRegistrationForm(BaseModel):
    """Complex user registration form with various validation rules."""
    
    username: str = FormField(
        input_type="text",
        title="Username",
        help_text="Must be 3-20 characters, alphanumeric only"
    )
    
    email: EmailStr = FormField(
        input_type="email",
        title="Email Address",
        help_text="We'll never share your email"
    )
    
    password: str = FormField(
        input_type="password",
        title="Password",
        help_text="At least 8 characters with uppercase, lowercase, number, and special character"
    )
    
    confirm_password: str = FormField(
        input_type="password",
        title="Confirm Password",
        help_text="Must match your password"
    )
    
    age: int = Field(
        ge=13, le=120,
        description="Must be between 13 and 120"
    )
    
    website: Optional[str] = FormField(
        input_type="url",
        title="Website (Optional)",
        help_text="Enter your personal or company website"
    )
    
    bio: Optional[str] = FormField(
        input_type="textarea",
        title="Bio (Optional)",
        help_text="Tell us about yourself"
    )


# Custom validators
def create_username_validator():
    """Create username validator with specific rules."""
    def validate_username(value: str) -> ValidationResponse:
        errors = []
        warnings = []
        suggestions = []
        
        if not value:
            return ValidationResponse(
                field_name="username",
                is_valid=False,
                errors=["Username is required"],
                value=value
            )
        
        if len(value) < 3:
            errors.append("Username must be at least 3 characters long")
        elif len(value) > 20:
            errors.append("Username cannot be longer than 20 characters")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            errors.append("Username can only contain letters, numbers, and underscores")
            suggestions.append("Use only a-z, A-Z, 0-9, and _ characters")
        
        if value.lower() in ['admin', 'root', 'user', 'test']:
            warnings.append("This username might be too common")
            suggestions.append("Consider adding numbers or making it more unique")
        
        return ValidationResponse(
            field_name="username",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            value=value
        )
    
    return validate_username


def create_age_validator():
    """Create age validator."""
    def validate_age(value: str) -> ValidationResponse:
        try:
            age = int(value)
            if age < 13:
                return ValidationResponse(
                    field_name="age",
                    is_valid=False,
                    errors=["You must be at least 13 years old to register"],
                    value=value
                )
            elif age > 120:
                return ValidationResponse(
                    field_name="age",
                    is_valid=False,
                    errors=["Please enter a valid age"],
                    value=value
                )
            elif age < 18:
                return ValidationResponse(
                    field_name="age",
                    is_valid=True,
                    warnings=["Users under 18 require parental consent"],
                    value=value
                )
            
            return ValidationResponse(
                field_name="age",
                is_valid=True,
                value=value
            )
            
        except ValueError:
            return ValidationResponse(
                field_name="age",
                is_valid=False,
                errors=["Please enter a valid number"],
                value=value
            )
    
    return validate_age


def create_website_validator():
    """Create website URL validator."""
    def validate_website(value: str) -> ValidationResponse:
        if not value:  # Optional field
            return ValidationResponse(
                field_name="website",
                is_valid=True,
                value=value
            )
        
        url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        
        if not re.match(url_pattern, value):
            return ValidationResponse(
                field_name="website",
                is_valid=False,
                errors=["Please enter a valid URL"],
                suggestions=["Include http:// or https://", "Example: https://example.com"],
                value=value
            )
        
        return ValidationResponse(
            field_name="website",
            is_valid=True,
            value=value
        )
    
    return validate_website


# Register validators
validator_instance.register_validator("username", create_username_validator())
validator_instance.register_validator("email", create_email_validator())
validator_instance.register_validator("password", create_password_strength_validator())
validator_instance.register_validator("age", create_age_validator())
validator_instance.register_validator("website", create_website_validator())


# Global validator instance getter for endpoints
def get_validator_instance():
    return validator_instance


@app.route('/')
def index():
    """Main page with live validation demo."""
    
    # Generate the complete form HTML
    form_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Validation Demo - Pydantic Forms</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    
    <style>
        .validation-indicator {{
            margin-left: 0.5rem;
            display: none;
        }}
        
        .is-validating {{
            border-color: #ffc107;
            background-image: none;
        }}
        
        .has-warning {{
            border-color: #ffc107;
        }}
        
        .valid-feedback, .invalid-feedback {{
            display: block;
        }}
        
        .feedback-warnings {{
            color: #ffc107;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }}
        
        .feedback-suggestions {{
            color: #6c757d;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }}
        
        .feedback-suggestions ul {{
            margin: 0;
            padding-left: 1rem;
        }}
        
        .demo-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }}
        
        .feature-badge {{
            background: rgba(255, 255, 255, 0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.875rem;
            margin: 0.25rem;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <!-- Demo Header -->
    <div class="demo-header">
        <div class="container">
            <div class="row">
                <div class="col-lg-8 mx-auto text-center">
                    <h1 class="display-4 mb-3">
                        <i class="bi bi-lightning-charge"></i>
                        Live Validation Demo
                    </h1>
                    <p class="lead mb-4">
                        Real-time server-side validation using Python 3.14 template strings and HTMX
                    </p>
                    <div>
                        <span class="feature-badge">✨ Instant Feedback</span>
                        <span class="feature-badge">🚀 No Page Reloads</span>
                        <span class="feature-badge">🎯 Server-Side Logic</span>
                        <span class="feature-badge">♿ Accessible</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">
                        <h3 class="card-title mb-0">
                            <i class="bi bi-person-plus"></i>
                            User Registration Form
                        </h3>
                        <small>All fields validate in real-time as you type or leave each field</small>
                    </div>
                    <div class="card-body">
                        <form id="registration-form" action="/submit" method="POST">
                            
                            <!-- Username Field -->
                            {validator_instance.render_field_with_live_validation(
                                field_name="username",
                                field_type="text",
                                label="Username",
                                placeholder="Enter your username",
                                class_="form-control",
                                required=True
                            )}
                            
                            <!-- Email Field -->
                            {validator_instance.render_field_with_live_validation(
                                field_name="email",
                                field_type="email",
                                label="Email Address",
                                placeholder="your@email.com",
                                class_="form-control",
                                required=True
                            )}
                            
                            <!-- Password Field -->
                            {validator_instance.render_field_with_live_validation(
                                field_name="password",
                                field_type="password",
                                label="Password",
                                placeholder="Create a strong password",
                                class_="form-control",
                                required=True
                            )}
                            
                            <!-- Age Field -->
                            {validator_instance.render_field_with_live_validation(
                                field_name="age",
                                field_type="number",
                                label="Age",
                                placeholder="Your age",
                                class_="form-control",
                                min="13",
                                max="120",
                                required=True
                            )}
                            
                            <!-- Website Field -->
                            {validator_instance.render_field_with_live_validation(
                                field_name="website",
                                field_type="url",
                                label="Website (Optional)",
                                placeholder="https://yourwebsite.com",
                                class_="form-control"
                            )}
                            
                            <div class="d-grid gap-2 mt-4">
                                <button type="submit" class="btn btn-primary btn-lg">
                                    <i class="bi bi-check-circle"></i>
                                    Create Account
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
                
                <!-- Demo Information -->
                <div class="card mt-4">
                    <div class="card-header">
                        <h4 class="card-title mb-0">
                            <i class="bi bi-info-circle"></i>
                            Live Validation Features
                        </h4>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h5>Username Validation</h5>
                                <ul class="list-unstyled">
                                    <li>✓ 3-20 characters</li>
                                    <li>✓ Alphanumeric + underscores only</li>
                                    <li>✓ Common name warnings</li>
                                </ul>
                                
                                <h5 class="mt-3">Email Validation</h5>
                                <ul class="list-unstyled">
                                    <li>✓ Valid email format</li>
                                    <li>✓ Auto-formatting</li>
                                    <li>✓ Helpful suggestions</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h5>Password Validation</h5>
                                <ul class="list-unstyled">
                                    <li>✓ Minimum 8 characters</li>
                                    <li>✓ Uppercase & lowercase</li>
                                    <li>✓ Numbers & special characters</li>
                                    <li>✓ Strength indicators</li>
                                </ul>
                                
                                <h5 class="mt-3">Age Validation</h5>
                                <ul class="list-unstyled">
                                    <li>✓ 13-120 years range</li>
                                    <li>✓ Parental consent warnings</li>
                                    <li>✓ Numeric validation</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- HTMX Live Validation Script -->
    {validator_instance.render_htmx_script()}
    
</body>
</html>
"""
    
    return form_html


@app.route('/validate/<field_name>', methods=['POST'])
def validate_field_endpoint(field_name):
    """Live validation endpoint for individual fields."""
    try:
        # Get the field value from the request
        if request.content_type == 'application/json':
            value = request.json.get('value', '')
        else:
            value = request.form.get('value', '')
        
        # Perform validation
        response = validator_instance.validate_field(field_name, value)
        
        # Generate feedback HTML
        if response.is_valid:
            if response.warnings:
                feedback_class = "valid-feedback"
                feedback_content = "✓ Valid"
                if validator_instance.config.show_warnings:
                    warnings_html = "<br>".join([f"⚠️ {w}" for w in response.warnings])
                    feedback_content += f'<div class="feedback-warnings">{warnings_html}</div>'
            else:
                feedback_class = "valid-feedback"
                feedback_content = "✓ Valid"
        else:
            feedback_class = "invalid-feedback"
            errors_html = "<br>".join([f"❌ {e}" for e in response.errors])
            feedback_content = errors_html
            
            if response.suggestions and validator_instance.config.show_suggestions:
                suggestions_html = "<ul>" + "".join([f"<li>{s}</li>" for s in response.suggestions]) + "</ul>"
                feedback_content += f'<div class="feedback-suggestions"><strong>Suggestions:</strong>{suggestions_html}</div>'
        
        # Return the feedback HTML
        return validator_instance.validation_template.render(
            feedback_class=feedback_class,
            field_name=field_name,
            feedback_content=feedback_content
        ), 200 if response.is_valid else 400
        
    except Exception as e:
        return f'<div class="invalid-feedback">❌ Validation error: {str(e)}</div>', 500


@app.route('/submit', methods=['POST'])
def submit_form():
    """Handle form submission."""
    try:
        # Get all form data
        form_data = request.form.to_dict()
        
        # Validate the complete form
        user_form = UserRegistrationForm(**form_data)
        
        # Success response
        return f"""
        <div class="alert alert-success" role="alert">
            <h4 class="alert-heading">Registration Successful! 🎉</h4>
            <p>Welcome, <strong>{user_form.username}</strong>! Your account has been created.</p>
            <hr>
            <p class="mb-0">
                <strong>Email:</strong> {user_form.email}<br>
                <strong>Age:</strong> {user_form.age}<br>
                {f'<strong>Website:</strong> {user_form.website}<br>' if user_form.website else ''}
            </p>
            <div class="mt-3">
                <a href="/" class="btn btn-primary">Try Again</a>
            </div>
        </div>
        """
        
    except Exception as e:
        return f"""
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">Validation Failed</h4>
            <p>Please correct the errors and try again.</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <div class="mt-3">
                <a href="/" class="btn btn-primary">Go Back</a>
            </div>
        </div>
        """


@app.route('/api/validation-endpoints')
def show_validation_endpoints():
    """Show example code for different frameworks."""
    return f"""
    <div class="container mt-4">
        <h2>Implementation Examples</h2>
        
        <div class="accordion" id="frameworkExamples">
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#flask-example">
                        Flask Implementation
                    </button>
                </h2>
                <div id="flask-example" class="accordion-collapse collapse show">
                    <div class="accordion-body">
                        <pre><code>{validator_instance.generate_validation_endpoint_code('flask')}</code></pre>
                    </div>
                </div>
            </div>
            
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#fastapi-example">
                        FastAPI Implementation
                    </button>
                </h2>
                <div id="fastapi-example" class="accordion-collapse collapse">
                    <div class="accordion-body">
                        <pre><code>{validator_instance.generate_validation_endpoint_code('fastapi')}</code></pre>
                    </div>
                </div>
            </div>
            
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#django-example">
                        Django Implementation
                    </button>
                </h2>
                <div id="django-example" class="accordion-collapse collapse">
                    <div class="accordion-body">
                        <pre><code>{validator_instance.generate_validation_endpoint_code('django')}</code></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


if __name__ == "__main__":
    print("🚀 Starting Live Validation Demo...")
    print("📄 Main demo: http://localhost:5000/")
    print("🔧 Implementation examples: http://localhost:5000/api/validation-endpoints")
    print("⚡ Features: Real-time validation, HTMX integration, Python 3.14 templates")
    
    app.run(debug=True, port=5000)