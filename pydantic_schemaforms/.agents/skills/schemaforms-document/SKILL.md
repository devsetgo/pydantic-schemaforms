---
name: schemaforms-document
description: Document the pydantic-schemaforms forms in an app - add docstrings, field titles and help text and explanatory comments to every FormModel, and write a Markdown page (such as docs/forms.md) describing each form - its purpose, routes, fields, validation rules, layout and where the data goes. Use when asked to document, describe, inventory or explain an app's forms.
---
<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/schemaforms-document/SKILL.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->

# Document an app's pydantic-schemaforms forms

Produce two things: documentation **in the code** (models that explain themselves) and a
**Markdown page** that describes every form for developers and reviewers. Document what the code
does; never describe behaviour you haven't checked.

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

1. **Find the forms.** Search the app for `FormModel` subclasses and for where each is used:
   `render_form_html`, `render_form_html_async`, `.render_form(`, `.validate(` and
   `render_with_errors`. Note each form's routes, `submit_url`, `layout=`, `framework=`,
   `csrf_mode=` and what the route does with `result.data` (saves it, emails it, calls an API).
   Nested forms (`address: Address`, `items: list[Item]`) belong to their parent's entry.
2. **List the fields.** Read them from the source. To get exact field tables, the bundled script
   can list them, but it imports the app's modules, so ask the user before running it:
   `python <this skill's folder>/scripts/list_forms.py app.forms app/admin/forms.py`
   (module names or files; `--json` for JSON).
3. **Document the code** (below). Change only documentation: don't change behaviour, field names,
   types or constraints. Adding a missing `title` or `description` does change what the form
   shows (they're the label and help text), so list those changes for the user.
4. **Write the page** using [the page template](references/forms-page.md). Default location:
   `docs/forms.md`, or wherever the app keeps its docs. Link it from the app's README or docs
   index if there is one.
5. **Check** the app still imports and its tests pass, and that every route and field on the page
   exists in the code.

## Documenting the code

- **Each `FormModel` gets a docstring:** what the form is for, who fills it in, and where it's
  used (route or page). One to three sentences.
- **Each field gets `title=`** (the label) when the generated one from the field name isn't right,
  and **`description=`** when the user needs help filling it in (format, why it's asked, what
  happens with it). These show in the form and in the JSON Schema, so write them for the person
  filling in the form.
- **Comment the non-obvious choices:** a `ui_element` that isn't what the type suggests, a
  constraint with a business reason (`max_length=500  # column size`), a validator's rule, a
  `layout=` choice, CSRF. Explain why, not what.
- **Validators get a one-line docstring** stating the rule in plain words ("End date must be after
  the start date").
- Keep the app's existing style (quote style, comment density, docstring format).

## What the page must cover

For each form: purpose, where it's used (route and template), the fields (label, type, input,
required, default, rules, help), the validation beyond field rules (validators, checks in the
route such as "username must be unused"), the layout and style, protection (CSRF, captcha,
honeypot), and what happens to the data after a valid submit. End with a short section on how
forms work in the app, for someone new to pydantic-schemaforms.
