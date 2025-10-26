"""
Flask Integration Example for Pydantic Forms

This example demonstrates how to integrate pydantic-forms with Flask
to create web applications with automatically generated forms.
"""

from flask import Flask, make_response
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from pydantic_forms.enhanced_renderer import EnhancedFormRenderer
from pydantic_forms.schema_form import FormModel

app = Flask(__name__)


# Define your Pydantic models with UI hints
class UserRegistrationForm(FormModel):
    username: str = Field(
        ..., min_length=3, max_length=20, description="Choose a unique username", ui_autofocus=True
    )
    email: str = Field(..., description="Your email address", ui_element="email")
    password: str = Field(
        ..., min_length=8, description="Choose a secure password", ui_element="password"
    )
    age: int = Field(..., ge=13, le=120, description="Your age", ui_element="number")
    newsletter: bool = Field(
        False, description="Subscribe to our newsletter", ui_element="checkbox"
    )
    birthday: Optional[date] = Field(None, description="Your birth date", ui_element="date")


class ContactForm(FormModel):
    name: str = Field(..., min_length=2, description="Your full name", ui_autofocus=True)
    email: str = Field(..., description="Your email address", ui_element="email")
    phone: Optional[str] = Field(None, description="Your phone number", ui_element="tel")
    website: Optional[str] = Field(None, description="Your website URL", ui_element="url")
    message: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Your message",
        ui_element="textarea",
        ui_options={"rows": 5},
    )


class EventForm(FormModel):
    event_name: str = Field(..., description="Name of the event", ui_autofocus=True)
    event_datetime: str = Field(
        ..., description="When the event starts", ui_element="datetime-local"
    )
    max_attendees: int = Field(
        ..., ge=1, le=1000, description="Maximum number of attendees", ui_element="number"
    )
    is_public: bool = Field(
        True, description="Make this event publicly visible", ui_element="checkbox"
    )
    event_color: str = Field("#3498db", description="Theme color for the event", ui_element="color")


# Initialize the form renderer
renderer = EnhancedFormRenderer()


@app.route("/user-registration", methods=["GET"])
def user_registration():
    """User registration form using Bootstrap framework."""
    html = _render_form_page(
        UserRegistrationForm,
        framework="bootstrap",
        title="User Registration",
        submit_url="/register",
    )
    return make_response(html)


@app.route("/contact", methods=["GET"])
def contact():
    """Contact form using Material Design framework."""
    html = _render_form_page(
        ContactForm, framework="material", title="Contact Us", submit_url="/contact"
    )
    return make_response(html)


@app.route("/event", methods=["GET"])
def event():
    """Event form using no framework (plain HTML)."""
    html = _render_form_page(
        EventForm, framework="none", title="Create Event", submit_url="/create-event"
    )
    return make_response(html)


def _render_form_page(form_model, framework="bootstrap", title="Form", submit_url="/submit"):
    """Helper function to render a complete HTML page with form."""

    # Get framework-specific CSS
    css_links = {
        "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
        "material": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css",
        "none": "",
    }

    js_links = {
        "bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
        "material": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js",
        "none": "",
    }

    # Render the form
    form_html = form_model.render_form(framework=framework, submit_url=submit_url)

    # Create complete HTML page
    css_link = (
        f'<link href="{css_links[framework]}" rel="stylesheet">' if css_links[framework] else ""
    )
    js_link = f'<script src="{js_links[framework]}"></script>' if js_links[framework] else ""

    container_class = {
        "bootstrap": "container my-5",
        "material": "container",
        "none": "form-container",
    }[framework]

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>{title}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {css_link}
        <style>
            .form-container {{ 
                max-width: 600px; 
                margin: 2rem auto; 
                padding: 2rem; 
            }}
            .form-title {{ 
                text-align: center; 
                margin-bottom: 2rem; 
            }}
        </style>
    </head>
    <body>
        <div class="{container_class}">
            <h1 class="form-title">{title}</h1>
            {form_html}
        </div>
        {js_link}
    </body>
    </html>
    """
    return html


@app.route("/", methods=["GET"])
def index():
    """Main index page with links to different form examples."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Pydantic Forms - Flask Integration Demo</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
      <div class="container my-5">
        <h1 class="text-center mb-4">Pydantic Forms - Flask Integration</h1>
        <div class="row justify-content-center">
          <div class="col-md-8">
            <p class="text-center mb-4">
              These forms are automatically generated from Pydantic models. 
              The Flask app only defines the models - the library handles all the rendering!
            </p>
            <div class="row">
              <div class="col-md-4 mb-3">
                <div class="card h-100">
                  <div class="card-body">
                    <h5 class="card-title">User Registration</h5>
                    <p class="card-text">Bootstrap-styled form for user registration with validation.</p>
                    <a href="/user-registration" class="btn btn-primary">View Form</a>
                  </div>
                </div>
              </div>
              <div class="col-md-4 mb-3">
                <div class="card h-100">
                  <div class="card-body">
                    <h5 class="card-title">Contact Form</h5>
                    <p class="card-text">Material Design contact form with optional fields.</p>
                    <a href="/contact" class="btn btn-primary">View Form</a>
                  </div>
                </div>
              </div>
              <div class="col-md-4 mb-3">
                <div class="card h-100">
                  <div class="card-body">
                    <h5 class="card-title">Event Creation</h5>
                    <p class="card-text">Plain HTML form for creating events.</p>
                    <a href="/event" class="btn btn-primary">View Form</a>
                  </div>
                </div>
              </div>
            </div>
            <div class="text-center mt-4">
              <a href="https://github.com/devsetgo/pydantic-forms" class="btn btn-outline-secondary">View on GitHub</a>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return make_response(html)


if __name__ == "__main__":
    print("Starting Flask app with Pydantic Forms integration...")
    print("Visit http://localhost:5001 to see the demo")
    app.run(debug=True, port=5001)
