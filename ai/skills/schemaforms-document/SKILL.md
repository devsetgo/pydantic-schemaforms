---
name: schemaforms-document
description: Document the pydantic-schemaforms forms in an app - add docstrings, field titles and help text and explanatory comments to every FormModel, and write a Markdown page (such as docs/forms.md) describing each form - its purpose, routes, fields, validation rules, layout and where the data goes. Use when asked to document, describe, inventory or explain an app's forms.
---

# Document an app's pydantic-schemaforms forms

Produce two things: documentation **in the code** (models that explain themselves) and a
**Markdown page** that describes every form for developers and reviewers. Document what the code
does; never describe behaviour you haven't checked.

<!-- INCLUDE: _shared.md -->

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
