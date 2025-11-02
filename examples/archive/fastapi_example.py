#!/usr/bin/env python3
"""
FastAPI Example using Pydantic Forms with ListLayout

A clean FastAPI demonstration focusing on the core functionality:
- Pet registration form with dynamic ListLayout
- Bootstrap and Material Design themes
- Form validation and error handling
- Modern async/await support

Install dependencies:
    pip install fastapi uvicorn python-multipart jinja2

Run with:
    python fastapi_example.py

Then visit:
    - http://localhost:8000/ (main page)
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
    PetModel, PetOwnerForm, MinimalLoginForm, 
    handle_form_submission
)

# Import pydantic-forms components
from pydantic_forms.form_layouts import ListLayout, SectionDesign
from pydantic_forms.enhanced_renderer import render_form_html, EnhancedFormRenderer
from pydantic_forms.material_renderer import MaterialDesign3Renderer

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
    return templates.TemplateResponse("fastapi_home.html", {
        "request": request,
        "title": "FastAPI Pydantic Forms Demo"
    })

@app.get("/bootstrap/login", response_class=HTMLResponse)
async def bootstrap_login_get(request: Request):
    """Show login form with Bootstrap styling."""
    form_html = render_form_html(MinimalLoginForm, framework="bootstrap")
    return templates.TemplateResponse("fastapi_login.html", {
        "request": request,
        "title": "Login Form",
        "success": False,
        "form_html": form_html
    })

@app.post("/bootstrap/login", response_class=HTMLResponse)
async def bootstrap_login_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission."""
    form_data = {
        'username': username,
        'email': email,
        'password': password
    }
    
    result = handle_form_submission(MinimalLoginForm, form_data)
    
    if result['success']:
        return templates.TemplateResponse("fastapi_login.html", {
            "request": request,
            "title": "Login Success",
            "success": True,
            "form_data": result['data']
        })
    else:
        form_html = render_form_html(MinimalLoginForm, framework="bootstrap", errors=result['errors'])
        return templates.TemplateResponse("fastapi_login.html", {
            "request": request,
            "title": "Login Form",
            "success": False,
            "form_html": form_html,
            "errors": result['errors']
        })

@app.get("/bootstrap/pets", response_class=HTMLResponse)
async def bootstrap_pets_get(request: Request):
    """Show Bootstrap pet registration form with ListLayout."""
    return await render_pets_form(request, "bootstrap")

@app.post("/bootstrap/pets", response_class=HTMLResponse)
async def bootstrap_pets_post(request: Request):
    """Handle Bootstrap pet registration form submission."""
    form_data = await request.form()
    return await handle_pets_submission(request, form_data, "bootstrap")

@app.get("/material/pets", response_class=HTMLResponse)
async def material_pets_get(request: Request):
    """Show Material Design pet registration form with ListLayout."""
    return await render_pets_form(request, "material")

@app.post("/material/pets", response_class=HTMLResponse)
async def material_pets_post(request: Request):
    """Handle Material Design pet registration form submission."""
    form_data = await request.form()
    return await handle_pets_submission(request, form_data, "material")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def render_pets_form(request: Request, framework: str):
    """Render the initial pet registration form."""
    # Choose renderer based on framework
    if framework == "material":
        renderer = MaterialDesign3Renderer()
    else:
        renderer = EnhancedFormRenderer()
    
    # Render owner form
    owner_form_html = renderer.render_form_from_model(
        PetOwnerForm.model_construct(), 
        framework=framework if framework != "material" else None,
        include_submit_button=False
    )
    
    # Create pet list layout
    pet_list_layout = ListLayout(
        form_model=PetModel,
        min_items=0,
        max_items=10,
        add_button_text="Add Another Pet",
        remove_button_text="Remove Pet",
        collapsible_items=True,
        items_expanded=True,
        section_design=SectionDesign(
            section_title="Your Pets",
            section_description="Add information about each of your pets (optional)",
            icon="pets",
            collapsible=False
        )
    )
    
    # Start with one empty pet form
    pets_html = pet_list_layout.render(
        data={'items': [{}]},
        framework=framework
    )
    
    return templates.TemplateResponse("fastapi_pets.html", {
        "request": request,
        "title": "Pet Registration Form",
        "framework": framework,
        "success": False,
        "owner_form_html": owner_form_html,
        "pets_html": pets_html
    })

async def handle_pets_submission(request: Request, form_data, framework: str):
    """Handle pet registration form submission."""
    # Convert form data to dict with lists
    form_dict = {}
    for key, value in form_data.items():
        if key in form_dict:
            if not isinstance(form_dict[key], list):
                form_dict[key] = [form_dict[key]]
            form_dict[key].append(value)
        else:
            form_dict[key] = [value] if key.startswith('item_') else value
    
    # Extract owner data
    owner_data = {
        'owner_name': form_dict.get('owner_name', ''),
        'email': form_dict.get('email', ''),
        'address': form_dict.get('address', ''),
        'emergency_contact': form_dict.get('emergency_contact', '')
    }
    
    # Extract pets data
    pets_data = []
    pet_index = 0
    while f'item_{pet_index}_name' in form_dict:
        pet_data = {
            'name': form_dict.get(f'item_{pet_index}_name', [''])[0] if isinstance(form_dict.get(f'item_{pet_index}_name'), list) else form_dict.get(f'item_{pet_index}_name', ''),
            'species': form_dict.get(f'item_{pet_index}_species', [''])[0] if isinstance(form_dict.get(f'item_{pet_index}_species'), list) else form_dict.get(f'item_{pet_index}_species', ''),
            'age': form_dict.get(f'item_{pet_index}_age', [None])[0] if isinstance(form_dict.get(f'item_{pet_index}_age'), list) else form_dict.get(f'item_{pet_index}_age'),
            'is_vaccinated': f'item_{pet_index}_is_vaccinated' in form_dict
        }
        if pet_data['name']:  # Only add pets with names
            pets_data.append(pet_data)
        pet_index += 1
    
    # Validate owner form
    result = handle_form_submission(PetOwnerForm, owner_data)
    
    if result['success']:
        return templates.TemplateResponse("fastapi_pets.html", {
            "request": request,
            "title": "Pet Registration Success",
            "framework": framework,
            "success": True,
            "owner_data": result['data'],
            "pets_data": pets_data
        })
    else:
        # Re-render form with errors
        if framework == "material":
            renderer = MaterialDesign3Renderer()
        else:
            renderer = EnhancedFormRenderer()
        
        owner_form_html = renderer.render_form_from_model(
            PetOwnerForm.model_construct(), 
            framework=framework if framework != "material" else None,
            include_submit_button=False, 
            errors=result.get('errors', {})
        )
        
        # Create pet list layout
        pet_list_layout = ListLayout(
            form_model=PetModel,
            min_items=0,
            max_items=10,
            add_button_text="Add Another Pet",
            remove_button_text="Remove Pet",
            collapsible_items=True,
            items_expanded=True,
            section_design=SectionDesign(
                section_title="Your Pets",
                section_description="Add information about each of your pets",
                icon="pets",
                collapsible=False
            )
        )
        
        pets_html = pet_list_layout.render(
            data={'items': pets_data},
            framework=framework
        )
        
        return templates.TemplateResponse("fastapi_pets.html", {
            "request": request,
            "title": "Pet Registration Form",
            "framework": framework,
            "success": False,
            "owner_form_html": owner_form_html,
            "pets_html": pets_html,
            "errors": result.get('errors', {})
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
    return templates.TemplateResponse("fastapi_error.html", {
        "request": request,
        "title": "Page Not Found",
        "error_code": 404,
        "error_message": "The page you're looking for doesn't exist."
    }, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors."""
    return templates.TemplateResponse("fastapi_error.html", {
        "request": request,
        "title": "Server Error",
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
    print(f"🔐 Login form: http://localhost:{port}/bootstrap/login")
    print(f"🐾 Bootstrap pets: http://localhost:{port}/bootstrap/pets")
    print(f"🐾 Material pets: http://localhost:{port}/material/pets")
    print(f"📚 API docs: http://localhost:{port}/docs")
    print(f"🔍 Interactive docs: http://localhost:{port}/redoc")
    print("⚡ Features: ListLayout, Bootstrap/Material Design, Async support, Auto-generated API docs")
    
    uvicorn.run(
        "fastapi_example:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )