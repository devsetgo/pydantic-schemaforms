# Accessibility

Accessible forms are part of what this library ships, not an add-on: every
release is tested with [axe-core](https://github.com/dequelabs/axe-core), the
accessibility engine behind many enterprise audit tools, and a release can't
pass CI with a serious or critical violation on any example page.

!!! note "Testing, not a compliance claim"
    pydantic-schemaforms does not claim ADA, Section 508, EN 301 549 or WCAG
    conformance. Conformance is a property of your whole application (page
    layout, content, navigation, your own CSS) and needs manual review with
    assistive technology as well as automated tools. What this library gives
    you is form markup that is automatically tested against the WCAG A and AA
    rules axe can check, so the forms are a sound starting point for your own
    audit.

## What is tested

| | |
|---|---|
| **Engine** | axe-core 4.14.0, pinned by version and SHA-256 |
| **Rule sets** | WCAG 2.0, 2.1 and 2.2 at levels A and AA, plus axe's best-practice rules. axe maps the same rules to Section 508 and EN 301 549. |
| **Fails the build on** | Any violation axe rates *serious* or *critical* |
| **Pages** | Every page of the example app, which renders every input type, widget option, layout and composite control the library supports |
| **Styles** | Bootstrap and Material |
| **States** | The initial form and the error state after a failed submit (messages, `aria-invalid`, the error summary) |
| **When** | On every pull request, in the Playwright CI job |

The test lives in `tests/playwright/test_example_pages.py`. Run it locally with:

```bash
playwright install chromium
pytest tests/playwright/test_example_pages.py -k accessibility --no-cov -p no:xdist
```

## What the library guarantees

Every built-in input meets this baseline under Bootstrap, Material and plain HTML:

- **Every control has an accessible name.** A field's `title` becomes its
  `<label for=...>`; radio and checkbox groups use a `<fieldset>` with a
  `<legend>`. Controls without a visible label of their own, such as
  `DataTableLayout` cells, carry an `aria-label` ("Email, row 3").
- **Help and errors are announced with the field.** The control's
  `aria-describedby` points at its help text (`<id>-help`) and, after a failed
  submit, its error message (`<id>-error`), and the control gets
  `aria-invalid="true"`.
- **Text meets WCAG AA contrast** (4.5:1) in the default themes, including the
  tags input and the code editor's syntax colors.
- **Click targets are at least 24×24 px** (WCAG 2.2 target size), including
  icon buttons such as the date picker toggle.
- **Decorative layers stay out of the way.** Visual-only elements, such as the
  code editor's syntax-highlight layer, are `aria-hidden` and never take
  keyboard focus.

## What automated testing does not cover

Automated tools find only part of what a full WCAG audit covers. These are
not checked by the gate and are worth reviewing by hand in your application:

- **Keyboard flow** through multi-step and grouped layouts (wizard, tabs,
  accordion): focus order and where focus lands after a step change.
- **Screen reader announcements** of live (HTMX) validation as the user types.
- **Your own page**: the template, headings, landmarks, navigation and any
  colors or CSS you add around the form.
- **Content**: whether labels, help text and error messages are clear.
- **Moderate and minor** axe findings, which the gate reports to axe but does
  not fail on.

## Keeping your app accessible

- Give every field a `title` (or rely on the generated one from the field
  name); it becomes the label. Don't hide labels with CSS without giving the
  control another name.
- Keep the library's ARIA attributes when post-processing rendered HTML.
- Run axe-core against your own pages in your end-to-end tests. The pattern in
  `tests/playwright/test_example_pages.py` (inject `axe.min.js`, call
  `axe.run()`, fail on serious or critical violations) works in any
  Playwright suite.
- Custom inputs registered with `register_input_class` should follow the
  rules in `docs/plugin_hooks.md` so they keep the same baseline.

Found an accessibility problem in a built-in input or layout? Please open an
issue; it is treated as a bug.
