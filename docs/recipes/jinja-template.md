# Embedding in a Jinja Template

Real pages have a layout, navigation and their own messages. Render the form
to a string and put it into your template.

```html title="templates/signup.html"
--8<-- "docs_src/recipes/jinja_template/templates/signup.html"
```

```python title="models.py"
--8<-- "docs_src/recipes/jinja_template/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/jinja_template/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/jinja_template/flask_app.py"
    ```

## How it works

- **`{{ form_html | safe }}`** inserts the form. The form is HTML the library
  built and escaped itself, so it must not be escaped again.
- **Everything else stays escaped.** `{{ name }}` is the user's input, and
  Jinja escapes it as usual. Only ever mark the library's output as `safe`.
- **The template loads Bootstrap**, so the form is rendered without
  `include_framework_assets`. Load the same framework you render with; see
  [Styling](../tutorial/styling.md).
- **A failed submit answers 422** with the form and its errors, inside the
  same page.
