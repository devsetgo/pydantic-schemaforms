# Next version: complex forms by nesting FormModels

## Handoff: read this first (written 2026-10-11)

This file is the complete memory of the work so far. Whoever picks it up (a person, or an AI
session with no history) should read this section, then skim "Decisions" and the wizard
follow-up below. The "Implementation guide" further down is the original plan; this section
says what was actually built and where it differs.

### Where things stand

- **Branch:** `feature/nested-forms`, created from `dev` at commit `dbe9a09`.
- **Nothing is committed.** All work sits in the working tree: 56 modified or deleted files, and
  5 new files (`NextVersion.md`, `docs/complex_forms.md`, `pydantic_schemaforms/error_tree.py`,
  `pydantic_schemaforms/rendering/nested_model_renderer.py`,
  `tests/test_nested_model_forms.py`). Commit it before switching machines or containers if
  there is any chance the working tree will not travel with you.
- **Steps 1 to 10 of the implementation guide are done, and so is the step wizard**
  (`layout="wizard"`, see "Step wizard: as built" below). What remains is the release
  (open item 6) and the smaller gaps listed under "Known gaps".
- **Last verified state (2026-10-11, wizard session):** 1467 tests passed with
  `pytest -n 2 --ignore=tests/playwright`, and all 34 Playwright tests passed
  (`pytest tests/playwright`; first run on this branch). Earlier: `ruff check` and `ruff format --check` were clean
  for `pydantic_schemaforms tests examples`, as were the protected invariant tests and a local
  `mkdocs build`. All 20 example-app routes rendered under Bootstrap and Material.
- **Not run:** the real docs deploy and `scripts/changelog.py` (it calls GitHub).
- **Playwright in the devcontainer** needed `python -m playwright install chromium` and
  `sudo env PATH=$PATH PYTHONPATH=~/.local/lib/python3.14/site-packages python -m playwright
  install-deps chromium` (system libraries). Neither is in the devcontainer image yet.
- **Two whitespace-only diffs were not made by this work:** the trailing newline in
  `.github/workflows/ai_pr_assistant.yml` and a removed trailing blank line in
  `docs/release-notes.md` (an editor or hook). Keep or revert them as you like.

### Environment notes

- The library requires Python 3.14. The original host only had 3.10, so a host-only setup was
  used: `uv` in `~/.local/bin`, Python 3.14.8 from `uv python install`, and a gitignored
  `.venv` at the repo root. **That `.venv` will not work inside a devcontainer**
  (its interpreter path points at the host). Delete it and use the devcontainer's Python, or
  recreate it there: `pip install -r requirements.txt -e ".[dev]"`.
- The makefile calls `python3` and copies from `/workspaces/$(REPONAME)/...`, so `make` targets
  should work inside the devcontainer as written.
- **Running pytest rewrites two tracked files, `coverage.xml` and `report.xml`.** Run
  `git checkout coverage.xml report.xml` afterwards, or they show up in the diff.
- **This repo's ruff also formats Python code blocks inside Markdown.** After editing a
  Python snippet in `pydantic_schemaforms/assets/ai/_shared_instructions.md`, run
  `ruff format` on that file, then `make ai-instructions` (or
  `python scripts/build_ai_instructions.py`). Never hand-edit the three generated
  `*_app_instructions.md` files; `tests/test_ai_instructions.py` checks they match the source.
- `ruff format examples/` also reformats `examples/templates/archive_old/README.md`, which
  was unformatted before this work. Don't commit that change; CI only checks
  `pydantic_schemaforms` and `tests`.

### What was built (file map)

New modules:

- `pydantic_schemaforms/error_tree.py` builds the nested error tree. Functions:
  `build_error_tree` (from Pydantic errors), `normalize_error_tree` (accepts a tree, wire-path
  keys, or the `{"errors": [...]}` contract), `field_message`, `child_errors`, `iter_errors`,
  `error_list`, `has_errors`. Container and form-wide messages use the reserved key `"_errors"`.
- `pydantic_schemaforms/rendering/nested_model_renderer.py` renders one sub-form. It is
  registered as `@LayoutEngine.layout_renderer('nested_model')` and imported for its side
  effect in `rendering/field_renderer.py`. Inputs are named `field.child`. It honours
  `ui_collapsible`/`ui_collapsed` via `<details>`, and skips its own titled card when its
  schema carries `IN_GROUP_FLAG` (inside a tab or accordion panel).
- `docs/complex_forms.md` is the user guide. Its `## Upgrading` section is linked from the
  removal error.
- `tests/test_nested_model_forms.py` holds 37 tests covering the whole round trip.

Key changes to existing modules:

- `rendering/schema_parser.py`: `resolve_nested_model_ref`, `resolve_list_item_ref`, and
  `ordered_properties` (declaration order, then `ui_order`). `resolve_ui_element` infers
  `nested_model` for a `FormModel`-typed field and `model_list` for `list[FormModel]`.
  `SchemaMetadata.group_fields` lists sub-form fields; `GROUP_ELEMENTS` is
  `{nested_model, model_list, layout}`.
- `form_data.py`: `decode_submission(raw)` accepts Starlette `FormData`, Werkzeug
  `MultiDict`, `(name, value)` pairs, a dict with wire keys, or nested JSON. It does not
  coerce values; `validation._coerce_html_form_values` does that, recursively and type-aware.
- `validation.py`: `validate_form_data(model, data)` decodes, validates, and returns
  `ValidationResult` with nested `data`, an error tree in `errors`, `instance`, and
  `error_list()`. The old layout-field branch, the string-path error mapper, the swallowed
  exceptions, and `FormValidator.validate_pydantic_model` are gone.
- `schema_form.py`: `FormModel.validate(data, *, submit_url, framework, **render_kwargs)`.
  Passing `flatten=` raises a `TypeError` with upgrade text. Render kwargs such as `layout=`
  are kept for `render_with_errors()`.
- `rendering/context.py`: `RenderContext.child_errors` replaces `all_errors`.
- `rendering/field_renderer.py`: `render_field(..., error, ...)` takes the field's error node
  (a string, or a dict holding child errors plus an optional `"_errors"`). It splits it into
  `context.error` (message) and `context.child_errors` before dispatching to composites,
  including `input_type="layout"` handlers. There is no `all_errors` parameter anywhere.
- `rendering/model_list_renderer.py`: reads list errors as `{index: {field: msg}}` through
  `item_errors()`, which also accepts string index keys from JSON round-trips.
- `rendering/layout_engine.py`: `LayoutEngine.render_groups(metadata, data, errors, context,
  mode=..., general_title=...)` implements `tabbed`, `side-by-side`, and `accordion`. It opens
  the first group that contains an error. Also added: `GROUPED_LAYOUTS`, `LAYOUTS`,
  `check_layout()` (unknown layout gives `ValueError`, `"wizard"` gives
  `NotImplementedError`), `IN_GROUP_FLAG`, and `TabLayout(active_index=...)`. Deleted: the
  keyword-heuristic tabbing, pairwise side-by-side, auto-tabbing of several layout fields, the
  `examples.shared_models` fallbacks, and `get_nested_form_data`.
- `enhanced_renderer.py`: `render_form_from_model` calls `check_layout`, decodes `data` with
  `decode_submission` (so `form_data=` can be a raw request form), normalizes errors, and
  either renders fields vertically or calls `render_groups`. Material dispatches composites
  through `resolve_ui_element`. The error summary walks the tree and produces labels like
  "Pet #2 — Age". Multipart detection now looks inside sub-forms.
- `form_layouts.py`: every removed class is a stub that raises `FormLayoutRemovedError`
  (`REMOVED_IN = '26.4.0'`) on subclassing or instantiation. `pydantic_schemaforms/layouts.py`
  is deleted.
- `__init__.py`: top-level `VerticalLayout`/`HorizontalLayout` are now the flex primitives.
  It exports `FormLayoutRemovedError` and `validate_form_data`. The removed names stay
  exported under a "REMOVED" comment.
- `integration/sync.py` adds `validate_submission()`; model-backed `handle_form` and
  `handle_form_async` return nested data and errors.
- `live_validation.py`: `register_model_validator` registers sub-form fields (`address.city`)
  and list-item fields (`pets[].name`). `validate_field` maps `pets[3].name` to `pets[].name`.
- `datatable_layout.py`: `parse_submitted_rows` uses `decode_submission`.
- Examples: `examples/shared_models.py` (`LayoutDemonstrationForm`, `WidgetGalleryForm`),
  `examples/nested_forms_example.py` (`ComprehensiveTabbedForm`), and
  `examples/date_time_formats_example.py` now compose by nesting.
  `examples/fastapi_routes.py` passes raw forms to `validate()`. `/layouts` accepts
  `?layout=vertical|tabbed|side-by-side|accordion`.
- Docs: README, `docs/{layouts,recipes,validation_guide,configuration,quickstart,
  tutorial_fastapi,plugin_hooks,testing_workflow}.md`, `mkdocs.yml` (nav entry), CHANGELOG
  (`## [26.4.0] — Unreleased`), CLAUDE.md (composite and nesting rules), and the AI
  instructions. The AI instructions gained two sections, "Composing complex forms from
  multiple FormModels" and "Upgrading to nested forms". `docs/index.md` and
  `docs/release-notes.md` are generated and were deliberately not regenerated.

### Where the build differs from the plan below

- **`result.data` keeps Python values** (`date`, `SecretStr`, ...), as `model_dump()` did
  before. "JSON" here means the shape. `model_dump(mode="json")` would have masked
  `SecretStr` passwords. `result.instance` gives the validated model.
- **`list[Model]` fields render as `model_list` without `ui_element`.** Also,
  `validate_form_data` became a top-level export because the docs already claimed it was.
- **`validate()` no longer turns arbitrary exceptions into a form error.** Only Pydantic
  validation errors become `result.errors`; anything else propagates.
- **Auto-tabbing of several `input_type="layout"` fields was removed**, not kept.
  `layout="tabbed"` does it explicitly.
- **Step 2's DataTableLayout renaming was not done.** It names cells `rows[i].col` and also
  uses fixed `csv_file` and `datatable_action` control names by design (one table per page),
  so renaming only the cells would not let two tables share a page. Its parser now uses
  `decode_submission`. That fixed a separate bug where cell values like `"1"` or `"yes"`
  were turned into booleans.
- **Docs examples fixed along the way:** three examples interpolated submitted values into
  HTML with f-strings, breaking the CLAUDE.md XSS rule, and now use `html(t"...")`. The
  recipes for `FormConfig`/`TabbedLayout((...))` and `HorizontalLayout(label_cols=...)`,
  which described an API that never existed, were replaced.

### Known gaps and open items

1. ~~An emptied list skips `min_length`.~~ Fixed: `validate_form_data` injects `[]` for an
   absent `list[Model]` field when the input is a form submission (`is_form_submission`).
2. **Same-page DataTableLayouts still collide**, as described above.
3. **`demo_app/` still uses the removed classes.** It pins `pydantic-schemaforms==26.3.7`
   from PyPI, so it keeps working until it upgrades. Migrate its mirrors
   (`demo_app/src/models.py`, `nested_forms_models.py`, `date_time_formats_models.py`,
   `examples_routes.py`) the same way `examples/` was migrated, after 26.4.0 is released.
4. **`TabLayout` and `AccordionLayout` use fixed element ids** (`tab-0`, `accordion-0`). Two
   grouped forms on one page would collide. This was pre-existing. `WizardLayout` avoids the
   problem by using no ids (data attributes, scoped by `closest('.form-wizard')`); tabs and
   accordion could be moved to the same approach.
5. ~~Internal-submodule imports in `examples/` (and in the AI instructions and
   `docs/recipes.md`/`docs/assets.md`).~~ Fixed: `validation_response_headers`,
   `wrap_with_schemaforms_markers`, `read_asset_text`, `bootstrap_icons_css_content` and
   `bootstrap_icons_css_tag` are top-level exports now and every example imports them there.
6. **Release:** bump to 26.4.0 with BumpCalver, set the CHANGELOG date, regenerate the docs
   copies (`make create-docs-local`), run the Playwright tests, then open a PR from
   `feature/nested-forms`. Per CLAUDE.md's attribution rules, the commit and PR need the
   Co-Authored-By / "Generated with Claude Code" lines.

### Step wizard: as built

- `rendering/layout_engine.py`: `WizardLayout` primitive (next to `TabLayout`); `"wizard"` is
  in `GROUPED_LAYOUTS`; `render_groups(..., wizard_options=)` passes `has_error` per group and
  uses `ui_step_title` for step titles in wizard mode only; `check_wizard_options()` rejects
  unknown keys (`linear`, `show_progress`, `back_label`, `next_label`).
- `rendering/form_style.py`: `FormStyleTemplates.wizard_layout`, `wizard_progress`,
  `wizard_progress_item`, `wizard_step`, `wizard_footer` (default/Bootstrap, plain, and Material
  variants for step and footer). `FormStyleAssets.wizard_assets`, and
  `RendererTheme.wizard_component_assets()`.
- `rendering/theme_assets.py`: `WIZARD_COMPONENT_ASSETS`, an inline idempotent script plus CSS,
  shipped the same way as the tab/accordion assets rather than as a separate
  `assets/js/wizard.js` file (one less loading path). No JS: all steps stacked, nav hidden.
- `enhanced_renderer.py`: `render_form_from_model` pops `wizard_options=` from kwargs, so it
  also flows through `validate(..., wizard_options=...)` into `render_with_errors()`.
- Differences from the design below: options are `wizard_options=` (not
  `ui_options={"wizard": ...}`, since render kwargs become `<form>` attributes); form-wide
  errors are not moved to the last step because the error summary at the top already shows on
  every step; Enter in an input before the last step advances instead of submitting.
- Tests: wizard section of `tests/test_nested_model_forms.py`, and
  `tests/playwright/test_wizard.py` (Next blocked by invalid input, Back, linear vs non-linear
  header, Enter, one POST).
- Found and fixed on the way: `Field()` dropped unlisted `ui_*` kwargs (e.g. `ui_collapsible`)
  whenever another `ui_*` param was passed; the Material theme's inline JS had two `#`
  comments, a syntax error that disabled it on every Material page (pre-existing since the
  rename). Both are in CHANGELOG "Fixed".

The original integration plan, kept for reference:

- **Groups are already built.** `LayoutEngine.render_groups` builds the groups (General plus
  one per sub-form). The wizard is a fourth `mode`: add `"wizard"` to `GROUPED_LAYOUTS`,
  remove the `NotImplementedError` in `check_layout`, and add a `WizardLayout` primitive next
  to `TabLayout`/`AccordionLayout` in `rendering/layout_engine.py`.
- **Steps and errors.** Pass the `IN_GROUP_FLAG` schema marker for wizard steps the same way
  tabs do. The active step is the `active_index` that `render_groups` already computes (the
  first group with an error).
- **Script and templates.** The vendored step script goes under `pydantic_schemaforms/assets/`,
  loaded the way the model_list script is (see how `enhanced_renderer.py` appends
  `ModelListRenderer` JS when `add-item-btn` appears in the markup). The framework templates
  go in `rendering/form_style.py` (`FormStyleTemplates`), and all HTML must use `html(t'...')`.
- **Tests and docs.** Add server-side tests to `tests/test_nested_model_forms.py`, and put
  the "Next blocked by an invalid field" behaviour in a Playwright test. Update
  `docs/complex_forms.md`'s layout table, the AI instructions (then `make ai-instructions`),
  and CHANGELOG.

### How to verify after any change

```bash
pytest -n 2 --ignore=tests/playwright && git checkout coverage.xml report.xml
pytest tests/test_invariants.py -v
ruff check pydantic_schemaforms tests examples
ruff format --check pydantic_schemaforms tests
make ai-instructions        # after editing _shared_instructions.md or _profile_*.md
mkdocs build -d /tmp/site   # quick docs check without touching generated docs/ files
python examples/main.py     # then try /layouts?layout=tabbed, /organization, /gallery
```

## Summary

Building a single `FormModel` is pleasant. Building a *complex* form out of several of them is not, because the library currently offers seven different ways to do it, each with its own declaration style, input-naming scheme, submitted-data shape, and validation path:

| # | Mechanism today | Declared how | Input names | Validation |
|---|---|---|---|---|
| 1 | `render_form_html(..., layout="tabbed")` | render kwarg | bare | the model; tabs by field-name keyword heuristic |
| 2 | Auto-tabbing of several `input_type="layout"` fields | multiple layout fields, no plain fields | bare / `data[field]` | `validation.py` layout branch + hardcoded name fallback |
| 3 | `TabbedLayout` / `VerticalLayout` / `HorizontalLayout` (`form_layouts.py`) embedded as a layout field | subclass per form (`form = X`), tabs by `dir()` scan | bare (forms collide) | each form against the same flat dict, merged |
| 4 | Standalone `TabbedLayout(FormDesign)` | object with `.render()` | bare | `.validate()` |
| 5 | `ListLayout(form_model, ...)` | constructor | `item_N_field` (regex rewrite) | its own parser, returns `{"valid_items", "item_count"}` |
| 6 | `model_list` | `list[Item]` + `ui_element="model_list"` | `field[i].sub` | plain Pydantic via `parse_nested_form_data` |
| 7 | `DataTableLayout` / `layout_handler` | `Any` field + `as_layout_value()` | `rows[i].col` | `parse_submitted_rows()` |

Concrete defects found during the review:

- `TabbedLayout` orders tabs alphabetically (`dir()` scan in `form_layouts.py:493-504`) although its docstring promises declaration order. Every shipped example overrides `_get_layouts()` by hand to work around it.
- Sub-form inputs are not namespaced. Two models that both have a `name` field collide on data and errors (`form_layouts.py:235-310`).
- Validation errors never reach forms inside a layout field on re-render: `rendering/layout_engine.py:830-837` calls `value.render(errors=None, ...)`.
- Nested-layout validation swallows exceptions and accepts the payload as valid (`validation.py:1279-1305`).
- Library code hardcodes the example app's field names and imports `examples.shared_models` (`rendering/layout_engine.py:843-911` and `1048-1065`).
- A plain nested sub-model field (`address: Address`) has no rendering support at all. `_infer_ui_element` (`rendering/field_renderer.py:416-432`) falls through to `"text"`, so the whole sub-model renders as one text box. Yet `parse_nested_form_data` and the Pydantic error-path mapper (`validation.py:1346-1389`) already handle nested data.
- Developers are exposed to the wire encoding: routes call `parse_nested_form_data(...)` themselves, error keys are strings like `pets[0].weight`, and `validate(flatten=True)` returns `{"pets[0].name": ...}`. The library's own result shapes disagree (`dict[str,str]`, `dict[str,list[str]]`, `RowError`, `{"valid_items", "item_count"}`).
- `docs/recipes.md:1020-1058` documents `class FormConfig: layout = TabbedLayout(("Personal", [...]))` and `HorizontalLayout(label_cols=3, input_cols=9)`. Neither exists. `docs/layouts.md` and the AI instructions never mention the `form_layouts` classes, and the AI instructions' sample `layout_renderer` signature (`def render(*, value, **kwargs)`) cannot be called by the engine, which passes six positional arguments.
- Putting six forms into tabs costs eight classes (`examples/nested_forms_example.py:1718-1785`).

**The change:**

1. **Composition is Pydantic nesting.** A parent `FormModel` declares other `FormModel`s as ordinary typed fields. Presentation (sections, tabs, side-by-side columns, accordion) is one `layout=` choice on the parent.
2. **Input and output are JSON.** `Model.validate()` accepts the raw request form (`await request.form()`, Flask's `request.form`, a list of pairs) *or* an already-nested dict, and decodes to nested JSON itself. `result.data` is nested JSON mirroring the model (`{"pets": [{"name": "a"}, {"name": "b"}]}`); `result.errors` is nested JSON mirroring the data. Developers never write or read `pets[0].name`; the `name=` attribute encoding becomes an internal wire format.
3. **Hard break.** The old orchestrators (`TabbedLayout`, `VerticalLayout`, `HorizontalLayout`, `ListLayout`, `SectionDesign`, `FormDesign`), `validate(flatten=True)`, the keyword-heuristic tabbing, and the `layouts.py` shim are removed. The names stay importable but any use raises `FormLayoutRemovedError` whose message *is* the upgrade guide (before/after snippet plus a pointer to the "Upgrading to nested forms" section of the AI instructions and `docs/complex_forms.md`). There is no real user base yet, so no compatibility shims.

## Example: what a complex form looks like after this change

```python
from pydantic_schemaforms import Field, FormModel, render_form_html


class Contact(FormModel):
    email: str = Field(title="Email", ui_element="email")
    phone: str = Field("", title="Phone", ui_element="tel")


class Address(FormModel):
    street: str = Field(title="Street")
    city: str = Field(title="City", min_length=2)
    country: str = Field("US", title="Country", ui_element="select",
                         ui_options={"options": ["US", "CA", "UK"]})


class Pet(FormModel):
    name: str = Field(title="Pet name")
    age: int = Field(0, title="Age", ge=0)


class ProfileForm(FormModel):
    nickname: str = Field(title="Nickname")                                   # plain field
    contact: Contact = Field(title="Contact details")                         # nested model
    address: Address = Field(title="Home address", ui_collapsible=True)       # nested model, collapsible
    pets: list[Pet] = Field(default_factory=list, title="Pets", min_length=1,
                            ui_element="model_list")                          # repeating sub-form


# Presentation is a single choice on the parent. Tabs follow declaration order.
html = render_form_html(ProfileForm, layout="tabbed", submit_url="/profile")
#   tabs: General | Contact details | Home address | Pets
#
# layout="vertical"      -> stacked titled sections (default)
# layout="side-by-side"  -> each group is a column
# layout="accordion"     -> each group is a collapsible panel, first open
# layout="wizard"        -> one group per step with Back/Next (follow-up, see "Step wizard" below)


# Route: FastAPI shown; Flask is `ProfileForm.validate(request.form, ...)`.
@app.post("/profile")
async def profile_post(request: Request):
    result = ProfileForm.validate(await request.form(), submit_url="/profile", layout="tabbed")
    if result.is_valid:
        profile = ProfileForm(**result.data)          # typed, nested instance
        # result.data == {
        #   "nickname": "mk",
        #   "contact": {"email": "a@b.c", "phone": ""},
        #   "address": {"street": "1 Main", "city": "Xy", "country": "US"},
        #   "pets": [{"name": "Rex", "age": 3}, {"name": "Tux", "age": 1}],
        # }
        return RedirectResponse("/done", status_code=303)
    return HTMLResponse(result.render_with_errors())
    # result.errors == {
    #   "address": {"city": "Must be at least 2 characters"},
    #   "pets": "List should have at least 1 item after validation, not 0"   # the list itself
    #           # or, per item:  "pets": {1: {"age": "Must be 0 or greater"}}
    #           # or both:       "pets": {"_errors": "...", 1: {...}}
    # }
    # -> the City error renders inside the "Home address" tab next to its input.
```

Deep nesting works the same way because every level is just a `FormModel` field: a sub-model can hold a `model_list`, whose items can hold sub-models; `result.data["org"]["departments"][0]["teams"][1]["lead"]["email"]` is the same path as `result.errors[...]`.

Migrating an existing tabbed form:

```python
# before (8 classes)                                   # after (1 class)
class OrganizationLayout(VerticalLayout):              class ComprehensiveTabbedForm(FormModel):
    form = CompanyOrganizationForm                         organization: CompanyOrganizationForm = Field(title="Organization")
class KitchenSinkLayout(VerticalLayout):                   kitchen_sink: KitchenSinkForm = Field(title="Kitchen Sink")
    form = KitchenSinkForm                                 contacts: ContactManagementForm = Field(title="Contacts")
...                                                        scheduling: SchedulingForm = Field(title="Scheduling")
class ComprehensiveTabbed(TabbedLayout):                   media: MediaFilesForm = Field(title="Media & Files")
    organization = OrganizationLayout()                    settings: SettingsForm = Field(title="Settings")
    kitchen_sink = KitchenSinkLayout()
    ...                                                render_form_html(ComprehensiveTabbedForm, layout="tabbed", submit_url=...)
class ComprehensiveTabbedForm(FormModel):
    comprehensive_tabs: ComprehensiveTabbed = FormField(
        default_factory=ComprehensiveTabbed, input_type="layout")
```

## Decisions

- **Hard break, with a guided error.** Removed APIs stay importable so the failure is a clear `FormLayoutRemovedError` (subclass of `TypeError`) at class-definition or call time, never an `ImportError`. The error message contains the compact upgrade guide (the before/after above, five lines) and ends with: `Full guide: python -m pydantic_schemaforms.ai_instructions claude  (section "Upgrading to nested forms"), or docs/complex_forms.md#upgrading`.
- **JSON in, JSON out.** `validate()` decodes the request form; `result.data` and `result.errors` are nested. `flatten=True` is removed. `parse_nested_form_data` / `flatten_nested_data` stay exported as low-level utilities but no documented path requires them.
- **Error shape: nested, mirrors the data.** Sub-models are dicts; list errors are dicts keyed by integer index (serialises to `"1"` in JSON); an error on a container itself (whole list, whole sub-model, cross-field `@model_validator`) goes under the reserved key `"_errors"`; form-wide errors go under top-level `"_errors"`. `ValidationResult.error_list()` returns the flat Pydantic-style `[{"loc": [...], "msg": ...}]` for summaries and HTMX.
- **Wire format stays internal.** The DOM needs a string in each `name=`; the library keeps `pets[0].name` / `address.city` there because it is unambiguous (a `.0.` segment could be a dict key), already implemented in the parser and in the model_list JavaScript re-indexer (`model_list.py:234-244`), and matches the `qs`/Rails convention. It is documented in one place as "wire format, you should never need it".
- **Ordering: no new option.** Pydantic preserves declaration order in `model_fields`, and `_compute_schema_metadata` already honours `ui_order` (`schema_parser.py` `order_key`). Nested-model fields are ordinary fields, so declaration order is the default and `Field(..., ui_order=n)` reorders a tab/section/column exactly like any other field. The implicit "General" group (the parent's plain fields) is always first; a parent that wants a different first tab moves those fields into a sub-model.
- **`layout="tabbed"` / `"side-by-side"` / `"accordion"` require nested models.** The keyword heuristic (`_group_fields_into_tabs`) is deleted. A form with no nested-model, `model_list`, or `layout` fields and one of those layouts raises `ValueError("layout='tabbed' needs groups: split the form into nested FormModel fields ...")`. Plain `vertical` is unaffected. (`side-by-side` for flat forms today pairs fields two per row; that use is dropped too. If it is missed, it can come back as `ui_options={"columns": 2}` later.)

## Design principles

1. **Composition is Pydantic nesting.** No wrapper classes, no `input_type="layout"` for composing, no `default_factory=SomeLayout`. If Pydantic can validate it, the library can render it.
2. **The developer only sees JSON.** Input: the request form or a nested dict. Output: nested `data`, nested `errors`. String paths never appear in the public API.
3. **Presentation is separate from structure.** The parent chooses `layout=`; a field tunes its own group with `ui_*` keys (`ui_collapsible`, `ui_collapsed`, `ui_order`, `title`). Structure never changes to get a different look.
4. **Reuse the composite registry.** The sub-model renderer is a built-in `@LayoutEngine.layout_renderer("nested_model")`, dispatched by `ui_element` exactly like `model_list`. No new dispatch branch in `field_renderer.py`.
5. **Library code never knows about examples.** All hardcoded example field names and `examples.*` imports are deleted from `pydantic_schemaforms/`.
6. **One error shape everywhere.** `FormModel.validate`, `handle_form`/`handle_form_async`, `DataTableLayout`, HTMX responses all speak the nested error tree (or `error_list()` derived from it).

## Implementation guide

Work through the steps in order; each is independently testable. All HTML must be built with `html(t'...')` / `SafeHTML` (`CLAUDE.md` t-string rule; `tests/test_invariants.py` scans every `.py` under `pydantic_schemaforms/` automatically).

### Step 1. Detect nested sub-model fields

File: `pydantic_schemaforms/rendering/schema_parser.py`

`_compute_schema_metadata()` builds from the raw `model_cls.model_json_schema()`, so a nested model appears as `{"$ref": "#/$defs/Address", "title": ..., "ui_collapsible": true}` and an `Optional[Address]` as `{"anyOf": [{"$ref": ...}, {"type": "null"}]}`. `$defs` is already captured on `SchemaMetadata.schema_defs` and reaches renderers via `RenderContext.schema_defs`.

- Add `resolve_nested_model_ref(field_schema) -> str | None` (direct `$ref`, or the `$ref` inside `anyOf`).
- In `resolve_ui_element()`, when nothing is declared and `resolve_nested_model_ref()` matches, return `'nested_model'`. Make `FieldRenderer._infer_ui_element()` (`field_renderer.py:416`) agree. A `list[Model]` field keeps `items.$ref` and is unaffected.
- Add `group_fields: list[tuple[str, dict]]` to `SchemaMetadata`: every field whose element is `nested_model`, `model_list`, or `layout`, in the already-sorted order (declaration, then `ui_order`). Keep `layout_fields` for the `DataTableLayout` auto-tab path.

### Step 2. JSON in: `validate()` decodes the request form

Files: `pydantic_schemaforms/form_data.py`, `validation.py`, `schema_form.py`

- Add `decode_submission(raw) -> dict` to `form_data.py`:
  - Starlette `FormData` / Werkzeug `MultiDict` (anything with `multi_items()` or `items(multi=True)`), or an iterable of `(key, value)` pairs → collect repeated keys into lists, then run the existing `parse_nested_form_data(..., coerce_values=False)`.
  - A `Mapping` whose keys contain `[` or `.` → treat as flat wire format, same path.
  - Any other `Mapping` → already nested JSON, returned as-is.
  - Value coercion is **not** done here; `_coerce_html_form_values` (`validation.py:~1095`) does it with knowledge of field types. Extend that function to recurse into nested-model fields and list items so `'on'`, `''`, and numeric strings are coerced at every depth.
- `validate_form_data(form_model_class, data)` calls `decode_submission` first. Remove the `flatten` parameter and the `flatten_nested_data` on output. Delete the whole `layout_field_names` branch (`validation.py:1252-1337`); nested models now validate through Pydantic like any field.
- `FormModel.validate(cls, data, *, submit_url=None, framework='bootstrap', **render_kwargs)`: drop `flatten`; passing it raises `TypeError("flatten= was removed: result.data is always nested JSON ...")`.
- `integration/sync.py`, `integration/async_support.py`, `integration/builder.py`: route `handle_form` / `handle_form_async` through `decode_submission` + `validate_form_data` and return `{"success", "data" (nested), "errors" (nested), "form_html"}`. Delete `validate_pydantic_model` (keeps only `loc[0]`) and `normalize_form_data`.
- `DataTableLayout.parse_submitted_rows()` / `handle_import_post()` (`datatable_layout.py:268-330`) accept the raw form via `decode_submission`; `RowError` stays as the table's own per-row report (it is a composite with its own review UI), but `rows[i].col` wire names are generated from the embedding field's name instead of the literal `rows` (fixes the two-tables-collide bug, `rendering/datatable_renderer.py:168,192`).

### Step 3. JSON out: nested error tree

File: `pydantic_schemaforms/validation.py`

- Replace the `loc`-to-string mapper (`validation.py:1346-1389`) with `build_error_tree(pydantic_errors) -> dict`:
  - Walk each `loc`; create dicts for string segments and for integer segments (a list's errors are a dict keyed by `int`, so `errors["pets"][1]["name"]`).
  - If `loc` points at a container that also has child errors, or at the whole model (`loc == ()` or a `@model_validator` error), store the message under `"_errors"` at that level. Form-wide errors land in `errors["_errors"]`.
  - Keep the friendlier message rewrites (ge/le/min_length/max_length).
- `ValidationResult.errors` is this tree. Add `error_list()` → `[{"loc": [...], "msg": ...}]` (depth-first, `_errors` reported at the container's `loc`) and `iter_errors()` yielding `(loc_tuple, msg)`. `render_with_errors()` passes the tree straight through.
- Renderer-side lookups change from string keys to tree walks:
  - `enhanced_renderer.render_form_from_model`: `errors.get(field_name)`; if the value is a dict, pass it as the field's *sub-tree*; `_render_error_summary` (`enhanced_renderer.py:647`) uses `iter_errors()` to list `"Home address › City: Must be at least 2 characters"` with titles resolved from the schema.
  - `field_renderer.render_field`: a plain field's `error` is `sub_tree` if it is a `str`, or `sub_tree.get("_errors")` if a dict.
  - `model_list_renderer`: delete `extract_nested_errors_for_field` (`:234-251`) and its copy in `enhanced_renderer.py:531-543` and `field_renderer.py:473-478`; item `i` receives `list_errors.get(i, {})`, the list-level message is `list_errors.get("_errors")`.
  - `datatable_renderer`: unchanged (uses `RowError`).
  - `RenderContext.all_errors` becomes the full tree (still needed so a composite can locate its own sub-tree by name).

### Step 4. The `nested_model` composite renderer

New file: `pydantic_schemaforms/rendering/nested_model_renderer.py`, imported next to `model_list_renderer` in `rendering/field_renderer.py:17-22` so `@LayoutEngine.layout_renderer('nested_model')` (default `builtin=True`) registers at import and survives `reset_layout_renderers()`.

Signature `(field_name, field_schema, value, ui_info, context, engine) -> str`, mirroring `render_model_list_field` (`model_list_renderer.py:78-122`):

1. `schema_def = context.schema_defs[resolve_nested_model_ref(field_schema)]`; HTML-comment error if missing.
2. Value: `dict` as-is, `BaseModel` via `model_dump()`, anything else `{}`.
3. Errors: `sub_tree = context.all_errors.get(field_name) or {}` (a dict; its `"_errors"` is the sub-model-level message).
4. For each `(key, sub_schema)` in `schema_def["properties"]` (sorted by `ui_order` like `_compute_schema_metadata`): input name `f"{field_name}.{key}"`, value `value.get(key)`, error `sub_tree.get(key)`, required from `schema_def["required"]`. Render via the field renderer's `render_field(...)` (the call `_render_item_field_cell` uses, `model_list_renderer.py:318-335`), passing a context whose `all_errors` is `sub_tree` so deeper composites find their own sub-trees. Because `render_field` dispatches by element, a sub-model containing a `model_list`, a `DataTableLayout`, or another sub-model recurses naturally.
5. Wrap: unless `ui_info.get("_in_group")`, use `engine._render_layout_card(title, body, help_text)` (`layout_engine.py:913-939`, backed by `FormStyleTemplates.layout_section`); if `ui_info.get("collapsible")`, wrap the body in the collapse markup `model_list` uses for collapsible items, honouring `ui_collapsed`. Render the sub-model-level `_errors` message above the body.
6. Treat `'nested_model'` like `'model_list'` in the width rule of `_render_item_field_cell` (`model_list_renderer.py:318-320`). Extend multipart detection (`enhanced_renderer.py:126-140`) to recurse into nested-model `$defs` for `input_type='file'`.

### Step 5. Group presentations on the parent

Files: `pydantic_schemaforms/enhanced_renderer.py` (`render_form_from_model`, `:251-310`), `rendering/layout_engine.py`

- Build groups when `layout in {"tabbed", "side-by-side", "accordion"}`: Group 0 "General" (parent's plain fields; title = parent schema `title` if it differs from the class name, else "General"; omitted when empty), then one group per entry of `metadata.group_fields`, titled by the field `title`. Render the composite field inside its group with `ui_info["_in_group"] = True` so no second titled card appears.
- No groups available → `ValueError` with guidance (see Decisions).
- Hand rendered groups to existing primitives: `TabLayout` (`layout_engine.py:140`) for `tabbed`; flex `HorizontalLayout` (`:32`) + `_wrap_side_by_side_column` for `side-by-side`; `AccordionLayout` (`:229`) for `accordion`, first panel open. Implement as `LayoutEngine.render_groups(groups, mode, ...)` next to the existing `render_tabbed_layout`; delete `render_tabbed_layout`, `_group_fields_into_tabs`, `render_side_by_side_layout`'s pairwise loop. Keep `render_layout_fields_as_tabs` for `DataTableLayout` embeds.
- On re-render with errors, the first group containing an error is the active tab/panel (walk `errors` for the group's field names; "General" is active if a plain field has an error).
- Accept `layout="accordion"` everywhere `layout` is validated/documented (`render_form_html`, `FormModel.render_form`, `docs/configuration.md`, AI instructions). Reserve `"wizard"` (see follow-up); until implemented it raises `NotImplementedError` pointing at the plan.

### Step 6. Remove the old orchestrators behind a guided error

Files: `pydantic_schemaforms/form_layouts.py`, `rendering/layout_engine.py`, `layouts.py`, `__init__.py`, `enhanced_renderer.py`

- Add `class FormLayoutRemovedError(TypeError)` in `form_layouts.py` with the message template:

  ```
  {name} was removed in {version}. Complex forms are now built by nesting FormModels:

      # before                                      # after
      class ContactTab(VerticalLayout):             class Profile(FormModel):
          form = Contact                                contact: Contact = Field(title="Contact")
      class Tabs(TabbedLayout):                         address: Address = Field(title="Address")
          contact = ContactTab()
      class Profile(FormModel):                     render_form_html(Profile, layout="tabbed", submit_url=...)
          tabs: Tabs = Field(input_type="layout")   Profile.validate(await request.form(), submit_url=...)

  Full guide: python -m pydantic_schemaforms.ai_instructions claude  (section "Upgrading to nested forms")
              or docs/complex_forms.md#upgrading
  ```

  Replace `FormLayoutBase`, `VerticalLayout`, `HorizontalLayout`, `TabbedLayout`, `ListLayout`, `SectionDesign`, `FormDesign` bodies with stubs whose `__init_subclass__` and `__init__` raise it (subclassing is the common usage, so the user's module fails at import with the guide). `ListLayout`'s message adds one line: `use  items: list[Item] = Field(default_factory=list, ui_element="model_list")`.
- Delete `pydantic_schemaforms/layouts.py` (the deprecated shim).
- `rendering/layout_engine.py`: delete `render_layout_field_fallback`, `render_layout_field_content_fallback`, `_extract_fallback_mapped_data`, `_safe_layout_tabs`, `_tab_payload_from_main_data`, `_extract_layout_nested_data`, and the `isinstance(value, BaseLayout)` branch in `_build_layout_body`. `get_nested_form_data(field_name, data)` reduces to `data.get(field_name) if dict else {}`. `_build_layout_body` becomes: registered `layout_handler` → call it; else raise `FormLayoutRemovedError`-style `ValueError("input_type='layout' needs layout_handler=...")`.
- `enhanced_renderer.py`: remove the `default_factory()` pre-population loop for layout fields (`:254-271`) if `DataTableLayout` does not depend on it (verify with `tests/test_datatable_layout.py`); keep otherwise.
- `__init__.py`: top-level `VerticalLayout` / `HorizontalLayout` now point at the flex primitives from `rendering/layout_engine.py` (they are the only ones left). Keep exporting `TabbedLayout`, `ListLayout`, `FormLayoutBase`, `SectionDesign`, `FormDesign` (the raising stubs) under a `# ── REMOVED: raise FormLayoutRemovedError with upgrade guide ──` comment; export `FormLayoutRemovedError`. Drop `flatten_nested_data` from the documented surface (keep importable).
- Hygiene test: no module under `pydantic_schemaforms/` contains `from examples` / `import examples`.

### Step 7. Migrate the shipped examples

Only `examples/` in this change; `demo_app/` pins the PyPI release (`demo_app/requirements.txt`) and is migrated after this ships.

- `examples/nested_forms_example.py:1718-1785`: one `ComprehensiveTabbedForm(FormModel)` with six nested-model fields (see Example). `create_sample_nested_data()` → nested shape.
- `examples/date_time_formats_example.py:268-317`: `DateTimeFormatsShowcaseForm` gets `dates`, `times`, `datetimes` nested fields; wrappers deleted.
- `examples/shared_models.py`: `LayoutDemonstrationForm` → four nested-model fields; its route takes `?layout=vertical|tabbed|side-by-side|accordion`. `WidgetGalleryForm`/`WidgetGalleryTabs` → nested fields. Delete all `*Layout` wrapper classes.
- `examples/fastapi_routes.py`: every POST handler becomes `Model.validate(await request.form(), submit_url=..., layout=...)`; delete `_group_form_data` (`:232-253`), all `parse_nested_form_data` calls, `flatten=` usages, and the `FormLayoutBase` JSON filter branch (`:350-361`). `examples/menu_order_example.py`: drop `flatten`. Drop inert `model_class=` / `section_design=` kwargs from `model_list` fields.
- `examples/README.md`: one paragraph on composing by nesting, pointing at `docs/complex_forms.md`.

### Step 8. Documentation and AI instructions

- **New `docs/complex_forms.md`** "Composing complex forms": nest models; `layout=` table (vertical/tabbed/side-by-side/accordion, wizard marked "planned"); ordering (declaration order, `ui_order`); per-group options; JSON in/out with the exact `result.data` / `result.errors` shapes and the `_errors` convention; the route round-trip; deep nesting; `error_list()` for summaries/HTMX; a short "Wire format (internal)" note; and `## Upgrading` with the before/after for `TabbedLayout`/`VerticalLayout`/`HorizontalLayout`, `ListLayout` → `model_list`, `parse_nested_form_data` + `flatten` → `validate(request.form)`, string error keys → tree. Add to `mkdocs.yml` nav after Layouts.
- **`docs/layouts.md`**: intro points at `complex_forms.md`; modes list updated (heuristic tabbing removed, accordion added); import examples use top-level names.
- **`docs/recipes.md`**: replace the fictitious Tabbed/Horizontal recipes (`:1020-1058`); update "Repeating sub-forms" (`:600-668`) and "Nested vs. flat form data" (`:1170-1205`) to the JSON contract (remove `flatten`, remove manual `parse_nested_form_data`); update the FastAPI/Flask GET+POST recipes (`:31-90`) to `validate(await request.form())`; add a "Sub-form (nested model)" recipe.
- **`docs/validation_guide.md`**: document the nested error tree, `_errors`, `error_list()`.
- **`README.md`** (source of `docs/index.md`): "Complex forms" bullet with a five-line snippet; plain-text doc references.
- **`pydantic_schemaforms/assets/ai/_shared_instructions.md`**, then `make ai-instructions`:
  - New section "Composing complex forms from multiple FormModels" (nest, `layout=`, ordering via `ui_order`, JSON in/out, error tree).
  - New section **"Upgrading to nested forms"** (the target of the error message): a table of removed API → replacement (`TabbedLayout`/`VerticalLayout`/`HorizontalLayout` wrappers → nested fields + `layout=`; `ListLayout` → `model_list`; `SectionDesign`/`FormDesign` → `Field(title=..., ui_help_text=...)` and page templating; `parse_nested_form_data(...)` in routes → `validate(request.form)`; `flatten=True` → removed, data is nested; error keys `"pets[0].name"` → `errors["pets"][0]["name"]`; `layout="tabbed"` on a flat form → split into sub-models), each with a before/after snippet, plus the rule "never construct wire-format keys yourself".
  - Rewrite "Nested vs. flat form data" (`:682-702`) and the model_list section (`:755-776`) to the JSON contract; update the ui_element table Structural row (`nested_model` inferred automatically); update Layout guidance; fix the composite sample to the positional signature `(field_name, field_schema, value, ui_info, context, engine)`; add the removals to Common mistakes.
- **`CHANGELOG.md`**: `## [26.4.0] — <date>` above the `## Latest Changes` sentinel with **Breaking Changes** (orchestrators removed with guided error; `flatten` removed; error shape is a nested tree; `layout="tabbed"` requires nested models; `layouts.py` removed; top-level `VerticalLayout`/`HorizontalLayout` now name the flex primitives), **Added** (nested sub-model rendering; `accordion`; `validate()` accepts the raw request form; `error_list()`; `docs/complex_forms.md`), **Fixed** (errors inside layouts, swallowed nested validation, example coupling, DataTable field-name collision). Version bump itself via BumpCalver.

### Step 9. Tests

New `tests/test_nested_model_forms.py`:

- **Rendering**: `address.city` input names; sub-model section title; `Optional[Address]`; sub-model containing `model_list` → `home.pets[0].name`; same inner field name in two sub-models stays distinct; `ui_collapsible`; file input inside a sub-model switches to multipart.
- **Groups**: `tabbed` order equals declaration order and respects `ui_order`; "General" only when plain fields exist; `side-by-side` columns; `accordion` panels; flat form + `tabbed` raises `ValueError`; first errored group is active on re-render.
- **JSON in**: `validate()` accepts a Starlette `FormData`, a Werkzeug `MultiDict`, a list of pairs, a flat dict, and a nested dict, all producing identical `result.data`; coercion at depth (`'on'` → `True` inside a sub-model, `'3'` → `3` inside a list item); repeated keys → list.
- **JSON out**: `result.data` nested; `result.errors` tree with `address.city`, `pets[1].age`, list-level `_errors`, model-validator `_errors`; `error_list()` locs; `render_with_errors()` places each message next to its input inside the right tab; `flatten=True` raises `TypeError`.
- **Removal**: subclassing or instantiating `TabbedLayout`, `VerticalLayout` (old), `ListLayout`, `SectionDesign`, `FormDesign` raises `FormLayoutRemovedError` whose message contains "Upgrading to nested forms"; `import pydantic_schemaforms.layouts` fails.
- **Hygiene**: no `examples` import inside the package.

Update/replace: `tests/test_form_layouts.py` (becomes the removal tests), `tests/test_layouts.py` (drop fallback/heuristic tests), `tests/test_deep_nested_validation.py` (tree lookups), `tests/test_form_data_parsing.py` and `tests/test_schema_form.py` (drop `flatten`), `tests/test_integration.py` (nested results), `tests/test_model_list_integration.py` and `tests/test_datatable_layout.py` (error tree / field-named rows). Leave `tests/test_invariants.py` and `tests/test_meta_invariants.py` untouched.

### Step 10. HTMX live validation follow-through (small)

`LiveValidator.register_model_validator` (`live_validation.py:258-284`) registers only top-level fields. Extend it to walk nested models and register validators under the wire name (`address.city`), and make the `/validate/{field_name}` examples accept dotted names. Responses keep `ValidationResponse` (single field), so no shape change.

## Follow-up: step wizard (`layout="wizard"`), designed on the new model

Built; see "Step wizard: as built" in the handoff for where it differs.

- **Structure**: identical to tabs. Groups (General + each nested/list/layout field, declaration order) become steps. One `<form>`, all steps rendered, only the active step visible, so a single POST submits everything and no server-side session state is needed.
- **Markup**: a new `WizardLayout` primitive in `rendering/layout_engine.py` (next to `TabLayout`), rendering a progress header (step n of N with titles), one `<section data-step="i">` per group, and a footer with Back / Next / Submit buttons. Framework styling via `FormStyleTemplates` entries (`wizard_header`, `wizard_step`, `wizard_footer`) for Bootstrap and Material, like `layout_section`.
- **Behaviour** (vendored script `assets/js/wizard.js`, loaded the same way as the model_list script): Next runs `reportValidity()` on the inputs inside the current step only (HTML5 constraints already emitted by the renderer: `required`, `min`, `max`, `minlength`, `pattern`), then advances; Back never validates; Submit is the normal form submit. Optional per-step server validation can reuse the HTMX `LiveValidator` endpoint per field. Without JavaScript, all steps are shown stacked and the form still submits (progressive enhancement).
- **Errors**: on re-render, the active step is the first group that has an error (same rule as tabs); other steps with errors get a marker in the progress header. `errors["_errors"]` (form-wide) shows on the last step.
- **Options**: `Field(..., ui_step_title="Your details")` overrides the step label (falls back to `title`); `render_form_html(..., layout="wizard", ui_options={"wizard": {"show_progress": True, "linear": True}})` where `linear=False` lets the header jump to any step.
- **Tests**: step count equals group count; only step 0 visible initially; Next blocked by HTML5-invalid input (Playwright, under `tests/playwright`); server re-render activates the errored step; no-JS fallback renders all steps.
- **Docs**: a "Wizard" subsection in `docs/complex_forms.md` and the `layout=` table; AI instructions Layout guidance.

## Files touched

- Modify: `pydantic_schemaforms/rendering/schema_parser.py`, `rendering/field_renderer.py`, `rendering/layout_engine.py`, `rendering/model_list_renderer.py`, `rendering/datatable_renderer.py`, `enhanced_renderer.py`, `validation.py`, `schema_form.py`, `form_data.py`, `form_layouts.py`, `datatable_layout.py`, `live_validation.py`, `integration/{sync,async_support,builder}.py`, `__init__.py`, `assets/ai/_shared_instructions.md` (+ regenerated profiles), `docs/{layouts,recipes,validation_guide,configuration}.md`, `README.md`, `mkdocs.yml`, `CHANGELOG.md`, `examples/*.py`, `examples/README.md`, the tests listed in Step 9.
- Create: `NextVersion.md` (this document), `pydantic_schemaforms/rendering/nested_model_renderer.py`, `docs/complex_forms.md`, `tests/test_nested_model_forms.py`.
- Delete: `pydantic_schemaforms/layouts.py`.

## Verification

Requires Python 3.14 (this host only has 3.10; the sibling `demo-pydantic-schemaforms/.venv` was built in a devcontainer). Use the devcontainer, or `uv python install 3.14 && uv venv && uv pip install -e .[dev]`.

```bash
pytest -n 2 --ignore=tests/playwright
pytest tests/test_invariants.py -v
ruff check pydantic_schemaforms tests && ruff format --check pydantic_schemaforms tests
make ai-instructions && git status --short pydantic_schemaforms/assets/ai/    # profiles regenerated, never hand-edited
make create-docs-local                                                          # docs build, new page in nav
python -c "import examples.nested_forms_example, examples.shared_models, examples.date_time_formats_example"
python -c "from pydantic_schemaforms import TabbedLayout
class T(TabbedLayout): pass" 2>&1 | grep -q 'Upgrading to nested forms'     # guided error fires at class definition
uvicorn examples.main:app --reload
#   /nested-forms: submit with an invalid City -> error shown inside the "Home address" tab; success page shows nested JSON
#   /layout-demo?layout=side-by-side and ?layout=accordion
```

## Out of scope (deliberately)

- `dict[str, Model]` fields (no wire encoding decided).
- The wizard itself (planned above; next change).
- A JSON-submit mode (`application/json` from the browser). Declined for now; `validate()` already accepts a nested dict, so a JSON API route works today with `Model.validate(await request.json())`.
- Migrating `demo_app/` (after release).
