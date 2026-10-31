# Contributing

Contributions are welcome: bug reports, fixes, documentation, tests and new features.
Check the [Roadmap](https://github.com/devsetgo/pydantic-schemaforms/blob/main/ROADMAP.md)
first, and open an issue before starting anything large.

## Setting up

Python 3.14 or newer is required.

```bash
git clone https://github.com/devsetgo/pydantic-schemaforms.git
cd pydantic-schemaforms
make install
```

## Before opening a pull request

- Run `make tests`. It runs pre-commit, pyright and the full test suite.
- Keep `tests/test_form_data_parsing.py` passing when changing nested form parsing. It's a
  required regression suite, run explicitly by `make tests` and in CI.
- A new input, layout or kind of validation needs a working example in `examples/`, under both
  Bootstrap and Material, in the same pull request. `tests/test_examples_coverage.py` checks this.
- Build HTML with `html(t'...')`, never an f-string around user data. `string.Template` is banned.

## Editing the documentation

Some files are generated. Change their source instead:

| Generated | Source |
|---|---|
| `docs/index.md`, `docs/contribute.md`, `docs/release-notes.md` | `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md` |
| The input list in `docs/reference/inputs.md` | `examples/input_type_reference.py`, then `scripts/generate_input_type_reference.py` |
| `pydantic_schemaforms/.agents/skills/`, `pydantic_schemaforms/assets/ai/` | `ai/`, then `make ai-instructions` |

Code examples in the docs live in `docs_src/`, where tests run them. `make docs-build` builds the
site locally.
