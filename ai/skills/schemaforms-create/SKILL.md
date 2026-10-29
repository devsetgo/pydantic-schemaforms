---
name: schemaforms-create
description: Create a new pydantic-schemaforms form from a short description, such as "create a login form", "create a contact form", "create a tabbed layout for a customer profile" or "create a 3-step job application wizard". Produces the FormModel and the GET/POST routes for the app's framework (FastAPI or Flask), with the code commented like a tutorial. Use when asked to create, generate, scaffold or give an example of a form or form layout with pydantic-schemaforms.
---

# Create a form with pydantic-schemaforms

Turn a short description into a working form in the user's app: a `FormModel`, its GET and POST
routes, and comments that explain each choice so the code also teaches the library. The request
may name a known form ("a login form"), a layout ("a tabbed layout for a blank form"), or describe
fields ("a feedback form with a 1-5 rating and a comment").

<!-- INCLUDE: _shared.md -->

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

<!-- INCLUDE-CODE: docs_src/tutorial/submissions/fastapi_app.py -->

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
