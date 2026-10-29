#!/usr/bin/env python3
"""Build the packaged AI-assistant files from the sources under ai/.

Outputs (build artifacts: never edit them directly; edit ai/ and re-run this script or
`make ai-instructions`):

- pydantic_schemaforms/.agents/skills/<name>/: one Agent Skill per ai/skills/<name>/, found by
  `uvx library-skills` in projects that install the package.
- pydantic_schemaforms/assets/ai/{generic,copilot,claude}_app_instructions.md: single-file
  instructions read by get_app_instructions() and the CLI. Each is ai/profiles/<profile>.md with
  its `<!-- INCLUDE: instructions -->` marker replaced by the shared rules, the entry skill with
  its references, and the convert and upgrade skills.

Source markers:

- `<!-- INCLUDE: _shared.md -->`: the rules in ai/_shared.md.
- `<!-- INCLUDE-CODE: path/from/repo/root.py [language] -->`: that file as a fenced code block,
  so examples come from docs_src/ files that tests/test_docs_examples.py runs.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / 'ai'
SKILLS_SOURCE = SOURCE_DIR / 'skills'
SKILLS_OUTPUT = ROOT / 'pydantic_schemaforms' / '.agents' / 'skills'
PROFILES_OUTPUT = ROOT / 'pydantic_schemaforms' / 'assets' / 'ai'

ENTRY_SKILL = 'pydantic-schemaforms'
# Skills whose body is also part of the single-file profiles, after the entry skill.
PROFILE_SKILLS = ('schemaforms-convert', 'schemaforms-upgrade')

_PROFILES = {
    'generic': 'generic_app_instructions.md',
    'copilot': 'copilot_app_instructions.md',
    'claude': 'claude_app_instructions.md',
}

_INSTRUCTIONS_MARKER = '<!-- INCLUDE: instructions -->'
_SHARED_MARKER = '<!-- INCLUDE: _shared.md -->'
_CODE_MARKER = re.compile(r'^<!-- INCLUDE-CODE: (\S+)(?: (\w+))? -->$', re.MULTILINE)
_REFERENCE_LINK = re.compile(r'\[([^\]]+)\]\((references/[\w.-]+\.md)\)')
_LANGUAGES = {'.py': 'python', '.html': 'html', '.md': 'markdown', '.toml': 'toml'}

_GENERATED = (
    '<!-- GENERATED FILE -- do not edit directly. Source: {source}. Regenerate with '
    '`make ai-instructions` (scripts/build_ai_instructions.py). -->\n'
)


def _include_code(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        path = ROOT / match.group(1)
        language = match.group(2) or _LANGUAGES.get(path.suffix, '')
        code = path.read_text(encoding='utf-8').rstrip('\n')
        return f'```{language}\n{code}\n```'

    return _CODE_MARKER.sub(replace, text)


def _expand(text: str, *, shared: bool = True) -> str:
    shared_text = (SOURCE_DIR / '_shared.md').read_text(encoding='utf-8').rstrip('\n')
    text = text.replace(_SHARED_MARKER, shared_text if shared else '')
    return _include_code(text)


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith('---\n'):
        return '', text
    end = text.index('\n---\n', 4) + len('\n---\n')
    return text[:end], text[end:]


def build_skills() -> dict[Path, str]:
    """Every skill's text files, keyed by output path. Other files are copied as is."""
    outputs: dict[Path, str] = {}
    for source in sorted(SKILLS_SOURCE.rglob('*.md')):
        relative = source.relative_to(SKILLS_SOURCE)
        text = _expand(source.read_text(encoding='utf-8'))
        header = _GENERATED.format(source=f'ai/skills/{relative.as_posix()}')
        frontmatter, body = _split_frontmatter(text)
        outputs[SKILLS_OUTPUT / relative] = frontmatter + header + body
    return outputs


def _demote(text: str, levels: int) -> str:
    """Push Markdown headings down, leaving code blocks alone."""
    lines, in_fence = [], False
    for line in text.splitlines():
        if line.startswith('```'):
            in_fence = not in_fence
        elif not in_fence and re.match(r'#{1,5} ', line):
            line = '#' * levels + line
        lines.append(line)
    return '\n'.join(lines)


def _reference_title(skill: str, relative: str) -> str:
    first = (SKILLS_SOURCE / skill / relative).read_text(encoding='utf-8').splitlines()[0]
    return first.lstrip('# ').strip()


def _profile_section(skill: str, relative: str = 'SKILL.md') -> str:
    text = (SKILLS_SOURCE / skill / relative).read_text(encoding='utf-8')
    _, body = _split_frontmatter(_expand(text, shared=False))
    body = _REFERENCE_LINK.sub(
        lambda m: f'{m.group(1)} (see "{_reference_title(skill, m.group(2))}" below)', body
    )
    return _demote(body.strip(), 1)


def build_instructions() -> str:
    parts = [(SOURCE_DIR / '_shared.md').read_text(encoding='utf-8').strip()]
    parts.append(_profile_section(ENTRY_SKILL))
    for reference in sorted((SKILLS_SOURCE / ENTRY_SKILL / 'references').glob('*.md')):
        parts.append(_profile_section(ENTRY_SKILL, f'references/{reference.name}'))
    parts.extend(_profile_section(skill) for skill in PROFILE_SKILLS)
    return '\n\n'.join(parts)


def build_profile(profile: str) -> str:
    source = (SOURCE_DIR / 'profiles' / f'{profile}.md').read_text(encoding='utf-8')
    if _INSTRUCTIONS_MARKER not in source:
        raise ValueError(f'ai/profiles/{profile}.md is missing the {_INSTRUCTIONS_MARKER!r} marker')
    header = _GENERATED.format(source=f'ai/profiles/{profile}.md + ai/_shared.md + ai/skills/')
    return header + source.replace(_INSTRUCTIONS_MARKER, build_instructions())


def main() -> None:
    if SKILLS_OUTPUT.exists():
        shutil.rmtree(SKILLS_OUTPUT)
    for source in sorted(SKILLS_SOURCE.rglob('*')):
        if source.is_file() and source.suffix != '.md':
            target = SKILLS_OUTPUT / source.relative_to(SKILLS_SOURCE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    for path, content in build_skills().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f'Wrote {path.relative_to(ROOT)}')
    for profile, output_name in _PROFILES.items():
        output_path = PROFILES_OUTPUT / output_name
        output_path.write_text(build_profile(profile), encoding='utf-8')
        print(f'Wrote {output_path.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
