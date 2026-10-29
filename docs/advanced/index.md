# Advanced User Guide

The [Tutorial](../tutorial/index.md) covers everything most forms need. The
pages here go further, each on its own, so read the ones you need.

## Validation

- [Live Validation (HTMX)](live-validation.md): check fields on the server
  while the user types.
- [Rule-Based Validation](rule-validation.md): `FormValidator` and
  ready-made rules such as `PhoneRule`, alongside the model's own validation.

## More kinds of forms

- [Data Tables (CSV Import)](data-tables.md): import a CSV into an editable,
  validated table.
- [Forms Built at Runtime](runtime-forms.md): create a form whose fields come
  from data, with `create_model()`.
- [JSON API and JSON Schema](json-api.md): one model for an HTML form and a
  JSON API, and standard JSON Schema output.

## Rendering

- [Assets and Self-Contained Forms](assets.md): where the CSS and JavaScript
  come from, and forms with no external files.
- [Render Timing and Logging](timing-logging.md): measure rendering and turn
  on the library's logs.
- [Layout Primitives](layout-primitives.md): grids, cards and tabs for HTML
  you've already rendered.

## Extending the library

- [Plugin Hooks and Custom Composites](plugin-hooks.md): register your own
  inputs and composite controls.
- [AI Assistants and Agent Skills](ai-instructions.md): five agent skills,
  installed with `uvx library-skills`, that teach coding assistants to build,
  create, convert, upgrade and document forms with the installed version.
