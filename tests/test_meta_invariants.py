"""Meta-guard: verifies that tests/test_invariants.py has not been gutted.

╔══════════════════════════════════════════════════════════════════════════════╗
║  PROTECTED FILE — DO NOT REMOVE, WEAKEN, OR SKIP THESE TESTS.               ║
║                                                                              ║
║  This file and tests/test_invariants.py form a mutual guard:                 ║
║    • Deleting test_invariants.py  → test_invariant_tests_not_removed fails.  ║
║    • Deleting test_meta_invariants.py → test_meta_guard_present fails.       ║
║    • Gutting either file           → the other file detects the absence.     ║
║                                                                              ║
║  See CLAUDE.md §"T-string rule" for the full rationale.                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from pathlib import Path

_TESTS_DIR = Path(__file__).parent
_INVARIANTS = _TESTS_DIR / 'test_invariants.py'


def test_invariant_tests_not_removed() -> None:
    """tests/test_invariants.py must still exist and contain its key assertions."""
    assert _INVARIANTS.exists(), (
        'tests/test_invariants.py has been deleted.\n'
        'Restore it from version control — it enforces the t-string XSS safety invariant.'
    )
    text = _INVARIANTS.read_text(encoding='utf-8')
    required = [
        'test_no_string_template_in_source',
        'test_tstring_ruff_config_present',
        'test_invariant_self_integrity',
        'test_meta_guard_present',
    ]
    missing = [name for name in required if name not in text]
    assert not missing, (
        'Key functions have been removed from tests/test_invariants.py:\n'
        + '\n'.join(f'  {n}' for n in missing)
        + '\nRestore them — they enforce the t-string XSS safety invariant.'
    )
