# Plugin Hooks for Inputs and Layouts

This project now exposes lightweight extension points so third-party packages (or your own app code) can add new inputs or layout renderers without patching core modules.

## Registering Custom Inputs

Use `pydantic_forms.inputs.registry.register_input_class` to bind a `BaseInput` subclass to one or more `ui_element` aliases. The registry augments the built-in discovery of subclasses so you can register at import time or inside your framework startup.

```python
from pydantic_forms.inputs.base import BaseInput
from pydantic_forms.inputs.registry import register_input_class

class ColorSwatchInput(BaseInput):
    ui_element = "color_swatch"

    # implement render_input / render_label, etc.

register_input_class(ColorSwatchInput)
```

- Aliases: pass `aliases=("color", "swatch")` if you want multiple trigger names.
- Bulk registration: use `register_inputs([Cls1, Cls2, ...])`.
- Reset (tests/hot reload): `reset_input_registry()` clears custom entries and cache.

Once registered, any field with `input_type="color_swatch"` (or alias) will resolve to your component.

## Registering Custom Layout Renderers

`LayoutEngine` can now dispatch layout fields to custom renderers before falling back to built-in demos. Provide a callable and reference it from a field via `layout_handler` (or `layout_renderer`) in `json_schema_extra` / `FormField` kwargs.

```python
from pydantic_forms.rendering.layout_engine import LayoutEngine

# signature: (field_name, field_schema, value, ui_info, context, engine) -> str
def render_steps(field_name, field_schema, value, ui_info, context, engine):
    # value may be your own layout descriptor; use engine._renderer if needed
    steps = value or []
    items = "".join(f"<li>{step}</li>" for step in steps)
    return f"<ol class='steps'>{items}</ol>"

LayoutEngine.register_layout_renderer("steps", render_steps)
```

Attach the handler in your form field:

```python
class WizardForm(FormModel):
    steps: list[str] = FormField(
        ["Account", "Billing", "Review"],
        input_type="layout",
        layout_handler="steps",
        title="Wizard Steps",
    )
```

- Names are arbitrary strings; collisions overwrite the previous handler.
- Call `LayoutEngine.reset_layout_renderers()` in tests to clear state.
- Handlers receive the active `LayoutEngine` instance and the original renderer via `engine._renderer` if you need to reuse field rendering helpers.

## Packaging Tips

- For libraries: register your inputs/layouts in your package `__init__` or an explicit `setup()` function that users call during startup.
- For app code: register once at process start (e.g., FastAPI lifespan, Django AppConfig.ready). Avoid per-request registration.
- Keep renderers pure and side-effect free; they should return HTML strings and not mutate shared state.
