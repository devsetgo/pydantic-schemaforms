# PySchemaForms Tutorial: Your First Dynamic Web Form

Welcome to PySchemaForms! This tutorial will guide you through creating your first dynamic web form from scratch. We'll explain every step in detail, so don't worry if you're new to web forms or Python web development.

## What You'll Learn

By the end of this tutorial, you'll understand:
- How to create a basic web form using PySchemaForms
- What each line of code does and why it's important
- How forms work in web applications
- How to handle user input safely

## What You Need Before Starting

Before we begin, make sure you have:
- **Python 3.14 or newer** installed on your computer
- **Basic Python knowledge** (variables, functions, imports)
- **A text editor** (VS Code, PyCharm, or even Notepad++)
- **5-10 minutes** of your time

You don't need to know Flask or web development - we'll explain everything!

## Step 1: Understanding Web Forms

Before we write code, let's understand what we're building. A web form is like a digital questionnaire that:
1. **Shows input fields** to users (text boxes, buttons, etc.)
2. **Collects information** when users type or click
3. **Sends data** to your Python program when submitted
4. **Processes the data** (save to database, send email, etc.)

Think of it like a restaurant order form - customers fill it out, and the kitchen receives the order details.

## Step 2: Install PySchemaForms

First, we need to install the required packages. Open your terminal or command prompt and run:

```bash
pip install Flask PySchemaForms
```

**What this does:**
- **Flask**: A web framework that handles web requests and responses
- **PySchemaForms**: Our library that makes creating forms super easy

## Step 3: Create Your First File

Create a new file called `my_first_form.py` and save it in a folder on your computer. This will contain all our code.

## Step 4: Build Your First Form (Line by Line)

Copy this code into your `my_first_form.py` file. We'll explain every single line:

```python
# Import the tools we need
from flask import Flask, render_template_string, request
from pydantic_schemaforms import FormBuilder

# Create a Flask web application
app = Flask(__name__)

# Define what happens when someone visits our website
@app.route("/", methods=["GET", "POST"])
def hello_form():
    # Check if someone submitted the form
    if request.method == "POST":
        # Get the name they typed and display it
        user_name = request.form['name']
        return f"<h1>Hello {user_name}! Nice to meet you!</h1>"

    # If they haven't submitted yet, show the form
    # Build a simple form with one text input
    form = FormBuilder().text_input("name", "What's your name?").render()

    # Create a complete HTML page with our form
    html_page = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My First Form</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Welcome to My First Form!</h1>
            <p>Please tell us your name:</p>
            {{ form | safe }}
        </div>
    </body>
    </html>
    """

    return render_template_string(html_page, form=form)

# Start the web server
if __name__ == "__main__":
    app.run(debug=True)
```

**Let's break down what each part does:**

### Line 1-2: Import Statements
```python
from flask import Flask, render_template_string, request
from pydantic_schemaforms import FormBuilder
```
**What this does:** Brings in the tools we need
- `Flask`: Creates our web application
- `render_template_string`: Converts our HTML template into a webpage
- `request`: Handles data coming from the form
- `FormBuilder`: Our magic tool for creating forms easily

### Line 4-5: Create the Web App
```python
app = Flask(__name__)
```
**What this does:** Creates a new web application. Think of this as opening a new restaurant - you now have a place where customers (users) can visit.

### Line 7-8: Define the Route
```python
@app.route("/", methods=["GET", "POST"])
def hello_form():
```
**What this does:**
- `@app.route("/")`: Says "when someone visits the main page of our website, run this function"
- `methods=["GET", "POST"]`: Allows both viewing the page (GET) and submitting forms (POST)
- `def hello_form():`: Creates a function that handles both showing and processing our form

### Line 9-12: Handle Form Submission
```python
if request.method == "POST":
    user_name = request.form['name']
    return f"<h1>Hello {user_name}! Nice to meet you!</h1>"
```
**What this does:**
- `if request.method == "POST":`: Checks if someone just submitted the form
- `user_name = request.form['name']`: Gets the text they typed in the "name" field
- `return f"<h1>Hello {user_name}!...`: Shows a personalized greeting with their name

### Line 14-16: Create the Form
```python
form = FormBuilder().text_input("name", "What's your name?").render()
```
**What this does (this is the magic!):**
- `FormBuilder()`: Creates a new form builder (like getting a blank form template)
- `.text_input("name", "What's your name?")`: Adds a text input field
  - `"name"`: The internal name for this field (how we'll reference it later)
  - `"What's your name?"`: The label users will see
- `.render()`: Converts our form description into actual HTML code

### Line 18-32: Create the Webpage
```python
html_page = """
<!DOCTYPE html>
<html>
...
{{ form | safe }}
...
"""
```
**What this does:**
- Creates a complete HTML webpage
- `{{ form | safe }}`: Inserts our form into the page
- The Bootstrap CSS makes everything look modern and professional

### Line 34: Return the Page
```python
return render_template_string(html_page, form=form)
```
**What this does:** Combines our HTML template with our form and sends it to the user's browser

### Line 36-38: Start the Server
```python
if __name__ == "__main__":
    app.run(debug=True)
```
**What this does:**
- Starts a web server on your computer
- `debug=True`: Shows helpful error messages if something goes wrong

## Step 5: Run Your Form

1. Save your `my_first_form.py` file
2. Open terminal/command prompt in the same folder
3. Run: `python my_first_form.py`
4. You'll see output like: `Running on http://127.0.0.1:5000`
5. Open your web browser and go to: `http://127.0.0.1:5000`

**Congratulations!** You just created your first web form! 🎉

## Step 6: Test Your Form

1. **View the form**: You should see a text input asking for your name
2. **Type your name**: Enter your name in the text field
3. **Submit**: Click the submit button
4. **See the result**: You should see a personalized greeting!

## What Just Happened?

When you submitted the form:
1. Your browser sent your name to your Python program
2. Your program received it in the `request.form['name']` variable
3. Your program created a new webpage with your name in it
4. Your browser displayed the greeting

This is the basic cycle of all web forms!

## Step 7: Understanding the FormBuilder Magic

The real magic happens in this line:
```python
form = FormBuilder().text_input("name", "What's your name?").render()
```

**Behind the scenes, this creates HTML like:**
```html
<form method="POST">
    <div class="mb-3">
        <label for="name" class="form-label">What's your name?</label>
        <input type="text" class="form-control" id="name" name="name">
    </div>
    <button type="submit" class="btn btn-primary">Submit</button>
</form>
```

But you don't have to write all that HTML yourself - PySchemaForms does it for you!

## Step 8: Add More Fields (Optional Challenge)

Try modifying your form to ask for more information:

```python
form = (FormBuilder()
        .text_input("name", "What's your name?")
        .text_input("city", "What city are you from?")
        .number_input("age", "How old are you?")
        .render())
```

Then update your greeting to use all the information:
```python
if request.method == "POST":
    name = request.form['name']
    city = request.form['city']
    age = request.form['age']
    return f"<h1>Hello {name}!</h1><p>It's nice to meet someone from {city} who is {age} years old!</p>"
```

## Bonus: Compose Layouts with LayoutComposer

Once you are comfortable rendering a single form, you can arrange multiple snippets with the **LayoutComposer** API. This is the single public entry point for layout primitives and it lives next to the renderer internals.

```python
from pydantic_schemaforms import FormBuilder
from pydantic_schemaforms.rendering.layout_engine import LayoutComposer

contact_form = (FormBuilder()
                .text_input("name", "What's your name?")
                .email_input("email", "Where can we reach you?")
                .render())

profile_card = LayoutComposer.card("Profile", contact_form)
settings_card = LayoutComposer.card("Settings", "<p>Coming soon...</p>")

two_column_layout = LayoutComposer.horizontal(
    profile_card,
    settings_card,
    gap="2rem",
    justify_content="space-between",
)

html = two_column_layout.render()
```

Every helper inside `LayoutComposer` returns a `BaseLayout` subclass, so you can freely nest them (e.g., a vertical stack of cards that contain grids). The legacy `pydantic_schemaforms.layouts` and `pydantic_schemaforms.form_layouts` modules now emit `DeprecationWarning`s and simply re-export this API for backward compatibility.

## Theme Hooks for Tabs, Accordions, and Model Lists

The renderers no longer embed framework-specific HTML in random places. Instead, `RendererTheme` exposes hook methods so you can replace the shared assets in one spot:

- `tab_component_assets()` and `accordion_component_assets()` return the CSS/JS that power tab/accordion interactions. The default implementation ships with Bootstrap-flavored styling, while `MaterialEmbeddedTheme` overrides both to emit Material Design tokens.
- `render_layout_section()` controls how layout cards/tabs are wrapped, replacing the inline `CardLayout` markup when a theme wants its own chrome.
- `render_model_list_container()` owns the wrapper for schema-driven and class-based `ModelListRenderer` instances (labels, help/error text, add buttons, etc.). Bootstrap/Material both call through this hook now, so future frameworks only need to provide a theme—not duplicate renderer code.
- `render_model_list_item()` owns the per-item chrome (card header, remove buttons, data attributes) for both schema-driven and imperative model lists. The renderer builds the inner field grid and hands the HTML off to this hook so your theme fully owns the markup users interact with.

Creating a custom theme is straightforward:

```python
from pydantic_schemaforms.enhanced_renderer import EnhancedFormRenderer
from pydantic_schemaforms.rendering.themes import RendererTheme


class ShadcnTheme(RendererTheme):
    name = "shadcn"

    def tab_component_assets(self) -> str:
        return """<script>/* shadcn tab switching */</script><style>.tab-button{font-family:var(--font-sans);}</style>"""

    def render_model_list_container(self, **kwargs) -> str:
        items_html = kwargs["items_html"] or ""
        return f"""
        <section class="shadcn-card">
            <div class="shadcn-card__header">
                <h3>{kwargs['label']}</h3>
            </div>
            <div class="shadcn-card__content">{items_html}</div>
            <div class="shadcn-card__footer">
                <button class="btn" data-target="{kwargs['field_name']}">
                    {kwargs['add_button_label']}
                </button>
            </div>
        </section>
        """

    def render_model_list_item(self, **kwargs) -> str:
        body_html = kwargs["body_html"]
        label = kwargs["model_label"]
        index = kwargs["index"] + 1
        return f"""
        <article class="shadcn-model-item" data-index="{index}">
            <header class="shadcn-model-item__header">
                <h4>{label} #{index}</h4>
                <button type="button" class="ghost-btn remove-item-btn" data-index="{kwargs['index']}">
                    Remove
                </button>
            </header>
            <div class="shadcn-model-item__body">{body_html}</div>
        </article>
        """


# Inject the theme while rendering
renderer = EnhancedFormRenderer(theme=ShadcnTheme())
html = renderer.render_form_from_model(MyForm)
```

Because both `FieldRenderer` and `ModelListRenderer` read from the active theme first, this one class controls the chrome for schema-derived fields, nested layouts, and repeatable models. Tests should assert for the presence of your wrapper classes (e.g., `.shadcn-card`) to verify the integration.

## Runtime Fields and New UI Elements

Need to add fields after a form model is defined? Call `FormModel.register_field()` to describe the type and UI metadata at runtime. The helper keeps the renderer, the validation stack, and the live schema in sync:

```python
from pydantic_schemaforms.schema_form import Field, FormModel

class ProfileForm(FormModel):
    pass

ProfileForm.register_field(
    "nickname",
    annotation=str,
    field=Field(..., ui_element="text", min_length=3),
)

ProfileForm.register_field(
    "terms_accepted",
    annotation=bool,
    field=Field(False, ui_element="toggle"),
)
```

`register_field` stores the new `FieldInfo`, rebuilds the runtime validator, and clears the schema cache, so `EnhancedFormRenderer`, `validate_form_data`, and the HTMX live validator all see the same set of fields. If you prefer to continue using `setattr(MyForm, name, Field(...))`, the renderer still picks up the new entries, but validation will only engage when the helper is used.

Two new `ui_element` identifiers ship with this release:

- `"toggle"` – renders the `ToggleSwitch` wrapper and maps to a checkbox value server-side.
- `"combobox"` – renders the enhanced combo-box (text input backed by a datalist) so users can search or pick from known options.

These map directly to the corresponding input components, so you can reference them in `Field(..., ui_element="toggle")` or inside `ui_options` blocks without writing custom renderer glue.

## What You've Learned

🎯 **You now know how to:**
- Create a web application with Flask
- Build forms using PySchemaForms' FormBuilder
- Handle form submissions in Python
- Display dynamic content based on user input

🧠 **Key concepts you understand:**
- **Form fields**: Different types of inputs (text, number, etc.)
- **Form submission**: How data travels from browser to Python
- **Request handling**: How to process incoming form data
- **Template rendering**: How to create dynamic HTML pages

## What's Next?

Now that you understand the basics, you can:
- **Add validation** to make sure users enter valid data
- **Use different input types** like email, password, or dropdown menus
- **Style your forms** with different CSS frameworks
- **Connect to databases** to save form data permanently

Ready to dive deeper? Check out our [Advanced Tutorial](advanced.md) or [API Reference](api.md)!

## Troubleshooting

**Form not showing?**
- Make sure you saved the file
- Check that you're visiting the right URL (http://127.0.0.1:5000)

**Errors when running?**
- Make sure you installed Flask and PySchemaForms
- Check that your Python indentation is correct

**Form submits but no greeting?**
- Make sure the field name in `request.form['name']` matches the field name in your FormBuilder

Great job completing your first PySchemaForms tutorial! 🚀
