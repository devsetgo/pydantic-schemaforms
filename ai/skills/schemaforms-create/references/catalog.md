# Form catalogue

Starting points for common forms. Each model is tested against the current library. Adapt the
fields to the request; add the routes from the pattern in `SKILL.md`.

## Contact form

A topic, a message and a honeypot against spam bots. When `website` comes back filled in, answer
as if the message was sent and drop it.

<!-- INCLUDE-CODE: docs_src/recipes/contact_form/models.py -->

## Login and registration

Passwords, a matching confirmation, a required "accept the terms" box. Checks only the app can
make (wrong password, username taken) are added in the route after `validate()`:
`render_form_html(Model, form_data=..., errors={"username": "That username is taken"}, ...)`, or
`errors={"_errors": "Wrong username or password"}` for the whole form. Only put the username
back on a failed login, never the password. Redirect (303) after success.

<!-- INCLUDE-CODE: docs_src/recipes/login_registration/models.py -->

## Edit form for a saved record (profile, product, settings)

Pre-fill with `form_data={name: row[name] for name in Model.model_fields}`; dates and `Enum`
members can be passed as they are. Only pass the form's own fields, so values such as `id` can't
be edited.

<!-- INCLUDE-CODE: docs_src/recipes/edit_form/models.py -->

## Checkout with shipping and billing addresses

One `Address` model used twice; the billing address is an optional sub-form that's validated only
when filled in.

<!-- INCLUDE-CODE: docs_src/recipes/address_subform/models.py -->

## Order with line items

A repeating sub-form; the total is computed on the server, never trusted from the browser.

<!-- INCLUDE-CODE: docs_src/recipes/order_line_items/models.py -->

## File upload

The file field is `Any`; the route checks that a file was chosen, its extension and its size.

<!-- INCLUDE-CODE: docs_src/recipes/file_upload/models.py -->

## Job application (wizard)

One step per sub-form; pass `layout="wizard"` to both `render_form_html()` and `validate()`.

<!-- INCLUDE-CODE: docs_src/recipes/wizard_application/models.py -->

## Settings with a code field

JSON or TOML typed into a code-editor text area, checked by validators.

<!-- INCLUDE-CODE: docs_src/recipes/settings_code_field/models.py -->

## Survey or feedback

<!-- INCLUDE-CODE: docs_src/skills/create/survey.py -->

## Blank tabbed layout

For "a tabbed layout for a blank form": placeholder sections to replace. The same model renders as
an accordion, columns or a wizard by changing `layout=`.

<!-- INCLUDE-CODE: docs_src/skills/create/tabbed_skeleton.py -->

## Blank wizard

<!-- INCLUDE-CODE: docs_src/skills/create/wizard_skeleton.py -->
