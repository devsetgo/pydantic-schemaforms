# First Form

A form is a Pydantic model. Subclass `FormModel`, declare the fields, and
render it.

=== "FastAPI"

    ```python
    --8<-- "docs_src/tutorial/first_form/fastapi_app.py"
    ```

=== "Flask"

    ```python
    --8<-- "docs_src/tutorial/first_form/flask_app.py"
    ```

Run it and open `/signup`: you get a styled form with a "Full name" text box,
an "Email" box and a submit button.

## What's going on

**`SignupForm(FormModel)`** is an ordinary Pydantic model. `FormModel` adds
the form rendering and validation on top, so the same class can still be
used anywhere a Pydantic model can.

**`Field(title=...)`** works like Pydantic's `Field` and adds the form
settings. `title` becomes the field's label; without it the label comes from
the field name (`email` becomes "Email").

**`ui_element="email"`** picks the input type. Without it, the library picks
one from the field's type: `str` gets a text box, `bool` a checkbox, `date` a
date picker. [Fields and Inputs](fields.md) covers this in detail.

**`render_form_html_async()`** returns the form as an HTML string, including
its labels, inline validation script and the submit button. The FastAPI
example uses the async version so rendering doesn't block the event loop;
Flask uses the plain `render_form_html()`.

**`submit_url`** is required: it's where the form posts to. The library never
guesses a default.

**`include_framework_assets=True, asset_mode="cdn"`** adds the `<link>` and
`<script>` tags that load Bootstrap from a CDN, so this one string is a
working page. In a real app your page template already loads Bootstrap: drop
these two options and put the form into your template.

??? note "Putting the form in your own page template"

    `render_form_html()` returns a plain string of trusted HTML. In a Jinja
    template, mark it safe so Jinja doesn't escape it:

    ```html
    <main class="container">
      <h1>Sign up</h1>
      {{ form_html | safe }}
    </main>
    ```

    Never build the page around it with an f-string if the page also shows
    anything the user typed; see [Handling Submissions](handling-submissions.md).
    The [Jinja template recipe](../recipes/jinja-template.md) has a complete
    example.

??? note "Rendering from the model class"

    `SignupForm.render_form(submit_url="/signup")` does the same as
    `render_form_html(SignupForm, submit_url="/signup")`. The docs use
    `render_form_html()` throughout because it has an async version.

Next: [Handling Submissions](handling-submissions.md).
