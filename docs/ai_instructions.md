# AI Assistant Instructions

`pydantic-schemaforms` ships packaged, verified integration instructions for AI coding
assistants (Claude, GitHub Copilot, and a generic profile), so an assistant working in an
app repo that depends on this library can produce correct, idiomatic integrations without
reverse-engineering package internals or guessing at deprecated patterns.

Two things make this different from a normal docs page copied into a prompt:

- **It ships with the library.** Every install of `pydantic-schemaforms` carries the current
  instructions as packaged data — they can't drift out of sync the way a copy-pasted snippet
  in someone's `CLAUDE.md` can.
- **It's discoverable without being asked.** The top-level package docstring and
  `FormModel`'s class docstring both point an AI assistant at this feature, so it can find
  it on its own the first time it inspects the library — see `pydantic_schemaforms/__init__.py`.

## What's covered

Each profile documents the same underlying integration contract:

- The `FormModel` + `Field()` + `render_form_html()` pattern, and the lower-boilerplate
  `FormModel.validate()` / `render_with_errors()` alternative.
- CSRF protection (`csrf_mode`, `csrf_token_provider`, verification before validation).
- Repeating sub-forms (`model_list`): resolving the item model from a `list[ItemModel]`
  annotation, and the `ui_add_button_label` / `ui_item_title_template` /
  `ui_collapsible_items` / `ui_items_expanded` customization knobs.
- Dual-use JSON + HTML models via `as_api_model()`.
- The distinction between Field constraints (`min_length`, `max_length`, `pattern`, `ge`/`le`
  — enforced server-side and reflected in HTML automatically) and `ui_options` (UI-only
  knobs with no constraint equivalent) — getting this wrong produces a form that *looks*
  validated but isn't.
- Deterministic field-mapping rules (Python type → `ui_element`) so repeated runs converge
  on the same output instead of drifting between requests.

HTMX live validation (`LiveValidator`) is intentionally **not** yet part of the packaged
instructions — see [Validation Guide](validation_guide.md) for that.

## Python API

```python
from pydantic_schemaforms import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)

available_instruction_profiles()
# ('claude', 'copilot', 'generic')

suggested_instruction_filename('claude')
# 'CLAUDE.md'
suggested_instruction_filename('copilot')
# '.github/copilot-instructions.md'
suggested_instruction_filename('generic')
# 'AI_INSTRUCTIONS.md'

get_app_instructions('claude')
# full instructions text for the Claude profile
```

Aliases are accepted where they're unambiguous — `get_app_instructions('github-copilot')`
and `get_app_instructions('anthropic-claude')` both resolve to the same profile as
`'copilot'` / `'claude'`.

An unsupported profile raises `ValueError` naming the supported profiles, rather than
silently falling back to one.

## CLI

Bootstrap an app repo's instruction file in one command instead of writing a throwaway
script:

```bash
python -m pydantic_schemaforms.ai_instructions claude --write
# writes ./CLAUDE.md

python -m pydantic_schemaforms.ai_instructions copilot --write
# writes ./.github/copilot-instructions.md (parent dirs created as needed)

python -m pydantic_schemaforms.ai_instructions generic > AI_INSTRUCTIONS.md
# or redirect stdout yourself
```

Full CLI usage:

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

## Try it in the example app

The FastAPI example app renders all three profiles as tabs at `/ai-instructions` (linked
from the "AI Assistant Instructions" card on the home page) — the same content
`get_app_instructions()` returns, rendered from the packaged markdown files.

## Keeping this feature honest

The packaged instructions are cross-checked against the library's actual behavior, not
just written once and left to drift — every claim in them (which `ui_*` kwargs exist,
what `model_list` options do, how CSRF verification works) has been verified by running
the corresponding code, not just read from source. If you add a Field kwarg or change
`model_list` behavior, update `pydantic_schemaforms/assets/ai/*.md` in the same change.
