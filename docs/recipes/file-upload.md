# File Upload

A form with a file. The library renders the file input (with drag and drop)
and sends the form as `multipart/form-data`; the server checks its type and
size, and your route stores it.

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

- **Type the field `UploadedFile`.** It renders the file input (with drag
  and drop) by itself, and the form gets `enctype="multipart/form-data"`.
  Use `UploadedFile | None = Field(None, ...)` for an optional file, or
  `list[UploadedFile]` for several (the input gets `multiple` by itself).
- **`validate()` turns the framework's upload into an `UploadedFile`**
  (Starlette's `UploadFile`, Werkzeug's `FileStorage`). It has `filename`,
  `content_type`, `size`, `read()` and `seek()`. Flask keeps files apart
  from the other fields, so the route combines `request.form` and
  `request.files` before validating.
- **The limits are checked on the server** and their messages show under
  the file input like any other error:
    - `ui_max_size=` is a size in bytes. It is measured from the file, not
      taken from the request.
    - `ui_max_files=` caps a `list[UploadedFile]`.
    - `accept` in `ui_options` is the same rule the browser uses: a file
      matches by extension or by content type, and `image/*` works.
- **An empty file input counts as not submitted.** An optional field gets
  its default; a required one gets "Field required".
- **Set `MAX_CONTENT_LENGTH` in Flask.** It refuses an oversized request
  before it is parsed, while `ui_max_size` checks a file after it is
  received.
- **Read the file inside the request handler.** The framework closes it
  afterwards.
- **The browser can't keep a chosen file** across a re-render, so after an
  error the user picks it again. The title is kept.

!!! warning "Treat uploads as untrusted"

    `accept` is not content sniffing: the extension and the content type
    both come from the browser, as does the file name. Check the content
    before you use it, store files outside your web root under names you
    generate, and never show a file name in HTML without escaping it
    (`html(t"...")` does).
