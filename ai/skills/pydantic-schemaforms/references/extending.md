# Extending reference

Reach for these only after checking the inputs reference and the existing composites
(`list[FormModel]` repeating sub-forms, `DataTableLayout`): most "custom" needs are a
`ui_element`, a `ui_options` key or a nested model.

## A custom input

Subclass an existing input and register it once at import time, before the app serves requests.
Subclassing a built-in keeps its escaping, label, help text, error message and accessibility
wiring; override `render()` to adjust attributes and hand off to `super().render()`.

<!-- INCLUDE-CODE: docs_src/advanced/plugin_hooks/custom_input.py -->

- `register_input_class(cls, aliases=(...))` registers it under its `ui_element` and any aliases;
  `register_inputs([...])` registers several; `reset_input_registry()` removes custom ones (tests).
- If `render()` writes its own HTML, build it with `html(t'...')`, never an f-string, and pass
  `aria-*` keyword arguments through to the control. Prefer `FormInput.render_with_label()` over
  writing your own label markup; `build_label()`, `build_help_text()` and
  `build_error_message()` produce markup matching the built-ins.
- Base classes: `BaseInput`, `FormInput`, `NumericInput`, `SelectInputBase`, `FileInputBase`.

## A custom composite control

Something bigger than one input (a board, a matrix, a custom picker) is a layout renderer, the
same mechanism `DataTableLayout` and repeating sub-forms are built on. Don't invent another.

<!-- INCLUDE-CODE: docs_src/advanced/plugin_hooks/composite.py -->

- The renderer is called with exactly `(field_name, field_schema, value, ui_info, context,
  engine)`. The field's own error is `context.error`; its nested errors are
  `context.child_errors` (a `RenderContext`).
- App code registers with `builtin=False`.
- A renderer that outputs its own file input must pass `requires_multipart=` so the form gets
  `enctype="multipart/form-data"`.
- When the composite's own fields are its structure (table columns, board lanes), subclass
  `CompositeLayoutModel` for that class instead of `FormModel`.
- Build every piece of HTML with `html(t'...')`.
