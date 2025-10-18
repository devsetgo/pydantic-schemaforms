<https://github.com/python/cpython/blob/3.14/Lib/string/templatelib.py>

<https://docs.python.org/id/3.14/library/string.templatelib.html>

Now that Python 3.14 has been released with Template Strings, I want to get back to working on this library. The purpose of the library is to generate HTML forms using template strings.

JSON Schema should configure the form to allow validation on the HTML page. When submitting, the validation should also happen server-side via Pydantic. Live server side validation would be good to have so complex validation would happen before submission of the form.

The general idea is a competitor to WTForms and a python version of the key abilities of React JSON Schema Forms (JSON Schema the driver of creating the form, ability to configure validation, theme -material, bootstrap, shadcn - and layout.  
[Introduction | react-jsonschema-form](https://rjsf-team.github.io/react-jsonschema-form/docs/)

The form sections should be configurable (default vertical) as sections for horizontal and vertical layouts. Future should allow tab forms (each tab has a section of the form).

The whole form should be delivered from the library (HTML Form, inputs, layouts, css, javascript) should be delivered with the idea that it will be embedded in an existing page/template (jinja, mako, html, etc.).

The library should be useable in any python app (Flask, FastAPI, Robyn) and support async and sync use.

Performance matters. It should be fast to render and validate. It should be easy to configure and development with.  
<br/>Code coverage should target 100% for unit, integration, and UI.

The Input Types should be separated into separate modules: Text Inputs, Numeric Inputs, Selection Inputs, Date Time Inputs, and Specialized Inputs.

**Text Inputs**

\- \`TextInput\`: Standard text input

\- \`PasswordInput\`: Password input with masking

\- \`EmailInput\`: Email validation input

\- \`TextArea\`: Multi-line text input

**Numeric Inputs**

\- \`NumberInput\`: Numeric input with step controls

\- \`RangeInput\`: Range slider

\- \`CurrencyInput\`: Currency formatted input

**Selection Inputs**

\- \`SelectInput\`: Dropdown selection

\- \`RadioGroup\`: Radio button group

\- \`CheckboxInput\`: Single checkbox

**Date/Time Inputs**

\- \`DateInput\`: Date picker

\- \`DatetimeInput\`: Date and time picker

**Specialized Inputs**

\- \`FileInput\`: File upload

\- \`ColorInput\`: Color picker

\- \`URLInput\`: URL validation input

\- \`PhoneInput\`: Phone number input

\- \`HiddenInput\`: Hidden field

**Custom Inputs**

\- 'CSRFInput': Cross-Site Request Forgery

\- \`SSNInput\`: Social Security Number input

\- \`CreditCardInput\`: Credit card input

The rules for all standard HTML input types should be in the library, with all attributes available for each input type.

- &lt;input type="button"&gt;
- &lt;input type="checkbox"&gt;
- &lt;input type="color"&gt;
- &lt;input type="date"&gt;
- &lt;input type="datetime-local"&gt;
- &lt;input type="email"&gt;
- &lt;input type="file"&gt;
- &lt;input type="hidden"&gt;
- &lt;input type="image"&gt;
- &lt;input type="month"&gt;
- &lt;input type="number"&gt;
- &lt;input type="password"&gt;
- &lt;input type="radio"&gt;
- &lt;input type="range"&gt;
- &lt;input type="reset"&gt;
- &lt;input type="search"&gt;
- &lt;input type="submit"&gt;
- &lt;input type="tel"&gt;
- &lt;input type="text"&gt; (default value)
- &lt;input type="time"&gt;
- &lt;input type="url"&gt;
- &lt;input type="week"&gt;

Attributes

| **Attribute** | **Value** | **Description** |
| --- | --- | --- |
| [accept](https://www.w3schools.com/tags/att_input_accept.asp) | _file_extension_  <br>audio/\*  <br>video/\*  <br>image/\*  <br>_media_type_ | Specifies a filter for what file types the user can pick from the file input dialog box (only for type="file") |
| [alt](https://www.w3schools.com/tags/att_input_alt.asp) | _text_ | Specifies an alternate text for images (only for type="image") |
| [autocomplete](https://www.w3schools.com/tags/att_input_autocomplete.asp) | on  <br>off | Specifies whether an &lt;input&gt; element should have autocomplete enabled |
| [autofocus](https://www.w3schools.com/tags/att_input_autofocus.asp) | autofocus | Specifies that an &lt;input&gt; element should automatically get focus when the page loads |
| [checked](https://www.w3schools.com/tags/att_input_checked.asp) | checked | Specifies that an &lt;input&gt; element should be pre-selected when the page loads (for type="checkbox" or type="radio") |
| [dirname](https://www.w3schools.com/tags/att_input_dirname.asp) | _inputname_.dir | Specifies that the text direction will be submitted |
| [disabled](https://www.w3schools.com/tags/att_input_disabled.asp) | disabled | Specifies that an &lt;input&gt; element should be disabled |
| [form](https://www.w3schools.com/tags/att_input_form.asp) | _form_id_ | Specifies the form the &lt;input&gt; element belongs to |
| [formaction](https://www.w3schools.com/tags/att_input_formaction.asp) | _URL_ | Specifies the URL of the file that will process the input control when the form is submitted (for type="submit" and type="image") |
| [formenctype](https://www.w3schools.com/tags/att_input_formenctype.asp) | application/x-www-form-urlencoded  <br>multipart/form-data  <br>text/plain | Specifies how the form-data should be encoded when submitting it to the server (for type="submit" and type="image") |
| [formmethod](https://www.w3schools.com/tags/att_input_formmethod.asp) | get  <br>post | Defines the HTTP method for sending data to the action URL (for type="submit" and type="image") |
| [formnovalidate](https://www.w3schools.com/tags/att_input_formnovalidate.asp) | formnovalidate | Defines that form elements should not be validated when submitted |
| [formtarget](https://www.w3schools.com/tags/att_input_formtarget.asp) | \_blank  <br>\_self  <br>\_parent  <br>\_top  <br>_framename_ | Specifies where to display the response that is received after submitting the form (for type="submit" and type="image") |
| [height](https://www.w3schools.com/tags/att_input_height.asp) | _pixels_ | Specifies the height of an &lt;input&gt; element (only for type="image") |
| [list](https://www.w3schools.com/tags/att_input_list.asp) | _datalist_id_ | Refers to a &lt;datalist&gt; element that contains pre-defined options for an &lt;input&gt; element |
| [max](https://www.w3schools.com/tags/att_input_max.asp) | _number  <br>date_ | Specifies the maximum value for an &lt;input&gt; element |
| [maxlength](https://www.w3schools.com/tags/att_input_maxlength.asp) | _number_ | Specifies the maximum number of characters allowed in an &lt;input&gt; element |
| [min](https://www.w3schools.com/tags/att_input_min.asp) | _number  <br>date_ | Specifies a minimum value for an &lt;input&gt; element |
| [minlength](https://www.w3schools.com/tags/att_input_minlength.asp) | _number_ | Specifies the minimum number of characters required in an &lt;input&gt; element |
| [multiple](https://www.w3schools.com/tags/att_input_multiple.asp) | multiple | Specifies that a user can enter more than one value in an &lt;input&gt; element |
| [name](https://www.w3schools.com/tags/att_input_name.asp) | _text_ | Specifies the name of an &lt;input&gt; element |
| [pattern](https://www.w3schools.com/tags/att_input_pattern.asp) | _regexp_ | Specifies a regular expression that an &lt;input&gt; element's value is checked against |
| [placeholder](https://www.w3schools.com/tags/att_input_placeholder.asp) | _text_ | Specifies a short hint that describes the expected value of an &lt;input&gt; element |
| [popovertarget](https://www.w3schools.com/tags/att_input_popovertarget.asp) | _element_id_ | Specifies which popover element to invoke (only for type="button") |
| [popovertargetaction](https://www.w3schools.com/tags/att_input_popovertargetaction.asp) | hide  <br>show  <br>toggle | Specifies what happens to the popover element when you click the button (only for type="button") |
| [readonly](https://www.w3schools.com/tags/att_input_readonly.asp) | readonly | Specifies that an input field is read-only |
| [required](https://www.w3schools.com/tags/att_input_required.asp) | required | Specifies that an input field must be filled out before submitting the form |
| [size](https://www.w3schools.com/tags/att_input_size.asp) | _number_ | Specifies the width, in characters, of an &lt;input&gt; element |
| [src](https://www.w3schools.com/tags/att_input_src.asp) | _URL_ | Specifies the URL of the image to use as a submit button (only for type="image") |
| [step](https://www.w3schools.com/tags/att_input_step.asp) | _number  <br>_any | Specifies the interval between legal numbers in an input field |
| [type](https://www.w3schools.com/tags/att_input_type.asp) | button  <br>checkbox  <br>color  <br>date  <br>datetime-local  <br>email  <br>file  <br>hidden  <br>image  <br>month  <br>number  <br>password  <br>radio  <br>range  <br>reset  <br>search  <br>submit  <br>tel  <br>text  <br>time  <br>url  <br>week | Specifies the type &lt;input&gt; element to display |
| [value](https://www.w3schools.com/tags/att_input_value.asp) | _text_ | Specifies the value of an &lt;input&gt; element |
| [width](https://www.w3schools.com/tags/att_input_width.asp) | _pixels_ | Specifies the width of an &lt;input&gt; element (only for type="image") |

AI Generated README.md.  
<br/>**\# Pydantic Forms**

A powerful, flexible Python library for automatically generating beautiful HTML forms from Pydantic models and manual form definitions. Supports multiple UI frameworks including Bootstrap, Material Design, and shadcn/ui with built-in validation, accessibility features, and HTMX integration.

**\## Overview**

Pydantic Forms bridges the gap between your data models and user interfaces by automatically generating forms with minimal code. Whether you're building a simple contact form or a complex multi-step wizard, this library handles the heavy lifting while giving you complete control over styling and behavior.

**\### Key Features**

\- **\*\*🚀 Zero-Configuration Forms\*\***: Generate complete HTML forms directly from Pydantic models

\- **\*\*🎨 Multi-Framework Support\*\***: Bootstrap 5, Material Design, shadcn/ui, and extensible for custom frameworks

\- **\*\*✅ Built-in Validation\*\***: Client and server-side validation with real-time feedback

\- **\*\*♿ Accessibility First\*\***: ARIA labels, keyboard navigation, and screen reader support

\- **\*\*🔧 Highly Customizable\*\***: Override any aspect of form generation and styling

\- **\*\*📱 Responsive Design\*\***: Mobile-friendly forms that work across all devices

\- **\*\*⚡ HTMX Integration\*\***: Modern, dynamic form interactions without JavaScript frameworks

\- **\*\*🎯 Type Safety\*\***: Full type hints and IDE support throughout

**\### Use Cases**

\- **\*\*Web Applications\*\***: Rapid form development for Flask, FastAPI, Django applications

\- **\*\*Admin Interfaces\*\***: Auto-generated CRUD forms from your data models

\- **\*\*API Documentation\*\***: Interactive forms for testing API endpoints

\- **\*\*Prototyping\*\***: Quick form mockups and demos

\- **\*\*Data Collection\*\***: Surveys, feedback forms, registration pages

**\### Quick Start Example**

\`\`\`python

from flask import Flask, make_response

from pydantic import BaseModel, Field

from pydantic_forms import FormRenderer

app = Flask(\__name_\_)

\# Define your data model

class UserForm(BaseModel):

&nbsp;   username: str = Field(..., min_length=3, description="Choose a username")

&nbsp;   email: str = Field(..., description="Your email address")

&nbsp;   age: int = Field(..., ge=13, le=120, description="Your age")

\# Generate the form with one line

renderer = FormRenderer()

@app.route("/form")

def show_form():

&nbsp;   return renderer.render_form_from_pydantic(UserForm, framework="bootstrap")

\`\`\`

That's it! You now have a fully functional, validated, accessible form.

\---

**\## Installation**

\`\`\`bash

pip install pydantic-forms

\`\`\`

**\### Development Installation**

\`\`\`bash

git clone <https://github.com/devsetgo/pydantic-forms.git>

cd pydantic-forms

pip install -e .

\`\`\`

**\### Requirements**

\- Python 3.8+

\- Pydantic 2.0+

\- Flask (for web framework integration)

\---

**\## Core Components**

**\### FormRenderer**

The main class responsible for rendering forms from Pydantic models or manual definitions.

**\#### Constructor**

\`\`\`python

FormRenderer(framework: str = "bootstrap")

\`\`\`

**\*\*Parameters:\*\***

\- \`framework\` (str): UI framework to use ("bootstrap", "material", "shadcn")

**\#### Methods**

**\##### \`render_form_from_pydantic()\`**

Automatically generates a complete HTML form from a Pydantic model.

\`\`\`python

def render_form_from_pydantic(

&nbsp;   model_cls: Type\[BaseModel\],

&nbsp;   framework: str = "bootstrap",

&nbsp;   title: Optional\[str\] = None,

&nbsp;   submit_url: str = "/submit",

&nbsp;   form_data: Optional\[Dict\[str, Any\]\] = None

) -> str:

\`\`\`

**\*\*Parameters:\*\***

\- \`model_cls\`: The Pydantic model class to generate the form from

\- \`framework\`: UI framework ("bootstrap", "material", "shadcn")

\- \`title\`: Form title (defaults to model class name)

\- \`submit_url\`: URL to submit form data to

\- \`form_data\`: Pre-populate form with this data

**\*\*Returns:\*\*** Complete HTML page with the form

**\*\*Example:\*\***

\`\`\`python

class ContactForm(BaseModel):

&nbsp;   name: str = Field(..., min_length=2)

&nbsp;   email: str = Field(...)

&nbsp;   message: str = Field(..., min_length=10)

renderer = FormRenderer("bootstrap")

html = renderer.render_form_from_pydantic(

&nbsp;   ContactForm,

&nbsp;   title="Contact Us",

&nbsp;   submit_url="/contact"

)

\`\`\`

**\##### \`render_complete_form()\`**

Renders a form from a manual FormDefinition object.

\`\`\`python

def render_complete_form(form_def: FormDefinition) -> str:

\`\`\`

**\*\*Parameters:\*\***

\- \`form_def\`: FormDefinition object containing fields and configuration

**\*\*Returns:\*\*** Complete HTML page with the form

\---

**\### FormDefinition**

Represents a complete form configuration for manual form building.

**\#### Constructor**

\`\`\`python

FormDefinition(

&nbsp;   title: str = "Form",

&nbsp;   fields: Optional\[List\[FormField\]\] = None,

&nbsp;   submit_url: str = "/submit",

&nbsp;   method: str = "POST",

&nbsp;   css_framework: str = "bootstrap"

)

\`\`\`

**\*\*Parameters:\*\***

\- \`title\`: Form title displayed to users

\- \`fields\`: List of FormField objects

\- \`submit_url\`: URL to submit form data to

\- \`method\`: HTTP method ("POST", "GET")

\- \`css_framework\`: UI framework to use

**\*\*Example:\*\***

\`\`\`python

form_def = FormDefinition(

&nbsp;   title="User Registration",

&nbsp;   fields=\[

&nbsp;       FormField("username", "text", required=True),

&nbsp;       FormField("email", "email", required=True),

&nbsp;       FormField("age", "number", min=13, max=120)

&nbsp;   \],

&nbsp;   submit_url="/register"

)

\`\`\`

\---

**\### FormField**

Represents a single form field with all its configuration options.

**\#### Constructor**

\`\`\`python

FormField(

&nbsp;   name: str,

&nbsp;   field_type: str = "text",

&nbsp;   label: Optional\[str\] = None,

&nbsp;   required: bool = False,

&nbsp;   placeholder: Optional\[str\] = None,

&nbsp;   value: Any = None,

&nbsp;   options: Optional\[List\[Dict\[str, Any\]\]\] = None,

&nbsp;   \*\*kwargs

)

\`\`\`

**\*\*Parameters:\*\***

\- \`name\`: Field name (used in form submission)

\- \`field_type\`: Type of input field (see Field Types section)

\- \`label\`: Display label (auto-generated from name if not provided)

\- \`required\`: Whether field is required

\- \`placeholder\`: Placeholder text

\- \`value\`: Default/pre-filled value

\- \`options\`: For select/radio fields, list of options

\- \`\*\*kwargs\`: Additional HTML attributes

**\*\*Field Types:\*\***

\- \`text\`: Standard text input

\- \`password\`: Password input (masked)

\- \`email\`: Email input with validation

\- \`number\`: Numeric input with min/max

\- \`checkbox\`: Checkbox input

\- \`radio\`: Radio button group

\- \`select\`: Dropdown select

\- \`textarea\`: Multi-line text area

\- \`date\`: Date picker

\- \`datetime\`: Date and time picker

\- \`file\`: File upload

\- \`color\`: Color picker

\- \`range\`: Range slider

\- \`url\`: URL input with validation

\- \`phone\`: Phone number input

\- \`ssn\`: Social Security Number input

\- \`currency\`: Currency input

\- \`credit_card\`: Credit card number input

\- \`hidden\`: Hidden field

**\*\*Example:\*\***

\`\`\`python

\# Text field with validation

username_field = FormField(

&nbsp;   name="username",

&nbsp;   field_type="text",

&nbsp;   label="Username",

&nbsp;   required=True,

&nbsp;   placeholder="Enter your username",

&nbsp;   minlength=3,

&nbsp;   maxlength=20

)

\# Select field with options

country_field = FormField(

&nbsp;   name="country",

&nbsp;   field_type="select",

&nbsp;   label="Country",

&nbsp;   required=True,

&nbsp;   options=\[

&nbsp;       {"value": "us", "label": "United States", "selected": True},

&nbsp;       {"value": "ca", "label": "Canada"},

&nbsp;       {"value": "uk", "label": "United Kingdom"}

&nbsp;   \]

)

\# Radio button group

gender_field = FormField(

&nbsp;   name="gender",

&nbsp;   field_type="radio",

&nbsp;   label="Gender",

&nbsp;   options=\[

&nbsp;       {"value": "male", "label": "Male"},

&nbsp;       {"value": "female", "label": "Female"},

&nbsp;       {"value": "other", "label": "Other"}

&nbsp;   \]

)

\`\`\`

\---

**\## UI Elements**

Low-level form input components that can be used directly for maximum customization.

**\### Available Components**

All UI elements inherit from a common base and provide a \`render(\*\*kwargs)\` method:

**\#### Text Inputs**

\- \`TextInput\`: Standard text input

\- \`PasswordInput\`: Password input with masking

\- \`EmailInput\`: Email validation input

\- \`TextArea\`: Multi-line text input

**\#### Numeric Inputs**

\- \`NumberInput\`: Numeric input with step controls

\- \`RangeInput\`: Range slider

\- \`CurrencyInput\`: Currency formatted input

**\#### Selection Inputs**

\- \`SelectInput\`: Dropdown selection

\- \`RadioGroup\`: Radio button group

\- \`CheckboxInput\`: Single checkbox

**\#### Date/Time Inputs**

\- \`DateInput\`: Date picker

\- \`DatetimeInput\`: Date and time picker

**\#### Specialized Inputs**

\- \`FileInput\`: File upload

\- \`ColorInput\`: Color picker

\- \`URLInput\`: URL validation input

\- \`PhoneInput\`: Phone number input

\- \`SSNInput\`: Social Security Number input

\- \`CreditCardInput\`: Credit card input

\- \`HiddenInput\`: Hidden field

**\#### Usage Example**

\`\`\`python

from pydantic_forms.ui_elements import TextInput, EmailInput, SelectInput

\# Manual field rendering

text_field = TextInput().render(

&nbsp;   name="username",

&nbsp;   id_="username",

&nbsp;   class_="form-control",

&nbsp;   required="required",

&nbsp;   placeholder="Enter username"

)

email_field = EmailInput().render(

&nbsp;   name="email",

&nbsp;   id_="email",

&nbsp;   class_="form-control",

&nbsp;   required="required",

&nbsp;   value="<user@example.com>"

)

select_field = SelectInput().render(

&nbsp;   name="country",

&nbsp;   id_="country",

&nbsp;   class_="form-select",

&nbsp;   option_named=\[

&nbsp;       {"value": "us", "label": "United States", "selected": True},

&nbsp;       {"value": "ca", "label": "Canada"}

&nbsp;   \]

)

\`\`\`

\---

**\## Framework Support**

**\### Bootstrap 5**

Full support for Bootstrap 5 components and styling.

**\*\*Features:\*\***

\- Form validation states

\- Input groups and sizing

\- Custom form controls

\- Grid system integration

**\*\*CSS Classes Used:\*\***

\- \`form-control\`: Text inputs, selects, textareas

\- \`form-select\`: Select dropdowns

\- \`form-check-input\`: Checkboxes and radios

\- \`btn btn-primary\`: Submit buttons

**\### Material Design**

Integration with Materialize CSS framework.

**\*\*Features:\*\***

\- Material Design form styling

\- Floating labels

\- Material icons support

\- Ripple effects

**\*\*CSS Classes Used:\*\***

\- \`validate\`: Input validation

\- \`browser-default\`: Select styling

\- \`btn waves-effect\`: Buttons with ripple

**\### shadcn/ui**

Modern design system built on Tailwind CSS.

**\## Advanced Features**

**\### Form Validation**

**\#### Client-Side Validation**

All forms include built-in HTML5 validation with enhanced JavaScript:

\- Real-time validation feedback

\- Custom error messages

\- Accessibility-compliant error handling

\- Prevent submission of invalid forms

**\#### Server-Side Integration**

\`\`\`python

from pydantic_forms.schema_form import FormModel

from pydantic_forms.render_form import SchemaFormValidationError

class UserForm(FormModel):

&nbsp;   username: str = Field(..., min_length=3)

&nbsp;   email: str = Field(...)

\# In your route handler

@app.route("/submit", methods=\["POST"\])

def handle_submit():

&nbsp;   try:

&nbsp;       form_data = UserForm(\*\*request.form)

&nbsp;       # Process valid data

&nbsp;       return "Success!"

&nbsp;   except ValidationError as e:

&nbsp;       # Handle validation errors

&nbsp;       errors = {error\['loc'\]\[0\]: error\['msg'\] for error in e.errors()}

&nbsp;       return render_form_with_errors(errors)

\`\`\`

**\### HTMX Integration**

All forms include HTMX for modern, dynamic interactions:

\`\`\`html

&lt;form hx-post="/submit" hx-target="#result" hx-swap="innerHTML"&gt;

&nbsp;   &lt;!-- Form fields --&gt;

&lt;/form&gt;

&lt;div id="result"&gt;&lt;/div&gt;

\`\`\`

**\### Accessibility Features**

\- **\*\*ARIA Labels\*\***: Automatic aria-label and aria-describedby attributes

\- **\*\*Keyboard Navigation\*\***: Full keyboard accessibility

\- **\*\*Screen Reader Support\*\***: Semantic HTML and proper labeling

\- **\*\*Focus Management\*\***: Logical tab order and focus indicators

\- **\*\*Error Announcements\*\***: Screen reader compatible error messages

**\### File Upload Handling**

\`\`\`python

file_field = FormField(

&nbsp;   name="resume",

&nbsp;   field_type="file",

&nbsp;   label="Resume",

&nbsp;   accept=".pdf,.docx",

&nbsp;   multiple=True,

&nbsp;   required=True

)

\`\`\`

The library handles file metadata display and validation automatically.

\---

**\## Examples**

**\### Complete Flask Application**

\`\`\`python

from flask import Flask, make_response, request

from pydantic import BaseModel, Field, ValidationError

from pydantic_forms import FormRenderer

app = Flask(\__name_\_)

renderer = FormRenderer()

class ContactForm(BaseModel):

&nbsp;   name: str = Field(..., min_length=2, description="Your full name")

&nbsp;   email: str = Field(..., description="Your email address")

&nbsp;   subject: str = Field(..., min_length=5, description="Message subject")

&nbsp;   message: str = Field(..., min_length=10, description="Your message")

&nbsp;   urgent: bool = Field(False, description="Mark as urgent")

@app.route("/contact", methods=\["GET"\])

def contact_form():

&nbsp;   return renderer.render_form_from_pydantic(

&nbsp;       ContactForm,

&nbsp;       framework="bootstrap",

&nbsp;       title="Contact Us",

&nbsp;       submit_url="/contact"

&nbsp;   )

@app.route("/contact", methods=\["POST"\])

def handle_contact():

&nbsp;   try:

&nbsp;       form_data = ContactForm(\*\*request.form)

&nbsp;       # Process the valid form data

&nbsp;       # send_email(form_data)

&nbsp;       return "Thank you for your message!"

&nbsp;   except ValidationError as e:

&nbsp;       # Re-render form with errors

&nbsp;       errors = {error\['loc'\]\[0\]: error\['msg'\] for error in e.errors()}

&nbsp;       return renderer.render_form_from_pydantic(

&nbsp;           ContactForm,

&nbsp;           framework="bootstrap",

&nbsp;           title="Contact Us",

&nbsp;           form_data=request.form,

&nbsp;           errors=errors

&nbsp;       )

if \__name__ == "\__main_\_":

&nbsp;   app.run(debug=True)

\`\`\`

**\### Manual Form Definition**

\`\`\`python

from pydantic_forms import FormDefinition, FormField, FormRenderer

\# Create form manually

registration_form = FormDefinition(

&nbsp;   title="User Registration",

&nbsp;   fields=\[

&nbsp;       FormField("username", "text", "Username", required=True,

&nbsp;                placeholder="Choose a username", minlength=3),

&nbsp;       FormField("email", "email", "Email Address", required=True,

&nbsp;                placeholder="<your@email.com>"),

&nbsp;       FormField("password", "password", "Password", required=True,

&nbsp;                minlength=8),

&nbsp;       FormField("age", "number", "Age", required=True,

&nbsp;                min=13, max=120, step=1),

&nbsp;       FormField("country", "select", "Country", required=True,

&nbsp;                options=\[

&nbsp;                    {"value": "us", "label": "United States"},

&nbsp;                    {"value": "ca", "label": "Canada"},

&nbsp;                    {"value": "uk", "label": "United Kingdom"}

&nbsp;                \]),

&nbsp;       FormField("newsletter", "checkbox", "Subscribe to Newsletter",

&nbsp;                value=True),

&nbsp;       FormField("gender", "radio", "Gender", options=\[

&nbsp;           {"value": "male", "label": "Male"},

&nbsp;           {"value": "female", "label": "Female"},

&nbsp;           {"value": "other", "label": "Prefer not to say"}

&nbsp;       \])

&nbsp;   \],

&nbsp;   submit_url="/register",

&nbsp;   css_framework="bootstrap"

)

renderer = FormRenderer("bootstrap")

html = renderer.render_complete_form(registration_form)

\`\`\`

\---

**\## API Reference**

**\### Utility Functions**

**\#### \`create_demo_form()\`**

Creates a demonstration form with various field types for testing and examples.

\`\`\`python

def create_demo_form() -> FormDefinition:

\`\`\`

**\*\*Returns:\*\*** FormDefinition with sample fields

**\*\*Usage:\*\***

\`\`\`python

from pydantic_forms import create_demo_form, FormRenderer

demo_form = create_demo_form()

renderer = FormRenderer("material")

html = renderer.render_complete_form(demo_form)

\`\`\`

**\### Schema Integration**

**\#### \`FormModel\`**

Base class for Pydantic models with form-specific enhancements.

\`\`\`python

class FormModel(BaseModel):

&nbsp;   @classmethod

&nbsp;   def get_json_schema(cls) -> Dict\[str, Any\]:

&nbsp;       """Get simplified JSON schema for form rendering."""

&nbsp;

&nbsp;   @classmethod  

&nbsp;   def get_example_form_data(cls) -> dict:

&nbsp;       """Generate example form data for testing."""

\`\`\`

**\#### \`render_form_html()\`**

Low-level function for rendering forms from FormModel classes.

\`\`\`python

def render_form_html(

&nbsp;   form_model_cls: Type\[FormModel\],

&nbsp;   form_data: Optional\[Dict\[str, Any\]\] = None,

&nbsp;   errors: Optional\[Dict\[str, str\]\] = None,

&nbsp;   htmx_post_url: str = "/submit",

) -> str:

\`\`\`