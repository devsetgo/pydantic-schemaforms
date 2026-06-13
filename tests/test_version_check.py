"""End-to-end tests for the version_check module-level guard.

These tests verify that the guard actually runs at import time and cannot be
accidentally removed or bypassed by a future refactor.
"""

from __future__ import annotations

import subprocess
import sys


def test_version_check_runs_on_import() -> None:
    """Importing pydantic_schemaforms must trigger the version guard."""
    result = subprocess.run(
        [
            sys.executable,
            '-c',
            'import pydantic_schemaforms; print("imported")',
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert 'imported' in result.stdout


def test_version_check_rejects_old_python() -> None:
    """The guard must raise RuntimeError on Python < 3.14."""
    from collections import namedtuple
    from unittest.mock import MagicMock, patch

    import pytest

    from pydantic_schemaforms.version_check import check_python_version

    VersionInfo = namedtuple('VersionInfo', ['major', 'minor', 'micro', 'releaselevel', 'serial'])
    mock_sys = MagicMock()
    mock_sys.version_info = VersionInfo(3, 13, 0, 'final', 0)
    with patch('pydantic_schemaforms.version_check.sys', mock_sys):
        with pytest.raises(RuntimeError, match='3.14'):
            check_python_version()
