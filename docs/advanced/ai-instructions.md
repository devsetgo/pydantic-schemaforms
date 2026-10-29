# AI Assistants and Agent Skills

AI coding assistants are trained on older code, so they tend to suggest APIs this library has
removed. pydantic-schemaforms ships its own instructions for them, inside the package, so they
always match the version you have installed.

## Agent skills (recommended)

The package includes five [Agent Skills](https://agentskills.io). Install them into your project
with [library-skills](https://library-skills.io/):

```bash
uvx library-skills --claude
```

It finds the skills in your installed packages and links them into `.agents/skills/`, and into
`.claude/skills/` with `--claude` (Claude Code reads only that folder). The links point into the
installed package, so upgrading pydantic-schemaforms updates the skills too; run the command
again after adding or removing packages. On Windows without symlink permission, add `--copy`.

| Skill | Your assistant uses it when you… |
|---|---|
| `pydantic-schemaforms` | build or change forms: fields, validation, nested forms, layouts, CSV import tables, live validation, CSRF, styling, or a form that misbehaves |
| `schemaforms-create` | ask for a new form from a description: "create a login form", "create a tabbed layout for a customer profile". The code comes commented like a tutorial. |
| `schemaforms-convert` | turn a Pydantic model, dataclass, JSON Schema, WTForms or Django form into a `FormModel` |
| `schemaforms-upgrade` | upgrade code that uses removed APIs such as `FormBuilder` or `TabbedLayout` |
| `schemaforms-document` | document the app's forms: docstrings and help text in the code, and a Markdown page describing every form |

In Claude Code you can also call one directly, for example `/schemaforms-create a contact form`.

## Single-file instructions

For assistants that don't read skills, the same guidance is available as one file to put in your
repository:

```bash
python -m pydantic_schemaforms.ai_instructions claude --write     # writes ./CLAUDE.md
python -m pydantic_schemaforms.ai_instructions copilot --write    # writes ./.github/copilot-instructions.md
python -m pydantic_schemaforms.ai_instructions generic > AI_INSTRUCTIONS.md
```

The file holds the shared rules, everything in the `pydantic-schemaforms` skill and its
references, and the convert and upgrade skills. Unlike the skills, a copied file doesn't update
with the package: write it again after upgrading.

```
usage: python -m pydantic_schemaforms.ai_instructions [-h] [--write]
                                                       [--output PATH]
                                                       [profile]

positional arguments:
  profile        Instruction profile (aliases accepted). One of: claude,
                 copilot, generic.

options:
  -h, --help     show this help message and exit
  --write        Write to the suggested destination file (e.g. CLAUDE.md)
                 instead of stdout.
  --output PATH  Write to an explicit path instead of stdout or the suggested
                 destination.
```

The same text is available from Python:

```python
from pydantic_schemaforms import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)

available_instruction_profiles()           # ('claude', 'copilot', 'generic')
suggested_instruction_filename('copilot')  # '.github/copilot-instructions.md'
get_app_instructions('claude')             # the full text
```

Aliases such as `'github-copilot'` and `'anthropic-claude'` are accepted; an unknown profile
raises `ValueError`.

## What the instructions cover

- The rules that matter most: import only from the top-level package, use the built-in inputs
  and composites instead of hand-written HTML or JavaScript, put limits in `Field()` constraints
  (not `ui_options`), and build HTML around submitted data with `html(t'...')`.
- The route pattern (`render_form_html()`, `validate()`, `render_with_errors()`) for FastAPI and
  Flask, taken from the tested examples in these docs.
- Every `ui_element`, every `ui_options` key and every `Field()` setting.
- Nested, optional and repeating sub-forms, layouts and the wizard; rule-based and live HTMX
  validation; data tables; CSRF, captcha, honeypot and uploads; JSON APIs; extending the library.
- Mapping tables for converting from Pydantic, WTForms, Django and JSON Schema, and upgrade
  tables for every removed API.

## Try it in the example app

The FastAPI example app renders all three single-file profiles at `/ai-instructions`.

## Maintaining the instructions

Everything shipped is generated; never edit it directly:

| Generated | Source |
|---|---|
| `pydantic_schemaforms/.agents/skills/<name>/` | `ai/skills/<name>/` |
| `pydantic_schemaforms/assets/ai/*_app_instructions.md` | `ai/profiles/<profile>.md`, `ai/_shared.md` and `ai/skills/` |

Edit the sources, then run `make ai-instructions` (`scripts/build_ai_instructions.py`). In the
sources, `<!-- INCLUDE: _shared.md -->` inserts the rules every skill shares, and
`<!-- INCLUDE-CODE: docs_src/... -->` inserts an example file from `docs_src/`, which
`tests/test_docs_examples.py` runs, so the skills' examples can't go stale.

`tests/test_ai_skills.py` checks that each skill has a valid name and description, stays under
500 lines, links only to files that exist, imports only from the top-level package, and matches
its sources. It also checks that every value in the `ui_element` table is a registered input. The
"Agent skills install from the wheel" CI job builds the wheel and installs the skills with the
real `library-skills` CLI.
