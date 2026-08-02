# Copilot instructions for app teams using pydantic-schemaforms

<!-- INCLUDE: _shared_instructions.md -->

### Copilot conversion prompt starters

- "Convert this Pydantic model into a FormModel + FastAPI form endpoint using pydantic-schemaforms. Keep bootstrap + vertical layout and full validation loop."
- "Convert this JSON schema into a tabbed pydantic-schemaforms FormModel and Flask route. Map every field to ui_element/ui_options, preserve constraints, and include sticky form_data + ValidationError mapping."

## Prompt starter for Copilot Chat

"Implement a [FastAPI/Flask] form route using pydantic-schemaforms. Use FormModel + Field metadata, choose framework and layout explicitly, render via render_form_html with explicit submit_url, validate POST data with the model, map ValidationError to field errors, and preserve posted values in form_data. Treat pydantic_schemaforms as an external dependency — never edit its source or import from its internal submodules, and never hand-write a widget/validator the library already provides."
