import json  # <-- Add this import
from typing import List, Tuple
from urllib.parse import parse_qs, urlencode

import silly
from dsg_lib.common_functions import logging_config
from examples.models.example import ExampleSchemaModel
from examples.models.kitchensink import KitchenSinkModel
from examples.models.minimal import MinimalSchemaModel
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import ValidationError

from PySchemaForms import STATIC_DIR
from PySchemaForms.render_form import (
    SchemaFormValidationError,
    pydantic_errors_to_rjsf,
    render_form_page,
)
from PySchemaForms.schema_form import FormModel


# Configure logging as before
logging_config.config_log(
    logging_directory="log",
    log_name="example-log",
    logging_level="INFO",
    log_rotation="100 MB",
    log_retention="10 days",
    log_backtrace=True,
    log_serializer=False,
    log_diagnose=True,
    log_propagate=False,
    intercept_standard_logging=True,
    enqueue=True,
)

# Create FastAPI app
app: FastAPI = FastAPI()

# Mount static files for the library under a unique path to avoid conflicts
app.mount("/pyschemaforms-static", StaticFiles(directory=STATIC_DIR), name="pyschemaforms-static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="examples/templates")


# @app.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#     logger.info("Rendering index page")
#     return templates.TemplateResponse("index.html", {"request": request})


example_data = {
    "name": "Ada Lovelace",
    "age": 36,
    "gender": "female",
    "bio": "First computer programmer.",
    "email": "ada@lovelace.org",
    "website": "https://en.wikipedia.org/wiki/Ada_Lovelace",
    "password": "securepassword",
    "acceptTerms": True,
    "favoriteColor": "#00bfff",
    "skills": ["Python", "JavaScript"],
    "experience": [{"company": "Analytical Engines", "role": "Mathematician", "years": 5}],
    "address": {
        "street": "123 Computing Ave",
        "city": "London",
        "state": "England",
        "zip": "12345",
    },
    "newsletter": True,
    "rating": 5,
    "customSelect": "b",
    "readonlyField": "This is read-only",
    "hiddenField": "You should not see this",
}


# List of available themes as (endpoint, display_label)
FORM_ENDPOINTS: List[Tuple[str, str]] = [
    ("material-design-basic", "Material Design Basic"),
    ("material-design-example", "Material Design Example"),
    ("bootstrap-5-example", "Bootstrap 5 Example"),
    ("kitchen-sink-example", "Kitchen Sink Example"),
]


@app.get("/", response_class=HTMLResponse)
async def forms(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
):
    """
    List available form endpoints with options.
    """
    return templates.TemplateResponse(
        "forms.html",
        {
            "request": request,
            "form_endpoints": FORM_ENDPOINTS,
            "liveValidate": liveValidate,
            "showErrorList": showErrorList,
        },
    )


@app.api_route("/material-design-example", methods=["GET", "POST"], response_class=HTMLResponse)
async def material_design_example(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
    debug: bool = Query(True, description="Show schema/data/errors debug info"),  # <-- Make sure this is bool
):
    """
    Render or process a Material UI themed form using render_form_page.
    """
    form_data = {
        "name": "Ada Lovelace",
        "age": 36,
        "gender": "female",
        "bio": "First computer programmer.",
        "email": "ada@lovelace.org",
        "website": "https://en.wikipedia.org/wiki/Ada_Lovelace",
        "password": "securepassword",
        "acceptTerms": True,
        "favoriteColor": "#00bfff",
        "skills": ["Python", "JavaScript"],
        "experience": [{"company": "Analytical Engines", "role": "Mathematician", "years": 5}],
        "address": {
            "street": "123 Computing Ave",
            "city": "London",
            "state": "England",
            "zip": "12345",
        },
        "newsletter": True,
        "rating": 5,
        "customSelect": "b",
        "readonlyField": "This is read-only",
        "hiddenField": "You should not see this",
    }
    errors = None

    if request.method == "POST":
        try:
            try:
                data = await request.json()
            except Exception:
                form = await request.form()
                data = dict(form)
            form_data = data
            ExampleSchemaModel(**data)
            html = f"""
            <div class="alert alert-success" role="alert" style="margin-top:1em;">
                <h4>Form submitted!</h4>
                <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
            </div>
            """
            return HTMLResponse(content=html)
        except ValidationError as e:
            errors = e.errors()
            print(f"ValidationError: {errors}")

    html = render_form_page(
        ExampleSchemaModel,
        theme="material5",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/material-design-example",
        errors=errors,
        error_schema=None,
        debug_info=debug,  # <-- Pass as boolean
    )
    return HTMLResponse(content=html)


@app.api_route("/bootstrap-5-example", methods=["GET", "POST"], response_class=HTMLResponse)
async def bootstrap_5_example(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
    debug: bool = Query(True, description="Show schema/data/errors debug info"),
):
    """
    Render or process a minimal Bootstrap 5 form for testing.
    """
    form_data = {
        "name": "Ada Lovelace",
        "age": 36,
        "gender": "female",
        "bio": "First computer programmer.",
        "email": "ada@lovelace.org",
        "website": "https://en.wikipedia.org/wiki/Ada_Lovelace",
        "password": "securepassword",
        "acceptTerms": True,
        "favoriteColor": "#00bfff",
        "skills": ["Python", "JavaScript"],
        "experience": [{"company": "Analytical Engines", "role": "Mathematician", "years": 5}],
        "address": {
            "street": "123 Computing Ave",
            "city": "London",
            "state": "England",
            "zip": "12345",
        },
        "newsletter": True,
        "rating": 5,
        "customSelect": "b",
        "readonlyField": "This is read-only",
        "hiddenField": "You should not see this",
    }
    errors = None

    if request.method == "POST":
        try:
            try:
                data = await request.json()
            except Exception:
                form = await request.form()
                data = dict(form)
            form_data = data
            ExampleSchemaModel(**data)
            html = f"""
            <div class="alert alert-success" role="alert" style="margin-top:1em;">
                <h4>Form submitted!</h4>
                <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
            </div>
            """
            return HTMLResponse(content=html)
        except ValidationError as e:
            errors = e.errors()
            print(f"ValidationError: {errors}")

    html = render_form_page(
        ExampleSchemaModel,
        theme="bootstrap5",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/bootstrap-5-example",
        errors=errors,
        error_schema=None,
        debug_info=debug,
    )
    return HTMLResponse(content=html)


@app.api_route("/kitchen-sink-example", methods=["GET", "POST"], response_class=HTMLResponse)
async def kitchen_sink_example(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
    debug: bool = Query(True, description="Show schema/data/errors debug info"),
):
    """
    Render or process a Kitchen Sink form using render_form_page.
    """
    # Use example data if available, else empty dict
    try:
        form_data = KitchenSinkModel.get_example_form_data()
    except Exception:
        form_data = {}
    errors = {}
    error_schema = {}
    html = render_form_page(
        KitchenSinkModel,
        theme="material5",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/kitchen-sink-example",
        errors=errors,
        error_schema=error_schema,
        debug_info=debug,
    )
    return HTMLResponse(content=html)


@app.api_route("/material-design-basic", methods=["GET", "POST"], response_class=HTMLResponse)
async def material_design_basic(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
    debug: bool = Query(True, description="Show schema/data/errors debug info"),  # <-- Make sure this is bool and True
):
    """
    Render or process a minimal Material UI form for testing.
    """
    form_data = {
        "userName": "bob",
        "password": "1234abcDEF",
        "passwordRepeat": "e1234abcDEFxxx",
        "biography": silly.paragraph(length=3),
    }
    errors = None  # <-- Ensure errors is always defined

    if request.method == "POST":
        try:
            try:
                data = await request.json()
            except Exception:
                form = await request.form()
                data = dict(form)
            form_data = data
            MinimalSchemaModel(**data)
            html = f"""
            <div class="alert alert-success" role="alert" style="margin-top:1em;">
                <h4>Form submitted!</h4>
                <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
            </div>
            """
            return HTMLResponse(content=html)
        except SchemaFormValidationError as e:
            errors = e.errors
            # print(f"SchemaFormValidationError: {errors}")
            errors.append(
                {"name": "userName", "property": ".userName", "message": "I can extend the toast error messages"}
            )
        # except ValidationError as e:
        #     errors = e.errors()
        #     print(f"ValidationError: {errors}")

    # Only for GET requests or after error
    html = render_form_page(
        MinimalSchemaModel,
        theme="material5",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/material-design-basic",
        errors=errors,
        error_schema=None,
        debug_info=debug,  # <-- Pass as boolean
    )
    # print(f"HTML: {html}")
    return HTMLResponse(content=html)
