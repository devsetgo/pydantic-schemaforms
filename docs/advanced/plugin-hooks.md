# Plugin Hooks and Custom Composites

You can add your own inputs and your own composite controls (a whole table,
a repeating structure, a custom picker) without changing the library. Both
are registered at startup and then used through `ui_element` or a layout
field like any built-in one.

## Custom inputs

Subclass an existing input and register it under a new `ui_element` name:

```python
--8<-- "docs_src/advanced/plugin_hooks/custom_input.py"
```

Subclassing a built-in input such as `TextInput` keeps everything it already
does: escaping every value, the label, help text, error message and the
accessibility wiring. Override `render()` to adjust the attributes, then hand
off to `super().render()`.

- `register_input_class(cls, aliases=(...))` registers one class, under its
  `ui_element` and any aliases.
- `register_inputs([...])` registers several at once.
- `reset_input_registry()` removes the custom ones, for tests or hot reload.

Keep custom inputs to the accessibility baseline in [Accessibility](../reference/accessibility.md): inherit
`render_with_label()` (from `FormInput`) rather than writing your own, so the label,
help text and error get their ids and the control gets `aria-invalid`/`aria-describedby`;
make sure `render()` passes `aria-*` keyword arguments through to the control (the
`validate_attributes()` helper does this); and keep text at 4.5:1 contrast. A built-in
input also needs a widget-gallery entry, which puts it under the axe-core gate in
`tests/playwright/test_example_pages.py`.

## Registering Custom Layout Renderers

`LayoutEngine` dispatches a field to a registered custom renderer through
**two independent keyspaces**, both backed by the same
`LayoutEngine._custom_renderers` registry and the same `LayoutRenderer`
callable signature — `(field_name, field_schema, value, ui_info, context,
engine) -> str`:

1. **`layout_handler` keyspace** — only reached when the field itself is
   declared `input_type="layout"`, plus a `layout_handler` (or
   `layout_renderer`) name in `json_schema_extra`/`FormField` kwargs. This
   is the mechanism `DataTableLayout` uses (see below): the field's own
   value carries whatever the renderer needs.
2. **`ui_element` keyspace** — reached directly by a field's own
   `ui_element`/`input_type` string, whatever it is, via
   `LayoutEngine.get_renderer_for_element(ui_element)`. This is the
   mechanism `model_list` uses internally
   (`FormField(..., input_type="model_list")`) — from the *field
   declaration's* point of view nothing about `model_list` changed, but
   internally it's dispatched through this same registry rather than a
   hardcoded check, so it's a second, real, load-bearing example of this
   mechanism working end-to-end (not just a name-collision risk to avoid).

Use `register_layout_renderer(name, renderer)` for either keyspace — which
one a given `name` lands in depends entirely on what triggers the lookup on
the field side (`input_type="layout"` + `layout_handler=name`, vs. a field
whose own `input_type`/`ui_element` literally equals `name`), not on
anything about the registration call itself.

```python
--8<-- "docs_src/advanced/plugin_hooks/composite.py"
```

The renderer builds its HTML with `html(t'...')`, like everything else in the
library, so each step's text is escaped. The field declares
`input_type="layout"` and names the renderer with `layout_handler`; its value
(here the list of steps) is what the renderer receives.

- Names are arbitrary strings; collisions overwrite the previous handler.
- Call `LayoutEngine.reset_layout_renderers()` in tests to clear
  non-builtin state (see `builtin=True` below — a renderer registered that
  way survives this call).
- Handlers receive the active `LayoutEngine` instance and the original
  renderer via `engine._renderer` if you need to reuse field rendering
  helpers.

### `requires_multipart` — declare a nested file input

If your renderer might emit its own `<input type="file">` inside the
field's own output (as `DataTableLayout` does when `csv_upload` is on), pass
`requires_multipart` to `register_layout_renderer`/`layout_renderer`. A
nested file input like that isn't a top-level `FormModel` field, so the
form's own file-field scan — which only sees this field's `layout` element,
not what it renders — can never discover it on its own, and the enclosing
`<form>` would silently miss `enctype="multipart/form-data"`, without which
a browser sends only the chosen file's *name*, never its contents:

```python
def _needs_multipart(value: Any) -> bool:
    # Called with this field's raw value (whatever your as_layout_value()-
    # equivalent built) at render time; return whether *that specific
    # value* needs multipart encoding.
    return bool(value) and value.get('csv_upload_enabled', False)

@LayoutEngine.layout_renderer('steps', requires_multipart=_needs_multipart)
def render_steps(field_name, field_schema, value, ui_info, context, engine):
    ...
```

`DataTableLayout` wires this to its own `csv_upload` config flag — see
`pydantic_schemaforms/rendering/datatable_renderer.py`. If your composite
never renders a file input, omit the parameter (the default `None` means
"never needs multipart").

### `builtin=True` and the `@LayoutEngine.layout_renderer` decorator

A renderer this library ships (like `DataTableLayout`'s or `model_list`'s)
only registers itself **once per process**, at import time. If you register
it the plain way and something later calls
`LayoutEngine.reset_layout_renderers()` — several test fixtures across this
project's own suite do, between tests — it's gone for the rest of the
process, since nothing re-imports the registering module afterward. Pass
`builtin=True` to `register_layout_renderer` to mark a renderer as
library-owned so resets leave it alone:

```python
LayoutEngine.register_layout_renderer("datatable", render_datatable_layout_field, builtin=True)
```

Or use the decorator form, which defaults `builtin=True` (it's meant for
exactly this "register my own reusable composite once, at import time"
case):

```python
@LayoutEngine.layout_renderer("datatable")
def render_datatable_layout_field(field_name, field_schema, value, ui_info, context, engine):
    ...
```

One-off, app-level, or test-only renderers should leave `builtin` at its
default (`False`) so `reset_layout_renderers()` still clears them between
tests, same as always.

### Real, working composite examples

Three real composites in this
library demonstrate both keyspaces end-to-end:

- **`DataTableLayout`** (`pydantic_schemaforms/datatable_layout.py` +
  `pydantic_schemaforms/rendering/datatable_renderer.py`) — the
  `layout_handler` keyspace. A `FormModel` subclass whose own fields ARE
  the composite's structure (table columns), embedded as
  `input_type="layout", layout_handler="datatable"`. See
  [Data Tables](data-tables.md) for the full pattern,
  including `as_layout_value()` for building the field's value.
- **`model_list`** (`pydantic_schemaforms/rendering/model_list_renderer.py`)
  — the `ui_element` keyspace. `FormField(..., input_type="model_list")` on
  a `list[ItemModel]`-annotated field, where `ItemModel` is any ordinary,
  unmodified `FormModel` — there's no wrapper class at all, since the
  item's shape already comes from its own type annotation.
- **`nested_model`** (`pydantic_schemaforms/rendering/nested_model_renderer.py`)
  — also the `ui_element` keyspace, inferred from a field typed as another
  `FormModel`. It renders the sub-form's fields under dotted input names and
  is how complex forms are composed (see [Nested Forms and Lists](../tutorial/nested-forms.md)).

Every registered renderer is called with six positional arguments,
`(field_name, field_schema, value, ui_info, context, engine)`. The field's
own error message is `context.error`, and its nested errors (same shape as
its value; see [Nested Forms and Lists](../tutorial/nested-forms.md)) are `context.child_errors`.

### `CompositeLayoutModel`: a base for FormModel-shaped composites

If your composite is shaped like `DataTableLayout` — a `FormModel` subclass
whose own fields define the composite's structure, meant to be embedded as
a layout field and never rendered on its own — subclass
`CompositeLayoutModel` (a top-level export) instead of `FormModel` directly. It disables `render_form()` with a clear
`NotImplementedError` pointing callers at your own value-bundling
classmethod (the `as_layout_value()` convention `DataTableLayout` uses), so
nobody accidentally calls it as if it rendered one instance's inputs.

Not every composite needs this base — `model_list` doesn't, since its item
model is just an ordinary `FormModel` referenced via a `list[ItemModel]`
annotation, not a class of its own that needs `render_form()` disabled.
Reach for `CompositeLayoutModel` specifically when your composite's own
fields ARE its structure (table columns, wizard steps, and similar).

## Packaging Tips

- For libraries: register your inputs/layouts in your package `__init__` or an explicit `setup()` function that users call during startup, and pass `builtin=True` (or use the `@LayoutEngine.layout_renderer(name)` decorator) so `reset_layout_renderers()` calls elsewhere (e.g. in a consuming app's own test suite) don't silently remove your renderer.
- For app code: register once at process start (e.g., FastAPI lifespan, Django AppConfig.ready). Avoid per-request registration. Leave `builtin` at its default (`False`) so your own tests can still reset cleanly between runs.
- Keep renderers pure and side-effect free; they should return HTML strings and not mutate shared state.
