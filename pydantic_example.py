from flask import Flask, make_response
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from pydantic_forms import FormRenderer

app = Flask(__name__)

# Define your Pydantic models - this is all you need to do!
class UserRegistrationForm(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="Choose a unique username")
    email: str = Field(..., description="Your email address")
    password: str = Field(..., min_length=8, description="Choose a secure password")
    age: int = Field(..., ge=13, le=120, description="Your age")
    newsletter: bool = Field(False, description="Subscribe to our newsletter")
    birthday: Optional[date] = Field(None, description="Your birth date")

class ContactForm(BaseModel):
    name: str = Field(..., min_length=2, description="Your full name")
    email: str = Field(..., description="Your email address")
    phone: Optional[str] = Field(None, description="Your phone number")
    website: Optional[str] = Field(None, description="Your website URL")
    message: str = Field(..., min_length=10, max_length=1000, description="Your message")

class EventForm(BaseModel):
    event_name: str = Field(..., description="Name of the event")
    event_datetime: datetime = Field(..., description="When the event starts")
    max_attendees: int = Field(..., ge=1, le=1000, description="Maximum number of attendees")
    is_public: bool = Field(True, description="Make this event publicly visible")
    event_color: str = Field("#3498db", description="Theme color for the event")

# Initialize the form renderer
renderer = FormRenderer()

@app.route("/user-registration", methods=["GET"])
def user_registration():
    """User registration form from Pydantic model."""
    html = renderer.render_form_from_pydantic(
        UserRegistrationForm, 
        framework="bootstrap",
        title="User Registration",
        submit_url="/register"
    )
    return make_response(html)

@app.route("/contact", methods=["GET"])
def contact():
    """Contact form from Pydantic model using Material Design."""
    html = renderer.render_form_from_pydantic(
        ContactForm, 
        framework="material",
        title="Contact Us",
        submit_url="/contact"
    )
    return make_response(html)

@app.route("/event", methods=["GET"])
def event():
    """Event form from Pydantic model using shadcn/ui."""
    html = renderer.render_form_from_pydantic(
        EventForm, 
        framework="shadcn",
        title="Create Event",
        submit_url="/create-event"
    )
    return make_response(html)

@app.route("/", methods=["GET"])
def index():
    """Main index page with links to different Pydantic form examples."""
    html = """
    <html>
    <head>
        <title>Pydantic Forms - Model-Based Examples</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
      <div class="container my-5">
        <h1 class="text-center mb-4">Pydantic Forms - Model-Based Demo</h1>
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
                    <p class="card-text">Modern shadcn/ui form for creating events.</p>
                    <a href="/event" class="btn btn-primary">View Form</a>
                  </div>
                </div>
              </div>
            </div>
            <div class="text-center mt-4">
              <a href="../simple_example.py" class="btn btn-outline-secondary">View Manual Form Examples</a>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return make_response(html)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
