# Layouts

To build a form out of several models (sections, tabs, columns, accordion
panels), nest `FormModel`s as fields of a parent `FormModel` and choose a
`layout=`. That is covered in full in `docs/complex_forms.md`; this page is the
reference for the layout values and the lower-level layout primitives.

## Form layouts (`layout=`)

Pass `layout=` to `render_form_html()`, `FormModel.render_form()`, or
`FormModel.validate()` (so `render_with_errors()` keeps it).

| Value | Result |
|---|---|
| `vertical` (default) | Fields stacked; each sub-form is a titled section |
| `tabbed` | The parent's plain fields in a first tab, then one tab per sub-form |
| `side-by-side` | The same groups as columns |
| `accordion` | The same groups as collapsible panels |
| `wizard` | The same groups as steps shown one at a time, with Back/Next |

```python
from pydantic_schemaforms import render_form_html

html = render_form_html(ProfileForm, layout="tabbed", submit_url="/profile")
```

`tabbed`, `side-by-side`, `accordion`, and `wizard` arrange *sub-forms*: fields typed as
another `FormModel`, a `list[FormModel]`, or a registered composite such as
`DataTableLayout`. On a form without any, they raise a `ValueError` asking you
to split the form into nested models. Groups follow field declaration order;
`ui_order` overrides it.

## Layout primitives (advanced)

Reusable HTML wrappers for composing arbitrary, already-rendered content, all
exported from the top-level package:

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
from pydantic_schemaforms import Layout

layout = Layout.create_grid(
    "<div>Left</div>",
    "<div>Right</div>",
    columns="1fr 2fr",
    gap="1rem",
)

html = layout.render(framework="bootstrap", renderer=my_renderer, data={}, errors={})
```

`LayoutComposer` (aliased as `Layout`) also exposes `create_horizontal()`, `create_vertical()`,
`responsive_grid()`, `create_tabs()`, and `create_accordion()`.

## Custom composite fields (`input_type="layout"`)

A field with `input_type="layout"` and a `layout_handler` is rendered by a
renderer you register. This is the extension point `DataTableLayout` uses; it
is for genuinely new controls, not for composing forms (nest models instead).

```python
from pydantic_schemaforms import LayoutEngine


@LayoutEngine.layout_renderer("my_layout", builtin=False)
def my_layout_renderer(field_name, field_schema, value, ui_info, context, engine):
    return "<div>Custom layout output</div>"
```

Then declare the field with `input_type="layout", layout_handler="my_layout"`.
The renderer receives the field's own error message as `context.error` and its
nested errors as `context.child_errors`. See `docs/plugin_hooks.md`.
