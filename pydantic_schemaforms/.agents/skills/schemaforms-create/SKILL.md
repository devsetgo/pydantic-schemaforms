---
name: schemaforms-create
description: Create a new pydantic-schemaforms form from a short description, such as "create a login form", "create a contact form", "create a tabbed layout for a customer profile" or "create a 3-step job application wizard". Produces the FormModel and the GET/POST routes for the app's framework (FastAPI or Flask), with the code commented like a tutorial. Use when asked to create, generate, scaffold or give an example of a form or form layout with pydantic-schemaforms.
---
<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/schemaforms-create/SKILL.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->

# Create a form with pydantic-schemaforms

Turn a short description into a working form in the user's app: a `FormModel`, its GET and POST
routes, and comments that explain each choice so the code also teaches the library. The request
may name a known form ("a login form"), a layout ("a tabbed layout for a blank form"), or describe
fields ("a feedback form with a 1-5 rating and a comment").

## Rules for any code that uses pydantic-schemaforms

These apply to every task. Read them before writing code.

1. **Treat the library as a dependency.** Never edit, copy or vendor its source into the app, and
   never import from its submodules (`pydantic_schemaforms.inputs`, `.rendering`, `.templates`,
   `.tstring`, `.validation`, `.live_validation`, ...). Everything app code needs is exported from
   the top level: `from pydantic_schemaforms import FormModel, Field, html, ...`. If a name won't
   import from there, re-check its spelling before looking anywhere else.
2. **A form is a `FormModel`.** It's a Pydantic `BaseModel` subclass, so the model is the form, its
   validation and its data. Ordinary Pydantic is expected: `@field_validator`,
   `@model_validator`, `EmailStr`, `Enum`, `Literal`, `Optional`, `create_model()`.
3. **Use what's built in before writing code.** Formatted inputs (phone, currency, tags, ratings,
   date formats, file upload), repeating sub-forms, layouts, wizards and CSV-import tables are all
   `Field(...)` settings or nested models, not HTML or JavaScript you write.
4. **Constraints validate; `ui_options` only decorates.** `min_length`, `max_length`, `pattern`,
   `ge`, `le`, `gt`, `lt` and `multiple_of` go on `Field()`: they're checked on submit, and most
   also become HTML attributes so the browser checks them first. The same value in `ui_options` is never checked on the server.
5. **Build HTML around user data with `html(t'...')`.** A value that passed `validate()` can still
   contain `<script>`. `html()` takes a Python 3.14 t-string and escapes every interpolated
   value; an f-string or `.format()` doesn't. Output the library rendered (`render_form_html()`,
   `render_with_errors()`) is already safe and can be placed as is.
6. **Mistakes fail silently, so check names.** An unknown `ui_element` renders a plain text box, an
   unknown `ui_options` key becomes an HTML attribute, and a misspelled `framework` falls back
   to another style. None of them raise. The frameworks are `"bootstrap"`, `"material"` and
   `"none"`.
7. **`EmailStr` needs the `email` extra** (`pydantic-schemaforms[email]`) just to define the
   model. Add it to the app's dependencies whenever a form has an email field typed `EmailStr`.

## Steps

1. **Read the app.** Find the web framework (FastAPI or Flask), where routes and models live, how
   pages are rendered (a Jinja base template, or plain responses), whether a CSS framework is
   loaded, and whether there's a session (for CSRF). Follow the app's own conventions for file
   placement and naming. If there's no app yet, write one runnable `main.py`.
2. **Pick the starting point.** If the description matches a form in
   [the catalogue](references/catalog.md), start from it. Otherwise build the model from the
   description, using the type-to-input table below.
3. **Pick the layout.** See "Choosing a layout" below. A grouped layout needs one nested
   `FormModel` per section.
4. **Write the model.** Every field gets a `title`, a type that picks the right input, and
   constraints on `Field()`. Use `@field_validator`/`@model_validator` for rules across fields.
5. **Write both routes** following the pattern below, with the same render options passed to
   `render_form_html()` and `validate()`.
6. **Comment it like a tutorial** (see below).
7. **Check it.** If the app has tests, add one that GETs the page and POSTs an invalid and a valid
   submission. Otherwise run it, or import it and render the form once.
8. **Explain briefly** what was created, where, and how to run it.

Ask the user only when the answer changes the code and can't be read from the app: for example,
which framework when there's no app, or where the data should go when saving matters.

## The route pattern

FastAPI:

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

Flask is the same with `render_form_html()` (not async), `request.form` and no `await`.

- `include_framework_assets=True, asset_mode="cdn"` makes the response a complete styled page.
  Leave both out when the app's base template already loads Bootstrap; render the form into the
  template instead (`{{ form_html | safe }}`).
- After a successful POST that changes data, redirect (303) instead of returning a page, so a
  reload doesn't submit again.
- A form behind a login that changes data needs CSRF protection: `csrf_mode="required-provider"`
  with a session token, checked before `validate()`.

## Choosing inputs

| The description says | Field |
|---|---|
| name, title, short text | `str` |
| long text, comment, message, notes | `str` with `ui_element="textarea"` |
| email | `EmailStr` (add the `email` extra) |
| password | `str` with `ui_element="password"`, `min_length` |
| phone | `str` with `ui_element="phone"` (or `"tel"`) |
| website, link | `AnyUrl` |
| number, count, age, quantity | `int` with `ge`/`le` |
| price, amount | `Decimal` with `ui_element="currency"`, `ge=0` |
| yes/no, agree, subscribe | `bool` |
| one of a few fixed choices | `Literal[...]` or an `Enum` (dropdown); `ui_element="radio"` for 2-4 visible options |
| several of fixed choices | `list[Literal[...]]` (multi-select) or `ui_element="checkbox_group"` |
| date, time, date and time | `date`, `time`, `datetime` |
| rating, stars | `int` with `ui_element="star_rating"`, `ge=1`, `le=5` |
| tags, keywords | `str` with `ui_element="tags"` |
| file, attachment, document | `Any` with `ui_element="file"` (checked in the route) |
| colour | `str` with `ui_element="color"` |
| an address, a person, a section | a nested `FormModel` |
| "add more", a list of items | `list[ItemForm]` with `ui_add_button_label` |
| optional section | `Section \| None` |

Fields the user didn't ask for stay out, apart from the ones a form type needs to work (a
password confirmation on registration, for example). Give optional fields a default.

## Choosing a layout

| The description says | Layout |
|---|---|
| a simple form, a few fields | `"vertical"` (default) |
| tabs, tabbed, sections the user switches between | `"tabbed"` |
| collapsible sections, accordion | `"accordion"` |
| columns, side by side | `"side-by-side"` |
| steps, wizard, multi-step, one page at a time | `"wizard"` |

Grouped layouts arrange **sub-forms**: write one `FormModel` per section and nest them as fields
of the main form; plain fields on the main form become its first group. For a "blank" or
"skeleton" layout, create two or three clearly named placeholder sections, each with one or two
example fields, and a comment saying to replace them. See the catalogue's layout skeletons.

## Comment like a tutorial

The comments should teach someone new to the library what each piece does and why:

- Above the model: what the form is for and how its fields become inputs.
- On non-obvious fields: why this type or `ui_element`, what a constraint enforces.
- On each route: what GET renders, what `validate()` returns, why the same options go to both.
- On HTML built from data: why it's `html(t'...')`.

Keep them short, explain *why*, and don't comment the obvious. One comment per idea; if the app's
own code is sparsely commented, keep the tutorial comments to the first form you create and
mention that in your summary.

## Before finishing

- The form renders, an invalid POST comes back with errors and the values kept, and a valid POST
  succeeds.
- Every `ui_element` and `ui_options` key exists (see the `pydantic-schemaforms` skill's inputs
  reference when installed).
- `layout=` and other options are passed to both `render_form_html()` and `validate()`.
- No f-string around submitted values, no submodule imports, CSRF on state-changing forms behind
  a login.
