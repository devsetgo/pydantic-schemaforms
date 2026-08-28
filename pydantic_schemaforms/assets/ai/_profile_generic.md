# Pydantic SchemaForms app integration instructions

Use these rules when generating form code in an application that depends on pydantic-schemaforms.

<!-- INCLUDE: _shared_instructions.md -->

### Prompt templates

- Simple conversion:
	"Convert this model into a pydantic-schemaforms FormModel and render route. Keep layout vertical, framework bootstrap, and include full GET/POST validation flow."

- Complex conversion:
	"Convert this schema into a pydantic-schemaforms FormModel for a production form. Group fields into tabbed layout sections, choose ui_element and ui_options per field, preserve all constraints, and generate a full [FastAPI/Flask] endpoint with sticky form_data and field-level errors."

## Suggested request prompt

"Use pydantic-schemaforms in this app. Build a FormModel, render with render_form_html, validate POST data with FormModel.validate() (not manual model instantiation), map the returned ValidationResult's errors to field errors, and preserve submitted values in form_data. Keep submit_url explicit. Never reimplement the library's own widgets, validation, or rendering — use the documented ui_element/ui_options/Field surface, and only reach for register_input_class/LayoutEngine/CustomRule when nothing built-in fits — standard Pydantic model_validator/field_validator are always fine."
