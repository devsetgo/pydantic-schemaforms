# Layouts

There are two layers of layout support:

1) **Top-level layout modes** (`layout=` when you render the form)
2) **Composable layout primitives** (horizontal/grid/tabs/etc) for advanced composition

## 1) Top-level layout modes

Pass `layout=` to `render_form_html()` / `FormModel.render_form()`.

Supported values:

- `vertical` (default)
- `tabbed`: groups fields into tabs automatically
- `side-by-side`: renders fields in two-column rows

```python
from pydantic_schemaforms.enhanced_renderer import render_form_html

html = render_form_html(MyFormModel, layout="side-by-side")
```

## 2) Layout primitives (advanced)

The module `pydantic_schemaforms.rendering.layout_engine` contains reusable wrappers:

- `HorizontalLayout`
- `VerticalLayout`
- `GridLayout`
- `ResponsiveGridLayout`
- `TabLayout`
- `AccordionLayout`
- `CardLayout`
- `ModalLayout`

A convenience factory is provided:

- `LayoutComposer` (aliases: `Layout`, `LayoutFactory`)

Example:

```python
from pydantic_schemaforms.rendering.layout_engine import Layout

layout = Layout.grid(
    "<div>Left</div>",
    "<div>Right</div>",
    columns="1fr 2fr",
    gap="1rem",
)

html = layout.render(framework="bootstrap", renderer=my_renderer, data={}, errors={})
```

## Schema-defined layout fields

A schema field with `ui_element="layout"` is treated as a layout field.

At render time, the renderer will:

- Call a custom layout renderer if you configured one (`layout_handler` / `layout_renderer`)
- Or, if the field value is a `BaseLayout` instance, call its `.render()`

This is intentionally an advanced feature (useful for complex nested forms and custom layout engines).

## Registering custom layout renderers

You can register a named layout renderer:

```python
from pydantic_schemaforms.rendering.layout_engine import LayoutEngine


def my_layout_renderer(field_name, field_schema, value, ui_info, context, engine):
    return "<div>Custom layout output</div>"


LayoutEngine.register_layout_renderer("my_layout", my_layout_renderer)
```

Then set `ui_options` (or schema `ui`) to reference it:

- `layout_handler="my_layout"` or `layout_renderer="my_layout"`

## Notes

- `tabbed` grouping is heuristic-based (field-name keywords). If you need deterministic tabbing, use explicit layout fields or custom renderers.
- Layout fields can include nested form markup via `EnhancedFormRenderer.render_form_fields_only()`.
