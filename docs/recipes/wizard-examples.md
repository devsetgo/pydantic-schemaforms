# Wizard Examples

The example app has a **Wizards** section: realistic multi-step forms, each
built to show a different mix of wizard features. Run it with
`python examples/main.py` and open `/wizards`. The models and routes are in
[`examples/wizard_examples.py`](https://github.com/devsetgo/pydantic-schemaforms/blob/main/examples/wizard_examples.py),
one model per example, so you can copy the one closest to what you need.

| Example | Page | What it shows |
|---|---|---|
| Car care appointment | `/wizards/car-care` | Steps from `ui_group`; a loaner-car step that applies only when a loaner is asked for, skipped otherwise (`ui_group_show_when`); services as checkboxes; a review step; progress ticks in the header |
| Team onboarding | `/wizards/team-onboarding` | The smallest one, a starter template: steps from sub-forms, an invite list (`model_list`) whose emails are checked with `EmailRule`, a `pattern` on the web address, progress ticks |
| Event registration | `/wizards/event-registration` | Guests as a repeating list, a capacity check in a `@field_validator`, dietary choices, no progress header (`show_progress: False`) and a renamed Next button |

Each example is rendered with `layout="wizard"` and validated with
`FormModel.validate()`, and its result page is built with `html(t'...')`, so
the answers are escaped. Every one renders under Bootstrap and Material, in
light and dark.

More examples are on the way, including a full job application with a resume
upload, step-by-step saving and an edit page that shows what changed.

For a short walk-through of one wizard and its routes, see
[Multi-Step Application](wizard-application.md); for saving each step on the
server, see [Save and Continue](save-and-continue.md).
