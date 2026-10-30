# Material Design 3

`framework="material"` renders every input, layout and composite as
[Material Design 3](https://m3.material.io) (the 2023 baseline). The form carries
its own CSS and script, and your page needs no CSS framework, web font or icon
font: icons are inline SVG.

## Outlined or filled

Text fields are outlined by default. Pass `material_variant="filled"` for filled
fields, the same way wherever you pass `framework=`:

```python
render_form_html(ContactForm, framework="material", material_variant="filled", submit_url="/contact")
```

Any other value raises `ValueError`.

## Dark scheme

Forms are light unless you opt in, in either of two ways:

- set `data-md-theme="dark"` on the form or any ancestor, such as `<html>`;
- declare `color-scheme: dark` on the page.

`data-md-theme` wins, so `data-md-theme="light"` keeps a form light on a dark page.

## Changing the colors

Every color comes from a `--md-sys-color-*` custom property on `.md-form`.
Override them for your brand:

```css
.md-form {
    --md-sys-color-primary: #00639b;
    --md-sys-color-on-primary: #ffffff;
    --md-sys-color-secondary-container: #d1e4ff;
    --md-sys-color-on-secondary-container: #001d36;
}
```

To keep the dark scheme working, set each one with `light-dark(<light>, <dark>)`.

| Token | Used for |
|---|---|
| `--md-sys-color-primary` / `on-primary` | Focused fields, checked controls, filled buttons, active tab |
| `--md-sys-color-secondary-container` / `on-secondary-container` | Selected chips and segments, tonal buttons, expanded accordion header |
| `--md-sys-color-error` / `error-container` / `on-error-container` | Invalid fields, the error summary, error banners |
| `--md-sys-color-surface-*` / `on-surface` / `on-surface-variant` | Backgrounds, cards, menus, text |
| `--md-sys-color-outline` / `outline-variant` | Field outlines, dividers |
| `--md-sys-shape-corner-*` | Corner radii |
| `--md-sys-typescale-font` / `-mono` | Font stacks |

Load your overrides after the form or with a more specific selector, because the
form's styles are inlined with the form.

## How controls are built

| Control | Material Design 3 component |
|---|---|
| Text, number, date, time, select, textarea | Text field: 56px box, label floating into a notch in the outline, supporting text below |
| Checkbox, radio | 18px box, 20px ring, 40px state layer |
| `toggle` | Switch: 52×32 track, label at the start of the row |
| `radio` with `variant="segmented"` | Segmented buttons |
| `checkbox_group` with `variant="button_group"` | Filter chips |
| `tags`, `multiselect` | Input chips; a `multiselect` menu is an elevated surface |
| `slider`, `range`, `rating` | 4px track with a 20px handle |
| `star_rating` | Radio group of 40px stars, arrow keys change the value |
| `file` | Dashed drop zone with a tonal button |
| Submit, Next | Filled button |
| Back | Outlined button |
| Add item, Load CSV | Tonal button |
| Sub-forms and list items | Outlined cards; collapsible ones use `<details>` |
| Tabs, accordion, wizard | Primary tabs, divided list, numbered stepper |

## What isn't Material Design 3

- A `select` opens the browser's own menu; only the closed field is styled.
- Native date and time inputs open the browser's own picker.
- Browsers without CSS `:has()` show the label above the field instead of floating it.
