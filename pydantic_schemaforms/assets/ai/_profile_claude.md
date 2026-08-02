# Claude instructions for app teams using pydantic-schemaforms

When asked to build forms in an application using pydantic-schemaforms, follow this contract.

<!-- INCLUDE: _shared_instructions.md -->

### Claude conversion prompt starters

- "Convert this model to a pydantic-schemaforms FormModel and FastAPI endpoint with bootstrap + vertical layout, sticky form_data, and field-level error mapping."
- "Convert this JSON schema to a complex tabbed pydantic-schemaforms form in Flask. Preserve constraints, choose ui_element/ui_options per field, and generate complete GET/POST code."

## Prompt starter for Claude

"Implement this form endpoint using pydantic-schemaforms with FormModel and Field metadata, explicit framework and layout, render_form_html with submit_url, POST validation via model instantiation, field-level error mapping from ValidationError, and sticky values via form_data. Treat pydantic_schemaforms as an external dependency: never edit its source, never import from its internal submodules, and never reimplement a widget or validation behavior the library already provides — use register_input_class/CustomRule only when nothing built-in fits — standard Pydantic model_validator/field_validator are always fine."
