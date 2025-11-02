#!/usr/bin/env python3
"""
FastAPI Example using Pydantic Forms with ListLayout

A clean FastAPI demonstration focusing on the core functionality:
- Pet registration form with dynamic ListLayout
- Bootstrap and Material Design themes
- Form validation and error handling
- Modern async/await support
- Proper use of pydantic-forms library for HTML generation

Install dependencies:
    pip install fastapi uvicorn python-multipart jinja2

Run with:
    python fastapi_example.py

Then visit:
    - http://localhost:8000/ (main page)
    - http://localhost:8000/bootstrap/login (Bootstrap login demo)
    - http://localhost:8000/bootstrap/pets (Bootstrap pets demo)
    - http://localhost:8000/material/pets (Material Design pets demo)
    - http://localhost:8000/docs (Auto-generated API docs)
"""

import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import shared models
from shared_models import (
    PetModel, PetOwnerForm, MinimalLoginForm, UserRegistrationForm, PetRegistrationForm,
    CompleteShowcaseForm, EmergencyContactModel, handle_form_submission
)

# Import pydantic-forms components
from pydantic_forms.form_layouts import ListLayout, SectionDesign
from pydantic_forms.enhanced_renderer import render_form_html, EnhancedFormRenderer
# from pydantic_forms.material_renderer import MaterialDesign3Renderer  # Temporarily disabled due to syntax issues
from pydantic_forms.simple_material_renderer import SimpleMaterialRenderer

# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="FastAPI Pydantic Forms Demo",
    description="Demonstration of pydantic-forms with ListLayout in FastAPI",
    version="1.0.0"
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main demo page."""
    return templates.TemplateResponse("home.html", {
        "request": request,
        "title": "FastAPI Pydantic Forms Demo",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "bootstrap",
        "renderer_info": "Enhanced Bootstrap Renderer"
    })

@app.get("/user", response_class=HTMLResponse)
async def user_get(request: Request, style: str = "bootstrap"):
    """Show user registration form."""
    # Use the same UserRegistrationForm for both frameworks
    # The icon mapping system will automatically convert icons to the appropriate framework
    form_html = render_form_html(UserRegistrationForm, framework=style)
    framework_type = "material" if style == "material" else "bootstrap"
    return templates.TemplateResponse("user.html", {
        "request": request,
        "title": "User Registration",
        "framework": "fastapi",
        "framework_name": "FastAPI", 
        "framework_type": framework_type,
        "theme": framework_type,  # Add this for the template theme check
        "success": False,
        "form_html": form_html
    })

@app.post("/user", response_class=HTMLResponse)
async def user_post(request: Request):
    """Handle user registration form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(UserRegistrationForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("user.html", {
            "request": request,
            "title": "Registration Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": True,
            "user_data": result['data']
        })
    else:
        form_html = render_form_html(UserRegistrationForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("user.html", {
            "request": request,
            "title": "User Registration",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/pets", response_class=HTMLResponse)
async def pets_get(request: Request, style: str = "bootstrap"):
    """Show pet registration form with unified form."""
    form_html = render_form_html(PetRegistrationForm, framework=style)
    framework_type = "material" if style == "material" else "bootstrap"
    return templates.TemplateResponse("pets.html", {
        "request": request,
        "title": "Pet Registration Form",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": framework_type,
        "success": False,
        "form_html": form_html
    })

@app.post("/pets", response_class=HTMLResponse)
async def pets_post(request: Request, style: str = "bootstrap"):
    """Handle pet registration form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(PetRegistrationForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("pets.html", {
            "request": request,
            "title": "Pet Registration Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": style if style == "material" else "bootstrap",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(PetRegistrationForm, framework=style, errors=result['errors'])
        return templates.TemplateResponse("pets.html", {
            "request": request,
            "title": "Pet Registration Form",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": style if style == "material" else "bootstrap",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/showcase", response_class=HTMLResponse)
async def showcase_get(request: Request, style: str = "bootstrap"):
    """Show complete showcase form with all pydantic-forms capabilities."""
    form_html = render_form_html(CompleteShowcaseForm, framework=style)
    framework_type = "material" if style == "material" else "bootstrap"
    return templates.TemplateResponse("showcase.html", {
        "request": request,
        "title": "Complete Features Showcase",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": framework_type,
        "success": False,
        "form_html": form_html
    })

@app.post("/showcase", response_class=HTMLResponse)
async def showcase_post(request: Request, style: str = "bootstrap"):
    """Handle complete showcase form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(CompleteShowcaseForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("showcase.html", {
            "request": request,
            "title": "Showcase Form Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": style if style == "material" else "bootstrap",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(CompleteShowcaseForm, framework=style, errors=result['errors'])
        return templates.TemplateResponse("showcase.html", {
            "request": request,
            "title": "Complete Features Showcase",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": style if style == "material" else "bootstrap",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/dynamic", response_class=HTMLResponse)
async def dynamic_get(request: Request, style: str = "bootstrap"):
    """Show dynamic form demo."""
    # Use the contact form for dynamic demo
    from shared_models import MediumContactForm
    form_html = render_form_html(MediumContactForm, framework=style)
    framework_type = "material" if style == "material" else "bootstrap"
    return templates.TemplateResponse("dynamic.html", {
        "request": request,
        "title": "Dynamic Form Demo",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": framework_type,
        "success": False,
        "form_html": form_html
    })

@app.post("/dynamic", response_class=HTMLResponse)
async def dynamic_post(request: Request):
    """Handle dynamic form submission."""
    form_data = await request.form()
    return templates.TemplateResponse("dynamic.html", {
        "request": request,
        "title": "Dynamic Form Success",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "bootstrap",
        "success": True,
        "form_data": dict(form_data)
    })

@app.get("/bootstrap/login", response_class=HTMLResponse)
async def bootstrap_login_get(request: Request):
    """Show login form with Bootstrap styling."""
    form_html = render_form_html(MinimalLoginForm, framework="bootstrap")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Login Form",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "bootstrap",
        "success": False,
        "form_html": form_html
    })

@app.post("/bootstrap/login", response_class=HTMLResponse)
async def bootstrap_login_post(request: Request):
    """Handle login form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(MinimalLoginForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Login Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(MinimalLoginForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Login Form",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/bootstrap/pets", response_class=HTMLResponse)
async def bootstrap_pets_get(request: Request):
    """Show Bootstrap pet registration form with unified form."""
    form_html = render_form_html(PetRegistrationForm, framework="bootstrap")
    return templates.TemplateResponse("pets.html", {
        "request": request,
        "title": "Pet Registration Form",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "bootstrap",
        "success": False,
        "form_html": form_html
    })

@app.post("/bootstrap/pets", response_class=HTMLResponse)
async def bootstrap_pets_post(request: Request):
    """Handle Bootstrap pet registration form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(PetRegistrationForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("pets.html", {
            "request": request,
            "title": "Pet Registration Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(PetRegistrationForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("pets.html", {
            "request": request,
            "title": "Pet Registration Form",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/material/pets", response_class=HTMLResponse)
async def material_pets_get(request: Request):
    """Show Material Design pet registration form with unified form."""
    # Use render_form_html with material framework to handle model_list properly
    form_html = render_form_html(PetRegistrationForm, framework="material")
    return templates.TemplateResponse("pets.html", {
        "request": request,
        "title": "Pet Registration Form",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "material",
        "theme": "material",  # Use material theme
        "success": False,
        "form_html": form_html
    })

@app.post("/material/pets", response_class=HTMLResponse)
async def material_pets_post(request: Request):
    """Handle Material Design pet registration form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(PetRegistrationForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("pets.html", {
            "request": request,
            "title": "Pet Registration Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "material",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(PetRegistrationForm, framework="material", errors=result['errors'])
        return templates.TemplateResponse("pets.html", {
            "request": request,
            "title": "Pet Registration Form",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "material",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/bootstrap/showcase", response_class=HTMLResponse)
async def bootstrap_showcase_get(request: Request):
    """Show Bootstrap complete showcase form."""
    form_html = render_form_html(CompleteShowcaseForm, framework="bootstrap")
    return templates.TemplateResponse("showcase.html", {
        "request": request,
        "title": "Bootstrap Features Showcase",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "bootstrap",
        "success": False,
        "form_html": form_html
    })

@app.post("/bootstrap/showcase", response_class=HTMLResponse)
async def bootstrap_showcase_post(request: Request):
    """Handle Bootstrap showcase form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(CompleteShowcaseForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("showcase.html", {
            "request": request,
            "title": "Bootstrap Showcase Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(CompleteShowcaseForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("showcase.html", {
            "request": request,
            "title": "Bootstrap Features Showcase",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "bootstrap",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/material/showcase", response_class=HTMLResponse)
async def material_showcase_get(request: Request):
    """Show Material Design complete showcase form."""
    # Use the new working Material Design renderer
    material_renderer = SimpleMaterialRenderer()
    form_html = material_renderer.render_form_from_model(CompleteShowcaseForm)
    return templates.TemplateResponse("showcase.html", {
        "request": request,
        "title": "Material Design Features Showcase",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "material",
        "theme": "material",  # Use material theme
        "success": False,
        "form_html": form_html
    })

@app.post("/material/showcase", response_class=HTMLResponse)
async def material_showcase_post(request: Request):
    """Handle Material Design showcase form submission."""
    form_data = await request.form()
    form_dict = dict(form_data)
    
    result = handle_form_submission(CompleteShowcaseForm, form_dict)
    
    if result['success']:
        return templates.TemplateResponse("showcase.html", {
            "request": request,
            "title": "Material Design Showcase Success",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "material",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(CompleteShowcaseForm, framework="material", errors=result['errors'])
        return templates.TemplateResponse("showcase.html", {
            "request": request,
            "title": "Material Design Features Showcase",
            "framework": "fastapi",
            "framework_name": "FastAPI",
            "framework_type": "material",
            "theme": "material",  # Add theme for template
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "fastapi-pydantic-forms"}

@app.get("/api/models/pet")
async def get_pet_model_schema():
    """Get Pet model JSON schema."""
    return PetModel.model_json_schema()

@app.get("/api/models/owner")
async def get_owner_model_schema():
    """Get Pet Owner model JSON schema."""
    return PetOwnerForm.model_json_schema()

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors."""
    return templates.TemplateResponse("404.html", {
        "request": request,
        "title": "Page Not Found",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "bootstrap",
        "error_code": 404,
        "error_message": "The page you're looking for doesn't exist."
    }, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors."""
    return templates.TemplateResponse("500.html", {
        "request": request,
        "title": "Server Error",
        "framework": "fastapi",
        "framework_name": "FastAPI",
        "framework_type": "bootstrap",
        "error_code": 500,
        "error_message": "An internal server error occurred."
    }, status_code=500)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('FASTAPI_PORT', 8000))
    
    print("🚀 Starting FastAPI Pydantic Forms Example...")
    print(f"📄 Home page: http://localhost:{port}/")
    print(f"� User registration: http://localhost:{port}/user")
    print(f"🐾 Pet registration: http://localhost:{port}/pets")
    print(f"🎨 Complete showcase: http://localhost:{port}/showcase")
    print(f"�🔐 Login form: http://localhost:{port}/bootstrap/login")
    print(f"🐾 Bootstrap pets: http://localhost:{port}/bootstrap/pets")
    print(f"🎨 Bootstrap showcase: http://localhost:{port}/bootstrap/showcase")
    print(f"🐾 Material pets: http://localhost:{port}/material/pets")
    print(f"🎨 Material showcase: http://localhost:{port}/material/showcase")
    print(f"📚 API docs: http://localhost:{port}/docs")
    print(f"🔍 Interactive docs: http://localhost:{port}/redoc")
    print(f"🧪 Self-contained test: http://localhost:{port}/test-self-contained")
    print("⚡ Features: Collapsible Cards, Dynamic Titles, All Input Types, Bootstrap/Material Design, Async support")

@app.get("/test-icons", response_class=HTMLResponse)
async def test_icons_get(request: Request):
    """Test Material Design icons in forms."""
    # Use existing UserRegistrationForm to test Material Design icons
    # This demonstrates the simplicity: just use shared models + render_form_html
    form_html = render_form_html(UserRegistrationForm, framework="material")
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Material Design Icons Test</title>
    </head>
    <body>
        <div style="max-width: 600px; margin: 40px auto; padding: 20px;">
            <h1 style="text-align: center; color: #6750a4; font-family: Roboto, sans-serif;">
                🎨 Material Design Icons Test
            </h1>
            <p style="text-align: center; color: #49454f; font-family: Roboto, sans-serif;">
                This form demonstrates Material Design 3 fields with Material Icons on the left<br>
                <strong>Simple approach: UserRegistrationForm + render_form_html(framework="material")</strong>
            </p>
            {form_html}
            <br><br>
            <div style="text-align: center;">
                <a href="/material/showcase" style="color: #6750a4; text-decoration: none;">← Back to Material Showcase</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/test-self-contained", response_class=HTMLResponse)
async def test_self_contained_get(request: Request):
    """Test self-contained form rendering."""
    # Use the new working Material Design renderer for self-contained test
    material_renderer = SimpleMaterialRenderer()
    my_form = material_renderer.render_form_from_model(UserRegistrationForm)
    
    # Return minimal HTML with just the form
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FastAPI Self-Contained Material Design Test</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 50px auto; padding: 20px; }}
        .form-showcase {{ border: 2px solid #e7e0ec; border-radius: 16px; padding: 20px; background: #fef7ff; }}
        .info-box {{ background: #f3f0ff; padding: 20px; border-radius: 12px; font-family: monospace; margin-top: 30px; }}
        pre {{ background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #e7e0ec; margin: 10px 0; }}
        .nav-link {{ color: #6750a4; text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 FastAPI Material Design Self-Contained Test</h1>
        <p><strong>This demonstrates complete Material Design 3 autonomy.</strong></p>
        <p>The form below includes ALL Material Design dependencies internally:</p>
        
        <!-- All Form Required Content -->
        <div class="form-showcase">
            {my_form}
        </div>
        
        <hr style="margin: 40px 0;">
        
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
                <li>Self-contained and fully functional</li>
            </ul>
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <a href="/" class="nav-link">← Back to FastAPI Home</a>
        </div>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_example:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )