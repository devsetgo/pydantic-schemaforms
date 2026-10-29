# Tutorial - User Guide

This tutorial builds a form step by step, from a two-field model to nested
sub-forms, layouts and CSRF protection. Each chapter builds on the one before,
so reading them in order is the fastest way to learn the library.

Every chapter shows the **recommended way** first. Alternatives, when there
are any, come in collapsed notes or in the [Advanced User Guide](../advanced/index.md).

## Install

Create a project and add pydantic-schemaforms with [uv](https://docs.astral.sh/uv/):

```bash
uv init signup-app --bare
cd signup-app
uv add "pydantic-schemaforms[fastapi]"
```

pydantic-schemaforms needs **Python 3.14 or newer**: it builds all of its HTML
with Python 3.14 template strings (t-strings), which escape every value
automatically.

??? note "Using Flask instead"

    Install the `flask` extra instead of `fastapi`:

    ```bash
    uv add "pydantic-schemaforms[flask]"
    ```

    Every example in these docs that has a route shows a **FastAPI** and a
    **Flask** tab. Pick Flask once and every example on the site switches to it.

??? note "Using pip instead"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install "pydantic-schemaforms[fastapi]"
    ```

??? note "Email fields"

    Pydantic's `EmailStr` type needs the `email-validator` package. Add the
    `email` extra if any of your forms use it:

    ```bash
    uv add "pydantic-schemaforms[fastapi,email]"
    ```

## Run the examples

Every example in the tutorial is a complete file. Save it as `main.py` and run it:

=== "FastAPI"

    ```bash
    uv run fastapi dev main.py
    ```

=== "Flask"

    ```bash
    uv run flask --app main run --debug
    ```

Then open the page the example serves, for example
<http://127.0.0.1:8000/signup> (FastAPI) or <http://127.0.0.1:5000/signup> (Flask).

The live demo at <https://pydantic-schemaforms.devsetgo.com> shows every input,
layout and validation the library supports.

## Chapters

1. [First Form](first-form.md): declare a form and render it.
2. [Handling Submissions](handling-submissions.md): validate a POST and show errors.
3. [Fields and Inputs](fields.md): titles, input types, defaults, choices.
4. [Validation](validation.md): constraints, field and form validators.
5. [Nested Forms and Lists](nested-forms.md): sub-forms and repeating items.
6. [Layouts](layouts.md): sections, tabs, accordions and a step wizard.
7. [Styling](styling.md): Bootstrap, Material or plain HTML.
8. [CSRF Protection](csrf.md): protect forms behind a login.
