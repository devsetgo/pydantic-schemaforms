# Pydantic SchemaForms Examples

This directory contains runnable examples that demonstrate current pydantic-schemaforms capabilities.

## Included examples

### 1) FastAPI demo (async)

Files: examples/main.py (composition root — FastAPI() construction, session
middleware, static mount, uvicorn entrypoint) and examples/fastapi_routes.py
(every route/endpoint, attached via `app.include_router(router)`).

What it demonstrates:

- Async rendering with render_form_html_async
- Multiple form routes (simple, medium, complex, nested, tabbed widget gallery)
- Dual-use FormModels serving both an HTML form and a typed JSON API
  (`/contact`, `/feedback`) via `as_api_model()`
- Live HTMX field validation (`/live-validation`, `/email-dns-validation`)
- CSRF token issue/verify flow for browser forms
- Style switching (`bootstrap`, `material`, `none`)
- Self-contained asset mode and hosted-template mode
- JSON API endpoints for schema, render, and submission
- Request-timing middleware + `log_timing()` (Loguru-based) for diagnosing
  slow routes; vendored (not CDN) Bootstrap/HTMX assets served under `/vendor/*`

Run:

```bash
python examples/main.py
# or, from within examples/:
make ex-run
```

Then open:

- http://localhost:8000/ (links to every demo below)
- http://localhost:8000/docs

### 2) Deep nested models demo data

File: examples/nested_forms_example.py

What it demonstrates:

- Deeply nested FormModel structures
- Complex model lists and tabbed layouts
- Broad input-type coverage in nested contexts

This module is imported by the FastAPI example to generate rich nested sample payloads.

### 3) DataTableLayout — CSV import to table

Files: examples/datatable_import_example.py (routes, mounted at `/employees/*`
in main.py), examples/generate_sample_csv.py (generates the sample CSV files
it links to at 10/100/1,000/10,000 rows).

What it demonstrates:

- DataTableLayout: a FormModel subclass whose fields are table columns,
  rendered as an HTML table with a built-in CSV-import UI (file input,
  "Load CSV"/"Submit"), progressively enhanced client-side by DataTables.js
- Row-by-row server-side validation against the same Pydantic model used
  for the columns, with per-row error highlighting

Then open http://localhost:8000/employees/import.

### 4) Other reference pages

- `/gallery` (examples/shared_models.py's `WidgetGalleryForm`) — every
  registered input type, tabbed by category
- `/date-time-formats` (examples/date_time_formats_example.py) — custom
  `date_format`/`time_format`/`datetime_format` `ui_options`, as a
  copy-pasteable format-string reference
- `/input-types` (examples/input_type_reference.py) — static "every
  ui_element with a code example" cheatsheet, not wired to the renderer
- `/ai-instructions` — the packaged AI-assistant instruction files, rendered
  from Markdown

## Shared model definitions

File: examples/shared_models.py

Contains reusable FormModel classes used by the examples, including:

- MinimalLoginForm
- UserRegistrationForm
- CompleteShowcaseForm
- CompanyOrganizationForm
- LayoutDemonstrationForm
- PetRegistrationForm
- WidgetGalleryForm

## Capability notes

- The examples are model-first and use the same renderer pipeline as the library docs.
- For template rendering, pass generated form HTML into Jinja as `{{ form_html | safe }}`.
- For Python f-string HTML responses, embed `{form_html}` directly.

## Asset behavior in examples

The examples show both patterns:

- Host page provides framework assets (default integration)
- Self-contained rendering where CSS/JS are included in returned form HTML

Related docs:

- docs/assets.md
- docs/configuration.md
- docs/csrf.md

## Local verification

From repository root:

```bash
make tests
make create-docs-local
```

These commands validate code and documentation locally without publishing.
