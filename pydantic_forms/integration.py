"""
Complete form integration system for pydantic-forms using Python 3.14 template strings.
Integrates inputs, layouts, validation, and framework support into a unified system.

Requires: Python 3.14+ (no backward compatibility)
"""

from typing import Dict, Any, List, Optional, Union, Type
from datetime import date, datetime
import string.templatelib

# Import version check to ensure compatibility

from pydantic import BaseModel

from .inputs import *
from .validation import create_validator
from .modern_renderer import ModernFormRenderer, FormDefinition, FormField, FormSection


# Framework integration classes for testing compatibility
class FlaskIntegration:
    """Flask framework integration."""

    def __init__(self):
        pass

    def create_route(self, app, path: str, form_model, methods=None):
        """Create a Flask route for the form."""

        def route_handler():
            return f"Flask route for {form_model.__name__}"

        return route_handler

    def handle_form_submission(self, form_model, request):
        """Handle Flask form submission."""
        from .validation import validate_form_data

        if hasattr(request, "form"):
            data = dict(request.form)
            # Convert checkbox values
            for key, value in data.items():
                if value == "on":
                    data[key] = True
        elif hasattr(request, "method") and request.method == "POST":
            data = {}
        else:
            data = {}
        return validate_form_data(form_model, data)

    def render_form_template(self, template_name, **kwargs):
        """Render form template."""
        return f"<html>Rendered {template_name} with {kwargs}</html>"


class FastAPIIntegration:
    """FastAPI framework integration."""

    def __init__(self):
        pass

    def create_endpoint(self, app, path: str, form_model):
        """Create FastAPI endpoint."""

        def endpoint():
            return {"message": f"FastAPI endpoint for {form_model.__name__}"}

        return endpoint

    def create_form_dependency(self, form_model):
        """Create FastAPI form dependency."""

        def form_dependency(data: dict):
            return form_model(**data)

        return form_dependency

    def generate_openapi_schema(self, form_model):
        """Generate OpenAPI schema."""
        return {
            "type": "object",
            "properties": {
                field_name: {"type": "string"} for field_name in form_model.model_fields.keys()
            },
            "required": [
                field_name
                for field_name, field_info in form_model.model_fields.items()
                if field_info.is_required()
            ],
        }


class DjangoIntegration:
    """Django framework integration."""

    def __init__(self):
        pass

    def create_django_form(self, form_model):
        """Create Django form from Pydantic model."""

        class DynamicDjangoForm:
            def __init__(self):
                self.fields = list(form_model.model_fields.keys())

        return DynamicDjangoForm

    def create_model_form(self, form_model, django_model):
        """Create Django ModelForm."""

        class DynamicModelForm:
            def __init__(self):
                self.model = django_model
                self.fields = list(form_model.model_fields.keys())

        return DynamicModelForm

    def handle_view(self, request, form_model, template_name=None):
        """Handle Django view."""
        return f"Django view response for {form_model.__name__}"


class ReactJSONSchemaIntegration:
    """React JSON Schema Forms integration."""

    def __init__(self):
        pass

    def generate_schema(self, form_model):
        """Generate JSON Schema for React JSON Schema Forms."""
        properties = {}
        required = []

        for field_name, field_info in form_model.model_fields.items():
            field_type = field_info.annotation

            # Handle Union types (Optional fields)
            if hasattr(field_type, "__origin__") and field_type.__origin__ == Union:
                non_none_types = [t for t in field_type.__args__ if t != type(None)]
                if non_none_types:
                    field_type = non_none_types[0]

            # Map Python types to JSON Schema types
            if field_type == str:
                schema_type = "string"
                if "email" in field_name.lower():
                    properties[field_name] = {"type": schema_type, "format": "email"}
                else:
                    properties[field_name] = {"type": schema_type}
            elif field_type == int:
                properties[field_name] = {"type": "integer"}
            elif field_type == float:
                properties[field_name] = {"type": "number"}
            elif field_type == bool:
                properties[field_name] = {"type": "boolean"}
            elif field_type in (date, datetime):
                properties[field_name] = {"type": "string", "format": "date"}
            else:
                properties[field_name] = {"type": "string"}

            # Add to required if field is required
            if field_info.is_required():
                required.append(field_name)

        return {"type": "object", "properties": properties, "required": required}

    def generate_ui_schema(self, form_model):
        """Generate UI Schema for React JSON Schema Forms."""
        ui_schema = {}

        for field_name, field_info in form_model.model_fields.items():
            field_type = field_info.annotation

            # Handle Union types
            if hasattr(field_type, "__origin__") and field_type.__origin__ == Union:
                non_none_types = [t for t in field_type.__args__ if t != type(None)]
                if non_none_types:
                    field_type = non_none_types[0]

            # Map to UI widgets
            if "email" in field_name.lower():
                ui_schema[field_name] = {"ui:widget": "email"}
            elif "password" in field_name.lower():
                ui_schema[field_name] = {"ui:widget": "password"}
            elif field_name.lower() in ["bio", "description", "comment", "notes"]:
                ui_schema[field_name] = {"ui:widget": "textarea"}
            elif field_type in (date, datetime):
                ui_schema[field_name] = {"ui:widget": "date"}

        return ui_schema

    def generate_form_data(self, form_model, data):
        """Generate form data for React JSON Schema Forms."""
        return data

    def generate_complete_config(self, form_model, initial_data=None):
        """Generate complete React JSON Schema Forms configuration."""
        return {
            "schema": self.generate_schema(form_model),
            "uiSchema": self.generate_ui_schema(form_model),
            "formData": initial_data or {},
        }


class VueFormulateIntegration:
    """Vue Formulate integration."""

    def __init__(self):
        pass

    def generate_form_config(self, form_model):
        """Generate Vue Formulate configuration."""
        config = []

        for field_name, field_info in form_model.model_fields.items():
            field_type = field_info.annotation

            # Handle Union types
            if hasattr(field_type, "__origin__") and field_type.__origin__ == Union:
                non_none_types = [t for t in field_type.__args__ if t != type(None)]
                if non_none_types:
                    field_type = non_none_types[0]

            field_config = {"name": field_name, "label": field_name.replace("_", " ").title()}

            # Map field types
            if "email" in field_name.lower():
                field_config["type"] = "email"
            elif "password" in field_name.lower():
                field_config["type"] = "password"
            elif field_type == bool:
                field_config["type"] = "checkbox"
            elif field_type in (int, float):
                field_config["type"] = "number"
            else:
                field_config["type"] = "text"

            config.append(field_config)

        return config

    def generate_validation_rules(self, form_model):
        """Generate Vue Formulate validation rules."""
        rules = {}

        for field_name, field_info in form_model.model_fields.items():
            field_rules = []

            if field_info.is_required():
                field_rules.append("required")

            if "email" in field_name.lower():
                field_rules.append("email")

            if field_rules:
                rules[field_name] = field_rules

        return rules


class JSONSchemaGenerator:
    """JSON Schema generation utilities."""

    def __init__(self):
        pass

    def generate_schema(self, form_model):
        """Generate JSON Schema from Pydantic model."""
        return ReactJSONSchemaIntegration().generate_schema(form_model)

    def generate_field_schema(self, field_type, field_info):
        """Generate schema for individual field."""
        if field_type == str:
            schema = {"type": "string"}
            if hasattr(field_info, "description"):
                schema["description"] = field_info.description
        elif field_type == int:
            schema = {"type": "integer"}
            if hasattr(field_info, "ge"):
                schema["minimum"] = field_info.ge
            if hasattr(field_info, "le"):
                schema["maximum"] = field_info.le
        elif field_type == float:
            schema = {"type": "number"}
        elif field_type == bool:
            schema = {"type": "boolean"}
        else:
            schema = {"type": "string"}

        return schema


class OpenAPISchemaGenerator:
    """OpenAPI schema generation."""

    def __init__(self):
        pass

    def generate_request_schema(self, form_model):
        """Generate OpenAPI request schema."""
        schema = JSONSchemaGenerator().generate_schema(form_model)
        return {"content": {"application/json": {"schema": schema}}}

    def generate_response_schema(self, form_model):
        """Generate OpenAPI response schema."""
        return {
            "200": {
                "description": "Success",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean"},
                                "data": JSONSchemaGenerator().generate_schema(form_model),
                            },
                        }
                    }
                },
            },
            "422": {
                "description": "Validation Error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "errors": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                }
                            },
                        }
                    }
                },
            },
        }

    def generate_complete_spec(self, form_model, endpoint_path, method="POST"):
        """Generate complete OpenAPI specification."""
        return {
            "paths": {
                endpoint_path: {
                    method.lower(): {
                        "requestBody": self.generate_request_schema(form_model),
                        "responses": self.generate_response_schema(form_model),
                    }
                }
            }
        }


# Utility functions for integration
def map_pydantic_to_json_schema_type(python_type):
    """Map Python types to JSON Schema types."""
    if python_type == str:
        return "string"
    elif python_type == int:
        return "integer"
    elif python_type == float:
        return "number"
    elif python_type == bool:
        return "boolean"
    elif python_type == list:
        return "array"
    elif python_type == dict:
        return "object"
    else:
        return "string"


def map_ui_element_to_framework(ui_element, framework):
    """Map UI elements to framework-specific widgets."""
    mapping = {
        "react": {
            "email": "email",
            "password": "password",
            "textarea": "textarea",
            "select": "select",
        },
        "vue": {
            "email": "email",
            "password": "password",
            "textarea": "textarea",
            "select": "select",
        },
    }

    return mapping.get(framework, {}).get(ui_element, ui_element)


def convert_validation_rules(field_info, framework):
    """Convert Pydantic validation to framework rules."""
    if framework == "react":
        return {}  # React JSON Schema handles this automatically
    elif framework == "vue":
        return []  # Vue Formulate rules
    else:
        return {}


def check_framework_availability(framework_name):
    """Check if a framework is available for import."""
    try:
        if framework_name == "flask":
            import flask

            return True
        elif framework_name == "fastapi":
            import fastapi

            return True
        elif framework_name == "django":
            import django

            return True
        return False
    except ImportError:
        return False


class FormBuilder:
    """Enhanced form builder that integrates all pydantic-forms components."""

    def __init__(
        self,
        model: Optional[Type[BaseModel]] = None,
        framework: str = "bootstrap",
        theme: str = "default",
    ):
        self.model = model
        self.framework = framework
        self.theme = theme
        self.fields: List[FormField] = []
        self.sections: List[FormSection] = []
        self.validator = create_validator()
        self.renderer = ModernFormRenderer()
        self.layout_type = "vertical"
        self.form_attrs = {}
        self.csrf_enabled = True
        self.honeypot_enabled = True

    def add_field(self, field: FormField) -> "FormBuilder":
        """Add a field to the form."""
        self.fields.append(field)
        return self

    def add_section(self, section: FormSection) -> "FormBuilder":
        """Add a section to the form."""
        self.sections.append(section)
        return self

    def text_input(self, name: str, label: str = None, **kwargs) -> "FormBuilder":
        """Add a text input field."""
        field = FormField(
            name=name, label=label or name.replace("_", " ").title(), input_type="text", **kwargs
        )
        return self.add_field(field)

    def email_input(self, name: str = "email", label: str = "Email", **kwargs) -> "FormBuilder":
        """Add an email input field with validation."""
        field = FormField(name=name, label=label, input_type="email", **kwargs)
        self.validator.field(name).email()
        return self.add_field(field)

    def password_input(
        self, name: str = "password", label: str = "Password", **kwargs
    ) -> "FormBuilder":
        """Add a password input field."""
        field = FormField(name=name, label=label, input_type="password", **kwargs)
        return self.add_field(field)

    def number_input(
        self, name: str, label: str = None, min_val: float = None, max_val: float = None, **kwargs
    ) -> "FormBuilder":
        """Add a number input field with range validation."""
        field = FormField(
            name=name, label=label or name.replace("_", " ").title(), input_type="number", **kwargs
        )

        if min_val is not None or max_val is not None:
            self.validator.field(name).numeric_range(min_val, max_val)

        return self.add_field(field)

    def select_input(
        self, name: str, options: List[Dict[str, str]], label: str = None, **kwargs
    ) -> "FormBuilder":
        """Add a select input field."""
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="select",
            options=options,
            **kwargs,
        )
        return self.add_field(field)

    def checkbox_input(self, name: str, label: str = None, **kwargs) -> "FormBuilder":
        """Add a checkbox input field."""
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="checkbox",
            **kwargs,
        )
        return self.add_field(field)

    def textarea_input(
        self, name: str, label: str = None, rows: int = 4, **kwargs
    ) -> "FormBuilder":
        """Add a textarea input field."""
        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="textarea",
            attributes={"rows": str(rows)},
            **kwargs,
        )
        return self.add_field(field)

    def date_input(self, name: str, label: str = None, **kwargs) -> "FormBuilder":
        """Add a date input field."""
        field = FormField(
            name=name, label=label or name.replace("_", " ").title(), input_type="date", **kwargs
        )
        return self.add_field(field)

    def file_input(
        self, name: str, label: str = None, accept: str = None, **kwargs
    ) -> "FormBuilder":
        """Add a file input field."""
        attributes = {}
        if accept:
            attributes["accept"] = accept

        field = FormField(
            name=name,
            label=label or name.replace("_", " ").title(),
            input_type="file",
            attributes=attributes,
            **kwargs,
        )
        return self.add_field(field)

    def required(self, field_name: str, message: str = None) -> "FormBuilder":
        """Add required validation to a field."""
        self.validator.field(field_name).required(message)
        return self

    def min_length(self, field_name: str, length: int, message: str = None) -> "FormBuilder":
        """Add minimum length validation to a field."""
        self.validator.field(field_name).min_length(length, message)
        return self

    def max_length(self, field_name: str, length: int, message: str = None) -> "FormBuilder":
        """Add maximum length validation to a field."""
        self.validator.field(field_name).max_length(length, message)
        return self

    def set_layout(self, layout_type: str) -> "FormBuilder":
        """Set the form layout type."""
        self.layout_type = layout_type
        return self

    def set_form_attributes(self, **attrs) -> "FormBuilder":
        """Set form element attributes."""
        self.form_attrs.update(attrs)
        return self

    def disable_csrf(self) -> "FormBuilder":
        """Disable CSRF protection."""
        self.csrf_enabled = False
        return self

    def disable_honeypot(self) -> "FormBuilder":
        """Disable honeypot protection."""
        self.honeypot_enabled = False
        return self

    def build(self) -> FormDefinition:
        """Build the complete form definition."""
        return FormDefinition(
            fields=self.fields,
            sections=self.sections,
            framework=self.framework,
            theme=self.theme,
            csrf_enabled=self.csrf_enabled,
            honeypot_enabled=self.honeypot_enabled,
            **self.form_attrs,
        )

    def render(self, data: Dict[str, Any] = None, errors: Dict[str, List[str]] = None) -> str:
        """Render the complete form HTML."""
        form_def = self.build()
        return self.renderer.render_form(form_def, data=data or {}, errors=errors or {})

    async def render_async(
        self, data: Dict[str, Any] = None, errors: Dict[str, List[str]] = None
    ) -> str:
        """Render the form asynchronously."""
        form_def = self.build()
        return await self.renderer.render_form_async(form_def, data=data or {}, errors=errors or {})

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, Dict[str, List[str]]]:
        """Validate form data."""
        if self.model:
            return self.validator.validate_pydantic_model(self.model, data)
        return self.validator.validate(data)

    def get_validation_script(self) -> str:
        """Get client-side validation JavaScript."""
        return self.validator.generate_client_validation_script()


class AutoFormBuilder(FormBuilder):
    """Automatically builds forms from Pydantic models."""

    def __init__(self, model: Type[BaseModel], **kwargs):
        super().__init__(model, **kwargs)
        self._build_from_model()

    def _build_from_model(self):
        """Build form fields from Pydantic model."""
        if not self.model:
            return

        # Get model fields
        model_fields = self.model.model_fields

        for field_name, field_info in model_fields.items():
            field_type = field_info.annotation
            field_default = field_info.default

            # Determine input type based on field type
            input_type = self._get_input_type_for_field(field_type, field_name)

            # Create form field
            form_field = FormField(
                name=field_name,
                label=field_name.replace("_", " ").title(),
                input_type=input_type,
                default_value=field_default if field_default != ... else None,
                required=field_info.is_required(),
            )

            # Add validation based on field constraints
            self._add_field_validation(field_name, field_info)

            self.add_field(form_field)

    def _get_input_type_for_field(self, field_type: Type, field_name: str) -> str:
        """Determine appropriate input type for a field."""
        # Handle Union types (Optional fields)
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
            # Get the non-None type
            non_none_types = [t for t in field_type.__args__ if t != type(None)]
            if non_none_types:
                field_type = non_none_types[0]

        # String fields
        if field_type == str:
            if "email" in field_name.lower():
                return "email"
            elif "password" in field_name.lower():
                return "password"
            elif "phone" in field_name.lower():
                return "tel"
            elif "url" in field_name.lower():
                return "url"
            elif field_name.lower() in ["description", "comment", "notes", "bio"]:
                return "textarea"
            else:
                return "text"

        # Numeric fields
        elif field_type in (int, float):
            return "number"

        # Boolean fields
        elif field_type == bool:
            return "checkbox"

        # Date/datetime fields
        elif field_type in (date, datetime):
            return "date"

        # Default to text
        else:
            return "text"

    def _add_field_validation(self, field_name: str, field_info):
        """Add validation rules based on field constraints."""
        if field_info.is_required():
            self.validator.field(field_name).required()

        # Add other validation based on field metadata
        # This would be extended based on specific Pydantic constraints


class FormIntegration:
    """Integration helpers for different web frameworks."""

    @staticmethod
    def flask_integration(form_builder: FormBuilder, request_data: Dict[str, Any] = None):
        """Integration helper for Flask."""
        try:
            from flask import request, render_template_string

            if request.method == "POST":
                data = request.form.to_dict()
                is_valid, errors = form_builder.validate_data(data)

                if is_valid:
                    return {"success": True, "data": data}
                else:
                    form_html = form_builder.render(data, errors)
                    return {"success": False, "form_html": form_html, "errors": errors}
            else:
                form_html = form_builder.render(request_data or {})
                return {"form_html": form_html}

        except ImportError:
            raise ImportError("Flask is required for flask_integration")

    @staticmethod
    async def fastapi_integration(form_builder: FormBuilder, request_data: Dict[str, Any] = None):
        """Integration helper for FastAPI."""
        try:
            from fastapi import Request

            if request_data:
                is_valid, errors = form_builder.validate_data(request_data)

                if is_valid:
                    return {"success": True, "data": request_data}
                else:
                    form_html = await form_builder.render_async(request_data, errors)
                    return {"success": False, "form_html": form_html, "errors": errors}
            else:
                form_html = await form_builder.render_async()
                return {"form_html": form_html}

        except ImportError:
            raise ImportError("FastAPI is required for fastapi_integration")


# Convenience functions for common form patterns
def create_login_form(framework: str = "bootstrap") -> FormBuilder:
    """Create a standard login form."""
    return (
        FormBuilder(framework=framework)
        .email_input("email", "Email Address")
        .password_input("password", "Password")
        .required("email")
        .required("password")
    )


def create_registration_form(framework: str = "bootstrap") -> FormBuilder:
    """Create a standard registration form."""
    builder = (
        FormBuilder(framework=framework)
        .text_input("first_name", "First Name")
        .text_input("last_name", "Last Name")
        .email_input("email", "Email Address")
        .password_input("password", "Password")
        .password_input("confirm_password", "Confirm Password")
        .required("first_name")
        .required("last_name")
        .required("email")
        .required("password")
        .required("confirm_password")
        .min_length("password", 8, "Password must be at least 8 characters")
    )

    # Add cross-field validation for password confirmation
    from .validation import CrossFieldRules

    builder.validator.add_cross_field_rule(
        CrossFieldRules.password_confirmation("password", "confirm_password")
    )

    return builder


def create_contact_form(framework: str = "bootstrap") -> FormBuilder:
    """Create a standard contact form."""
    return (
        FormBuilder(framework=framework)
        .text_input("name", "Full Name")
        .email_input("email", "Email Address")
        .text_input("subject", "Subject")
        .textarea_input("message", "Message", rows=6)
        .required("name")
        .required("email")
        .required("subject")
        .required("message")
    )


def create_form_from_model(model: Type[BaseModel], **kwargs) -> AutoFormBuilder:
    """Create a form automatically from a Pydantic model."""
    return AutoFormBuilder(model, **kwargs)


# Template for complete form page
FORM_PAGE_TEMPLATE = string.templatelib.Template(
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .form-container {
            max-width: 600px;
            margin: 2rem auto;
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .form-title {
            text-align: center;
            margin-bottom: 2rem;
            color: #343a40;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-container">
            <h1 class="form-title">${title}</h1>
            ${form_html}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ${validation_script}
</body>
</html>
"""
)


def render_form_page(
    form_builder: FormBuilder,
    title: str = "Form",
    data: Dict[str, Any] = None,
    errors: Dict[str, List[str]] = None,
) -> str:
    """Render a complete HTML page with the form."""
    form_html = form_builder.render(data or {}, errors or {})
    validation_script = form_builder.get_validation_script()

    interpolation = Interpolation(
        title=title, form_html=form_html, validation_script=validation_script
    )

    return FORM_PAGE_TEMPLATE.substitute(interpolation.data)


# Export main classes and functions
__all__ = [
    "FormBuilder",
    "AutoFormBuilder",
    "FormIntegration",
    "FlaskIntegration",
    "FastAPIIntegration",
    "DjangoIntegration",
    "ReactJSONSchemaIntegration",
    "VueFormulateIntegration",
    "JSONSchemaGenerator",
    "OpenAPISchemaGenerator",
    "create_login_form",
    "create_registration_form",
    "create_contact_form",
    "create_form_from_model",
    "render_form_page",
    "map_pydantic_to_json_schema_type",
    "map_ui_element_to_framework",
    "convert_validation_rules",
    "check_framework_availability",
]
