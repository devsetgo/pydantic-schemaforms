# Testing & Contribution Workflow

This document describes the authoritative workflow for running tests, linting, and contributing to pydantic-schemaforms.

## Single Entry Point: `make tests`

Use **`make tests`** (or **`make test`**) as the single, canonical command for running all quality checks before committing:

```bash
make tests
```

This runs:
1. **Pre-commit hooks** (Ruff linting + formatting, YAML/TOML checks, trailing whitespace)
2. **Type check** (`pyright`)
3. **Parser regression suite** (`tests/test_form_data_parsing.py`)
4. **Full pytest suite** (~1,700 tests covering validation, rendering, async, layouts, examples, integration)
5. **Coverage badge generation** (summarizes test coverage)

## Workflow

### Before Committing

```bash
# Full quality check
make tests

# Or run individual steps if debugging:
make ruff          # Lint + format only
make isort         # Sort imports
make cleanup       # Run all formatters (isort + ruff + autoflake)
```

### What Happens in `make tests`

```
🔍 Running pre-commit (ruff, formatting, yaml/toml checks)...
✅ Pre-commit passed. Running type check...
✅ Type check passed. Running form-data parser regression tests...
🧪 Regression passed. Running full pytest suite...
[full suite runs]
📊 Generating coverage and test badges...
✨ Tests complete. Badges updated.
```

## Test Organization

Tests are organized in `tests/` by domain — one file per subject area:

| Test File | Purpose | ~Tests |
|-----------|---------|--------|
| `test_inputs.py` | All input component types (text, datetime, selection, specialized) | 185 |
| `test_validation.py` | Validation rules, engine, HTMX live validation | 180 |
| `test_assets.py` | Vendor assets, CDN/vendored modes, Bootstrap Icons | 130 |
| `test_input_rendering.py` | Rendered HTML of each input type and its widget options | 140 |
| `test_integration.py` | Schema generators, FastAPI integration, HTML markers | 50 |
| `test_rendering.py` | EnhancedFormRenderer, themes, templates | 115 |
| `test_layouts.py` | Layout engine, TabLayout, AccordionLayout, async rendering | 95 |
| `test_examples_coverage.py` | Every layout, input, widget option, and validation kind has a working example; every example route renders under both styles | 80 |
| `test_docs_examples.py` | Runs every `docs_src/` app's GET and POST routes | 65 |
| `test_ai_skills.py` + `test_ai_instructions.py` | Packaged skills and instructions are valid and match their sources | 60 |
| `test_nested_model_forms.py` | Composing forms by nesting FormModels: rendering, grouped layouts, nested data and errors | 85 |
| `test_field_renderer_coverage.py` | Field-level rendering logic | 60 |
| `test_schema_form.py` + `test_schema_form_coverage.py` | FormModel, Field, schema parsing | 95 |
| `test_template_coverage.py` | t-string templates in `templates.py` / `FormStyle` | 55 |
| `test_datatable_layout.py` | DataTableLayout composite (CSV import, row errors) | 60 |
| `test_live_validation_coverage.py` | HTMX live validation config | 45 |
| `test_form_data_parsing.py` | Nested form data parsing | 25 |
| `test_form_layouts.py` | Removed layout classes raise `FormLayoutRemovedError` with upgrade steps | 20 |
| `test_invariants.py` + `test_meta_invariants.py` | **Protected.** Enforce the t-string / no-`string.Template` rule; never remove or weaken | 6 |
| `test_theme_contract.py` | No framework branching outside the themes; Material CSS uses tokens | 5 |
| Smaller focused files | CSRF, debug mode, model lists, plugin hooks, benchmarks, etc. | ~150 |

`tests/playwright/` holds browser tests: every example page must load without a JavaScript error and pass axe-core (WCAG 2.0–2.2 A/AA plus best practices) with no serious or critical accessibility violation (both styles, light and dark, plus the validation error state); see `docs/reference/accessibility.md`. axe-core is vendored for tests only in `tests/playwright/vendor/`, pinned by version and SHA-256. CI runs these in their own job. `test_material_screenshots.py` writes Material page PNGs to `tests/playwright/screenshots/` to look at, since a passing test doesn't show how a page looks.

## Linting Rules (Ruff)

Ruff runs these rule sets (see `[tool.ruff.lint]` in `pyproject.toml`):
- **F**: unused imports and variables, undefined names
- **E, W**: style errors and warnings
- **B**: likely bugs
- **C**: comprehensions
- **TID**: banned APIs, including `string.Template`

If Ruff finds issues, run:
```bash
make ruff  # Auto-fix what it can
```

Then manually review any remaining issues and re-run `make tests`.

## CI/CD Integration

- **Local**: `make tests` validates code before pushing
- **GitHub Actions** (`.github/workflows/testing.yml`): Runs lint, pyright, the test matrix (Python 3.14 and 3.15 on Linux, macOS and Windows) and Playwright on each PR
- **Pre-commit**: Enabled for all developers via `.pre-commit-config.yaml`

## Dependencies

All test dependencies are in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key packages:
- `pytest` + `pytest-asyncio` + `pytest-cov` (testing)
- `ruff` (linting + formatting)
- `isort` (import sorting)
- `genbadge` (coverage reporting)
- `pre-commit` (hook management)

## Troubleshooting

### "pre-commit not found"

```bash
pip install pre-commit
# or
make install
```

### "pytest not found"

```bash
pip install -r requirements.txt
```

### Ruff keeps failing on the same file

Check what Ruff found:
```bash
make ruff
```

If it's an actual issue (not auto-fixable), edit the file manually and re-run.

### Running only pytest (skip pre-commit)

```bash
pytest tests/
```

⚠️ **Not recommended** — linting failures will catch issues in CI anyway.

### Running a specific test

```bash
# Run all tests for a domain
pytest tests/test_validation.py -v
pytest tests/test_rendering.py -v

# Run a specific test class or function
pytest tests/test_layouts.py::TestAsyncFormRendering::test_async_render_returns_same_html_as_sync -v
pytest tests/test_assets.py -k "bootstrap_icons" -v
```

## Contributing

1. Create a branch: `git checkout -b feature/my-feature`
2. Make changes, add tests
3. Run `make tests` to validate
4. Commit and push
5. Open a PR — CI will run the same checks

All PRs must pass:
- ✅ Ruff linting
- ✅ Type check (pyright)
- ✅ pytest (all tests, 90% coverage)
- ✅ Playwright (browser and accessibility tests)
