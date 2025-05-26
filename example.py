from flask import Flask, make_response
from pydantic_forms.ui_elements import (
    TextInput, PasswordInput, EmailInput, NumberInput, CheckboxInput,
    SelectInput, DateInput, DatetimeInput, FileInput, ColorInput, RangeInput,
    HiddenInput, SSNInput, PhoneInput, URLInput, CurrencyInput, CreditCardInput
)
from pydantic_forms.ui_elements import RadioGroup

app = Flask(__name__)

def render_form_page(css_links, js_links, form_class="p-4 border rounded bg-light"):
    text_input = TextInput().render(
        name="username", id_="username", class_="form-control", style="width: 100%;", required="required", placeholder="Enter your username"
    )
    password_input = PasswordInput().render(
        name="password", id_="password", class_="form-control", style="width: 100%;", required="required", maxlength=32, autocomplete="off"
    )
    email_input = EmailInput().render(
        name="email", id_="email", class_="form-control", style="width: 100%;", required="required",
        placeholder="Enter your email", pattern=r"[^@]+@[^@]+\.[^@]+",value="me@something.com"
    )
    number_input = NumberInput().render(
        name="age", id_="age", class_="form-control", style="width: 100%;", required="required", min=0, max=120, step=1, value=30
    )
    checkbox_input = CheckboxInput().render(
        name="subscribe", id_="subscribe", class_="form-check-input", style="", checked=True, value="yes"
    )
    radio_input = RadioGroup().render(
        group_name="gender", required="required",
        options=[
            {"value": "male", "label": "Male"},#, "checked": True},
            {"value": "female", "label": "Female"},
            {"value": "other", "label": "Other"},
        ],
        class_="form-check",
        group_label="Gender"
    )
    select_input = SelectInput().render(
        name="country", id_="country", class_="form-select", style="width: 100%;",
        option_named=[
            {"value": "us", "label": "United States", "selected": True},
            {"value": "ca", "label": "Canada", "selected": False},
            {"value": "ie", "label": "Ireland", "selected": False},
        ],
        required="required",
        label="Country of Residence"  # <-- Set the label here
    )
    date_input = DateInput().render(
        name="birthday", id_="birthday", class_="form-control", style="width: 100%;",
        min="1900-01-01", max="2100-12-31", value="2000-01-01"
    )
    datetime_input = DatetimeInput().render(
        name="event_time",
        id_="event_time",
        class_="form-control",
        value="2023-10-01T12:00",
        required="",
        style="width: 100%;",
        with_set_now_button=False,
        auto_set_on_load=True
    )
    file_input = FileInput().render(
        name="resume", id_="resume", class_="form-control", style="",  accept=".pdf,.docx", multiple="multiple", required="required"
    )
    color_input = ColorInput().render(
        name="favorite_color", id_="favorite_color", class_="form-control", style="", required="", value="#ff0000"
    )
    range_input = RangeInput().render(
        name="volume", id_="volume", class_="form-range", style="", required="", min=0, max=100, step=1, value=50
    )
    hidden_input = HiddenInput().render(
        name="secret", id_="secret", class_="form-control", style="", value="hidden_value"
    )
    ssn_input = SSNInput().render(
        name="ssn", id_="ssn", class_="form-control", style="", required="", value="987-65-4321", label="Social Security Number"
    )
    phone_input = PhoneInput().render(
        name="phone", id_="phone", class_="form-control", style="", required="", value="838341551", country_code="+353"
    )
    url_input = URLInput().render(
        name="website", id_="website", class_="form-control", style="", required="", pattern="https?://.+", value="https://example.com"
    )
    currency_input = CurrencyInput().render(
        name="amount", id_="amount", class_="form-control", style="", required="", pattern="^\\$?\\d+(\\.(\\d{2}))?$", value="$100.00"
    )
    credit_card_input = CreditCardInput().render(
        name="ccn", id_="ccn", class_="form-control", style="", required="", pattern="\\d{16}", value="1234567812345678"
    )

    html = f"""
    <html>
    <head>
        {css_links}
        {js_links}
    </head>
    <body>
      <div class="container my-5">
      <div class="row justify-content-center"><a href="/">Back to Index</a></div>
        <div class="row justify-content-center">
          <div class="col-md-8 col-lg-6 col-xl-4">
            <form id="mainForm" hx-post="/submit" hx-target="#result" hx-swap="innerHTML" class="{form_class}">
              {text_input}<br/>
              {password_input}<br/>
              {email_input}<br/>
              {number_input}<br/>
              {checkbox_input}<br/>
              {radio_input}<br/>
              {select_input}<br/>
              {date_input}<br/>
              {datetime_input}<br/>
              {file_input}<br/>
              {color_input}<br/>
              {range_input}<br/>
              {hidden_input}<br/>
              {ssn_input}<br/>
              {phone_input}<br/>
              {url_input}<br/>
              {currency_input}<br/>
              {credit_card_input}<br/>
              <button type="submit" class="btn btn-primary mt-3">Submit</button>
            </form>
            <div id="result" class="mt-4"></div>
          </div>
        </div>
      </div>
      <script>
        document.getElementById('mainForm').addEventListener('submit', function (e) {{
            e.preventDefault();
            const form = e.target;
            const data = {{}};
            const fd = new FormData(form);
            
            // Process all form data including files
            for (const [key, value] of fd.entries()) {{
                // Special handling for File objects
                if (value instanceof File) {{
                    // If we already have a file array for this key
                    if (data[key] && Array.isArray(data[key])) {{
                        data[key].push({{
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes",
                            lastModified: new Date(value.lastModified).toLocaleString()
                        }});
                    }} else if (data[key]) {{
                        // Convert existing file to array
                        const existingFile = data[key];
                        data[key] = [existingFile, {{
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes",
                            lastModified: new Date(value.lastModified).toLocaleString()
                        }}];
                    }} else {{
                        // First file for this key
                        data[key] = {{
                            name: value.name,
                            type: value.type,
                            size: value.size + " bytes",
                            lastModified: new Date(value.lastModified).toLocaleString()
                        }};
                    }}
                }} else {{
                    // Handle non-file inputs as before
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
            
            document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }});
      </script>
    </body>
    </html>
    """
    return make_response(html)

@app.route("/bootstrap", methods=["GET"])
def form_bootstrap():
    css_links = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'
    js_links = """
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://unpkg.com/htmx.org@2.0.4"></script>
        <script src="https://unpkg.com/imask"></script>
    """
    return render_form_page(css_links, js_links, form_class="p-4 border rounded bg-light")

@app.route("/material", methods=["GET"])
def form_material():
    css_links = '<link href="https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/css/materialize.min.css" rel="stylesheet">'
    js_links = """
        <script src="https://cdn.jsdelivr.net/npm/@materializecss/materialize@1.0.0/dist/js/materialize.min.js"></script>
        <script src="https://unpkg.com/htmx.org@2.0.4"></script>
        <script src="https://unpkg.com/imask"></script>
    """
    return render_form_page(css_links, js_links, form_class="card-panel")

@app.route("/shadcn", methods=["GET"])
def form_shadcn():
    css_links = '<link href="https://unpkg.com/@shadcn/ui@latest/dist/style.css" rel="stylesheet">'
    js_links = """
        <script src="https://unpkg.com/htmx.org@2.0.4"></script>
        <script src="https://unpkg.com/imask"></script>
        <script src="https://cdn.jsdelivr.net/npm/shadcn@2.5.0/dist/index.min.js"></script>
    """
    return render_form_page(css_links, js_links, form_class="shadcn-form")


# Optionally, keep "/" as the default (e.g., Bootstrap)
@app.route("/", methods=["GET"])
def index():
    html = """
    <html>
    <head>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
      <div class="container my-5">
        <h2>UI Framework Examples</h2>
        <ul class="list-group">
          <li class="list-group-item"><a href="/bootstrap">Bootstrap 5 Example</a></li>
          <li class="list-group-item"><a href="/material">Material Design Example</a></li>
          <li class="list-group-item"><a href="/shadcn">shadcn/ui Example</a></li>
        </ul>
      </div>
    </body>
    </html>
    """
    return make_response(html)

