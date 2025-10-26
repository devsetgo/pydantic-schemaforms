#!/usr/bin/env python3
"""
FastAPI Pydantic Forms Demo
===========================

An async FastAPI demonstration of pydantic-forms library featuring:
- Minimal, medium, and complex (kitchen sink) forms
- Bootstrap 5 and Material Design 3 themes
- Multiple layouts: vertical (default), horizontal, side-by-side, and tabbed
- Complete form validation and error handling
- Async form rendering for high performance
- Modern Python 3.14+ template strings

Run with:
    uvicorn fastapi_demo:app --reload

Then visit:
    - http://localhost:8000/ (main demo page)
    - http://localhost:8000/bootstrap/minimal (simple login form)
    - http://localhost:8000/bootstrap/medium (contact form)
    - http://localhost:8000/bootstrap/complex (kitchen sink)
    - http://localhost:8000/material/minimal (Material Design login)
    - http://localhost:8000/material/medium (Material Design contact)
    - http://localhost:8000/material/complex (Material Design kitchen sink)
    - http://localhost:8000/layouts (layout demonstrations)
    - http://localhost:8000/material/layouts (Material Design layouts)
"""

import os
import sys
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT

# Add the parent directory to the path to import our library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel, Field, EmailStr, field_validator
from pydantic_forms.schema_form import FormModel
from pydantic_forms.form_field import FormField
from pydantic_forms.form_layouts import VerticalLayout, HorizontalLayout, TabbedLayout
from pydantic_forms.enhanced_renderer import render_form_html_async
from pydantic_forms.material_renderer import render_material_form_html_async
from pydantic_forms.validation import validate_form_data

# FastAPI app setup
app = FastAPI(
    title="FastAPI Pydantic Forms Demo",
    description="Async demonstration of pydantic-forms with FastAPI",
    version="1.0.0"
)

# Template setup
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=template_dir)

# ============================================================================
# ENUMS AND CONSTANTS (Same as Flask demo)
# ============================================================================

class Priority(str, Enum):
    """Priority levels for forms."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class Country(str, Enum):
    """Countries for selection."""
    US = "United States"
    CA = "Canada"
    UK = "United Kingdom"
    AU = "Australia"
    DE = "Germany"
    FR = "France"
    JP = "Japan"

# ============================================================================
# PYDANTIC FORM MODELS (Same as Flask demo)
# ============================================================================

class MinimalLoginForm(FormModel):
    """Minimal form example - Simple login form."""
    
    username: str = FormField(
        title="Username",
        input_type="text",
        placeholder="Enter your username",
        help_text="Your username or email address",
        icon="bi bi-person",
        min_length=3,
        max_length=50
    )
    
    password: str = FormField(
        title="Password", 
        input_type="password",
        placeholder="Enter your password",
        help_text="Your account password",
        icon="bi bi-lock",
        min_length=6
    )
    
    remember_me: bool = FormField(
        False,
        title="Remember me",
        input_type="checkbox",
        help_text="Keep me logged in on this device",
        icon="bi bi-check2-square"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()

class MediumContactForm(FormModel):
    """Medium complexity form - Contact form with validation."""
    
    # Personal Information
    first_name: str = FormField(
        title="First Name",
        input_type="text",
        placeholder="Enter your first name",
        help_text="Your given name",
        icon="bi bi-person",
        min_length=2,
        max_length=50
    )
    
    last_name: str = FormField(
        title="Last Name",
        input_type="text", 
        placeholder="Enter your last name",
        help_text="Your family name",
        icon="bi bi-person",
        min_length=2,
        max_length=50
    )
    
    email: EmailStr = FormField(
        title="Email Address",
        input_type="email",
        placeholder="your.email@example.com",
        help_text="We'll never share your email",
        icon="bi bi-envelope"
    )
    
    phone: Optional[str] = FormField(
        None,
        title="Phone Number",
        input_type="tel",
        placeholder="+1 (555) 123-4567",
        help_text="Optional phone number",
        icon="bi bi-telephone"
    )
    
    # Message Details
    subject: str = FormField(
        title="Subject",
        input_type="text",
        placeholder="Brief subject line",
        help_text="What is this message about?",
        icon="bi bi-chat-left-text",
        min_length=5,
        max_length=200
    )
    
    message: str = FormField(
        title="Message",
        input_type="textarea",
        placeholder="Enter your detailed message here...",
        help_text="Please provide details about your inquiry",
        icon="bi bi-chat-left-dots",
        min_length=10,
        max_length=2000
    )
    
    priority: Priority = FormField(
        Priority.MEDIUM,
        title="Priority Level",
        input_type="select",
        options=[
            {"value": p.value, "label": p.value.title()} for p in Priority
        ],
        help_text="How urgent is your request?",
        icon="bi bi-exclamation-triangle"
    )
    
    # Preferences
    subscribe_newsletter: bool = FormField(
        False,
        title="Subscribe to Newsletter",
        input_type="checkbox",
        help_text="Receive updates and news",
        icon="bi bi-newspaper"
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise ValueError("Phone number must be at least 10 digits")
        return v

class ComplexKitchenSinkForm(FormModel):
    """Complex form example - Kitchen sink with all input types."""
    
    # === TEXT INPUTS ===
    text_field: str = FormField(
        title="Text Input",
        input_type="text",
        placeholder="Enter any text",
        help_text="Basic text input field",
        icon="bi bi-input-cursor-text",
        min_length=1,
        max_length=100
    )
    
    email_field: EmailStr = FormField(
        title="Email Field",
        input_type="email", 
        placeholder="user@example.com",
        help_text="Must be a valid email address",
        icon="bi bi-at"
    )
    
    password_field: str = FormField(
        title="Password Field",
        input_type="password",
        placeholder="Enter secure password",
        help_text="At least 8 characters with mixed case",
        icon="bi bi-shield-lock",
        min_length=8
    )
    
    # === NUMERIC INPUTS ===
    number_field: int = FormField(
        title="Number Input",
        input_type="number",
        placeholder="42",
        help_text="Integer number input",
        icon="bi bi-123",
        min_value=0,
        max_value=1000
    )
    
    # === SELECTION INPUTS ===
    select_field: str = FormField(
        title="Select Dropdown",
        input_type="select",
        options=["Option 1", "Option 2", "Option 3", "Option 4"],
        help_text="Choose one option from dropdown",
        icon="bi bi-list"
    )
    
    country_field: Country = FormField(
        Country.US,
        title="Country Selection",
        input_type="select",
        options=[c.value for c in Country],
        help_text="Select your country",
        icon="bi bi-globe"
    )
    
    # === BOOLEAN INPUTS ===
    checkbox_field: bool = FormField(
        False,
        title="Checkbox Input",
        input_type="checkbox",
        help_text="Check this box to agree",
        icon="bi bi-check-square"
    )
    
    # === DATE/TIME INPUTS ===
    date_field: date = FormField(
        title="Date Input",
        input_type="date",
        help_text="Select a date",
        icon="bi bi-calendar-date"
    )

    @field_validator("password_field")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def handle_form_submission_async(form_class, form_data, success_message="Form submitted successfully!"):
    """Async handle form submission with validation and error handling."""
    try:
        # Validate the form data using Pydantic
        result = validate_form_data(form_class, form_data)
        
        if result.is_valid:
            # Return success response
            return {
                'success': True,
                'message': success_message,
                'data': result.data
            }
        else:
            # Return validation errors
            return {
                'success': False,
                'errors': result.errors
            }
    except Exception as e:
        # Return unexpected errors
        return {
            'success': False,
            'errors': {'form': str(e)}
        }

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    """Main demo page with overview."""
    return templates.TemplateResponse("home.html", {"request": request, "title": "Home"})

# ============================================================================
# BOOTSTRAP ROUTES
# ============================================================================

@app.get("/bootstrap/minimal", response_class=HTMLResponse, name="bootstrap_minimal")
async def bootstrap_minimal_get(request: Request):
    """Bootstrap minimal form example - GET."""
    form_html = await render_form_html_async(MinimalLoginForm, framework="bootstrap")
    return templates.TemplateResponse("bootstrap_minimal.html", {
        "request": request,
        "title": "Bootstrap Minimal Form",
        "success": False,
        "form_html": form_html
    })

@app.post("/bootstrap/minimal", response_class=HTMLResponse, name="bootstrap_minimal_post")
async def bootstrap_minimal_post(request: Request):
    """Bootstrap minimal form example - POST."""
    form_data = await request.form()
    result = await handle_form_submission_async(MinimalLoginForm, dict(form_data))
    
    if result['success']:
        return templates.TemplateResponse("bootstrap_minimal.html", {
            "request": request,
            "title": "Bootstrap Minimal Form",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = await render_form_html_async(MinimalLoginForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("bootstrap_minimal.html", {
            "request": request,
            "title": "Bootstrap Minimal Form",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/bootstrap/medium", response_class=HTMLResponse, name="bootstrap_medium")
async def bootstrap_medium_get(request: Request):
    """Bootstrap medium complexity form example - GET."""
    form_html = await render_form_html_async(MediumContactForm, framework="bootstrap")
    return templates.TemplateResponse("bootstrap_medium.html", {
        "request": request,
        "title": "Bootstrap Medium Form",
        "success": False,
        "form_html": form_html
    })

@app.post("/bootstrap/medium", response_class=HTMLResponse, name="bootstrap_medium_post")
async def bootstrap_medium_post(request: Request):
    """Bootstrap medium complexity form example - POST."""
    form_data = await request.form()
    result = await handle_form_submission_async(MediumContactForm, dict(form_data))
    
    if result['success']:
        return templates.TemplateResponse("bootstrap_medium.html", {
            "request": request,
            "title": "Bootstrap Medium Form",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = await render_form_html_async(MediumContactForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("bootstrap_medium.html", {
            "request": request,
            "title": "Bootstrap Medium Form",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/bootstrap/complex", response_class=HTMLResponse, name="bootstrap_complex")
async def bootstrap_complex_get(request: Request):
    """Bootstrap complex form example - GET."""
    form_html = await render_form_html_async(ComplexKitchenSinkForm, framework="bootstrap")
    return templates.TemplateResponse("bootstrap_complex.html", {
        "request": request,
        "title": "Bootstrap Complex Form",
        "success": False,
        "form_html": form_html
    })

@app.post("/bootstrap/complex", response_class=HTMLResponse, name="bootstrap_complex_post")
async def bootstrap_complex_post(request: Request):
    """Bootstrap complex form example - POST."""
    form_data = await request.form()
    result = await handle_form_submission_async(ComplexKitchenSinkForm, dict(form_data))
    
    if result['success']:
        return templates.TemplateResponse("bootstrap_complex.html", {
            "request": request,
            "title": "Bootstrap Complex Form",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = await render_form_html_async(ComplexKitchenSinkForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("bootstrap_complex.html", {
            "request": request,
            "title": "Bootstrap Complex Form",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

# ============================================================================
# MATERIAL DESIGN ROUTES
# ============================================================================

@app.get("/material/minimal", response_class=HTMLResponse, name="material_minimal")
async def material_minimal_get(request: Request):
    """Material Design minimal form example - GET."""
    form_html = await render_material_form_html_async(MinimalLoginForm)
    return templates.TemplateResponse("material_minimal.html", {
        "request": request,
        "title": "Material Design Minimal Form",
        "theme": "material",
        "success": False,
        "form_html": form_html
    })

@app.post("/material/minimal", response_class=HTMLResponse, name="material_minimal_post")
async def material_minimal_post(request: Request):
    """Material Design minimal form example - POST."""
    form_data = await request.form()
    result = await handle_form_submission_async(MinimalLoginForm, dict(form_data))
    
    if result['success']:
        return templates.TemplateResponse("material_minimal.html", {
            "request": request,
            "title": "Material Design Minimal Form",
            "theme": "material",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = await render_material_form_html_async(MinimalLoginForm, errors=result['errors'])
        return templates.TemplateResponse("material_minimal.html", {
            "request": request,
            "title": "Material Design Minimal Form",
            "theme": "material",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/material/medium", response_class=HTMLResponse, name="material_medium")
async def material_medium_get(request: Request):
    """Material Design medium complexity form example - GET."""
    form_html = await render_material_form_html_async(MediumContactForm)
    return templates.TemplateResponse("material_medium.html", {
        "request": request,
        "title": "Material Design Medium Form",
        "theme": "material",
        "success": False,
        "form_html": form_html
    })

@app.post("/material/medium", response_class=HTMLResponse, name="material_medium_post")
async def material_medium_post(request: Request):
    """Material Design medium complexity form example - POST."""
    form_data = await request.form()
    result = await handle_form_submission_async(MediumContactForm, dict(form_data))
    
    if result['success']:
        return templates.TemplateResponse("material_medium.html", {
            "request": request,
            "title": "Material Design Medium Form",
            "theme": "material",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = await render_material_form_html_async(MediumContactForm, errors=result['errors'])
        return templates.TemplateResponse("material_medium.html", {
            "request": request,
            "title": "Material Design Medium Form",
            "theme": "material",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/material/complex", response_class=HTMLResponse, name="material_complex")
async def material_complex_get(request: Request):
    """Material Design complex form example - GET."""
    form_html = await render_material_form_html_async(ComplexKitchenSinkForm)
    return templates.TemplateResponse("material_complex.html", {
        "request": request,
        "title": "Material Design Complex Form",
        "theme": "material",
        "success": False,
        "form_html": form_html
    })

@app.post("/material/complex", response_class=HTMLResponse, name="material_complex_post")
async def material_complex_post(request: Request):
    """Material Design complex form example - POST."""
    form_data = await request.form()
    result = await handle_form_submission_async(ComplexKitchenSinkForm, dict(form_data))
    
    if result['success']:
        return templates.TemplateResponse("material_complex.html", {
            "request": request,
            "title": "Material Design Complex Form",
            "theme": "material",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = await render_material_form_html_async(ComplexKitchenSinkForm, errors=result['errors'])
        return templates.TemplateResponse("material_complex.html", {
            "request": request,
            "title": "Material Design Complex Form",
            "theme": "material",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

# ============================================================================
# LAYOUT DEMONSTRATION ROUTES
# ============================================================================

@app.get("/layouts", response_class=HTMLResponse, name="layouts_demo")
async def layouts_demo(request: Request):
    """Demonstrate different layout systems using pydantic-forms library."""
    
    # Render all layouts concurrently using async
    import asyncio
    
    vertical_task = render_form_html_async(MinimalLoginForm, framework="bootstrap", layout="vertical")
    horizontal_task = render_form_html_async(MinimalLoginForm, framework="bootstrap", layout="horizontal")
    side_by_side_task = render_form_html_async(MediumContactForm, framework="bootstrap", layout="side-by-side")
    tabbed_task = render_form_html_async(MediumContactForm, framework="bootstrap", layout="tabbed")
    
    # Wait for all renders to complete concurrently
    vertical_form_html, horizontal_form_html, side_by_side_form_html, tabbed_form_html = await asyncio.gather(
        vertical_task, horizontal_task, side_by_side_task, tabbed_task
    )
    
    return templates.TemplateResponse("layouts.html", {
        "request": request,
        "title": "Layout Demonstrations",
        "vertical_form_html": vertical_form_html,
        "horizontal_form_html": horizontal_form_html,
        "side_by_side_form_html": side_by_side_form_html,
        "tabbed_form_html": tabbed_form_html
    })

@app.get("/material/layouts", response_class=HTMLResponse, name="material_layouts_demo")
async def material_layouts_demo(request: Request):
    """Demonstrate different layout systems using Material Design renderer."""
    
    # Render all Material Design layouts concurrently
    import asyncio
    
    vertical_task = render_material_form_html_async(MinimalLoginForm, layout="vertical")
    horizontal_task = render_material_form_html_async(MinimalLoginForm, layout="horizontal")
    side_by_side_task = render_material_form_html_async(MediumContactForm, layout="side-by-side")
    tabbed_task = render_material_form_html_async(MediumContactForm, layout="tabbed")
    
    # Wait for all renders to complete concurrently
    vertical_form_html, horizontal_form_html, side_by_side_form_html, tabbed_form_html = await asyncio.gather(
        vertical_task, horizontal_task, side_by_side_task, tabbed_task
    )
    
    return templates.TemplateResponse("material_layouts.html", {
        "request": request,
        "title": "Material Design Layout Demonstrations",
        "theme": "material",
        "vertical_form_html": vertical_form_html,
        "horizontal_form_html": horizontal_form_html,
        "side_by_side_form_html": side_by_side_form_html,
        "tabbed_form_html": tabbed_form_html
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def page_not_found(request: Request, exc):
    """Handle 404 errors."""
    return templates.TemplateResponse("404.html", {"request": request, "title": "Page Not Found"}, status_code=404)

@app.exception_handler(500)
async def internal_server_error(request: Request, exc):
    """Handle 500 errors."""
    return templates.TemplateResponse("500.html", {"request": request, "title": "Server Error"}, status_code=500)

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('FASTAPI_PORT', 5000))
    
    print("🚀 Starting FastAPI Pydantic Forms Demo...")
    print(f"📄 Home page: http://localhost:{port}/")
    print(f"🎨 Bootstrap examples: http://localhost:{port}/bootstrap/")
    print(f"🎨 Material examples: http://localhost:{port}/material/")
    print(f"📐 Layout examples: http://localhost:{port}/layouts")
    print("⚡ Features: Async rendering, Python 3.14+ templates, multiple themes, all layouts")
    print("")
    print("💡 For development with auto-reload, use:")
    print("   uvicorn fastapi_demo:app --reload")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)