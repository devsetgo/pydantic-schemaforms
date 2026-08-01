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
edit those directly.

To verify a doc change (including regenerating the three copies above from
their sources) without touching the deploy pipeline: `make create-docs-local`
(runs `scripts/changelog.py`, copies the three files, then `mkdocs build`).
Cross-links between `README.md`/`docs/index.md` and other `docs/*.md` files
can't use a single relative path that resolves correctly in both GitHub's
README rendering and mkdocs' site (the same file serves both), so prefer
plain-text references (e.g. "see `docs/recipes.md`") over `[text](path)`
links there.

## Repository layout

```
pydantic_schemaforms/
  tstring.py          # SafeHTML + html() processor — the XSS safety core
  templates.py        # FormTemplates: t-string render functions for form elements
  rendering/
    form_style.py     # FormStyle / FormStyleTemplates — framework-specific templates
    layout_engine.py  # Layout rendering pipeline
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

## Coding standards

- No comments unless the WHY is non-obvious.
- No docstrings on trivial methods.
- No backwards-compatibility shims unless specifically requested.
- Prefer editing existing files to creating new ones.
- Run `pytest -n 2 --ignore=tests/playwright` before reporting a task done.
