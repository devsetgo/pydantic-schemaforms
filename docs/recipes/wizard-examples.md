# Wizard Examples

The example app has a **Wizards** section: realistic multi-step forms, each
built to show a different mix of wizard features. Run it with
`python examples/main.py` and open `/wizards`. The models and routes are in
[`examples/wizard_examples.py`](https://github.com/devsetgo/pydantic-schemaforms/blob/main/examples/wizard_examples.py),
one model per example, so you can copy the one closest to what you need.

| Example | Page | What it shows |
|---|---|---|
| Job application | `/wizards/job-application` | The fullest one, in its own module ([`examples/job_application_example.py`](https://github.com/devsetgo/pydantic-schemaforms/blob/main/examples/job_application_example.py)). A sign-in page outside the wizard, with a password match check; then the application, each step saved on the server (`save_steps`) and resumed from the draft; a resume upload limited to PDF or Word and 2 MB, stored once by its `ref`; work history as a repeating list with a start-before-end check; a sponsorship question that shows only when needed; consent; autosave and a warning before leaving; a review step. Its edit page reopens the submitted application as a one-POST wizard, and the review step marks each change as old → new |
| Car care appointment | `/wizards/car-care` | Steps from `ui_group`; make, model and year; a loaner-car step that applies only when a loaner is asked for, skipped otherwise (`ui_group_show_when`); services as checkboxes; a US phone number checked with a `pattern` and formatted as it's typed; a review step; progress ticks in the header |
| Rental application | `/wizards/rental-application` | Co-applicants and references as repeating lists (`model_list`, with item titles from `ui_item_title_template`); a `@model_validator` that checks everyone's income together against three times the rent, across steps; several proof-of-income uploads (`list[UploadedFile]`, `ui_max_files`); a pets question that shows only when ticked; a review step; progress ticks |
| Team onboarding | `/wizards/team-onboarding` | The smallest one, a starter template: steps from sub-forms, an invite list (`model_list`) whose emails are checked with `EmailRule`, a `pattern` on the web address, progress ticks |
| Event registration | `/wizards/event-registration` | Guests as a repeating list, a capacity check in a `@field_validator`, dietary choices, no progress header (`show_progress: False`) and a renamed Next button |

Each example opens with demo values filled in, so it can be tried right away
(add `?demo=false` for a blank form). Apart from the job application, each one is rendered with `layout="wizard"` and validated with
`FormModel.validate()`, and its result page is built with `html(t'...')`, so
the answers are escaped. Every one renders under Bootstrap and Material, in
light and dark.

The job application is the exception: it saves each step with
`FormModel.validate_step()`, so its pages are its own routes. Its accounts,
drafts and files live in memory for the demo; a real app uses its session,
database and file store. The demo can't fill in a file input, so choose any
PDF or Word file on the Resume step.

For a short walk-through of one wizard and its routes, see
[Multi-Step Application](wizard-application.md); for saving each step on the
server, see [Save and Continue](save-and-continue.md).
