# Pydantic SchemaForms Examples

This directory contains runnable examples that demonstrate current pydantic-schemaforms capabilities.

## Included examples

### 1) FastAPI demo (async)

File: examples/fastapi_example.py

What it demonstrates:

- Async rendering with render_form_html_async
- Multiple form routes (simple, medium, complex, nested)
- CSRF token issue/verify flow for browser forms
- Style switching (`bootstrap`, `material`, `none`)
- Self-contained asset mode and hosted-template mode
- JSON API endpoints for schema, render, and submission

Run:

```bash
python examples/fastapi_example.py
```

Then open:

- http://localhost:8000/
- http://localhost:8000/docs

### 2) Deep nested models demo data

File: examples/nested_forms_example.py

What it demonstrates:

- Deeply nested FormModel structures
- Complex model lists and tabbed layouts
- Broad input-type coverage in nested contexts

This module is imported by the FastAPI example to generate rich nested sample payloads.

## Shared model definitions

File: examples/shared_models.py

Contains reusable FormModel classes used by the examples, including:

- MinimalLoginForm
- UserRegistrationForm
- CompleteShowcaseForm
- CompanyOrganizationForm
- LayoutDemonstrationForm
- PetRegistrationForm

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
