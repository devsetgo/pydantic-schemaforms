from __future__ import annotations

import re

import pytest

from pydantic_schemaforms import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)
from pydantic_schemaforms.ai_instructions import main
from pydantic_schemaforms.inputs.registry import get_input_component_map

# ui_element values that are handled outside the input registry (special-cased
# in the field renderer) rather than backed by a BaseInput subclass.
_STRUCTURAL_UI_ELEMENTS = {'model_list', 'layout'}


def _authoritative_table_tokens(instructions: str) -> set[str]:
    """Extract every backticked token from the "Supported ui_element values" table."""
    section = instructions.split('## Supported ui_element values (authoritative)', 1)[1]
    section = section.split('\n## ', 1)[0]
    tokens = set(re.findall(r'`([a-z0-9_-]+)`', section))
    return tokens - {'ui_element'}


def test_available_instruction_profiles_contains_expected_profiles() -> None:
    profiles = available_instruction_profiles()
    assert profiles == ('claude', 'copilot', 'generic')


def test_get_app_instructions_copilot_contains_core_pattern() -> None:
    text = get_app_instructions('copilot')
    assert 'FormModel' in text
    assert 'render_form_html' in text
    assert 'submit_url' in text


def test_get_app_instructions_supports_aliases() -> None:
    by_alias = get_app_instructions('github-copilot')
    canonical = get_app_instructions('copilot')
    assert by_alias == canonical


def test_get_app_instructions_unknown_profile_raises() -> None:
    with pytest.raises(ValueError, match='Unsupported instruction profile'):
        get_app_instructions('unknown-assistant')


def test_suggested_instruction_filename_is_profile_specific() -> None:
    assert suggested_instruction_filename('copilot') == '.github/copilot-instructions.md'
    assert suggested_instruction_filename('claude') == 'CLAUDE.md'
    assert suggested_instruction_filename('generic') == 'AI_INSTRUCTIONS.md'


def test_cli_prints_to_stdout_by_default(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(['claude'])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == get_app_instructions('claude')


def test_cli_write_flag_uses_suggested_filename(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(['copilot', '--write'])
    assert exit_code == 0
    written = tmp_path / '.github' / 'copilot-instructions.md'
    assert written.read_text(encoding='utf-8') == get_app_instructions('copilot')


def test_cli_output_flag_writes_explicit_path(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / 'nested' / 'INSTRUCTIONS.md'
    exit_code = main(['generic', '--output', str(destination)])
    assert exit_code == 0
    assert destination.read_text(encoding='utf-8') == get_app_instructions('generic')


def test_cli_unknown_profile_exits_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(['unknown-assistant'])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert 'Unsupported instruction profile' in captured.err


def test_cli_output_flag_rejects_path_traversal_outside_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    escape_target = tmp_path.parent / 'escaped.md'
    escape_target.unlink(missing_ok=True)

    with pytest.raises(SystemExit) as exc_info:
        main(['generic', '--output', '../escaped.md'])
    assert exc_info.value.code == 2
    assert not escape_target.exists()


def test_cli_output_flag_rejects_absolute_path_outside_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / 'other-dir'
    outside.mkdir(exist_ok=True)
    escape_target = outside / 'escaped.md'
    escape_target.unlink(missing_ok=True)
    escape_target_arg = str(escape_target)

    with pytest.raises(SystemExit) as exc_info:
        main(['generic', '--output', escape_target_arg])
    assert exc_info.value.code == 2
    assert not escape_target.exists()


def test_cli_output_flag_allows_dotdot_that_stays_inside_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'subdir').mkdir()

    exit_code = main(['generic', '--output', 'subdir/../ALLOWED.md'])
    assert exit_code == 0
    assert (tmp_path / 'ALLOWED.md').read_text(encoding='utf-8') == get_app_instructions('generic')


@pytest.mark.parametrize('profile', ['claude', 'copilot', 'generic'])
def test_authoritative_ui_element_table_matches_registry(profile: str) -> None:
    """Every ui_element/alias claimed in the docs must actually be registered.

    This is the guard the packaged docs promise in docs/ai_instructions.md's
    "Keeping this feature honest" section: the table is checked against the
    real registry, not just written once and left to drift.
    """
    instructions = get_app_instructions(profile)
    documented = _authoritative_table_tokens(instructions)
    registered = set(get_input_component_map()) | _STRUCTURAL_UI_ELEMENTS

    undocumented_but_real = documented - registered
    assert undocumented_but_real == set(), (
        f'{profile} doc claims ui_element values that do not exist: {undocumented_but_real}'
    )


def test_resolve_output_path_rejects_sibling_directory_with_shared_prefix(tmp_path) -> None:
    from pydantic_schemaforms.ai_instructions import _resolve_output_path

    base = tmp_path / 'project'
    base.mkdir()
    sibling = tmp_path / 'project-evil' / 'file.md'
    sibling_arg = str(sibling)

    with pytest.raises(ValueError, match='Refusing to write outside'):
        _resolve_output_path(sibling_arg, base_dir=base)
