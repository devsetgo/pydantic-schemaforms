# Layout Primitives

To arrange a form's own fields, nest sub-forms and choose a `layout=`; see
[Layouts](../tutorial/layouts.md). The primitives on this page are for
something else: arranging pieces of HTML you've **already rendered** on a
page, such as two separate forms side by side.

```python
--8<-- "docs_src/advanced/layout_primitives/two_forms.py"
```

`Layout` (also exported as `LayoutComposer` and `LayoutFactory`) creates
each primitive; `.render()` returns its HTML:

| Factory | Primitive | Arranges content as |
|---|---|---|
| `Layout.create_horizontal(*content)` | `HorizontalLayout` | A row |
| `Layout.create_vertical(*content)` | `VerticalLayout` | A column |
| `Layout.create_grid(*content, columns=...)` | `GridLayout` | A CSS grid |
| `Layout.responsive_grid(*content)` | `ResponsiveGridLayout` | A grid that wraps on small screens |
| `Layout.create_tabs([...])` | `TabLayout` | Tabs, from `{"title": ..., "content": ...}` items |
| `Layout.create_accordion([...])` | `AccordionLayout` | Collapsible panels |
| `Layout.create_card(title, content)` | `CardLayout` | A card with a title |
| `Layout.create_modal(...)` | `ModalLayout` | A modal dialog |

!!! warning "Content is inserted as HTML"
    Titles are escaped, but **content is placed into the page as is**: the
    primitives are meant for HTML the library or your templates have already
    produced. Never pass text a user typed as content; build it with
    `html(t"...")` first, which escapes it.
