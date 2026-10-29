"""The Agent Skills shipped in pydantic_schemaforms/.agents/skills/.

They're built from ai/ by scripts/build_ai_instructions.py and installed into
app projects by `uvx library-skills`, which reads each SKILL.md's frontmatter
the way these tests do. The checks mirror library-skills' own validation and
the Agent Skills spec (https://agentskills.io/specification).
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

from pydantic_schemaforms.inputs.registry import get_input_component_map

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / 'pydantic_schemaforms' / '.agents' / 'skills'
EXPECTED = {
    'pydantic-schemaforms',
    'schemaforms-create',
    'schemaforms-convert',
    'schemaforms-upgrade',
    'schemaforms-document',
}
SKILL_FILES = sorted(SKILLS.rglob('*.md'))
_NAME = re.compile(r'^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$')


def _load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frontmatter(skill: str) -> dict:
    text = (SKILLS / skill / 'SKILL.md').read_text(encoding='utf-8')
    assert text.startswith('---\n'), skill
    return yaml.safe_load(text[4 : text.index('\n---\n', 4)])


def test_every_skill_is_shipped() -> None:
    assert {path.name for path in SKILLS.iterdir() if path.is_dir()} == EXPECTED


@pytest.mark.parametrize('skill', sorted(EXPECTED))
def test_frontmatter_is_valid(skill: str) -> None:
    meta = _frontmatter(skill)
    assert meta['name'] == skill
    assert _NAME.fullmatch(skill) and '--' not in skill
    assert 1 <= len(meta['description']) <= 1024


def test_descriptions_are_distinct() -> None:
    descriptions = [_frontmatter(skill)['description'] for skill in EXPECTED]
    assert len(set(descriptions)) == len(descriptions)


@pytest.mark.parametrize('skill', sorted(EXPECTED))
def test_skill_md_stays_short(skill: str) -> None:
    # The spec loads the whole SKILL.md once a skill is chosen; detail goes in references/.
    lines = (SKILLS / skill / 'SKILL.md').read_text(encoding='utf-8').count('\n')
    assert lines < 500, f'{skill}/SKILL.md has {lines} lines; move detail into references/'


@pytest.mark.parametrize('path', SKILL_FILES, ids=lambda p: str(p.relative_to(SKILLS)))
def test_relative_links_resolve(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)#\s]+)\)', text):
        if '://' in target:
            continue
        assert (path.parent / target).is_file(), f'{path.name} links to missing {target}'


@pytest.mark.parametrize('path', SKILL_FILES, ids=lambda p: str(p.relative_to(SKILLS)))
def test_skill_follows_the_app_rules(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    assert '<!-- INCLUDE' not in text, 'unexpanded include marker'
    # Imports only from the top-level package (prose may name submodules to forbid them).
    for line in re.findall(r'^\s*(?:from|import) pydantic_schemaforms\S*', text, re.MULTILINE):
        assert line.split()[1] == 'pydantic_schemaforms', line
    assert not re.search(r"""\bf(['"])<""", text), 'HTML built with an f-string; use html(t"...")'


def test_generated_skills_match_their_sources() -> None:
    build = _load_script(ROOT / 'scripts' / 'build_ai_instructions.py', 'build_ai_instructions')
    expected = build.build_skills()
    for source in build.SKILLS_SOURCE.rglob('*'):
        if source.is_file() and source.suffix != '.md':
            expected[build.SKILLS_OUTPUT / source.relative_to(build.SKILLS_SOURCE)] = (
                source.read_text(encoding='utf-8')
            )
    shipped = {
        path for path in SKILLS.rglob('*') if path.is_file() and '__pycache__' not in path.parts
    }
    assert shipped == set(expected), 'run `make ai-instructions` and commit the result'
    for path, content in expected.items():
        assert path.read_text(encoding='utf-8') == content, (
            f'{path.relative_to(ROOT)} is out of date: run `make ai-instructions`'
        )


def test_input_table_names_only_registered_inputs() -> None:
    text = (SKILLS / 'pydantic-schemaforms' / 'references' / 'inputs.md').read_text(
        encoding='utf-8'
    )
    section = text.split('## Supported ui_element values (authoritative)', 1)[1].split('\n## ', 1)[
        0
    ]
    documented = set(re.findall(r'`([a-z0-9_-]+)`', section)) - {'ui_element'}
    registered = set(get_input_component_map()) | {'model_list', 'nested_model', 'layout'}
    assert documented <= registered, documented - registered


def test_list_forms_script_describes_the_forms(capsys: pytest.CaptureFixture[str]) -> None:
    script = _load_script(
        SKILLS / 'schemaforms-document' / 'scripts' / 'list_forms.py', 'list_forms'
    )
    models = ROOT / 'docs_src' / 'recipes' / 'login_registration' / 'models.py'
    assert script.main([str(models)]) == 0
    out = capsys.readouterr().out
    assert '## RegistrationForm' in out
    assert (
        '| `username` | Username | `str` | (from type) | yes |  | min_length 3, max_length 30'
        in out
    )
    assert '`passwords_match`' in out
