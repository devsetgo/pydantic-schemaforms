"""
UI Elements Demo - Low-level form components

This demonstrates the low-level UI element components that power
the pydantic-forms library. This shows direct usage of individual
input components with different CSS frameworks.

For higher-level Pydantic model integration, see:
- example_usage.py (React JSON Schema Forms style)
- pydantic_example.py (Flask integration)
- simple_example.py (Basic examples)
"""

from flask import Flask, make_response
from pydantic_forms.inputs import (
    TextInput,
    PasswordInput,
    EmailInput,
    NumberInput,
    CheckboxInput,
    SelectInput,
    DateInput,
    DatetimeInput,
    FileInput,
    ColorInput,
    RangeInput,
    HiddenInput,
    SSNInput,
    PhoneInput,
    URLInput,
    CurrencyInput,
    CreditCardInput,
    TextArea,
    RadioGroup,
)

app = Flask(__name__)


def render_form_page(css_links, js_links, form_class="p-4 border rounded bg-light"):
    """Render a comprehensive form using low-level UI elements."""

    # Common CSS for required fields
    required_css = """
    <style>
        /* Show asterisk for required fields */
        label[data-required="true"]::after {
            content: "*";
            color: red;
            margin-left: 3px;
        }
        
        /* Style for invalid inputs */
        input:invalid, select:invalid, textarea:invalid {
            border-color: red;
            box-shadow: 0 0 0 0.25rem rgba(220, 53, 69, 0.25);
        }
        
        /* Bootstrap validation styles */
        .was-validated .form-control:invalid {
            border-color: red;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right calc(0.375em + 0.1875rem) center;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        }
    </style>
    """
    css_links += required_css

    # Create all the form inputs using low-level components
    text_input = TextInput().render(
        name="username",
        id_="username",
        class_="form-control",
        required="required",
        placeholder="Enter your username",
    )

    password_input = PasswordInput().render(
        name="password",
        id_="password",
        class_="form-control",
        required="required",
        maxlength=32,
        autocomplete="off",
    )

    biography_input = TextArea().render(
        name="biography",
        id_="biography",
        class_="form-control",
        required="required",
        placeholder="Tell us about yourself",
        rows=4,
        maxlength=500,
        value="This is a sample biography.",
    )

    email_input = EmailInput().render(
        name="email",
        id_="email",
        class_="form-control",
        required="required",
        placeholder="Enter your email",
        pattern=r"[^@]+@[^@]+\.[^@]+",
        value="me@something.com",
    )

    number_input = NumberInput().render(
        name="age",
        id_="age",
        class_="form-control",
        required="required",
        min=0,
        max=120,
        step=1,
        value=30,
        placeholder="Enter your age",
    )

    checkbox_input = CheckboxInput().render(
        name="subscribe", id_="subscribe", class_="form-check-input", checked=True, value="yes"
    )

    radio_input = RadioGroup().render(
        group_name="gender",
        required="required",
        options=[
            {"value": "male", "label": "Male"},
            {"value": "female", "label": "Female"},
            {"value": "other", "label": "Other"},
        ],
        class_="form-check",
        group_label="Gender",
    )

    select_input = SelectInput().render(
        name="country",
        id_="country",
        class_="form-select",
        option_named=[
            {"value": "us", "label": "United States", "selected": True},
            {"value": "ca", "label": "Canada", "selected": False},
            {"value": "ie", "label": "Ireland", "selected": False},
        ],
        required="required",
        label="Country of Residence",
    )

    date_input = DateInput().render(
        name="birthday",
        id_="birthday",
        class_="form-control",
        min="1900-01-01",
        max="2100-12-31",
        value="2000-01-01",
    )

    datetime_input = DatetimeInput().render(
        name="event_time",
        id_="event_time",
        class_="form-control",
        value="2023-10-01T12:00",
        required="",
        with_set_now_button=False,
        auto_set_on_load=True,
    )

    file_input = FileInput().render(
        name="resume",
        id_="resume",
        class_="form-control",
        accept=".pdf,.docx",
        multiple="multiple",
        required="required",
    )

    color_input = ColorInput().render(
        name="favorite_color",
        id_="favorite_color",
        class_="form-control",
        required="",
        value="#ff0000",
    )

    range_input = RangeInput().render(
        name="volume",
        id_="volume",
        class_="form-range",
        required="",
        min=0,
        max=100,
        step=1,
        value=50,
    )

    hidden_input = HiddenInput().render(name="secret", id_="secret", value="hidden_value")

    ssn_input = SSNInput().render(
        name="ssn",
        id_="ssn",
        class_="form-control",
        required="",
        value="987-65-4321",
        label="Social Security Number",
    )

    phone_input = PhoneInput().render(
        name="phone",
        id_="phone",
        class_="form-control",
        required="",
        value="838341551",
        country_code="+353",
    )

    url_input = URLInput().render(
        name="website",
        id_="website",
        class_="form-control",
        required="",
        pattern="https?://.+",
        value="https://example.com",
    )

    currency_input = CurrencyInput().render(
        name="amount",
        id_="amount",
        class_="form-control",
        required="",
        pattern="^\\$?\\d+(\\.(\\d{2}))?$",
        value="$100.00",
    )

    credit_card_input = CreditCardInput().render(
        name="ccn",
        id_="ccn",
        class_="form-control",
        required="",
        pattern="\\d{16}",
        value="1234567812345678",
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UI Elements Demo - Pydantic Forms</title>
        {css_links}
        {js_links}
    </head>
    <body>
      <div class="container my-5">
        <div class="text-center mb-4">
          <h1>UI Elements Demo</h1>
          <p class="text-muted">Low-level form components demonstration</p>
          <a href="/" class="btn btn-secondary">← Back to Framework Examples</a>
        </div>
        
        <div class="row justify-content-center">
          <div class="col-md-8 col-lg-6">
            <form id="mainForm" novalidate class="{form_class}">
              <h3 class="mb-3">Complete Form Example</h3>
              
              <!-- Basic Inputs -->
              <div class="mb-3">
                <h5>Basic Inputs</h5>
                {text_input}
                {password_input}
                {email_input}
              </div>
              
              <!-- Text Areas -->
              <div class="mb-3">
                <h5>Text Area</h5>
                {biography_input}
              </div>
              
              <!-- Numbers & Ranges -->
              <div class="mb-3">
                <h5>Numbers & Ranges</h5>
                {number_input}
                {range_input}
              </div>
              
              <!-- Selections -->
              <div class="mb-3">
                <h5>Selection Inputs</h5>
                {checkbox_input}
                {radio_input}
                {select_input}
              </div>
              
              <!-- Date & Time -->
              <div class="mb-3">
                <h5>Date & Time</h5>
                {date_input}
                {datetime_input}
              </div>
              
              <!-- Files & Colors -->
              <div class="mb-3">
                <h5>Files & Colors</h5>
                {file_input}
                {color_input}
              </div>
              
              <!-- Specialized Inputs -->
              <div class="mb-3">
                <h5>Specialized Inputs</h5>
                {ssn_input}
                {phone_input}
                {url_input}
                {currency_input}
                {credit_card_input}
              </div>
              
              {hidden_input}
              
              <div class="text-center">
                <button type="submit" class="btn btn-primary">Submit Form</button>
                <button type="reset" class="btn btn-secondary ms-2">Reset</button>
              </div>
            </form>
            
            <div id="result" class="mt-4"></div>
          </div>
        </div>
      </div>
      
      <script>
        // Enhanced form validation and submission handling
        document.getElementById('mainForm').addEventListener('submit', function (e) {{
            e.preventDefault();
            
            // Check form validity
            if (!this.checkValidity()) {{
                this.classList.add('was-validated');
                
                // Find and focus first invalid field
                const invalidFields = this.querySelectorAll(':invalid');
                if (invalidFields.length > 0) {{
                    invalidFields[0].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    invalidFields[0].focus();
                }}
                
                // Show error message
                showMessage('Please fill in all required fields marked with *', 'danger');
                return;
            }}
            
            // Process form data
            const form = e.target;
            const data = {{}};
            const fd = new FormData(form);
            
            for (const [key, value] of fd.entries()) {{
                if (value instanceof File) {{
                    // Handle file inputs
                    if (data[key] && Array.isArray(data[key])) {{
                        data[key].push({{
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes"
                        }});
                    }} else if (data[key]) {{
                        const existingFile = data[key];
                        data[key] = [existingFile, {{
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes"
                        }}];
                    }} else {{
                        data[key] = {{
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes"
                        }};
                    }}
                }} else {{
                    // Handle regular inputs
                    if (data[key]) {{
                        if (Array.isArray(data[key])) {{
                            data[key].push(value);
                        }} else {{
                            data[key] = [data[key], value];
                        }}
                    }} else {{
                        data[key] = value;
                    }}
                }}
            }}
            
            // Display results
            document.getElementById('result').innerHTML = `
              <div class="alert alert-success">
                <h5>Form Submitted Successfully!</h5>
                <pre>${{JSON.stringify(data, null, 2)}}</pre>
              </div>
            `;
        }});
        
        function showMessage(message, type) {{
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${{type}} alert-dismissible fade show`;
            alertDiv.innerHTML = `
              ${{message}}
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Remove existing alerts
            const existingAlerts = document.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());
            
            // Insert new alert
            const form = document.getElementById('mainForm');
            form.parentNode.insertBefore(alertDiv, form);
        }}
      </script>
    </body>
    </html>
    """
    return make_response(html)


@app.route("/bootstrap", methods=["GET"])
def form_bootstrap():
    """Bootstrap 5 styled form example."""
    css_links = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'
    js_links = """
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://unpkg.com/htmx.org@2.0.4"></script>
        <script src="https://unpkg.com/imask"></script>
    """
    return render_form_page(css_links, js_links, form_class="p-4 border rounded bg-light")


@app.route("/material", methods=["GET"])
def form_material():
    """Material Design styled form example."""
    css_links = '<link href="https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css" rel="stylesheet">'
    js_links = """
        <script src="https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js"></script>
        <script src="https://unpkg.com/htmx.org@2.0.4"></script>
        <script src="https://unpkg.com/imask"></script>
    """
    return render_form_page(css_links, js_links, form_class="card-panel")


@app.route("/shadcn", methods=["GET"])
def form_shadcn():
    """shadcn/ui styled form example."""
    css_links = '<link href="https://unpkg.com/@shadcn/ui@latest/dist/style.css" rel="stylesheet">'
    js_links = """
        <script src="https://unpkg.com/htmx.org@2.0.4"></script>
        <script src="https://unpkg.com/imask"></script>
        <script src="https://cdn.jsdelivr.net/npm/shadcn@2.5.0/dist/index.min.js"></script>
    """
    return render_form_page(css_links, js_links, form_class="shadcn-form")


@app.route("/", methods=["GET"])
def index():
    """Main index page with links to different framework examples."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UI Elements Demo - Framework Examples</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
      <div class="container my-5">
        <div class="text-center mb-5">
          <h1>UI Elements Demo</h1>
          <p class="lead">Low-level form components with different CSS frameworks</p>
          <p class="text-muted">
            This demonstrates the individual UI element components that power pydantic-forms.<br>
            For higher-level Pydantic model integration, see the other example files.
          </p>
        </div>
        
        <div class="row justify-content-center">
          <div class="col-md-8">
            <div class="list-group">
              <a href="/bootstrap" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                  <h5 class="mb-1">Bootstrap 5 Example</h5>
                  <small class="text-primary">Recommended</small>
                </div>
                <p class="mb-1">Complete form using Bootstrap 5 styling and components</p>
              </a>
              
              <a href="/material" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                  <h5 class="mb-1">Material Design Example</h5>
                </div>
                <p class="mb-1">Form styled with Material Design components</p>
              </a>
              
              <a href="/shadcn" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                  <h5 class="mb-1">shadcn/ui Example</h5>
                  <small class="text-info">Modern</small>
                </div>
                <p class="mb-1">Form using shadcn/ui modern component library</p>
              </a>
            </div>
            
            <div class="mt-5 p-4 bg-light rounded">
              <h4>Other Examples</h4>
              <ul class="list-unstyled">
                <li><strong>example_usage.py</strong> - React JSON Schema Forms compatible examples</li>
                <li><strong>pydantic_example.py</strong> - Flask integration with Pydantic models</li>
                <li><strong>simple_example.py</strong> - Basic usage without frameworks</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return make_response(html)


if __name__ == "__main__":
    print("🎨 Starting UI Elements Demo")
    print("📱 Visit http://localhost:5002 to see the low-level components")
    print("🔧 This demonstrates the building blocks of pydantic-forms")
    app.run(debug=True, host="0.0.0.0", port=5002)
