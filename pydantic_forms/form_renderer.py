"""
Enhanced Form Renderer that can handle different UI frameworks and render complete forms
from just a form definition.
"""
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel
from .ui_elements import (
    TextInput, PasswordInput, EmailInput, NumberInput, CheckboxInput,
    SelectInput, DateInput, DatetimeInput, FileInput, ColorInput, RangeInput,
    HiddenInput, SSNInput, PhoneInput, URLInput, CurrencyInput, CreditCardInput,
    TextArea, RadioGroup
)


class FormField:
    """Represents a single form field with its configuration."""
    
    def __init__(
        self,
        name: str,
        field_type: str = "text",
        label: Optional[str] = None,
        required: bool = False,
        placeholder: Optional[str] = None,
        value: Any = None,
        options: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        self.name = name
        self.field_type = field_type
        self.label = label or name.replace("_", " ").title()
        self.required = required
        self.placeholder = placeholder
        self.value = value
        self.options = options or []
        self.extra_attrs = kwargs


class FormDefinition:
    """Defines a complete form with fields and rendering options."""
    
    def __init__(
        self,
        title: str = "Form",
        fields: Optional[List[FormField]] = None,
        submit_url: str = "/submit",
        method: str = "POST",
        css_framework: str = "bootstrap"
    ):
        self.title = title
        self.fields = fields or []
        self.submit_url = submit_url
        self.method = method
        self.css_framework = css_framework


class FormRenderer:
    """Main form renderer that can output complete HTML forms."""
    
    # Framework configurations
    FRAMEWORKS = {
        "bootstrap": {
            "css_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
            "js_url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
            "form_class": "p-4 border rounded bg-light",
            "input_class": "form-control",
            "select_class": "form-select",
            "checkbox_class": "form-check-input",
            "radio_class": "form-check",
            "button_class": "btn btn-primary mt-3",
            "container_class": "container my-5",
            "row_class": "row justify-content-center",
            "col_class": "col-md-8 col-lg-6 col-xl-4"
        },
        "material": {
            "css_url": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css",
            "js_url": "https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js",
            "form_class": "card-panel",
            "input_class": "validate",
            "select_class": "browser-default",
            "checkbox_class": "filled-in",
            "radio_class": "",
            "button_class": "btn waves-effect waves-light",
            "container_class": "container",
            "row_class": "row",
            "col_class": "col s12 m8 l6 offset-m2 offset-l3"
        },
        "shadcn": {
            "css_url": "https://unpkg.com/@shadcn/ui@latest/dist/style.css",
            "js_url": "https://cdn.jsdelivr.net/npm/shadcn@2.5.0/dist/index.min.js",
            "form_class": "shadcn-form space-y-4 p-6 border rounded-lg",
            "input_class": "w-full px-3 py-2 border border-gray-300 rounded-md",
            "select_class": "w-full px-3 py-2 border border-gray-300 rounded-md",
            "checkbox_class": "rounded",
            "radio_class": "",
            "button_class": "bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded",
            "container_class": "container mx-auto p-4",
            "row_class": "flex justify-center",
            "col_class": "w-full max-w-md"
        }
    }
    
    def __init__(self, framework: str = "bootstrap"):
        self.framework = framework
        self.config = self.FRAMEWORKS.get(framework, self.FRAMEWORKS["bootstrap"])
    
    def _get_field_renderer(self, field_type: str):
        """Get the appropriate UI element renderer for a field type."""
        field_map = {
            "text": TextInput,
            "password": PasswordInput,
            "email": EmailInput,
            "number": NumberInput,
            "checkbox": CheckboxInput,
            "select": SelectInput,
            "date": DateInput,
            "datetime": DatetimeInput,
            "file": FileInput,
            "color": ColorInput,
            "range": RangeInput,
            "hidden": HiddenInput,
            "ssn": SSNInput,
            "phone": PhoneInput,
            "url": URLInput,
            "currency": CurrencyInput,
            "credit_card": CreditCardInput,
            "textarea": TextArea,
            "radio": RadioGroup,
        }
        return field_map.get(field_type, TextInput)
    
    def _render_field(self, field: FormField) -> str:
        """Render a single form field."""
        renderer_cls = self._get_field_renderer(field.field_type)
        renderer = renderer_cls()
        
        # Base attributes
        attrs = {
            "name": field.name,
            "id_": field.name,
            "label": field.label,
            "required": "required" if field.required else "",
            "class_": self._get_field_class(field.field_type),
            "style": "width: 100%;" if field.field_type not in ["checkbox", "radio"] else "",
        }
        
        # Add value if provided
        if field.value is not None:
            if field.field_type == "checkbox":
                attrs["checked"] = field.value
                attrs["value"] = "yes"
            else:
                attrs["value"] = field.value
        
        # Add placeholder if provided
        if field.placeholder:
            attrs["placeholder"] = field.placeholder
        
        # Handle special field types
        if field.field_type == "select" and field.options:
            attrs["option_named"] = field.options
        elif field.field_type == "radio" and field.options:
            attrs["group_name"] = field.name
            attrs["options"] = field.options
            attrs["group_label"] = field.label
        
        # Add any extra attributes
        attrs.update(field.extra_attrs)
        
        return renderer.render(**attrs)
    
    def _get_field_class(self, field_type: str) -> str:
        """Get the CSS class for a field type based on the framework."""
        if field_type == "select":
            return self.config["select_class"]
        elif field_type == "checkbox":
            return self.config["checkbox_class"]
        elif field_type == "radio":
            return self.config["radio_class"]
        else:
            return self.config["input_class"]
    
    def _get_required_css(self) -> str:
        """Get CSS for required field indicators."""
        return """
        <style>
            /* Only show one asterisk for required fields */
            label[data-required="true"]::after {
                content: "*";
                color: red;
                margin-left: 3px;
            }
            
            /* Remove any existing asterisks that might be in the label text */
            label[data-required="true"] .required-indicator {
                display: none;
            }
            
            /* Simple override for invalid inputs */
            input:invalid, select:invalid, textarea:invalid {
                border-color: red;
                box-shadow: 0 0 0 0.25rem rgba(220, 53, 69, 0.25);
            }
            
            /* Style for Bootstrap's was-validated mode */
            .was-validated .form-control:invalid {
                border-color: red;
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e");
                background-repeat: no-repeat;
                background-position: right calc(0.375em + 0.1875rem) center;
                background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
            }
        </style>
        """
    
    def _get_validation_script(self) -> str:
        """Get JavaScript for form validation."""
        return """
        <script>
        // Enhanced form validation that prevents submission if invalid
        document.getElementById('mainForm').addEventListener('submit', function (e) {
            // First check if the form is valid
            if (!this.checkValidity()) {
                e.preventDefault();
                
                // Mark the form as validated to show error styles
                this.classList.add('was-validated');
                
                // Find all invalid fields and highlight them
                const invalidFields = this.querySelectorAll(':invalid');
                invalidFields.forEach(field => {
                    field.setAttribute('aria-invalid', 'true');
                    
                    // Add scrollIntoView for the first invalid field
                    if (field === invalidFields[0]) {
                        setTimeout(() => field.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
                        field.focus();
                    }
                });
                
                // Display an alert at the top of the form
                const errorMsgDiv = document.createElement('div');
                errorMsgDiv.className = 'alert alert-danger';
                errorMsgDiv.textContent = 'Please fill in all required fields marked with *';
                errorMsgDiv.style.marginBottom = '20px';
                
                // Remove any existing error message
                const existingError = this.querySelector('.alert.alert-danger');
                if (existingError) {
                    existingError.remove();
                }
                
                // Insert at the top of the form
                this.insertBefore(errorMsgDiv, this.firstChild);
                
                // Return - don't process further
                return;
            }
            
            // If form is valid, continue with form data processing
            e.preventDefault();
            const form = e.target;
            const data = {};
            const fd = new FormData(form);
            
            // Process all form data including files
            for (const [key, value] of fd.entries()) {
                // Special handling for File objects
                if (value instanceof File) {
                    // If we already have a file array for this key
                    if (data[key] && Array.isArray(data[key])) {
                        data[key].push({
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes",
                            lastModified: new Date(value.lastModified).toLocaleString()
                        });
                    } else if (data[key]) {
                        // Convert existing file to array
                        const existingFile = data[key];
                        data[key] = [existingFile, {
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes",
                            lastModified: new Date(value.lastModified).toLocaleString()
                        }];
                    } else {
                        // First file for this key
                        data[key] = {
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes",
                            lastModified: new Date(value.lastModified).toLocaleString()
                        };
                    }
                } else {
                    // Handle non-file inputs as before
                    if (data[key]) {
                        if (Array.isArray(data[key])) {
                            data[key].push(value);
                        } else {
                            data[key] = [data[key], value];
                        }
                    } else {
                        data[key] = value;
                    }
                }
            }
            
            document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        });
        </script>
        """
    
    def render_complete_form(self, form_def: FormDefinition) -> str:
        """Render a complete HTML page with the form."""
        # Render all fields
        field_html = []
        for field in form_def.fields:
            field_html.append(self._render_field(field))
            field_html.append("<br/>")
        
        fields_str = "\n".join(field_html)
        
        # Build the complete HTML
        html = f"""
        <html>
        <head>
            <title>{form_def.title}</title>
            <link href="{self.config['css_url']}" rel="stylesheet">
            <script src="https://unpkg.com/htmx.org@2.0.4"></script>
            <script src="https://unpkg.com/imask"></script>
            {self.config.get('js_url', '')}
            {self._get_required_css()}
        </head>
        <body>
          <div class="{self.config['container_class']}">
            <div class="{self.config['row_class']}"><a href="/">Back to Index</a></div>
            <div class="{self.config['row_class']}">
              <div class="{self.config['col_class']}">
                <h2>{form_def.title}</h2>
                <form id="mainForm" novalidate hx-post="{form_def.submit_url}" hx-target="#result" hx-swap="innerHTML" class="{self.config['form_class']}" method="{form_def.method}">
                  {fields_str}
                  <button type="submit" class="{self.config['button_class']}">Submit</button>
                </form>
                <div id="result" class="mt-4"></div>
              </div>
            </div>
          </div>
          {self._get_validation_script()}
        </body>
        </html>
        """
        return html
    
    def render_form_from_pydantic(
        self, 
        model_cls: Type[BaseModel], 
        framework: str = "bootstrap",
        title: Optional[str] = None,
        submit_url: str = "/submit",
        form_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render a complete form from a Pydantic model."""
        form_data = form_data or {}
        
        # Create form definition from Pydantic model
        fields = []
        for field_name, field_info in model_cls.model_fields.items():
            field_type = "text"  # default
            
            # Determine field type from annotation
            annotation = getattr(field_info, 'annotation', None)
            if annotation:
                if annotation == int:
                    field_type = "number"
                elif annotation == float:
                    field_type = "number"
                elif annotation == bool:
                    field_type = "checkbox"
                elif "email" in field_name.lower():
                    field_type = "email"
                elif "password" in field_name.lower():
                    field_type = "password"
                elif "phone" in field_name.lower():
                    field_type = "phone"
                elif "url" in field_name.lower() or "website" in field_name.lower():
                    field_type = "url"
                elif "date" in field_name.lower() and "time" not in field_name.lower():
                    field_type = "date"
                elif "datetime" in field_name.lower() or "timestamp" in field_name.lower():
                    field_type = "datetime"
                elif "color" in field_name.lower():
                    field_type = "color"
                elif "file" in field_name.lower() or "upload" in field_name.lower():
                    field_type = "file"
            
            # Check if field is required
            is_required = field_info.is_required() if hasattr(field_info, 'is_required') else True
            
            # Get default value
            default_value = form_data.get(field_name)
            if default_value is None and hasattr(field_info, 'default'):
                default_value = field_info.default
            
            field = FormField(
                name=field_name,
                field_type=field_type,
                required=is_required,
                value=default_value,
                placeholder=f"Enter {field_name.replace('_', ' ')}"
            )
            fields.append(field)
        
        form_def = FormDefinition(
            title=title or f"{model_cls.__name__} Form",
            fields=fields,
            submit_url=submit_url,
            css_framework=framework
        )
        
        # Update framework and config
        self.framework = framework
        self.config = self.FRAMEWORKS.get(framework, self.FRAMEWORKS["bootstrap"])
        
        return self.render_complete_form(form_def)


def create_demo_form() -> FormDefinition:
    """Create a demonstration form with various field types."""
    fields = [
        FormField("username", "text", "Username", required=True, placeholder="Enter your username"),
        FormField("password", "password", "Password", required=True, placeholder="Enter your password"),
        FormField("biography", "textarea", "Biography", required=True, 
                 placeholder="Tell us about yourself", rows=4, maxlength=500, 
                 value="This is a sample biography."),
        FormField("email", "email", "Email", required=True, placeholder="Enter your email",
                 pattern=r"[^@]+@[^@]+\.[^@]+", value="me@something.com"),
        FormField("age", "number", "Age", required=True, min=0, max=120, step=1, 
                 value=30, placeholder="Enter your age"),
        FormField("subscribe", "checkbox", "Subscribe to Newsletter", value=True),
        FormField("gender", "radio", "Gender", required=True, options=[
            {"value": "male", "label": "Male"},
            {"value": "female", "label": "Female"},
            {"value": "other", "label": "Other"},
        ]),
        FormField("country", "select", "Country of Residence", required=True, options=[
            {"value": "us", "label": "United States", "selected": True},
            {"value": "ca", "label": "Canada", "selected": False},
            {"value": "ie", "label": "Ireland", "selected": False},
        ]),
        FormField("birthday", "date", "Birthday", min="1900-01-01", max="2100-12-31", value="2000-01-01"),
        FormField("event_time", "datetime", "Event Time", value="2023-10-01T12:00", 
                 auto_set_on_load=True, with_set_now_button=False),
        FormField("resume", "file", "Resume", required=True, accept=".pdf,.docx", multiple="multiple"),
        FormField("favorite_color", "color", "Favorite Color", value="#ff0000"),
        FormField("volume", "range", "Volume", min=0, max=100, step=1, value=50),
        FormField("ssn", "ssn", "Social Security Number", value="987-65-4321"),
        FormField("phone", "phone", "Phone Number", value="838341551", country_code="+353"),
        FormField("website", "url", "Website", pattern="https?://.+", value="https://example.com"),
        FormField("amount", "currency", "Amount", pattern=r"^\$?\d+(\.\d{2})?$", value="$100.00"),
        FormField("ccn", "credit_card", "Credit Card Number", pattern=r"\d{16}", value="1234567812345678"),
    ]
    
    return FormDefinition(
        title="Demo Form",
        fields=fields,
        submit_url="/submit"
    )
