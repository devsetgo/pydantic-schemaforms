#!/usr/bin/env python3
"""Generate the packaged AI-assistant instruction files from shared sources.

The 3 files `pydantic_schemaforms/assets/ai/{generic,copilot,claude}_app_instructions.md`
are build artifacts, same convention as `docs/index.md` <- `README.md` (see CLAUDE.md's
"Documentation pipeline" section) -- never hand-edit them directly. Edit
`pydantic_schemaforms/assets/ai/_shared_instructions.md` (the ~90% common body) or
`_profile_{generic,copilot,claude}.md` (the small per-profile intro + prompt-starter
wrapper, which contains an `<!-- INCLUDE: _shared_instructions.md -->` marker) instead,
then re-run this script (or `make ai-instructions`).

`pydantic_schemaforms/ai_instructions.py` (the runtime loader used by
`get_app_instructions()`/the CLI) is unaffected -- it only ever reads the generated
output files, unchanged filenames and format.
"""

from __future__ import annotations

from pathlib import Path

_AI_ASSETS_DIR = Path(__file__).resolve().parent.parent / 'pydantic_schemaforms' / 'assets' / 'ai'

_PROFILES = {
    'generic': 'generic_app_instructions.md',
    'copilot': 'copilot_app_instructions.md',
    'claude': 'claude_app_instructions.md',
}

_INCLUDE_MARKER = '<!-- INCLUDE: _shared_instructions.md -->'

_GENERATED_HEADER = (
    '<!-- GENERATED FILE -- do not edit directly. Source: '
    '_shared_instructions.md + _profile_{profile}.md. Regenerate with '
    '`make ai-instructions` (scripts/build_ai_instructions.py). -->\n'
)


def build_profile(profile: str) -> str:
    shared_body = (_AI_ASSETS_DIR / '_shared_instructions.md').read_text(encoding='utf-8')
    profile_source = (_AI_ASSETS_DIR / f'_profile_{profile}.md').read_text(encoding='utf-8')

    if _INCLUDE_MARKER not in profile_source:
        raise ValueError(f'_profile_{profile}.md is missing the {_INCLUDE_MARKER!r} marker')

    expanded = profile_source.replace(_INCLUDE_MARKER, shared_body.rstrip('\n'))
    return _GENERATED_HEADER.format(profile=profile) + expanded


def main() -> None:
    for profile, output_name in _PROFILES.items():
        content = build_profile(profile)
        output_path = _AI_ASSETS_DIR / output_name
        output_path.write_text(content, encoding='utf-8')
        print(f'Wrote {output_path.relative_to(_AI_ASSETS_DIR.parent.parent.parent)}')


if __name__ == '__main__':
    main()
