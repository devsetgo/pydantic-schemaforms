# Contributing

Contributions are welcome — bug reports, docs improvements, and new widgets/layouts are all valuable.

## Quick ways to help

- Report bugs with a minimal repro (model + render call + expected/actual HTML)
- Improve docs (especially around assets, layouts, and input widgets)
- Add tests for regressions or new features

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run tests

```bash
pytest
```

If you’re working on asset behavior or HTML output, the most relevant tests live under `tests/` and generally assert for specific tags or markers.

## Formatting and linting

The repo includes common Python tooling (ruff/black/isort). Use whichever workflow you prefer, but please keep diffs focused and run the formatters before sending a PR.

## Docs

Docs are built with MkDocs Material.

```bash
mkdocs serve
```

### Release notes page

The release notes page can be generated from GitHub releases:

```bash
python scripts/generate_release_notes.py --repo devsetgo/pydantic-schemaforms --max 1000
```

If you hit API limits:

```bash
export GITHUB_TOKEN=...
python scripts/generate_release_notes.py --repo devsetgo/pydantic-schemaforms --max 1000
```
