<!-- GENERATED FILE -- do not edit directly. Source: ai/skills/schemaforms-document/references/forms-page.md. Regenerate with `make ai-instructions` (scripts/build_ai_instructions.py). -->
# Forms page template

Fill this in for the app; drop sections that don't apply. Keep it factual: every route, field and
rule must exist in the code.

```markdown
# Forms

This app's forms are built with [pydantic-schemaforms](https://github.com/devsetgo/pydantic-schemaforms):
each form is a Pydantic model (`FormModel`), rendered to HTML on the server and validated with
the same model when it's submitted.

| Form | Purpose | Route | Layout |
|---|---|---|---|
| [Sign up](#sign-up) | Create an account | `GET/POST /signup` | vertical |
| [Profile](#profile) | Edit the user's profile | `GET/POST /profile` | tabbed |

## Sign up

Creates a user account. Shown at `/signup`, linked from the login page.

- **Model:** `SignupForm` in `app/forms.py`
- **Routes:** `GET /signup` renders it; `POST /signup` validates it, creates the user and
  redirects to `/welcome`.
- **Style:** Bootstrap, vertical layout.
- **Protection:** CSRF token (session), honeypot field `website`.

### Fields

| Field | Label | Type / input | Required | Default | Rules | Help |
|---|---|---|---|---|---|---|
| `username` | Username | text | yes | | 3–30 characters, lowercase letters, numbers, `_` | |
| `email` | Email | email | yes | | valid email address | |
| `password` | Password | password | yes | | at least 12 characters | |
| `plan` | Plan | dropdown: free, pro | no | free | | |

### Validation beyond the fields

- The password confirmation must match the password (`passwords_match`).
- In the route: the username must not already exist ("That username is taken").

### After a valid submit

The user is created with `create_user(result.data)`, and the browser is redirected to
`/welcome`.

## How forms work in this app

- A form is a class in `app/forms.py` that subclasses `FormModel`; each field is one input.
  The field's type picks the input, `title` is the label, `description` is the help text, and
  constraints such as `min_length` are checked both in the browser and on the server.
- A route renders it with `render_form_html(Form, submit_url=...)` and handles the POST with
  `Form.validate(request.form, ...)`. When validation fails, `result.render_with_errors()`
  returns the form with the user's input and an error under each field.
- To add a field, add it to the model with a `title`, a type and its constraints; the form and
  its validation update together.
```
