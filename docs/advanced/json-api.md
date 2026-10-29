# JSON API and JSON Schema

A `FormModel` is a Pydantic model, so the same class can validate an HTML
form and a JSON API request, with the same rules and the same error shape.

## One model, two routes

```python title="models.py"
--8<-- "docs_src/advanced/json_api/models.py"
```

=== "FastAPI"

    ```python title="main.py" hl_lines="7 25-27"
    --8<-- "docs_src/advanced/json_api/fastapi_app.py"
    ```

    **`ContactForm.as_api_model()`** returns a plain Pydantic model with the
    same fields and the same validation (`min_length`, `title`, `examples`,
    ...), but without the form settings such as `ui_element` and
    `ui_autofocus`. Use it as the request body or `response_model`, and
    FastAPI's OpenAPI docs show a clean schema, exactly as for a model written
    by hand. Create it once, at import time.

=== "Flask"

    ```python title="main.py" hl_lines="23-28"
    --8<-- "docs_src/advanced/json_api/flask_app.py"
    ```

    **`validate()` takes a JSON body as well as a form.** Give it the parsed
    JSON (a nested dict) and it returns the same `ValidationResult`, so the
    API route can answer with `result.errors`, nested like the data, and a
    422 status.

## JSON Schema for other tools

`get_pydantic_json_schema()` returns the standard JSON Schema of the form,
with nested sub-forms as `$defs` and `$ref`, for OpenAPI tooling, schema
validators or code generators. Like `as_api_model()`, it leaves out the form
settings. Pydantic's own options pass through:

```python
--8<-- "docs_src/advanced/json_api/schema.py"
```

??? note "`get_json_schema()`"

    `FormModel.get_json_schema()` returns the schema in the shape the form
    renderer uses internally, with the form settings included and sub-forms
    not resolved. Use `get_pydantic_json_schema()` for anything outside the
    library.
