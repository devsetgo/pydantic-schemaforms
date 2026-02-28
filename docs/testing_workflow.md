# Testing & Contribution Workflow

This document describes the authoritative workflow for running tests, linting, and contributing to pydantic-schemaforms.

## Single Entry Point: `make tests`

Use **`make tests`** (or **`make test`**) as the single, canonical command for running all quality checks before committing:

```bash
make tests
```

This runs:
1. **Pre-commit hooks** (Ruff linting + formatting, YAML/TOML checks, trailing whitespace)
2. **Parser regression suite** (`tests/test_form_data_parsing.py`)
3. **Full pytest suite** (900+ tests covering validation, rendering, async, layouts, integration)
4. **Coverage badge generation** (summarizes test coverage)

## What Changed

- **Ruff is now enabled** in `.pre-commit-config.yaml` and runs as part of `make tests`
- **Pre-commit hooks are mandatory** before pytest runs; if linting fails, tests don't start
- **No manual ruff invocation needed** — it's automatic via pre-commit

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
✅ Pre-commit passed. Running form-data parser regression tests...
🧪 Regression passed. Running full pytest suite...
[900+ tests run]
📊 Generating coverage and test badges...
✨ Tests complete. Badges updated.
```

## Test Organization

Tests are organized in `tests/` directory:

| Test File | Purpose | Count |
|-----------|---------|-------|
| `test_layout_demo_smoke.py` | Tab/accordion initial render | 3 |
| `test_e2e_layouts_async.py` | E2E: structure, integration, async | 14 |
| `test_plugin_hooks.py` | Input/layout registration | 2 |
| `test_model_list_integration.py` | Model list rendering & validation | 4 |
| `test_validation_consolidation.py` | Validation engine unification | 10 |
| `test_layouts.py` | Layout classes (tabs, accordions, cards) | 35+ |
| ... | Other units, integration, fixtures | 800+ |

## Linting Rules (Ruff)

Ruff checks for:
- **Import ordering** (`from __future__` first, stdlib, third-party, local)
- **Unused imports** and variables
- **Deprecated patterns** (old Pydantic v1 syntax)
- **Style** (line length, unused code)
- **Type hints** (basic checks)

If Ruff finds issues, run:
```bash
make ruff  # Auto-fix what it can
```

Then manually review any remaining issues and re-run `make tests`.

## CI/CD Integration

- **Local**: `make tests` validates code before pushing
- **GitHub Actions** (`.github/workflows/testing.yml`): Runs same checks on each PR
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
pytest tests/test_validation_consolidation.py -v
pytest tests/test_e2e_layouts_async.py::TestAsyncFormRendering::test_async_render_returns_same_html_as_sync -v
```

## Contributing

1. Create a branch: `git checkout -b feature/my-feature`
2. Make changes, add tests
3. Run `make tests` to validate
4. Commit and push
5. Open a PR — CI will run the same checks

All PRs must pass:
- ✅ Ruff linting
- ✅ Import ordering (isort)
- ✅ pytest (all tests)
- ✅ Coverage thresholds
