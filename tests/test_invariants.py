"""Architectural invariant tests for pydantic-schemaforms.

╔══════════════════════════════════════════════════════════════════════════════╗
║  PROTECTED FILE — DO NOT REMOVE, WEAKEN, OR SKIP THESE TESTS.               ║
║                                                                              ║
║  These tests enforce structural constraints that cannot be caught by the     ║
║  type checker alone. Removing them would silently allow regressions that     ║
║  re-introduce XSS vulnerabilities or break the t-string architecture.        ║
║                                                                              ║
║  If you believe a test is wrong, discuss it with the project owner before    ║
║  changing it. See CLAUDE.md §"T-string rule" for the full rationale.         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Invariants enforced here:
  1. No source file in pydantic_schemaforms/ may import string.Template.
  2. The ruff banned-api config in pyproject.toml must still name string.Template.
  3. This file itself must not be gutted (checked by tests/test_meta_invariants.py).
"""

from __future__ import annotations

from pathlib import Path


_SRC_ROOT = Path(__file__).parent.parent / 'pydantic_schemaforms'
_PYPROJECT = Path(__file__).parent.parent / 'pyproject.toml'


# ---------------------------------------------------------------------------
# Invariant 1: no string.Template usage in library source
# ---------------------------------------------------------------------------

_BANNED_PATTERNS = [
    'from string import Template',
    'string.Template(',
    'string.Template (',
]

# Files that are allowed to mention the banned strings in non-executable
# contexts (e.g., documentation strings or the banned-api config itself).
_ALLOWLIST: set[str] = {
    'version_check.py',  # mentions string.templatelib (different module, allowed)
}


def _find_violations() -> list[str]:
    violations: list[str] = []
    for path in sorted(_SRC_ROOT.rglob('*.py')):
        if path.name in _ALLOWLIST:
            continue
        text = path.read_text(encoding='utf-8')
        for pattern in _BANNED_PATTERNS:
            if pattern in text:
                rel = path.relative_to(_SRC_ROOT.parent)
                violations.append(f'{rel}: found "{pattern}"')
    return violations


def test_no_string_template_in_source() -> None:
    """string.Template must not appear in any library source file.

    All HTML generation uses t-strings with the html() processor from
    pydantic_schemaforms.tstring.  string.Template offers no XSS
    protection and is banned by the ruff TID251 rule as well.
    """
    violations = _find_violations()
    assert not violations, (
        'string.Template found in source — use t-strings with html() instead:\n'
        + '\n'.join(f'  {v}' for v in violations)
    )


# ---------------------------------------------------------------------------
# Invariant 2: ruff banned-api config must still reference string.Template
# ---------------------------------------------------------------------------


def test_tstring_ruff_config_present() -> None:
    """pyproject.toml must still have string.Template in the banned-api table.

    If this entry is removed, the lint-time guard disappears and future
    contributors can reintroduce string.Template without any warning.
    """
    pyproject_text = _PYPROJECT.read_text(encoding='utf-8')
    assert 'string.Template' in pyproject_text, (
        'pyproject.toml no longer bans string.Template via TID251.\n'
        'Restore the [tool.ruff.lint.flake8-tidy-imports.banned-api] entry.'
    )
    assert 'TID' in pyproject_text, (
        'TID rule family has been removed from ruff select in pyproject.toml.\n'
        'Restore "TID" to [tool.ruff.lint] select so the banned-api rule is active.'
    )


# ---------------------------------------------------------------------------
# Invariant 3: self-integrity — key test functions must still exist here
# ---------------------------------------------------------------------------


def test_invariant_self_integrity() -> None:
    """This file must still contain the core invariant test functions.

    Together with tests/test_meta_invariants.py this creates a mutual
    guard: deleting or gutting either file causes the other to fail.
    """
    own_text = Path(__file__).read_text(encoding='utf-8')
    required = [
        'test_no_string_template_in_source',
        'test_tstring_ruff_config_present',
        'test_meta_guard_present',
    ]
    missing = [name for name in required if name not in own_text]
    assert not missing, (
        f'Invariant test functions have been removed from {__file__}:\n'
        + '\n'.join(f'  {n}' for n in missing)
    )


def test_meta_guard_present() -> None:
    """tests/test_meta_invariants.py must exist and reference this file."""
    meta = Path(__file__).parent / 'test_meta_invariants.py'
    assert meta.exists(), (
        'tests/test_meta_invariants.py is missing — the mutual invariant guard is broken.\n'
        'Restore that file from version control.'
    )
    meta_text = meta.read_text(encoding='utf-8')
    assert 'test_invariant_self_integrity' in meta_text, (
        'tests/test_meta_invariants.py no longer checks test_invariant_self_integrity.\n'
        'The mutual guard has been weakened — restore the check.'
    )
