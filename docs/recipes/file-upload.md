# File Upload

A form with a file. The library renders the file input (with drag and drop)
and sends the form as `multipart/form-data`; your route checks and stores the
file.

```python title="models.py"
--8<-- "docs_src/recipes/file_upload/models.py"
```

=== "FastAPI"

    ```python title="main.py"
    --8<-- "docs_src/recipes/file_upload/fastapi_app.py"
    ```

=== "Flask"

    ```python title="main.py"
    --8<-- "docs_src/recipes/file_upload/flask_app.py"
    ```

## How it works

- **`ui_element="file"`** renders the file input. `accept` limits what the
  file picker offers; `multiple=True` would allow several files. A form with
  a file input gets `enctype="multipart/form-data"` by itself.
- **The field is typed `Any`**, because the uploaded file arrives as your
  framework's own object: Starlette's `UploadFile` or Werkzeug's
  `FileStorage`. Flask keeps files apart from the other fields, so the route
  combines `request.form` and `request.files` before validating.
- **`check_upload()` checks the file itself**: that one was chosen, its
  extension, and its size, reading at most one byte more than the limit. Its
  message is added to the form's errors so it shows under the file input.
- **The browser can't keep a chosen file** across a re-render, so after an
  error the user picks it again. The title is kept.

!!! warning "Treat uploads as untrusted"

    `accept` and the file name are only hints: check the content before you
    use it, store files outside your web root under names you generate, and
    never show a file name in HTML without escaping it (`html(t"...")` does).
