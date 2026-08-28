# pydantic-schemaforms — Claude Code guide

## Project overview

Server-rendered HTML form library for Pydantic 2 models. Requires Python 3.14+.
Calendar versioning: `YY.Q.patch` (e.g. `26.2.2`).

## Key commands

```bash
pytest -n 2 --ignore=tests/playwright          # fast parallel test run
pytest tests/test_invariants.py -v             # check architectural invariants
ruff check pydantic_schemaforms tests          # lint
ruff format --check pydantic_schemaforms tests # format check
make ai-instructions                           # rebuild packaged AI-instruction files after editing their source
```

## Documentation pipeline — generated files, never hand-edit

Three files under `docs/` are **build artifacts**, copied verbatim from
repo-root source files by `scripts/changelog.py` + `make create-docs` /
`make create-docs-local` (and by `.github/workflows/deploy-docs.yml` on
release). Any hand edit made directly to the `docs/` copy is silently
overwritten the next time docs are built:

| Generated (`docs/…`, don't edit) | Source of truth (edit this instead) |
|---|---|
| `docs/index.md`         | `README.md` |
| `docs/contribute.md`    | `CONTRIBUTING.md` |
| `docs/release-notes.md` | `CHANGELOG.md` (its `## Latest Changes` section is further regenerated from GitHub Releases by `scripts/changelog.py` — don't hand-edit that section either; edit the static part above the sentinel if you need a permanent entry) |

Everything else under `docs/` (`recipes.md`, `validation_guide.md`,
`quickstart.md`, `tutorial_fastapi.md`, etc.) is genuinely hand-maintained —
edit those directly. One exception: `docs/recipes.md`'s "Every input type"
section (between the `<!-- BEGIN/END GENERATED: input-type-reference -->`
markers) is generated from `examples/input_type_reference.py` — the same
data backing the FastAPI demo's `/input-types` page — by
`scripts/generate_input_type_reference.py`; edit that Python file and rerun
the script, don't hand-edit the generated markdown. `tests/test_docs_generated_sections.py`
fails the suite if the two drift out of sync.

To verify a doc change (including regenerating the three copies above from
their sources) without touching the deploy pipeline: `make create-docs-local`
(runs `scripts/changelog.py`, copies the three files, then `mkdocs build`).

The 3 packaged AI-assistant instruction files under
`pydantic_schemaforms/assets/ai/` (`generic_app_instructions.md`,
`copilot_app_instructions.md`, `claude_app_instructions.md` — read by
`pydantic_schemaforms/ai_instructions.py`'s `get_app_instructions()`/CLI) are
**also build artifacts**, same rule: never hand-edit them directly. Edit
`pydantic_schemaforms/assets/ai/_shared_instructions.md` (the common body) or
`_profile_{generic,copilot,claude}.md` (the small per-profile intro/outro,
each containing an `<!-- INCLUDE: _shared_instructions.md -->` marker)
instead, then run `make ai-instructions` (`scripts/build_ai_instructions.py`
— also runs automatically as part of `make create-docs`/`create-docs-local`).
Cross-links between `README.md`/`docs/index.md` and other `docs/*.md` files
can't use a single relative path that resolves correctly in both GitHub's
README rendering and mkdocs' site (the same file serves both), so prefer
plain-text references (e.g. "see `docs/recipes.md`") over `[text](path)`
links there.

## Public API surface — keep exports and AI instructions honest

`pydantic_schemaforms/assets/ai/_shared_instructions.md` tells AI agents building apps with this
library that **the only supported import surface is the top-level package**
(`from pydantic_schemaforms import ...`) — never an internal submodule. That promise is only true
if every name the instructions reference is actually re-exported top-level. When adding a new
public class/function meant for app-author use:

1. Add it to `pydantic_schemaforms/__init__.py`'s imports and `__all__` list — or, for a new
   input-related utility living under `pydantic_schemaforms/inputs/`, add it to the appropriate
   list in `inputs/__init__.py` (`UTILITIES`/`SPECIALIZED_UTILITIES`/`REGISTRY_UTILITIES`) and map
   it to its defining module in `_MODULE_MAP` right below; the top-level package then forwards it
   automatically via its own lazy `__getattr__`, no separate top-level import needed.
2. If it's something an app-building agent would plausibly need, document it in
   `pydantic_schemaforms/assets/ai/_shared_instructions.md` and run `make ai-instructions`.
3. Never let an example inside `_shared_instructions.md`, `docs/*.md`, or `examples/*.py` import
   from an internal submodule to work around a missing top-level export — that means the export
   is missing, not that the example needs a workaround. Add the export instead.

This was violated for `register_input_class` and `LayoutEngine` — real, working extension points
with no top-level export, silently contradicting the AI instructions' own stated rule — until an
audit caught it and both were added. Verify a name genuinely imports from the top level before
referencing it in any doc or AI-instructions example.

## Repository layout

```
pydantic_schemaforms/
  tstring.py           # SafeHTML + html() processor — the XSS safety core
  templates.py         # FormTemplates: t-string render functions for form elements
  composite_layout.py  # CompositeLayoutModel — base for FormModel-shaped composites
  datatable_layout.py  # DataTableLayout — reference composite (CSV-import-to-table)
  rendering/
    form_style.py           # FormStyle / FormStyleTemplates — framework-specific templates
    layout_engine.py        # Layout rendering pipeline + composite-renderer registry
    datatable_renderer.py   # DataTableLayout's registered renderer
    model_list_renderer.py  # model_list's registered renderer
  inputs/             # Field-level input classes
  integration/        # Framework adapters (FastAPI, Flask)
examples/             # Live usage examples (not part of the package)
tests/
  test_invariants.py      # ← PROTECTED, see below
  test_meta_invariants.py # ← PROTECTED, see below
```

---

## ══ HARD RULES — READ BEFORE MAKING ANY CHANGES ══

### T-string rule (structural XSS safety)

**`string.Template` is permanently banned from this codebase.**

All HTML generation uses Python 3.14 t-strings (`t"..."`) with the `html()`
processor from `pydantic_schemaforms/tstring.py`. This is the core
differentiator of the library: XSS protection is structural, not optional.

```python
# WRONG — never do this
from string import Template
html_out = Template('<input value="${val}">').substitute(val=user_input)

# RIGHT — use t-strings with the html() processor
from pydantic_schemaforms.tstring import SafeHTML, html
html_out = html(t'<input value="{user_input}">')   # user_input auto-escaped
```

**Rules:**
1. `string.Template` / `from string import Template` must NEVER appear in
   `pydantic_schemaforms/` source files.
2. Pre-rendered HTML fragments must be wrapped in `SafeHTML(...)` before
   interpolation so the processor does not double-escape them.
3. User-supplied values (form field values, labels, placeholders, help text)
   must be passed as plain `str` and let the processor escape them.
4. JavaScript generation (validation scripts, not HTML) may use f-strings —
   that's not an HTML context, so the html() processor doesn't apply there.
5. **This bar applies equally to every example this project ships, not just
   `pydantic_schemaforms/` source** — `pydantic_schemaforms/assets/ai/*.md`,
   `docs/*.md`, and `examples/*.py`. These are literally copy-paste templates
   for real apps; a vulnerable example is exactly as dangerous as a
   vulnerable library function. Any example that builds HTML from
   submitted/validated form data must use `html(t'...')`, never an f-string
   or `.format()` — a real instance of this (an f-string interpolating
   `result.data["full_name"]` into an `<h1>` in the flagship AI-instructions
   example) shipped and went unnoticed until an explicit audit found it.
   `.validate()`/`Field()` constraints succeeding confirms type/constraint
   compliance, not that a value is safe to place in HTML. Note this is a
   convention to enforce in review, not something `test_invariants.py`/ruff's
   TID251 catches — those only scan `pydantic_schemaforms/` source.

### Protected test files — NEVER remove or weaken

`tests/test_invariants.py` and `tests/test_meta_invariants.py` form a
**mutual guard** that enforces the t-string rule at test time (in addition to
the ruff TID251 lint-time check).

- **Do not delete either file.**
- **Do not remove or `pytest.mark.skip` any test inside them.**
- **Do not weaken assertions** (e.g., by adding paths to the allowlist without
  a concrete reason).
- **Do not add `# noqa: TID251`** to a line that actually uses `string.Template`.

If a test in these files fails after a legitimate refactor, fix the code that
broke the invariant — do not fix the test.

### ruff banned-api — NEVER remove

`pyproject.toml` contains:
```toml
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"string.Template" = {msg = "..."}
```

Do NOT remove this entry or remove `"TID"` from `[tool.ruff.lint] select`.

---

## Template authoring guide

To add a new template:

1. Write a private function in `templates.py` (or `rendering/form_style.py`
   for framework-specific variants):

```python
def _my_widget(*, label: str = '', value: str = '', **_: object) -> SafeHTML:
    return html(t'<div class="widget"><label>{label}</label><input value="{value}"></div>')
    #                                          ↑ text, auto-escaped   ↑ user input, auto-escaped
```

2. Wrap it in a `TemplateString` and add it to `FormTemplates`:

```python
class FormTemplates:
    MY_WIDGET = TemplateString(_my_widget)
```

3. For HTML fragment params (pre-rendered HTML passed in from another renderer),
   cast to `SafeHTML` at the top of the function so the processor passes them through:

```python
def _my_wrapper(*, content: str = '') -> SafeHTML:
    _content = SafeHTML(content)          # already-rendered HTML — pass through
    return html(t'<section>{_content}</section>')
```

## Composite layout controls — reuse this pattern, don't invent a new one

A "composite" control renders something bigger than a single input — a
whole table, a repeating list of sub-forms, wizard steps, and similar.
`DataTableLayout` (CSV-import-to-table) and `model_list` (repeating
sub-form items) are the two shipped examples; both go through the same
mechanism below. **When asked to build a new composite control, reuse this
mechanism instead of hand-rolling a bespoke rendering path** — this
codebase used to have three inconsistent ones (DataTableLayout's registry,
model_list's hardcoded dispatch branch, `form_layouts.py`'s unrelated
multi-FormModel orchestrators) before they were consolidated into this.
Full details and worked examples: `docs/plugin_hooks.md`. This section is
about *this library* shipping a new built-in composite (`builtin=True`); an
*app author* registering their own composite via this same `LayoutEngine`
mechanism (`builtin=False`) is the AI-instructions-facing use case — see
"Public API surface" above and `_shared_instructions.md`'s own coverage of it.

- **`CompositeLayoutModel`** (`pydantic_schemaforms/composite_layout.py`) —
  subclass this instead of `FormModel` directly when the composite's *own
  fields ARE its structure* (table columns, wizard steps, ...), meant to be
  embedded as a layout field and never rendered on its own. It disables
  `render_form()` with a `NotImplementedError` pointing at the class's own
  value-bundling classmethod (the `as_layout_value()` convention
  `DataTableLayout` uses), since `FormModel.render_form()`'s single-instance
  data/errors/submit_url shape doesn't apply. Not every composite needs
  this base — `model_list` doesn't, since its item model is just an
  ordinary, unmodified `FormModel` referenced via a `list[ItemModel]`
  annotation, not a wrapper class of its own.
- **Register the renderer** via `@LayoutEngine.layout_renderer(name)`
  (`pydantic_schemaforms/rendering/layout_engine.py`), in its own dedicated
  `rendering/<name>_renderer.py` module — not inline in
  `field_renderer.py`'s general field-dispatch logic.
- **Always keep `builtin=True`** (the decorator's default) for a renderer
  shipped by this library. `LayoutEngine.reset_layout_renderers()` is
  called by several test fixtures between tests across this project's own
  suite; module-level registration only ever runs once per process, so a
  non-builtin renderer is silently wiped for the rest of the process the
  first time that fires. Only one-off/app-level/test-only renderers should
  pass `builtin=False` (the plain `register_layout_renderer()` default).
- **Two independent dispatch keyspaces**, same registry: `layout_handler`
  (`input_type="layout"` + a `layout_handler` name — the field's own
  *value* carries what the renderer needs, as `DataTableLayout` does) or
  `ui_element` (the field's own `input_type`/`ui_element` string, looked up
  directly via `LayoutEngine.get_renderer_for_element` — as `model_list`
  does, with no change to its field-declaration API). Pick whichever
  matches how the composite's data actually flows in. Don't repurpose
  `input_type="layout"` for something that isn't shaped like a layout
  field — it also drives `SchemaMetadata.layout_fields` grouping and
  auto-tabbing behavior elsewhere in the renderer.
- `form_layouts.py`'s `TabbedLayout`/`VerticalLayout`/`HorizontalLayout`/
  `ListLayout` are a deliberately separate, out-of-scope mechanism — they
  orchestrate multiple independent `FormModel`s rendered together (their
  own `render()`/`validate()`, composed explicitly by app code), not one
  field rendering something complex. Don't fold a new composite into that
  family instead of this one without asking first.

## Coding standards

- No comments unless the WHY is non-obvious.
- No docstrings on trivial methods.
- No backwards-compatibility shims unless specifically requested.
- Prefer editing existing files to creating new ones.
- Run `pytest -n 2 --ignore=tests/playwright` before reporting a task done.
