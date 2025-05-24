""" """

import datetime
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

import silly
from dsg_lib.common_functions import logging_config
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    UUID6,
    UUID7,
    UUID8,
    AwareDatetime,
    ByteSize,
    DirectoryPath,
    Field,
    FilePath,
    FiniteFloat,
    FutureDate,
    FutureDatetime,
    Json,
    NaiveDatetime,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PastDate,
    PastDatetime,
    PaymentCardNumber,
    PositiveFloat,
    PositiveInt,
    SecretBytes,
    SecretStr,
    StrictBool,
    StrictBytes,
    StrictFloat,
    StrictInt,
    StrictStr,
    ValidationError,
    conbytes,
    condate,
    condecimal,
    confloat,
    confrozenset,
    conint,
    conlist,
    conset,
    constr,
    model_validator,
)

from PySchemaForms import STATIC_DIR
from PySchemaForms.render_form import pydantic_errors_to_rjsf, render_form_page
from PySchemaForms.schema_form import FormModel

# Configure logging as before
logging_config.config_log(
    logging_directory="log",
    log_name="log",
    logging_level="DEBUG",
    log_rotation="100 MB",
    log_retention="10 days",
    log_backtrace=True,
    log_serializer=False,
    log_diagnose=True,
    # app_name='my_app',
    # append_app_name=True,
    intercept_standard_logging=True,
    enqueue=True,
)

# Create FastAPI app
app: FastAPI = FastAPI()

# Serve static files from the library folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AddressModel(FormModel):
    street: Optional[str] = Field(None, title="Street", ui_placeholder="123 Main St")
    city: Optional[str] = Field(None, title="City", ui_placeholder="Metropolis")
    state: Optional[str] = Field(None, title="State", ui_widget="select")
    zip: Optional[str] = Field(None, title="ZIP Code", ui_placeholder="12345")


class ExperienceModel(FormModel):
    company: str = Field(..., title="Company", ui_placeholder="e.g. Acme Corp")
    role: str = Field(..., title="Role", ui_placeholder="e.g. Developer")
    years: Optional[int] = Field(None, title="Years", ge=0)


def patch_ui_kwargs_to_json_schema_extra(cls):
    """
    Move all ui_* kwargs from field metadata to json_schema_extra for a Pydantic model class.
    Compatible with Pydantic v2 where metadata is a tuple of arbitrary objects.
    """
    for field in cls.__fields__.values():
        # Pydantic v1: field.field_info, v2: field
        field_info = getattr(field, "field_info", field)
        # Pydantic v2: metadata is a tuple of arbitrary objects (not always key-value pairs)
        metadata = getattr(field_info, "metadata", ())
        if not metadata:
            continue
        # Only process items that are (str, value) and key startswith "ui_"
        ui_items = [
            (k, v)
            for item in metadata
            if isinstance(item, tuple)
            and len(item) == 2
            and isinstance(item[0], str)
            and item[0].startswith("ui_")
            for k, v in [item]
        ]
        if ui_items:
            if getattr(field_info, "json_schema_extra", None) is None:
                field_info.json_schema_extra = {}
            for k, v in ui_items:
                field_info.json_schema_extra[k] = v
        # Optionally: Remove ui_* items from metadata (not strictly necessary)


class ExampleSchemaModel(FormModel):
    name: str = Field(
        ...,
        title="Full Name",
        min_length=2,
        max_length=40,
        description="Enter your full name.",
    )
    age: int = Field(
        ...,
        title="Age",
        ge=21,
        le=120,
    )
    gender: Optional[str] = Field(
        None,
        title="Gender",
        enum=["male", "female", "other"],
    )
    bio: str = Field(
        ...,
        title="Biography",
        description="Tell us about yourself.",
        ui_widget="textarea",
        ui_options={"rows": 6, "placeholder": "Write a short bio..."},
    )
    email: Optional[str] = Field(
        None,
        title="Email Address",
        format="email",
    )
    website: Optional[str] = Field(
        None,
        title="Personal Website",
        format="uri",
    )
    option_string_test: Optional[str] = Field(
        None,
        title="String Option Test",
        description="This is a string option test.",
        min_length=3,
        max_length=10,
        ui_widget="text",
        ui_options={"placeholder": "3-10 characters"},
    )

    # Optional is not working with this example
    password: SecretStr = Field(
        None,
        title="Password",
        min_length=6,
        ui_widget="password",
        ui_options={"placeholder": "Create a secure password"},
        type="string",
    )

    acceptTerms: bool = Field(
        ...,
        title="Accept Terms and Conditions",
        ui_widget="checkbox",
        ui_options={"label": "I agree to the terms and conditions"},
    )
    # Optional is not working with this example
    favoriteColor: str = Field(
        "#ff0000",
        title="Favorite Color",
        format="color",
        ui_widget="color",
    )
    skills: Optional[list[str]] = Field(
        None,
        title="Skills",
        min_items=1,
        enum=["Python", "JavaScript", "C++", "Java", "Go", "Rust"],
        type="array",
    )
    experience: list[ExperienceModel] = Field(
        ...,
        title="Work Experience",
        description="List your work experience.",
        min_items=1,
        max_items=5,
        type="array",
    )
    address: Optional[AddressModel] = Field(
        None,
        title="Address",
        type="object",
    )

    # Optional is not working with this example
    profilePhoto: str = Field(
        None,
        title="Profile Photo",
        # format="data-url",
        ui_widget="file",
        # type="string",
    )
    newsletter: Optional[bool] = Field(
        False,
        title="Subscribe to newsletter",
        ui_help="Subscribe to receive updates.",
        type="boolean",
    )
    rating: Optional[int] = Field(
        3,
        title="Rate your experience",
        ge=1,
        le=5,
        type="integer",
    )
    customSelect: Optional[str] = Field(
        None,
        title="Custom Select",
        enum=["a", "b", "c"],
        ui_widget="radio",
        type="string",
    )
    readonlyField: Optional[str] = Field(
        "This is read-only",
        title="Read Only Example",
        read_only=True,
        ui_readonly=True,
        type="string",
    )
    hiddenField: Optional[str] = Field(
        "You should not see this",
        title="Hidden Example",
        ui_widget="hidden",
        type="string",
    )

    class Config:
        populate_by_name = True


patch_ui_kwargs_to_json_schema_extra(ExampleSchemaModel)

# Example data for the model
example_data: Dict[str, Any] = {
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


class KitchenSinkModel(FormModel):
    """
    A model to test every possible Pydantic field type.
    """

    strict_str: StrictStr = Field(
        ...,
        title="Strict String",
        description="A strict string value",
        ui_options={"placeholder": "Strict string"},
        ui_widget="text",
    )
    strict_int: StrictInt = Field(
        ...,
        title="Strict Int",
        description="A strict integer value",
        ui_widget="updown",
    )
    strict_float: StrictFloat = Field(
        ...,
        title="Strict Float",
        description="A strict float value",
        ui_widget="updown",
    )
    strict_bool: StrictBool = Field(
        ...,
        title="Strict Bool",
        description="A strict boolean value",
        ui_widget="checkbox",
    )
    strict_bytes: StrictBytes = Field(
        ...,
        title="Strict Bytes",
        description="A strict bytes value",
        ui_widget="file",
    )
    constr_field: constr(min_length=3, max_length=10) = Field(
        ...,
        title="Constrained String",
        description="A string with length 3-10",
        ui_options={"placeholder": "3-10 chars"},
        ui_widget="text",
    )
    conint_field: conint(gt=0, lt=100) = Field(
        ...,
        title="Constrained Int",
        description="An int between 1 and 99",
        ui_widget="updown",
    )
    confloat_field: confloat(ge=0.0, le=10.0) = Field(
        ...,
        title="Constrained Float",
        description="A float between 0.0 and 10.0",
        ui_widget="range",
    )
    conlist_field: conlist(int, min_length=2, max_length=5) = Field(
        ...,
        title="Constrained List",
        description="A list of 2-5 integers",
        ui_widget="checkboxes",
    )
    conset_field: conset(str, min_length=1, max_length=3) = Field(
        ...,
        title="Constrained Set",
        description="A set of 1-3 strings",
        ui_widget="checkboxes",
    )
    confrozenset_field: confrozenset(float, min_length=1, max_length=3) = Field(
        ...,
        title="Constrained FrozenSet",
        description="A frozenset of 1-3 floats",
        ui_widget="checkboxes",
    )
    conbytes_field: conbytes(min_length=2, max_length=8) = Field(
        ...,
        title="Constrained Bytes",
        description="Bytes of length 2-8",
        ui_widget="file",
    )
    condecimal_field: condecimal(gt=0, lt=100) = Field(
        ...,
        title="Constrained Decimal",
        description="Decimal between 0 and 100",
        ui_widget="updown",
    )
    positive_int: PositiveInt = Field(
        ...,
        title="Positive Int",
        description="A positive integer",
        ui_widget="updown",
    )
    negative_int: NegativeInt = Field(
        ...,
        title="Negative Int",
        description="A negative integer",
        ui_widget="updown",
    )
    non_negative_int: NonNegativeInt = Field(
        ...,
        title="Non-Negative Int",
        description="A non-negative integer",
        ui_widget="updown",
    )
    non_positive_int: NonPositiveInt = Field(
        ...,
        title="Non-Positive Int",
        description="A non-positive integer",
        ui_widget="updown",
    )
    positive_float: PositiveFloat = Field(
        ...,
        title="Positive Float",
        description="A positive float",
        ui_widget="updown",
    )
    negative_float: NegativeFloat = Field(
        ...,
        title="Negative Float",
        description="A negative float",
        ui_widget="updown",
    )
    non_negative_float: NonNegativeFloat = Field(
        ...,
        title="Non-Negative Float",
        description="A non-negative float",
        ui_widget="updown",
    )
    non_positive_float: NonPositiveFloat = Field(
        ...,
        title="Non-Positive Float",
        description="A non-positive float",
        ui_widget="updown",
    )
    finite_float: FiniteFloat = Field(
        ...,
        title="Finite Float",
        description="A finite float",
        ui_widget="updown",
    )
    uuid1_field: UUID1 = Field(
        default_factory=uuid.uuid1,
        title="UUID1",
        description="UUID version 1",
        ui_widget="text",
    )
    uuid3_field: UUID3 = Field(
        default_factory=lambda: uuid.uuid3(uuid.NAMESPACE_DNS, "example.com"),
        title="UUID3",
        description="UUID version 3",
        ui_widget="text",
    )
    uuid4_field: UUID4 = Field(
        default_factory=uuid.uuid4,
        title="UUID4",
        description="UUID version 4",
        ui_widget="text",
    )
    uuid5_field: UUID5 = Field(
        default_factory=lambda: uuid.uuid5(uuid.NAMESPACE_DNS, "example.com"),
        title="UUID5",
        description="UUID version 5",
        ui_widget="text",
    )
    uuid6_field: UUID6 = Field(
        default_factory=lambda: uuid.uuid4(),
        title="UUID6",
        description="UUID version 6 (simulated)",
        ui_widget="text",
    )
    uuid7_field: UUID7 = Field(
        default_factory=lambda: uuid.uuid4(),
        title="UUID7",
        description="UUID version 7 (simulated)",
        ui_widget="text",
    )
    uuid8_field: UUID8 = Field(
        default_factory=lambda: uuid.uuid4(),
        title="UUID8",
        description="UUID version 8 (simulated)",
        ui_widget="text",
    )
    file_path: FilePath = Field(
        ...,
        title="File Path",
        description="A file path",
        ui_widget="file",
    )
    dir_path: DirectoryPath = Field(
        ...,
        title="Directory Path",
        description="A directory path",
        ui_widget="file",
    )
    json_field: Json[Any] = Field(
        ...,
        title="JSON Field",
        description="A JSON value",
        ui_widget="textarea",
    )
    secret_str: SecretStr = Field(
        ...,
        title="Secret String",
        description="A secret string",
        ui_widget="password",
    )
    secret_bytes: SecretBytes = Field(
        ...,
        title="Secret Bytes",
        description="A secret bytes value",
        ui_widget="file",
    )
    payment_card: PaymentCardNumber = Field(
        ...,
        title="Payment Card Number",
        description="A payment card number",
        ui_widget="text",
    )
    byte_size: ByteSize = Field(
        ...,
        title="Byte Size",
        description="A byte size value",
        ui_widget="updown",
    )
    past_date: PastDate = Field(
        ...,
        title="Past Date",
        description="A date in the past",
        ui_widget="date",
    )
    future_date: FutureDate = Field(
        ...,
        title="Future Date",
        description="A date in the future",
        ui_widget="date",
    )
    past_datetime: PastDatetime = Field(
        ...,
        title="Past Datetime",
        description="A datetime in the past",
        ui_widget="alt-datetime",
    )
    future_datetime: FutureDatetime = Field(
        ...,
        title="Future Datetime",
        description="A datetime in the future",
        ui_widget="alt-datetime",
    )
    aware_datetime: AwareDatetime = Field(
        ...,
        title="Aware Datetime",
        description="A timezone-aware datetime",
        ui_widget="alt-datetime",
    )
    naive_datetime: NaiveDatetime = Field(
        ...,
        title="Naive Datetime",
        description="A naive datetime",
        ui_widget="alt-datetime",
    )
    condate_field: condate(ge=datetime.date(2000, 1, 1), le=datetime.date(2100, 1, 1)) = Field(
        ...,
        title="Constrained Date",
        description="A date between 2000 and 2100",
        ui_widget="date",
    )

    class Config:
        populate_by_name = True


patch_ui_kwargs_to_json_schema_extra(KitchenSinkModel)

# List of available themes as (theme_key, display_label)
THEMES: List[Tuple[str, str]] = [
    ("bootstrap-4", "Bootstrap 4"),
    ("mui", "Material UI"),
    ("mui-basic", "mui basic"),
]

# Mapping from theme name to required CSS links
THEME_CSS: Dict[str, List[str]] = {
    "bootstrap-4": ["https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css"],
    "mui": [
        "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap",
        "https://fonts.googleapis.com/icon?family=Material+Icons",
    ],
}

# URL for HTMX form submission
# htmx_post_url: str = "/xx-xx"


@app.get("/", response_class=HTMLResponse)
async def form(
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
) -> HTMLResponse:
    """
    Main theme selection page with validation options.
    """
    # Generate links to each theme, preserving validation options in query params
    links: str = "".join(
        f'<li><a href="/{theme}?liveValidate={str(liveValidate).lower()}&showErrorList={showErrorList}">{label}</a></li>'
        for theme, label in THEMES
    )
    # Add Kitchen Sink endpoint
    links += f'<li><a href="/kitchen-sink?liveValidate={str(liveValidate).lower()}&showErrorList={showErrorList}">Kitchen Sink</a></li>'

    # Render HTML with checkboxes for validation options
    html: str = f"""
    <html>
        <head><title>JSON Schema Form Themes</title></head>
        <body>
            <h1>Available Themes</h1>
            <form method="get" action="/">
                <label>
                    <input type="checkbox" name="liveValidate" value="true" {'checked' if liveValidate else ''}>
                    Live Validate
                </label>
                <label style="margin-left:2em;">
                    Show Error List:
                    <select name="showErrorList" style="margin-left:0.5em;">
                        <option value="false" {"selected" if showErrorList == "false" else ""}>None</option>
                        <option value="top" {"selected" if showErrorList == "top" else ""}>Top</option>
                        <option value="bottom" {"selected" if showErrorList == "bottom" else ""}>Bottom</option>
                    </select>
                </label>
                <button type="submit" style="margin-left:2em;">Apply</button>
            </form>
            <ul>
                {links}
            </ul>
        </body>
    </html>
    """
    return HTMLResponse(content=html)


# Minimal password form JSON Schema (camelCase keys)
class MinimalSchemaModel(FormModel):
    userName: str = Field(
        ...,
        alias="userName",
        description="Choose a username (at least 3 characters).",
        min_length=3,
        ui_autofocus=True,
    )
    password: str = Field(
        ...,
        alias="password",
        description="Password must be at least 8 characters and include 1 uppercase letter, 1 number, and 1 special character.",
        min_length=8,
        ui_element="password",
    )
    password_repeat: str = Field(
        ...,
        alias="passwordRepeat",
        description="Re-enter your password. Must match the password above.",
        title="Repeat Password",
        ui_element="password",
    )
    biography: str = Field(
        ...,
        alias="biography",
        description="Write a short biography.",
        title="Biography",
        min_length=1,
        max_length=500,
        ui_element="textarea",
        ui_options={"rows": 6},
    )

    @model_validator(mode="after")
    def passwords_match(self) -> "MinimalSchemaModel":
        if self.password != self.password_repeat:
            raise ValueError("Passwords do not match")
        return self

    class Config:
        populate_by_name = True


patch_ui_kwargs_to_json_schema_extra(MinimalSchemaModel)


@app.api_route("/mui-basic", methods=["GET", "POST"], response_class=HTMLResponse)
async def mui_basic_form(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
) -> HTMLResponse:
    """
    Render or process a minimal Material UI form for testing.
    """
    logger.info(f"Accessed endpoint: {request.url}")
    form_data = {
        "userName": f"{silly.verb()}-{silly.noun()}",
        "password": "passwordCorrect1!",
        "passwordRepeat": "passwordNotCorrect1!",
        "biography": silly.paragraph(length=4),
    }
    errors = {}
    error_schema = {}
    if request.method == "POST":
        try:
            try:
                data: Any = await request.json()
            except Exception:
                form = await request.form()
                logger.debug(f"Form data received: {dict(form)}")
                data: Dict[str, Any] = dict(form)
            form_data = data
            MinimalSchemaModel(**data)
            html: str = f"""
            <div class="alert alert-success" role="alert" style="margin-top:1em;">
                <h4>Form submitted!</h4>
                <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
            </div>
            """
            logger.info("Form submitted successfully.")
            return HTMLResponse(content=html)
        except ValidationError as e:
            logger.warning("Validation error occurred during form submission.")
            rjsf_errors = pydantic_errors_to_rjsf(e)
            errors = rjsf_errors.get("errors", [])
            error_schema = rjsf_errors.get("errorSchema", {})
            # fall through to render form with errors and submitted data

    html = render_form_page(
        MinimalSchemaModel,
        theme="mui",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/mui-basic",
        errors=errors,
        error_schema=error_schema,
    )
    return HTMLResponse(content=html)


@app.api_route("/bootstrap-4", methods=["GET", "POST"], response_class=HTMLResponse)
async def bootstrap4_form(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
) -> HTMLResponse:
    """
    Render or process a Bootstrap 4 themed form using render_form_page.
    """
    form_data = example_data.copy()
    errors = {}
    error_schema = {}
    if request.method == "POST":
        try:
            try:
                data: Any = await request.json()
            except Exception:
                form = await request.form()
                data: Dict[str, Any] = dict(form)
            form_data = data
            ExampleSchemaModel(**data)
            html: str = f"""
            <div class="alert alert-success" role="alert" style="margin-top:1em;">
                <h4>Form submitted!</h4>
                <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
            </div>
            """
            return HTMLResponse(content=html)
        except ValidationError as e:
            rjsf_errors = pydantic_errors_to_rjsf(e)
            errors = rjsf_errors.get("errors", [])
            error_schema = rjsf_errors.get("errorSchema", {})
            # fall through to render form with errors and submitted data

    html = render_form_page(
        ExampleSchemaModel,
        theme="bootstrap-4",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/bootstrap-4",
        errors=errors,
        error_schema=error_schema,
    )
    return HTMLResponse(content=html)


@app.api_route("/mui", methods=["GET", "POST"], response_class=HTMLResponse)
async def mui_form(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
) -> HTMLResponse:
    """
    Render or process a Material UI themed form using render_form_page.
    """
    form_data = example_data.copy()
    errors = {}
    error_schema = {}
    if request.method == "POST":
        try:
            try:
                data: Any = await request.json()
            except Exception:
                form = await request.form()
                data: Dict[str, Any] = dict(form)
            form_data = data
            ExampleSchemaModel(**data)
            html: str = f"""
            <div class="alert alert-success" role="alert" style="margin-top:1em;">
                <h4>Form submitted!</h4>
                <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
            </div>
            """
            return HTMLResponse(content=html)
        except ValidationError as e:
            rjsf_errors = pydantic_errors_to_rjsf(e)
            errors = rjsf_errors.get("errors", [])
            error_schema = rjsf_errors.get("errorSchema", {})
            # fall through to render form with errors and submitted data

    html = render_form_page(
        ExampleSchemaModel,
        theme="mui",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/mui",
        errors=errors,
        error_schema=error_schema,
    )
    return HTMLResponse(content=html)


for theme, label in THEMES:
    route_path: str = f"/{theme}"

    @app.api_route(route_path, methods=["GET", "POST"], response_class=HTMLResponse)
    async def themed_form(
        request: Request,
        theme: str = theme,
        label: str = label,
        liveValidate: bool = Query(False, description="Enable live validation"),
        showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
    ) -> HTMLResponse:
        """
        Render or process a themed form page using render_form_page, just like mui-basic.
        """
        form_data = example_data.copy()
        errors = {}
        error_schema = {}
        if request.method == "POST":
            try:
                try:
                    data: Any = await request.json()
                except Exception:
                    form = await request.form()
                    data: Dict[str, Any] = dict(form)
                form_data = data
                ExampleSchemaModel(**data)
                html: str = f"""
                <div class="alert alert-success" role="alert" style="margin-top:1em;">
                    <h4>Form submitted!</h4>
                    <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                    <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
                </div>
                """
                return HTMLResponse(content=html)
            except ValidationError as e:
                rjsf_errors = pydantic_errors_to_rjsf(e)
                errors = rjsf_errors.get("errors", [])
                error_schema = rjsf_errors.get("errorSchema", {})
                # fall through to render form with errors and submitted data

        html = render_form_page(
            ExampleSchemaModel,
            theme=theme,
            form_data=form_data,
            live_validate=liveValidate,
            show_error_list=showErrorList,
            htmx_post_url=route_path,
            errors=errors,
            error_schema=error_schema,
        )
        return HTMLResponse(content=html)


@app.api_route("/kitchen-sink", methods=["GET", "POST"], response_class=HTMLResponse)
async def kitchen_sink(
    request: Request,
    liveValidate: bool = Query(False, description="Enable live validation"),
    showErrorList: str = Query("top", description="Show error list (false, top, bottom)"),
) -> HTMLResponse:
    """
    Render or process the KitchenSinkModel form with all supported Pydantic types.
    """
    # Generate example data for the kitchen sink model
    form_data = KitchenSinkModel.get_example_form_data()
    errors = {}
    error_schema = {}
    if request.method == "POST":
        try:
            try:
                data: Any = await request.json()
            except Exception:
                form = await request.form()
                data: Dict[str, Any] = dict(form)
            form_data = data
            KitchenSinkModel(**data)
            html: str = f"""
            <div class="alert alert-success" role="alert" style="margin-top:1em;">
                <h4>Form submitted!</h4>
                <pre style="white-space:pre-wrap;">{json.dumps(data, indent=2)}</pre>
                <a href="javascript:history.back()" class="btn btn-secondary mt-2">Back</a>
            </div>
            """
            return HTMLResponse(content=html)
        except ValidationError as e:
            rjsf_errors = pydantic_errors_to_rjsf(e)
            errors = rjsf_errors.get("errors", [])
            error_schema = rjsf_errors.get("errorSchema", {})
            # fall through to render form with errors and submitted data

    html = render_form_page(
        KitchenSinkModel,
        theme="mui",
        form_data=form_data,
        live_validate=liveValidate,
        show_error_list=showErrorList,
        htmx_post_url="/kitchen-sink",
        errors=errors,
        error_schema=error_schema,
    )
    return HTMLResponse(content=html)


if __name__ == "__main__":
    print("=== JSON Schema ===")
    print(json.dumps(ExampleSchemaModel.schema(), indent=2))
    print("=== UI Schema ===")
    print(json.dumps(ExampleSchemaModel.get_schemas()["ui_schema"], indent=2))
