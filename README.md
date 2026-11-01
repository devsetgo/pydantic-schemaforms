# Pydantic SchemaForms

<img align="right" src="https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/main/docs/pydantic-schemaform-logo.png" alt="Pydantic SchemaForms logo" width="336" />

[![PyPI version](https://badge.fury.io/py/pydantic-schemaforms.svg)](https://pypi.python.org/pypi/pydantic-schemaforms/)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms)](https://pepy.tech/project/pydantic-schemaforms)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms/month)](https://pepy.tech/project/pydantic-schemaforms)
[![Downloads](https://static.pepy.tech/badge/pydantic-schemaforms/week)](https://pepy.tech/project/pydantic-schemaforms)
[![XERJ Corpus Hub contributor](https://hub.xerj.org/contributors/devsetgo/badge.svg)](https://hub.xerj.org/contributors/devsetgo)

**Support Python Versions**

![Static Badge](https://img.shields.io/badge/Python-3.14%20%7C%203.15-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Coverage Status](https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/refs/heads/main/coverage-badge.svg)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Tests Status](https://raw.githubusercontent.com/devsetgo/pydantic-schemaforms/refs/heads/main/tests-badge.svg)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)
![Versioning: Year-Quarter-Build](https://img.shields.io/badge/Versioning-Year--Quarter--Build-informational)

**CI/CD Pipeline:**
[![Testing - Main](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml/badge.svg?branch=main)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)
[![Testing - Dev](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml/badge.svg?branch=dev)](https://github.com/devsetgo/pydantic-schemaforms/actions/workflows/testing.yml)

**SonarCloud:**

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=coverage)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=alert_status)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_pydantic-schemaforms&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=devsetgo_pydantic-schemaforms)

<br clear="right" />

> **Requires Python 3.14+** — this library uses Python 3.14 language features and will not import on older versions.

## Overview

**pydantic-schemaforms** turns a Pydantic model into a server-rendered HTML
form, and validates what comes back with the same model.

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from pydantic_schemaforms import Field, FormModel, html, render_form_html_async


class SignupForm(FormModel):
    name: str = Field(title='Full name', min_length=2)
    email: str = Field(title='Email', ui_element='email')


app = FastAPI()
RENDER_OPTIONS = {'include_framework_assets': True, 'asset_mode': 'cdn'}


@app.get('/signup', response_class=HTMLResponse)
async def show_signup():
    return await render_form_html_async(SignupForm, submit_url='/signup', **RENDER_OPTIONS)


@app.post('/signup', response_class=HTMLResponse)
async def submit_signup(request: Request):
    result = SignupForm.validate(await request.form(), submit_url='/signup', **RENDER_OPTIONS)
    if not result.is_valid:
        return await result.render_with_errors_async()

    name = result.data['name']
    return html(t'<p>Thanks for signing up, {name}!</p>')
```

That's a complete FastAPI app: a styled signup form, browser and server
validation, errors shown next to each field with the user's input kept, and
the validated data as a plain dictionary. A Flask version is the same model
with `render_form_html()` and `request.form`.

**Features**

- **One model for everything.** The form, its validation, the validated data
  and, with `as_api_model()`, a typed JSON API all come from one Pydantic class.
- **Inputs from types.** `str`, `int`, `date`, `bool`, `Enum`, `Literal`,
  `EmailStr` and more pick their input; `Field(ui_element=...)` chooses any of
  40+ others (currency, tags, rating, code editor, file upload, ...).
- **Complex forms by nesting.** Sub-forms, optional sub-forms and repeating
  lists, shown as sections, tabs, columns, an accordion or a step wizard with
  one `layout=` argument. Data and errors come back nested like the model.
- **Fields that respond.** Show a field only when it applies with `ui_show_when`,
  enforced on the server too. Group fields and share rows with `ui_group` and
  `ui_cols`, keeping the data flat.
- **Review pages for free.** `render_display()` shows validated data read-only,
  with the form's labels and sections, for confirmation pages.
- **Bootstrap, Material Design 3 or plain HTML**, with opt-in dark mode for
  Bootstrap and Material, and assets inlined, linked from a CDN or left to your
  page.
- **Escaped by construction.** All HTML is built with Python 3.14 t-strings
  and an escaping processor.
- **Accessibility-tested.** Every input, layout and error state is checked
  with axe-core against WCAG 2.0–2.2 A and AA rules on every pull request.
- **More when you need it:** live validation over HTMX, CSV import into an
  editable table, CSRF protection, rule-based validators and plugin hooks for
  your own inputs.

## Install

```bash
uv add "pydantic-schemaforms[fastapi]"     # or [flask]
pip install "pydantic-schemaforms[fastapi]"
```

Requires **Python 3.14+** (the library uses t-strings) and Pydantic 2.13+;
tested on 3.14 and 3.15. Add the `email` extra if your forms use `EmailStr`.

## Documentation

The docs at <https://devsetgo.github.io/pydantic-schemaforms/> have:

- [Tutorial](https://devsetgo.github.io/pydantic-schemaforms/tutorial/): from a first form to nested forms, layouts,
  styling and CSRF protection, with FastAPI and Flask versions of every
  example.
- [Advanced User Guide](https://devsetgo.github.io/pydantic-schemaforms/advanced/): live validation, data tables,
  JSON APIs, forms built at runtime, assets and plugin hooks.
- [Recipes](https://devsetgo.github.io/pydantic-schemaforms/recipes/): complete apps for contact forms, login and
  registration, edit forms, line items, file uploads, wizards and more.
- [Reference](https://devsetgo.github.io/pydantic-schemaforms/reference/): every input, layout, field option and
  function.

The [live demo](https://pydantic-schemaforms.devsetgo.com) shows every input,
layout and kind of validation.

## Using an AI coding assistant?

The package ships [Agent Skills](https://agentskills.io) that match the installed version, so
assistants don't suggest removed APIs. Install them into your project with
[library-skills](https://library-skills.io/):

```bash
uvx library-skills --claude
```

You get `pydantic-schemaforms` (build and fix forms), `schemaforms-create` ("create a login
form"), `schemaforms-convert` (from Pydantic, WTForms, Django or JSON Schema),
`schemaforms-upgrade` (from removed APIs) and `schemaforms-document` (document your forms).
For assistants without skills support, `python -m pydantic_schemaforms.ai_instructions claude
--write` writes the same guidance to `CLAUDE.md`; see the
[AI Assistants and Agent Skills](https://devsetgo.github.io/pydantic-schemaforms/advanced/ai-instructions/) page.

## Accessibility

axe-core 4.14 runs against every example page, under Bootstrap and Material, in
light and dark, and in the error state after a failed submit, and any serious or critical
violation fails CI. This is testing, not a compliance claim: conformance
depends on your whole application. See the
[Accessibility reference](https://devsetgo.github.io/pydantic-schemaforms/reference/accessibility/).

## Contributing

Contributions are welcome; see the [Contributing Guide](https://github.com/devsetgo/pydantic-schemaforms/blob/main/CONTRIBUTING.md)
and the [Roadmap](https://github.com/devsetgo/pydantic-schemaforms/blob/main/ROADMAP.md).

```bash
git clone https://github.com/devsetgo/pydantic-schemaforms.git
cd pydantic-schemaforms
make install
make tests
```

## Links

- **Documentation**: [pydantic-schemaforms Docs](https://devsetgo.github.io/pydantic-schemaforms/)
- **Live demo**: <https://pydantic-schemaforms.devsetgo.com>
- **Repository**: [GitHub](https://github.com/devsetgo/pydantic-schemaforms)
- **PyPI**: [pydantic-schemaforms](https://pypi.org/project/pydantic-schemaforms/)
- **Issues**: [Bug Reports & Feature Requests](https://github.com/devsetgo/pydantic-schemaforms/issues)

## License

This project is licensed under the MIT License - see the LICENSE file for details:
https://github.com/devsetgo/pydantic-schemaforms/blob/main/LICENSE
