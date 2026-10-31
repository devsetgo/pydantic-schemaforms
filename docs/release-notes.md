# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

Versions follow **CalVer**: `YY.Quarter.Build` — e.g. `26.2.1` = year 2026, quarter 2, build 1.
Beta releases append `.beta` (e.g. `26.2.1.beta`); production releases have no suffix.

## [Unreleased]

## [26.4.4] — 2026-10-31

The Material style is rebuilt on Material Design 3 and shares one rendering path
with Bootstrap and plain HTML. A checkbox can now be required with `Literal[True]`.
This is a breaking release for apps that customize Material forms.

### 💥 Breaking Changes

- **`framework="material"` is rewritten on Material Design 3 and now renders
  through the same path as Bootstrap and plain.** Every input gets a Material
  field: outlined with a floating label and a real notch, with error, disabled
  and icon states. The CSS uses design tokens (`--md-sys-color-*`) and has no
  `!important`. CSS written against the old Material markup needs updating. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- **`MaterialEmbeddedTheme` is renamed `MaterialTheme`.** Update any import or
  subclass of it. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))

### 🔄 Changed

- **Star rating stars are now buttons in every style**, in a `radiogroup` with
  arrow-key support, so the widget works from the keyboard. The default
  colors are darker, to meet contrast requirements. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))

### ✨ Added

- `Field(unchecked_message="...")` sets the error shown when a required checkbox
  is left unticked. ([#273](https://github.com/devsetgo/pydantic-schemaforms/pull/273))
- Radio `variant="segmented"` and checkbox group `variant="button_group"` now
  ship their own CSS instead of leaving it to the app. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- `docs/advanced/material.md` documents the Material style. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- `material_variant="filled"` selects filled text fields (the default is
  `"outlined"`). ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- Opt-in dark mode for Bootstrap forms: under `data-bs-theme="dark"` the library's
  widgets, tabs, accordion and wizard now follow Bootstrap's dark colors. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- `--sf-*` CSS tokens re-color those same parts under Bootstrap. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- Opt-in dark scheme for Material: `data-md-theme="dark"` on the form or an
  ancestor, or the page's `color-scheme`. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))

### 🐛 Fixed

- A checkbox typed `Literal[True]` can now pass validation: ticking it used to
  fail with "Input should be True". This is the way to require a box to be ticked,
  such as accepting terms. ([#273](https://github.com/devsetgo/pydantic-schemaforms/pull/273))
- Material forms now submit to the server and show every error at once, like
  Bootstrap. They used to drop `novalidate`, so the browser stopped a single-page
  form at its first invalid field. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- A model list item's title no longer goes through `innerHTML` as the user
  types, so markup in a title field can't run in the page. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))
- Material: invalid fields now get a red outline, and textareas, radios,
  multiselects, comboboxes and data tables are no longer unstyled. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))

### 🗑️ Removed

- **Materialize is no longer vendored or referenced.** The Material style has
  long used its own self-contained theme and never loaded Materialize, but the
  package still shipped Materialize 1.0.0 (about 320 KB), a
  `vendor-update-materialize` make target, and a Materialize config behind
  `framework_css_tag`/`framework_js_tag`. They're gone: both functions now
  return nothing for `"material"`, and `get_theme_for_framework("material")`
  returns the Material theme the renderer actually uses. ([#265](https://github.com/devsetgo/pydantic-schemaforms/pull/265))

## [26.4.3] — 2026-10-29

`FormModel` is now the only way to build a form: the builder API, the
prebuilt forms, `@form_validator` and the React/Vue adapters are removed.
Five Agent Skills ship inside the package, and a long list of form bugs is
fixed. This is a breaking release; see `docs/upgrading.md`.

### 💥 Breaking Changes

- **React and Vue adapters removed.** `ReactJSONSchemaFormAdapter`,
  `VueFormulateAdapter`, and their modules
  (`integration.json_schema_form_adapter`, `integration.vue_formulate_adapter`,
  and the `integration.react`/`integration.vue` shims) are deleted, along with
  the React/Vue-only helpers `map_ui_element_to_framework` and
  `convert_validation_rules`. They produced config blobs for client-side form
  libraries, outside this library's server-rendered scope, and had no examples
  or docs. For a JSON Schema of a form, use `FormModel.get_json_schema()`;
  for a plain Pydantic model, use `FormModel.as_api_model()`. ([#248](https://github.com/devsetgo/pydantic-schemaforms/pull/248))
- **The builder API is removed; `FormModel` is the only way to build a form.**
  `FormBuilder`, `AutoFormBuilder`, `create_form_from_model`,
  `create_login_form`, `create_registration_form`, `create_contact_form`,
  `render_form_page`, `FormIntegration`, `handle_form` and `handle_form_async`
  are deleted, along with `ModernFormRenderer`, `FormDefinition` and
  `FormSection` (which only existed to render builder forms) and the
  `integration.builder`/`adapters`/`sync`/`async_support` modules. The builder
  rendered through its own path, so it never got `layout=`, the wizard, nested
  sub-forms, `model_list` or `DataTableLayout`. To upgrade: declare a
  `FormModel` (or build one at runtime with Pydantic's
  `create_model(..., __base__=FormModel)`), render it with `render_form_html()`
  and handle submissions with `FormModel.validate()` and
  `result.render_with_errors()`. See `docs/upgrading.md`. Importing any
  removed name raises an `ImportError` that names its replacement. ([#255](https://github.com/devsetgo/pydantic-schemaforms/pull/255))
- **`@form_validator` is removed.** It never ran: nothing called the methods
  it decorated, so cross-field checks written with it were silently skipped.
  Use Pydantic's `@model_validator(mode="after")` (its message lands in the
  form-wide `_errors`) or `FormValidator.add_cross_field_rule`. ([#254](https://github.com/devsetgo/pydantic-schemaforms/pull/254))
- **`DataTableLayout` input names are namespaced by the embedding field.**
  Cells, the CSV file input and the Load/Submit buttons used to have fixed
  names (`rows[i].col`, `csv_file`, `datatable_action`), so two tables on one
  page overwrote each other. They are now named under the field the table is
  embedded in (an `employees` field submits `employees.rows[i].col`,
  `employees.csv_file`, `employees.datatable_action`), and the default table
  id comes from the field name instead of the row model's class name.
  `handle_import_post()` and `parse_submitted_rows()` find their table in the
  submission themselves, so app code using them doesn't change. Code that
  reads those form keys directly, or builds test submissions by hand, must use
  the new names. When two tables share a row model, pass the new
  `field=` argument to say which one to read. ([#253](https://github.com/devsetgo/pydantic-schemaforms/pull/253))

### ✨ Added

- **Agent Skills ship inside the package.** `uvx library-skills --claude`
  installs five skills into an app project, linked to the installed version:
  `pydantic-schemaforms` (build and fix forms, with references for inputs,
  complex forms, validation, data tables, security, rendering and extending),
  `schemaforms-create` (a new form from a description such as "create a login
  form", commented like a tutorial), `schemaforms-convert` (from Pydantic,
  dataclasses, JSON Schema, WTForms or Django), `schemaforms-upgrade` (from
  removed APIs) and `schemaforms-document` (docstrings, help text and a
  Markdown page for an app's forms). The single-file instructions from
  `get_app_instructions()` and the CLI are now built from the same sources,
  and their examples come from tested files. ([#264](https://github.com/devsetgo/pydantic-schemaforms/pull/264))
- **Accessibility gate.** The Playwright suite runs axe-core 4.14 against
  WCAG 2.0, 2.1 and 2.2 A and AA rules plus axe best practices on every
  example page under Bootstrap and Material, plus the validation page's error
  state, and fails on any serious or critical violation. axe-core is vendored
  for tests only (`tests/playwright/vendor/`, pinned by version and SHA-256);
  it is not shipped in the package. What is tested, the baseline the inputs
  meet, and what automated testing does not cover are in the new
  `docs/reference/accessibility.md` page and the README. This is testing, not a claim of
  ADA, Section 508 or WCAG conformance. ([#246](https://github.com/devsetgo/pydantic-schemaforms/pull/246))

### 🐛 Fixed

- **Two tabbed or accordion forms on one page no longer collide.** Tab and
  accordion ids were numbered from `tab-0`/`accordion-0` in every form, so
  the second form's tabs and panels controlled the first form's. Each layout
  now gets its own id prefix, and tab and accordion scripts only act inside
  their own layout (which also stops an outer tab hiding a nested tabbed
  sub-form). ([#252](https://github.com/devsetgo/pydantic-schemaforms/pull/252))
- **Accordion fixes:** under Bootstrap the open section rendered closed, and
  under plain HTML and Material clicking a section header submitted the
  form. ([#252](https://github.com/devsetgo/pydantic-schemaforms/pull/252))
- **Invalid fields are announced.** After a failed submit, a field's control
  gets `aria-invalid="true"` and an `aria-describedby` pointing at its error
  message, and at its help text whenever it has one, under Bootstrap,
  Material and plain HTML. Help and error elements now carry matching
  `<id>-help` / `<id>-error` ids. ([#246](https://github.com/devsetgo/pydantic-schemaforms/pull/246))
- **`DataTableLayout` cells have accessible names.** Each editable cell gets
  an `aria-label` such as "Email, row 3", since its column header is not a
  `<label>`. ([#246](https://github.com/devsetgo/pydantic-schemaforms/pull/246))
- **The tags input's label names its text box.** The visible text box now
  takes the field's id, so `<label for=...>` points at it, and it receives
  the `aria-*` wiring above. ([#246](https://github.com/devsetgo/pydantic-schemaforms/pull/246))
- **The code editor's highlight layer no longer takes keyboard focus.** It is
  `aria-hidden`, but Prism made it tabbable. ([#246](https://github.com/devsetgo/pydantic-schemaforms/pull/246))
- **Contrast meets WCAG AA (4.5:1)** for tag chips, the code editor's
  property/tag syntax color and the "Rendered in" timing line. ([#246](https://github.com/devsetgo/pydantic-schemaforms/pull/246))
- **The date picker toggle is a 24×24 px target** (WCAG 2.2 target size). ([#246](https://github.com/devsetgo/pydantic-schemaforms/pull/246))
- **Inputs are inferred from more field types.** Without a `ui_element`,
  `date`, `datetime`, `time`, `EmailStr` and `AnyUrl` fields render as date,
  datetime-local, time, email and URL inputs; `Enum` and `Literal` fields render
  as a select with their values; and a `list` of either renders as a
  multiselect. `Optional` fields keep their input type instead of falling back
  to a text box. Previously an `Enum` field rendered an empty section (or a
  select with no options), so its choices had to be built by hand. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **A fresh form shows the model's defaults.** When no `form_data` is
  passed, every field starts at its default (an `int = 1` shows 1, an Enum or
  `Literal` default is selected, a `bool = True` checkbox is ticked,
  `default_factory` values included). Passed data, such as a submission being
  re-rendered or an edit form, is still used as is. Previously defaults were
  never rendered, so they had to be passed in `form_data` by hand. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **Validator messages are shown as written.** A `ValueError` raised in a
  `@field_validator` or `@model_validator` shows its own message, without
  Pydantic's "Value error, " prefix. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **Optional selects can be left empty.** An `Optional` select gets an empty
  first choice, and submitting it validates to `None`, including for
  `str`-based enums. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **An `Enum` field keeps its title** when it matches the Enum class's name
  (`Field(title="Size")` on a `Size` enum), including inside list items; it
  used to fall back to the field name. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **Material renders datetime fields as `datetime-local`**, not the invalid
  `datetime` input type. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **Pre-filling an `Enum` field selects its option.** `form_data` holding an
  Enum member, as a database row or `model_dump()` does, used to leave the
  select (or radio) with nothing chosen. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **A checkbox that defaults to `True` can be unticked.** An unticked
  checkbox sends nothing, so `validate()` used to fill in the default and
  return `True`. In a form submission, a missing checkbox that has a default
  is now `False`; one without a default is still required, and nested JSON
  that omits it still gets the default. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **An optional sub-form (`Address | None`) can be left empty.** Its inputs
  are no longer `required`, and when every one of them is blank or still at
  its default, `validate()` returns `None` for it instead of field errors.
  ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **A `currency` input works on a `Decimal`, `float` or `int` field.** The
  input formats what is typed as `$1,234.50`, which used to fail validation
  as "Input should be a valid decimal". In a form submission the symbol and
  thousands separators are now stripped first. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **A `float` field accepts decimals in the browser.** Number inputs always
  had `step="1"`, so the browser refused 39.50. A `float` field now gets
  `step="any"`, and `multiple_of` sets the step. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **Material inputs carry the field's constraints.** `min_length`,
  `max_length`, `ge`, `le` and `pattern` now become `minlength`, `maxlength`,
  `min`, `max` and `pattern` attributes under Material too, as they already
  did under Bootstrap and plain HTML. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))
- **`MinLengthRule` skips an empty value**, like every other rule except
  `RequiredRule` and like its own client-side check. It used to reject `""`,
  so an optional field with a minimum length couldn't be left blank. ([#258](https://github.com/devsetgo/pydantic-schemaforms/pull/258))

## [26.4.1] — 2026-10-12

Complex forms are now built one way: nest `FormModel`s as fields of a parent
`FormModel` and pick a `layout=`. Data in and out is nested JSON. This is a
breaking release; see `docs/upgrading.md`.

### 💥 Breaking Changes

- **Form-orchestration classes removed.** `TabbedLayout`, `ListLayout`,
  `SectionDesign`, `FormDesign`, `FormLayoutBase`, and the `form_layouts`
  `VerticalLayout`/`HorizontalLayout` wrappers now raise
  `FormLayoutRemovedError` (a `TypeError`) when subclassed or called. The
  message contains the upgrade steps and points to the new "Upgrading to
  nested forms" section of the AI instructions.
- **Top-level `VerticalLayout`/`HorizontalLayout`** now name the flex layout
  primitives from `rendering/layout_engine.py`, which the removed wrappers
  used to shadow.
- **`pydantic_schemaforms.layouts`** (the deprecated re-export shim) is deleted.
- **`FormModel.validate(flatten=...)` removed.** `result.data` is always nested
  like the model. Passing `flatten` raises a `TypeError` explaining this.
- **`ValidationResult.errors` is a nested error tree** shaped like the data
  (`errors["pets"][1]["name"]`) instead of string-path keys
  (`errors["pets[1].name"]`). Container and form-wide messages use the
  reserved `"_errors"` key instead of `"general"`.
- **`layout="tabbed"`/`"side-by-side"` group sub-forms.** The field-name
  keyword heuristic and the two-fields-per-row pairing are gone; on a form
  with no sub-form fields these layouts raise `ValueError`. Several
  `input_type="layout"` fields no longer auto-render as tabs; pass
  `layout="tabbed"`.
- **Unknown `layout=` values raise `ValueError`** instead of rendering vertically.
- **Non-validation exceptions propagate from `validate()`** instead of being
  shown on the form as `errors["general"]`.
- **Renderer internals:** `RenderContext.all_errors` is replaced by
  `child_errors` (the field's own error sub-tree), and `render_field()` takes
  the field's error node as `error` with no `all_errors` argument.
  `get_nested_form_data`, `EnhancedFormRenderer._humanize_error_field`, and
  `FieldRenderer.extract_nested_errors_for_field` are removed.
- **`handle_form`/`handle_form_async` with a model** return nested data and a
  nested error tree. `FormValidator.validate_pydantic_model()` (which kept
  only the first segment of each error path) is removed.

### ✨ Added

- **Sub-form fields.** A field typed as another `FormModel` (or `Optional` of
  one) renders as a titled section with inputs named `address.city`, with no
  `ui_element` needed. `ui_collapsible`/`ui_collapsed` render it as a
  `<details>` section that opens when it holds an error.
- **Grouped layouts:** `layout="tabbed"`, `"side-by-side"`, and the new
  `"accordion"` arrange the parent's plain fields plus one group per sub-form,
  in declaration order (`ui_order` overrides). Re-rendering after a failed
  submit opens the first group that contains an error.
- **Step wizard:** `layout="wizard"` shows the same groups one step at a time
  with a progress header and Back/Next. All steps are in one `<form>`, so one
  POST submits everything. Next runs the browser's validation on the current
  step; a re-render opens the first step with an error and marks the others.
  Options: `wizard_options={"linear", "show_progress", "back_label",
  "next_label"}` and `Field(ui_step_title=...)`. Without JavaScript all steps
  show stacked.
- **Examples cover every layout, input, and validation**, enforced by
  `tests/test_examples_coverage.py` and a browser test that loads every
  example page: the widget gallery shows every input type and alias with each
  of its options plus field-level options (`ui_disabled`, `ui_readonly`,
  `icon`, ...); `/validation` shows every Pydantic constraint, validator, rule
  class, and a cross-field rule failing on one form; `/layouts` takes the
  wizard options as query parameters; `/employees/directory` shows the
  read-only `DataTableLayout` options.
- **`validate()` takes the raw request form** (Starlette `FormData`, Werkzeug
  `MultiDict`, `(name, value)` pairs) as well as nested dicts, keeping
  repeated values as lists. `render_form_html(form_data=...)` accepts the same.
- **`render_with_errors(errors=...)`** re-renders with a different error tree, e.g.
  the result's own errors merged with a rule-based `FormValidator`'s.
- **AI instructions** now list every `ui_options` key per widget with its default,
  every field-level option, the rule classes and cross-field rules, the
  `FormModel`/`ValidationResult` API, every render option, and the asset helpers.
- **`ValidationResult.error_list()`** (flat `[{"loc": [...], "msg": ...}]`) and
  **`ValidationResult.instance`** (the validated model).
- **`list[FormModel]` fields render as repeating sub-forms** without
  `ui_element="model_list"`.
- **`LiveValidator.register_model_validator()`** registers sub-form and
  list-item fields under their input names (`address.city`, `pets[].name`).
- **`validate_form_data`** is exported from the top-level package, as the
  validation guide already documented.
- **`docs/complex_forms.md`**, a guide to composing forms and upgrading.

### 🐛 Fixed

- Decoding a submission compacts list indices instead of padding gaps with
  `None`: `pets[0]` and `pets[2]` decode to a two-item list, so an item removed
  without re-indexing still validates, and one field named like
  `pets[500000000].name` no longer makes the server allocate a list that long.
- `validation_response_headers`, `wrap_with_schemaforms_markers`,
  `read_asset_text`, `bootstrap_icons_css_content` and `bootstrap_icons_css_tag`
  are exported from the top-level package; the docs and examples imported them
  from internal modules.
- Removing every item of a repeating sub-form now fails its `min_length`
  instead of passing as the field's default (form submissions only; nested
  JSON that omits the key still gets the default).
- Under `layout="tabbed"`/`"accordion"`/`"wizard"`, Material forms no longer
  let the browser block submission on a required input in a hidden group with
  no visible message; the server re-renders with that group open.
- A layout field's `default_factory` that raises is no longer silently
  swallowed (the table rendered empty); the error propagates.
- `radio` and `checkbox_group` never showed the current value: a re-rendered
  form lost the user's choices. A `combobox` lost its value the same way.
- A field declared `ui_element="hidden"` rendered a visible label (only
  `ui_hidden=True` produced a bare hidden input).
- Custom `date_format`/`time_format`/`datetime_format` were not applied to ISO
  string values (JSON data), which showed as `2024-06-15` instead of the format.
- The file input's preview script failed to parse (a `#` comment in
  JavaScript), so no preview appeared; it now shows file names as text, never
  as markup.
- Material: the colour picker's hex readout (`show_value`) was missing, and a
  `select` with a placeholder had its label overlapping the placeholder text.
- Switching tabs left the `active` class on the first panel.
- `Field(icon=...)`, like other non-Pydantic keywords, was silently dropped
  when any `ui_*` option was also passed.
- Material forms' inline script failed to parse (a `#` comment in
  JavaScript), so its floating-label and field enhancements never ran.
- `Field()` silently dropped any `ui_*` option it doesn't name as a parameter
  (such as `ui_collapsible`) when another `ui_*` option like `ui_help_text` was
  also passed. All `ui_*` options are now kept.
- Validation errors now reach fields inside sub-forms and are namespaced per
  sub-form, so two sub-forms with the same field name no longer collide.
- Library code no longer imports from the `examples/` package or hard-codes
  the demo app's field names.
- `DataTableLayout.parse_submitted_rows()` no longer turns cell values like
  `"1"` or `"yes"` into booleans before validation.
- The documented `FormConfig`/`TabbedLayout((...))` and
  `HorizontalLayout(label_cols=...)` recipes, which never worked, are replaced.
- Several documentation examples that interpolated submitted values into
  HTML with f-strings now use `html(t"...")`.

---

## [26.2.3] — 2026-06-28

### 🐛 Fixed

- **`LiveValidator.register_model_validator` partial-validation bug** — previously called
  `model_class.model_validate({field: value})` with only one field's data; if the model
  had other required fields, Pydantic raised `ValidationError` for them, causing all
  unrelated fields to produce `is_valid=False` with no errors even when the value was valid.
  Now uses `__pydantic_validator__.validate_assignment(model_construct(), field_name, value)`
  to validate each field in isolation, independent of sibling required fields.

- **`LiveValidator.render_field_with_live_validation` single-trigger limitation** — the
  `if/elif/elif` chain for `validate_on_blur` / `validate_on_input` / `validate_on_change`
  silently dropped every trigger after the first truthy one. Changed to independent `if`
  checks so all enabled triggers combine into a single `hx-trigger` attribute
  (e.g. `hx-trigger="blur, change"` when both are `True`).

### ✨ Added

- **Live-validation example** — `GET /live-validation` demo route in the FastAPI example
  app shows a contact form with per-field HTMX validation on blur. Includes
  `POST /validate/{field_name}` HTMX endpoint using `validation_response_headers()` and
  `GET /vendor/htmx.min.js` to serve the vendored HTMX asset.

---

## [26.2.2] — 2026-06-28

### ✨ Added

- **`FormModel.as_api_model()`** — new class method that returns a pure Pydantic `BaseModel`
  with `ui_*` rendering metadata stripped from `json_schema_extra`. Allows the same model
  class to serve both as an HTML form and as a typed FastAPI body / `response_model` without
  `ui_element`, `ui_placeholder`, etc. appearing in the OpenAPI/Swagger docs.
  `Field(title=...)`, `Field(examples=[...])`, descriptions, and all validation constraints
  (`min_length`, `ge`, `pattern`, …) are fully preserved. Result is cached per subclass and
  safe to assign at module level (`ContactSchema = ContactForm.as_api_model()`).

### 🔄 Changed

- Reduced SonarCloud code smells: extracted duplicate magic strings to named constants,
  prefixed unused parameters with `_`, renamed methods that shadowed class attributes,
  and merged nested `if` statements into compound conditions across multiple modules.

---

## [26.2.1] — 2026-05-17

First production release. All public Quick Start code paths verified working end-to-end.

### 💥 Breaking Changes

- `submit_url` is now explicit across public form render APIs and no longer defaults silently.
  Calls that omit `submit_url` raise a clear `ValueError`, enforcing app-owned routing boundaries.

### ✨ Added

- **HTMX live validation** — `LiveValidator`, `HTMXValidationConfig`, and `validation_response_headers()`
  provide server-side field validation triggered by blur/input events via HTMX without page reloads.
- **Branch coverage** — `branch = true` added to coverage configuration for deeper test quality.
- **HTML structural validation** — `tests/test_html_structural.py` validates tag balance across all
  frameworks and field types.
- **HTTP integration tests** — FastAPI `TestClient` and Flask `test_client` round-trip tests.
- **Property-based tests** — Hypothesis suite covering arbitrary field names, labels, and frameworks.
- **Performance benchmarks** — `pytest-benchmark` suite for small, medium, and large form rendering.
- **Playwright browser tests** — End-to-end HTMX validation tests against a live FastAPI server
  (`tests/playwright/`), running in CI on Chromium.
- **macOS in CI matrix** — Tests now run on ubuntu-latest, windows-latest, and macos-latest.
- `py.typed` marker for PEP 561 compatibility.
- Vendored assets (htmx, Bootstrap, Materialize, iMask) with sha256 manifest verification.
- `.gitattributes` forcing LF line endings on vendored assets for cross-platform checksum stability.

### 🐛 Fixed

- **`create_form_from_model` crashed with any Pydantic model** — `AutoFormBuilder._build_from_model`
  used the wrong parameter name (`default_value` instead of `value`) and compared against `...`
  instead of `PydanticUndefined`; the sentinel leaked into `json_schema_extra`, causing
  `PydanticSerializationError` on every render call.
- Windows path separator in test assertion caused CI failure on win32.
- Dependabot config used unsupported `interval: "cron"` — silently ignored, causing weekly runs.
  Replaced with `interval: "monthly"`.
- HTMX live validation JS used `JSON.parse(responseText)` on HTML responses; replaced with
  the idiomatic `HX-Trigger: validationResult` header pattern so CSS classes are applied correctly.
- `except A, B:` tuple syntax preserved via `# fmt: skip` to prevent ruff from removing parentheses
  that pyright requires.

### 🔄 Changed

- Layout rendering internals refactored for maintainability and reduced cognitive complexity.
- Reliability and maintainability improvements to satisfy SonarCloud quality gate.
- Improved nested/collapsible form behavior when multiple forms are rendered on a page.
- Pre-commit ruff version pinned to match `requirements.txt` to eliminate local/CI formatting drift.
- Pyright added to `make tests` so type errors surface before commit.

### ⬆️ Dependencies

- `fastapi[all]`: `0.121.2` → `0.128.4`
- `ruff`: `0.14.14` → `0.15.0`
- `tqdm`: `4.67.1` → `4.67.3`
- `pytest-html`: `4.1.1` → `4.2.0`
- `packaging`: `25.0` → `26.0`
- `black`: `25.12.0` → `26.1.0`
- `mkdocstrings[python]`: `1.0.0` → `1.0.1`
- `pymdown-extensions`: `10.20` → `10.20.1`

## Latest Changes

## 🚀 Production Releases

### 🚀 [26.4.2 · Support for Python 3.15](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.4.2)

📅 Published 2026 October 24, 21:09

#### 🎁 Changes
- Test: Update Coverage XML Timestamp ([#231](https://github.com/devsetgo/pydantic-schemaforms/pull/231)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Documentation: Clarify Python Requirement, Asset Modes, Examples, and Testing Workflow ([#234](https://github.com/devsetgo/pydantic-schemaforms/pull/234)) ([@devsetgo](https://github.com/devsetgo))
- Documentation: Remove Stale 26.4.1 Release-Notes Draft From Repo Root ([#232](https://github.com/devsetgo/pydantic-schemaforms/pull/232)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Chore: Bump Version To 26.4.2 For Python 3.15 Support ([#233](https://github.com/devsetgo/pydantic-schemaforms/pull/233)) ([@devsetgo](https://github.com/devsetgo))
- Documentation: Remove Stale 26.4.1 Release-Notes Draft From Repo Root ([#232](https://github.com/devsetgo/pydantic-schemaforms/pull/232)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo)

### 🚀 [26.3.7 · Enhancement: Collapse and Select Improvements](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.7)

📅 Published 2026 August 29, 22:05

#### 🎁 Changes
- Update project dependencies and configurations ([#219](https://github.com/devsetgo/pydantic-schemaforms/pull/219)) ([@devsetgo](https://github.com/devsetgo))

#### ✨ Features

- Add collapsible option groups and menu order example for checkboxes/radios ([#221](https://github.com/devsetgo/pydantic-schemaforms/pull/221)) ([@devsetgo](https://github.com/devsetgo))
- Add optional forced-selection placeholder to select dropdowns ([#220](https://github.com/devsetgo/pydantic-schemaforms/pull/220)) ([@devsetgo](https://github.com/devsetgo))

#### 🐛 Bug Fixes

- Expand and improve AI assistant app-building instructions ([#218](https://github.com/devsetgo/pydantic-schemaforms/pull/218)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Bump version to 26.3.7 ([#223](https://github.com/devsetgo/pydantic-schemaforms/pull/223)) ([@devsetgo](https://github.com/devsetgo))
- Dev ([#222](https://github.com/devsetgo/pydantic-schemaforms/pull/222)) ([@devsetgo](https://github.com/devsetgo))
- Add collapsible option groups and menu order example for checkboxes/radios ([#221](https://github.com/devsetgo/pydantic-schemaforms/pull/221)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Bump version to 26.3.7 ([#223](https://github.com/devsetgo/pydantic-schemaforms/pull/223)) ([@devsetgo](https://github.com/devsetgo))
- Dev ([#222](https://github.com/devsetgo/pydantic-schemaforms/pull/222)) ([@devsetgo](https://github.com/devsetgo))
- Add collapsible option groups and menu order example for checkboxes/radios ([#221](https://github.com/devsetgo/pydantic-schemaforms/pull/221)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo) and [@claude](https://github.com/claude)

### 🚀 [26.3.6 · Browser Cache Bug](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.6)

📅 Published 2026 August 23, 21:17

#### 🎁 Changes
#### 🐛 Bug Fixes

- Reset CSV import page to blank state on each new visit ([#216](https://github.com/devsetgo/pydantic-schemaforms/pull/216)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Reset CSV import page to blank state on each new visit ([#216](https://github.com/devsetgo/pydantic-schemaforms/pull/216)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Reset CSV import page to blank state on each new visit ([#216](https://github.com/devsetgo/pydantic-schemaforms/pull/216)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo) and [@claude](https://github.com/claude)

### 🚀 [26.3.5 · Bug Fix: CSV Import](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.5)

📅 Published 2026 August 23, 20:54

#### 🎁 Changes
#### 🐛 Bug Fixes

- Fix DataTableLayout to submit all pages during large data imports ([#215](https://github.com/devsetgo/pydantic-schemaforms/pull/215)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Fix DataTableLayout to submit all pages during large data imports ([#215](https://github.com/devsetgo/pydantic-schemaforms/pull/215)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Fix DataTableLayout to submit all pages during large data imports ([#215](https://github.com/devsetgo/pydantic-schemaforms/pull/215)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo) and [@claude](https://github.com/claude)

### 🚀 [26.3.4 · Enhancement: CSV Import](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.4)

📅 Published 2026 August 23, 19:08

#### 🎁 Changes
#### 📝 Documentation

- Deep documentation pass across library, examples, and docs ([#213](https://github.com/devsetgo/pydantic-schemaforms/pull/213)) ([@devsetgo](https://github.com/devsetgo))
- Add DataTableLayout composite control for CSV import to table ([#212](https://github.com/devsetgo/pydantic-schemaforms/pull/212)) ([@devsetgo](https://github.com/devsetgo))
- Demo Application and MonoRepo ([#207](https://github.com/devsetgo/pydantic-schemaforms/pull/207)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Bump of Version to 26.3.4 ([#214](https://github.com/devsetgo/pydantic-schemaforms/pull/214)) ([@devsetgo](https://github.com/devsetgo))
- Deep documentation pass across library, examples, and docs ([#213](https://github.com/devsetgo/pydantic-schemaforms/pull/213)) ([@devsetgo](https://github.com/devsetgo))
- Add DataTableLayout composite control for CSV import to table ([#212](https://github.com/devsetgo/pydantic-schemaforms/pull/212)) ([@devsetgo](https://github.com/devsetgo))
- Demo Application and MonoRepo ([#207](https://github.com/devsetgo/pydantic-schemaforms/pull/207)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo) and [@claude](https://github.com/claude)

### 🚀 [26.3.3 · Enhancements to JSON output and new input types](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.3)

📅 Published 2026 August 07, 21:33

#### 🎁 Changes
#### ✨ Features

- Fix register\_input\_class registry and expand AI-assistant instructions ([#202](https://github.com/devsetgo/pydantic-schemaforms/pull/202)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Add code/data mode to TextArea: format + optional syntax highlighting ([#205](https://github.com/devsetgo/pydantic-schemaforms/pull/205)) ([@devsetgo](https://github.com/devsetgo))
- Refactoring Live Validation to Simplify ([#204](https://github.com/devsetgo/pydantic-schemaforms/pull/204)) ([@devsetgo](https://github.com/devsetgo))
- Add option for DNS and MX email deliverability validation ([#203](https://github.com/devsetgo/pydantic-schemaforms/pull/203)) ([@devsetgo](https://github.com/devsetgo))
- Fix register\_input\_class registry and expand AI-assistant instructions ([#202](https://github.com/devsetgo/pydantic-schemaforms/pull/202)) ([@devsetgo](https://github.com/devsetgo))
- 187 enhance date datetime and time ([#192](https://github.com/devsetgo/pydantic-schemaforms/pull/192)) ([@devsetgo](https://github.com/devsetgo))
- 189 enhancement json schema model output ([#191](https://github.com/devsetgo/pydantic-schemaforms/pull/191)) ([@devsetgo](https://github.com/devsetgo))
- Dev ([#185](https://github.com/devsetgo/pydantic-schemaforms/pull/185)) ([@devsetgo](https://github.com/devsetgo))

#### 👷 GitHub Actions

- Refactoring Live Validation to Simplify ([#204](https://github.com/devsetgo/pydantic-schemaforms/pull/204)) ([@devsetgo](https://github.com/devsetgo))
- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.2.0 to 8.2.1 ([#193](https://github.com/devsetgo/pydantic-schemaforms/pull/193)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/labeler from 6 to 7 ([#194](https://github.com/devsetgo/pydantic-schemaforms/pull/194)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.5.1 to 7.7.0 ([#195](https://github.com/devsetgo/pydantic-schemaforms/pull/195)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/setup-python from 6 to 7 ([#196](https://github.com/devsetgo/pydantic-schemaforms/pull/196)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- Dev ([#185](https://github.com/devsetgo/pydantic-schemaforms/pull/185)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Bump version to 26.3.3 ([#206](https://github.com/devsetgo/pydantic-schemaforms/pull/206)) ([@devsetgo](https://github.com/devsetgo))
- Add code/data mode to TextArea: format + optional syntax highlighting ([#205](https://github.com/devsetgo/pydantic-schemaforms/pull/205)) ([@devsetgo](https://github.com/devsetgo))
- Refactoring Live Validation to Simplify ([#204](https://github.com/devsetgo/pydantic-schemaforms/pull/204)) ([@devsetgo](https://github.com/devsetgo))
- Add option for DNS and MX email deliverability validation ([#203](https://github.com/devsetgo/pydantic-schemaforms/pull/203)) ([@devsetgo](https://github.com/devsetgo))
- Fix register\_input\_class registry and expand AI-assistant instructions ([#202](https://github.com/devsetgo/pydantic-schemaforms/pull/202)) ([@devsetgo](https://github.com/devsetgo))
- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.2.0 to 8.2.1 ([#193](https://github.com/devsetgo/pydantic-schemaforms/pull/193)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/labeler from 6 to 7 ([#194](https://github.com/devsetgo/pydantic-schemaforms/pull/194)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.5.1 to 7.7.0 ([#195](https://github.com/devsetgo/pydantic-schemaforms/pull/195)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/setup-python from 6 to 7 ([#196](https://github.com/devsetgo/pydantic-schemaforms/pull/196)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- 187 enhance date datetime and time ([#192](https://github.com/devsetgo/pydantic-schemaforms/pull/192)) ([@devsetgo](https://github.com/devsetgo))
- pip(deps): bump pymdown-extensions from 11.0 to 11.0.1 ([#201](https://github.com/devsetgo/pydantic-schemaforms/pull/201)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump hatchling from 1.30.1 to 1.31.0 ([#200](https://github.com/devsetgo/pydantic-schemaforms/pull/200)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- 189 enhancement json schema model output ([#191](https://github.com/devsetgo/pydantic-schemaforms/pull/191)) ([@devsetgo](https://github.com/devsetgo))
- Dev ([#185](https://github.com/devsetgo/pydantic-schemaforms/pull/185)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo), [@dependabot[bot]](https://github.com/apps/dependabot) and [@claude](https://github.com/claude)

### 🚀 [26.3.2 · New Input Types and Bug Fixes](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.2)

📅 Published 2026 July 19, 18:46

#### 🎁 Changes
#### 🐛 Bug Fixes

- Feature: Fix ui\_element registry collisions; expand AI assistant docs with a verified example ([#180](https://github.com/devsetgo/pydantic-schemaforms/pull/180)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Dev ([#183](https://github.com/devsetgo/pydantic-schemaforms/pull/183)) ([@devsetgo](https://github.com/devsetgo))
- Add Tier-2 input widgets and Widget Gallery example, fix Material bugs ([#181](https://github.com/devsetgo/pydantic-schemaforms/pull/181)) ([@devsetgo](https://github.com/devsetgo))
- Feature: Fix ui\_element registry collisions; expand AI assistant docs with a verified example ([#180](https://github.com/devsetgo/pydantic-schemaforms/pull/180)) ([@devsetgo](https://github.com/devsetgo))

#### 👷 GitHub Actions

- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.1.0 to 8.2.0 ([#172](https://github.com/devsetgo/pydantic-schemaforms/pull/172)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/checkout from 5 to 7 ([#169](https://github.com/devsetgo/pydantic-schemaforms/pull/169)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.3.1 to 7.5.1 ([#170](https://github.com/devsetgo/pydantic-schemaforms/pull/170)) (@[dependabot[bot]](https://github.com/apps/dependabot))

#### 🔧 Maintenance

- Dev ([#183](https://github.com/devsetgo/pydantic-schemaforms/pull/183)) ([@devsetgo](https://github.com/devsetgo))
- Dev ([#182](https://github.com/devsetgo/pydantic-schemaforms/pull/182)) ([@devsetgo](https://github.com/devsetgo))
- Add Tier-2 input widgets and Widget Gallery example, fix Material bugs ([#181](https://github.com/devsetgo/pydantic-schemaforms/pull/181)) ([@devsetgo](https://github.com/devsetgo))
- Feature: Fix ui\_element registry collisions; expand AI assistant docs with a verified example ([#180](https://github.com/devsetgo/pydantic-schemaforms/pull/180)) ([@devsetgo](https://github.com/devsetgo))
- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.1.0 to 8.2.0 ([#172](https://github.com/devsetgo/pydantic-schemaforms/pull/172)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest-asyncio from 1.3.0 to 1.4.0 ([#173](https://github.com/devsetgo/pydantic-schemaforms/pull/173)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi from 0.138.1 to 0.139.0 ([#171](https://github.com/devsetgo/pydantic-schemaforms/pull/171)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest from 9.0.3 to 9.1.1 ([#174](https://github.com/devsetgo/pydantic-schemaforms/pull/174)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/checkout from 5 to 7 ([#169](https://github.com/devsetgo/pydantic-schemaforms/pull/169)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.3.1 to 7.5.1 ([#170](https://github.com/devsetgo/pydantic-schemaforms/pull/170)) (@[dependabot[bot]](https://github.com/apps/dependabot))

#### 🙌 Contributors
[@dependabot](https://github.com/dependabot)[bot], [@devsetgo](https://github.com/devsetgo) and [dependabot[bot]](https://github.com/apps/dependabot)

### 🚀 [26.3.1 · America 250 Release: Adding AI Help Instructions and Clean Up.](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.1)

📅 Published 2026 July 03, 23:12

#### 🎁 Changes

Happy 250th Birthday USA!!!!

#### ✨ Features

- Enhancement: Adding AI Helper Documentation ([#177](https://github.com/devsetgo/pydantic-schemaforms/pull/177)) ([@devsetgo](https://github.com/devsetgo))
- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))

#### 🐛 Bug Fixes

- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Enhancement: Adding AI Helper Documentation ([#177](https://github.com/devsetgo/pydantic-schemaforms/pull/177)) ([@devsetgo](https://github.com/devsetgo))
- Documentation Fix ([#168](https://github.com/devsetgo/pydantic-schemaforms/pull/168)) ([@devsetgo](https://github.com/devsetgo))
- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))
- Production Release - Final Edits ([#166](https://github.com/devsetgo/pydantic-schemaforms/pull/166)) ([@devsetgo](https://github.com/devsetgo))

#### 👷 GitHub Actions

- Enhancement: Adding AI Helper Documentation ([#177](https://github.com/devsetgo/pydantic-schemaforms/pull/177)) ([@devsetgo](https://github.com/devsetgo))
- Documentation Fix ([#168](https://github.com/devsetgo/pydantic-schemaforms/pull/168)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Enhancement: Adding AI Helper Documentation ([#177](https://github.com/devsetgo/pydantic-schemaforms/pull/177)) ([@devsetgo](https://github.com/devsetgo))
- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))
- Production Release - Final Edits ([#166](https://github.com/devsetgo/pydantic-schemaforms/pull/166)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo)

### 🚀 [26.2.4 · Live Validation Fix, Example, and Doc Updates](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.2.4)

📅 Published 2026 June 28, 14:32

#### 🎁 Changes
#### ✨ Features

- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))

#### 🐛 Bug Fixes

- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))

#### 📝 Documentation

- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- Fix: Live Validation ([#167](https://github.com/devsetgo/pydantic-schemaforms/pull/167)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo)

### 🚀 [26.2.1.beta · CSRF Feature Release](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.2.1.beta)

📅 Published 2026 April 26, 19:26

#### 🎁 Changes
- Documentation Updates ([#116](https://github.com/devsetgo/pydantic-schemaforms/pull/116)) ([@devsetgo](https://github.com/devsetgo))

#### ✨ Features

- bump to v26.2.1.beta ([#117](https://github.com/devsetgo/pydantic-schemaforms/pull/117)) ([@devsetgo](https://github.com/devsetgo))
- CSRF Feature ([#114](https://github.com/devsetgo/pydantic-schemaforms/pull/114)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- feat(csrf): add CSRFMode enum with backward-compatible mode handling ([#115](https://github.com/devsetgo/pydantic-schemaforms/pull/115)) ([@devsetgo](https://github.com/devsetgo))
- pip(deps): bump tox from 4.52.0 to 4.52.1 ([#104](https://github.com/devsetgo/pydantic-schemaforms/pull/104)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump python-multipart from 0.0.24 to 0.0.26 ([#106](https://github.com/devsetgo/pydantic-schemaforms/pull/106)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/upload-pages-artifact from 4 to 5 ([#107](https://github.com/devsetgo/pydantic-schemaforms/pull/107)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mike from 2.1.4 to 2.2.0 ([#108](https://github.com/devsetgo/pydantic-schemaforms/pull/108)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi from 0.134.0 to 0.135.3 ([#97](https://github.com/devsetgo/pydantic-schemaforms/pull/97)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest-cov from 7.0.0 to 7.1.0 ([#98](https://github.com/devsetgo/pydantic-schemaforms/pull/98)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pydantic-extra-types from 2.11.1 to 2.11.2 ([#99](https://github.com/devsetgo/pydantic-schemaforms/pull/99)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump python-multipart from 0.0.22 to 0.0.24 ([#100](https://github.com/devsetgo/pydantic-schemaforms/pull/100)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest from 9.0.1 to 9.0.3 ([#101](https://github.com/devsetgo/pydantic-schemaforms/pull/101)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/github-script from 7 to 9 ([#102](https://github.com/devsetgo/pydantic-schemaforms/pull/102)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 6.2.0 to 7.2.0 ([#103](https://github.com/devsetgo/pydantic-schemaforms/pull/103)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- dependency update and tests ([#96](https://github.com/devsetgo/pydantic-schemaforms/pull/96)) ([@devsetgo](https://github.com/devsetgo))
- update of dependencies ([#87](https://github.com/devsetgo/pydantic-schemaforms/pull/87)) ([@devsetgo](https://github.com/devsetgo))
- pip(deps): bump hatchling from 1.28.0 to 1.29.0 ([#73](https://github.com/devsetgo/pydantic-schemaforms/pull/73)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump tox from 4.44.0 to 4.46.3 ([#74](https://github.com/devsetgo/pydantic-schemaforms/pull/74)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi[all] from 0.128.4 to 0.134.0 ([#75](https://github.com/devsetgo/pydantic-schemaforms/pull/75)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mkdocs-material from 9.7.2 to 9.7.3 ([#76](https://github.com/devsetgo/pydantic-schemaforms/pull/76)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump ruff from 0.15.1 to 0.15.4 ([#77](https://github.com/devsetgo/pydantic-schemaforms/pull/77)) (@[dependabot[bot]](https://github.com/apps/dependabot))

#### 🙌 Contributors
[@dependabot](https://github.com/dependabot)[bot], [@devsetgo](https://github.com/devsetgo) and [dependabot[bot]](https://github.com/apps/dependabot)

### 🚀 [26.1.8.beta · Removing External Validation Logic](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.8.beta)

📅 Published 2026 February 27, 21:32

#### 🎁 Changes
#### 🐛 Bug Fixes

- Removing validation logic outside of library. ([#71](https://github.com/devsetgo/pydantic-schemaforms/pull/71)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo)

### 🚀 [26.1.7.beta · Bug fix and cleanup.](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.7.beta)

📅 Published 2026 February 22, 19:56

#### 🎁 Changes
- Move of examples ([#69](https://github.com/devsetgo/pydantic-schemaforms/pull/69)) ([@devsetgo](https://github.com/devsetgo))

#### 🐛 Bug Fixes

- fix(layouts): validate nested layout submissions and restore Preferen… ([#70](https://github.com/devsetgo/pydantic-schemaforms/pull/70)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo)

### 🚀 [26.1.6.beta · Many fixes, enhancements, and increasing code coverage](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.6.beta)

📅 Published 2026 February 22, 16:35

#### 🎁 Changes
- bumping version to 26.1.6.beta ([#68](https://github.com/devsetgo/pydantic-schemaforms/pull/68)) ([@devsetgo](https://github.com/devsetgo))
- feat(examples,docs): add plain HTML style support and document render… ([#67](https://github.com/devsetgo/pydantic-schemaforms/pull/67)) ([@devsetgo](https://github.com/devsetgo))
- improving documents ([#59](https://github.com/devsetgo/pydantic-schemaforms/pull/59)) ([@devsetgo](https://github.com/devsetgo))
- improving test coverage ([#58](https://github.com/devsetgo/pydantic-schemaforms/pull/58)) ([@devsetgo](https://github.com/devsetgo))
- improving reliability rating ([#57](https://github.com/devsetgo/pydantic-schemaforms/pull/57)) ([@devsetgo](https://github.com/devsetgo))
- working on sonarcloud issue ([#41](https://github.com/devsetgo/pydantic-schemaforms/pull/41)) ([@devsetgo](https://github.com/devsetgo))
- fixing examples ([#33](https://github.com/devsetgo/pydantic-schemaforms/pull/33)) ([@devsetgo](https://github.com/devsetgo))

#### ✨ Features

- working on example. ([#65](https://github.com/devsetgo/pydantic-schemaforms/pull/65)) ([@devsetgo](https://github.com/devsetgo))
- Improvements - docs, examples, and bug fixes ([#43](https://github.com/devsetgo/pydantic-schemaforms/pull/43)) ([@devsetgo](https://github.com/devsetgo))
- 34 add timing ([#42](https://github.com/devsetgo/pydantic-schemaforms/pull/42)) ([@devsetgo](https://github.com/devsetgo))
- adding start line and end line for HTML sent to browser ([#32](https://github.com/devsetgo/pydantic-schemaforms/pull/32)) ([@devsetgo](https://github.com/devsetgo))

#### 🐛 Bug Fixes

- working on material design render issues ([#66](https://github.com/devsetgo/pydantic-schemaforms/pull/66)) ([@devsetgo](https://github.com/devsetgo))
- working on example. ([#65](https://github.com/devsetgo/pydantic-schemaforms/pull/65)) ([@devsetgo](https://github.com/devsetgo))
- Improvements - docs, examples, and bug fixes ([#43](https://github.com/devsetgo/pydantic-schemaforms/pull/43)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- pip(deps): bump tox from 4.36.0 to 4.44.0 ([#60](https://github.com/devsetgo/pydantic-schemaforms/pull/60)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mkdocs-material from 9.7.1 to 9.7.2 ([#61](https://github.com/devsetgo/pydantic-schemaforms/pull/61)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump isort from 7.0.0 to 8.0.0 ([#62](https://github.com/devsetgo/pydantic-schemaforms/pull/62)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump flask from 3.1.2 to 3.1.3 ([#63](https://github.com/devsetgo/pydantic-schemaforms/pull/63)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump autoflake from 2.3.1 to 2.3.3 ([#64](https://github.com/devsetgo/pydantic-schemaforms/pull/64)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest-html from 4.1.1 to 4.2.0 ([#45](https://github.com/devsetgo/pydantic-schemaforms/pull/45)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump ruff from 0.14.14 to 0.15.0 ([#44](https://github.com/devsetgo/pydantic-schemaforms/pull/44)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump tqdm from 4.67.1 to 4.67.3 ([#47](https://github.com/devsetgo/pydantic-schemaforms/pull/47)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi[all] from 0.121.2 to 0.128.4 ([#48](https://github.com/devsetgo/pydantic-schemaforms/pull/48)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mkdocstrings[python] from 1.0.0 to 1.0.1 ([#39](https://github.com/devsetgo/pydantic-schemaforms/pull/39)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pymdown-extensions from 10.20 to 10.20.1 ([#36](https://github.com/devsetgo/pydantic-schemaforms/pull/36)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 6.1.0 to 6.2.0 ([#35](https://github.com/devsetgo/pydantic-schemaforms/pull/35)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump black from 25.12.0 to 26.1.0 ([#37](https://github.com/devsetgo/pydantic-schemaforms/pull/37)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump ruff from 0.14.11 to 0.14.14 ([#38](https://github.com/devsetgo/pydantic-schemaforms/pull/38)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump packaging from 25.0 to 26.0 ([#40](https://github.com/devsetgo/pydantic-schemaforms/pull/40)) (@[dependabot[bot]](https://github.com/apps/dependabot))

#### 🙌 Contributors
[@dependabot](https://github.com/dependabot)[bot], [@devsetgo](https://github.com/devsetgo) and [dependabot[bot]](https://github.com/apps/dependabot)

### 🚀 [26.1.2.beta · Bug fixes and Improvements](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.2.beta)

📅 Published 2026 January 09, 21:46

#### 🎁 Changes
- Publishing Improvements ([#17](https://github.com/devsetgo/pydantic-schemaforms/pull/17)) ([@devsetgo](https://github.com/devsetgo))
- Doc ([#16](https://github.com/devsetgo/pydantic-schemaforms/pull/16)) ([@devsetgo](https://github.com/devsetgo))
- GitHub Actions Improvements ([#10](https://github.com/devsetgo/pydantic-schemaforms/pull/10)) ([@devsetgo](https://github.com/devsetgo))
- first release ([#9](https://github.com/devsetgo/pydantic-schemaforms/pull/9)) ([@devsetgo](https://github.com/devsetgo))
- working on documentation ([#5](https://github.com/devsetgo/pydantic-schemaforms/pull/5)) ([@devsetgo](https://github.com/devsetgo))
- working on coverage ([#4](https://github.com/devsetgo/pydantic-schemaforms/pull/4)) ([@devsetgo](https://github.com/devsetgo))

#### ✨ Features

- Improving Workflow ([#1](https://github.com/devsetgo/pydantic-schemaforms/pull/1)) ([@devsetgo](https://github.com/devsetgo))

#### 🐛 Bug Fixes

- 18 bootstrap not included in self contained example ([#24](https://github.com/devsetgo/pydantic-schemaforms/pull/24)) ([@devsetgo](https://github.com/devsetgo))
- Fix model-list delete for dynamically added items ([#23](https://github.com/devsetgo/pydantic-schemaforms/pull/23)) ([@devsetgo](https://github.com/devsetgo))
- working on coverage issue ([#3](https://github.com/devsetgo/pydantic-schemaforms/pull/3)) ([@devsetgo](https://github.com/devsetgo))
- working on publishing issue ([#2](https://github.com/devsetgo/pydantic-schemaforms/pull/2)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- github-actions(deps): bump actions/upload-pages-artifact from 3 to 4 ([#19](https://github.com/devsetgo/pydantic-schemaforms/pull/19)) (@[dependabot[bot]](https://github.com/apps/dependabot))
- updating release drafter ([#11](https://github.com/devsetgo/pydantic-schemaforms/pull/11)) ([@devsetgo](https://github.com/devsetgo))
- Pre-Release Checks ([#6](https://github.com/devsetgo/pydantic-schemaforms/pull/6)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@dependabot](https://github.com/dependabot)[bot], [@devsetgo](https://github.com/devsetgo) and [dependabot[bot]](https://github.com/apps/dependabot)


## 🧪 Pre-releases

### 🧪 [26.1.1.beta · Initial Beta Release](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.1.beta)

📅 Published 2026 January 02, 19:13

#### 🎁 Changes
- GitHub Actions Improvements ([#10](https://github.com/devsetgo/pydantic-schemaforms/pull/10)) ([@devsetgo](https://github.com/devsetgo))
- first release ([#9](https://github.com/devsetgo/pydantic-schemaforms/pull/9)) ([@devsetgo](https://github.com/devsetgo))
- working on documentation ([#5](https://github.com/devsetgo/pydantic-schemaforms/pull/5)) ([@devsetgo](https://github.com/devsetgo))
- working on coverage ([#4](https://github.com/devsetgo/pydantic-schemaforms/pull/4)) ([@devsetgo](https://github.com/devsetgo))

#### ✨ Features

- Improving Workflow ([#1](https://github.com/devsetgo/pydantic-schemaforms/pull/1)) ([@devsetgo](https://github.com/devsetgo))

#### 🐛 Bug Fixes

- working on coverage issue ([#3](https://github.com/devsetgo/pydantic-schemaforms/pull/3)) ([@devsetgo](https://github.com/devsetgo))
- working on publishing issue ([#2](https://github.com/devsetgo/pydantic-schemaforms/pull/2)) ([@devsetgo](https://github.com/devsetgo))

#### 🔧 Maintenance

- updating release drafter ([#11](https://github.com/devsetgo/pydantic-schemaforms/pull/11)) ([@devsetgo](https://github.com/devsetgo))
- Pre-Release Checks ([#6](https://github.com/devsetgo/pydantic-schemaforms/pull/6)) ([@devsetgo](https://github.com/devsetgo))

#### 🙌 Contributors
[@devsetgo](https://github.com/devsetgo)

