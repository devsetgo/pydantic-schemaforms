"""Guards the generated "Every input type" section of docs/reference/inputs.md against drift.

That section is produced by scripts/generate_input_type_reference.py from
examples/input_type_reference.py (also the source for the FastAPI demo's
/input-types page). If someone edits either source without re-running the
generator, docs/reference/inputs.md silently goes stale -- this test catches that.
"""

from __future__ import annotations

import re

from scripts.generate_input_type_reference import (
    BEGIN_MARKER,
    END_MARKER,
    REFERENCE_PATH,
    render_markdown,
)


def test_input_types_reference_matches_generator():
    text = REFERENCE_PATH.read_text(encoding='utf-8')
    pattern = re.compile(
        re.escape(BEGIN_MARKER) + r'.*?' + re.escape(END_MARKER) + r'\n?', re.DOTALL
    )
    match = pattern.search(text)
    assert match, (
        'docs/reference/inputs.md is missing the generated input-type-reference section -- '
        'run `python scripts/generate_input_type_reference.py`'
    )

    assert match.group(0) == render_markdown(), (
        'docs/reference/inputs.md\'s "Every input type" section is out of sync with '
        'examples/input_type_reference.py -- run '
        '`python scripts/generate_input_type_reference.py` and commit the result'
    )
