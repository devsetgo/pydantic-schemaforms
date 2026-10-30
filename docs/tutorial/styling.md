# Styling

The same form renders for three styles. Pick one with `framework=`:

```python
--8<-- "docs_src/tutorial/styling/frameworks.py"
```

=== "Bootstrap (recommended)"

    The default. The form uses Bootstrap 5's classes (`form-control`,
    `form-select`, `invalid-feedback`, ...), so it matches the rest of a
    Bootstrap site, and validation states, icons and the grouped layouts
    use Bootstrap's components.

    **Your page loads Bootstrap.** The form HTML contains the markup, not
    Bootstrap itself, so add Bootstrap's CSS and JS to your page template:

    ```html
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ```

    The tutorial's `include_framework_assets=True, asset_mode="cdn"` adds
    these two tags to the form itself, which is handy for a page that has no
    template.

=== "Material"

    A Material Design 3 look with floating labels, built into the library:
    the form carries its own styles, so your page needs nothing extra and
    no CSS framework. See [Material Design 3](../advanced/material.md) for the
    filled variant, the dark scheme and changing the colors.

=== "Plain HTML"

    `framework="none"` gives clean, semantic HTML with no framework classes,
    ready for your own CSS.

Use the same `framework=` in `validate()` so a failed submit re-renders in the
same style. The live demo can show any page in either style: add
`?style=material` to its address.

## Your own CSS

Every style keeps its markup predictable, so you can target it:

- the `<form>` has the class `pydantic-form` (Material: `md-form`);
- each input's `id` is its field name (`email`, `address.city`), and its help
  and error messages are `<id>-help` and `<id>-error`;
- `ui_class="..."` and `ui_style="..."` on a `Field()` add a class or inline
  style to that field's input.

??? note "Forms with no external files"

    `self_contained=True` inlines all of Bootstrap, its icons and the
    library's scripts into the form HTML: no CDN, no static files. That's
    useful for an offline app, an intranet without internet access or a
    sandboxed iframe, but it adds several hundred kilobytes to every page.
    See [Assets and Self-Contained Forms](../advanced/assets.md).

Next: [CSRF Protection](csrf.md).
