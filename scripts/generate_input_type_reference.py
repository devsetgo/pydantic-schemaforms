"""Regenerate the "Every input type" section of docs/recipes.md.

Single source of truth is examples/input_type_reference.py -- the same
data backing the FastAPI demo's /input-types page. Run this after editing
that file so docs/recipes.md doesn't drift out of sync:

    python scripts/generate_input_type_reference.py

Everything outside the BEGIN/END GENERATED sentinel markers in
docs/recipes.md is left untouched.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.input_type_reference import INPUT_TYPE_CATEGORIES  # noqa: E402

BEGIN_MARKER = (
    '<!-- BEGIN GENERATED: input-type-reference (scripts/generate_input_type_reference.py) -->'
)
END_MARKER = '<!-- END GENERATED: input-type-reference -->'

RECIPES_PATH = Path(__file__).resolve().parents[1] / 'docs' / 'recipes.md'


def render_markdown() -> str:
    lines: list[str] = [
        BEGIN_MARKER,
        '',
        '## Every input type',
        '',
        'Every registered `ui_element`, generated from `examples/input_type_reference.py`'
        " (the same data backing the FastAPI demo's `/input-types` page). Run"
        ' `python scripts/generate_input_type_reference.py` after changing that file to'
        ' regenerate this section.',
        '',
    ]

    for category_name, entries in INPUT_TYPE_CATEGORIES:
        lines.append(f'### {category_name}')
        lines.append('')
        for entry in entries:
            alias_note = ''
            if entry.aliases:
                alias_list = ', '.join(f'`{a}`' for a in entry.aliases)
                alias_note = f' (also accepts: {alias_list})'
            lines.append(f'**`{entry.ui_element}`**{alias_note} — {entry.description}')
            lines.append('```python')
            lines.append(entry.example)
            lines.append('```')
            lines.append('')

    lines.append(END_MARKER)
    return '\n'.join(lines) + '\n'


def update_recipes() -> None:
    text = RECIPES_PATH.read_text(encoding='utf-8')
    generated = render_markdown()

    pattern = re.compile(
        re.escape(BEGIN_MARKER) + r'.*?' + re.escape(END_MARKER) + r'\n?', re.DOTALL
    )

    if pattern.search(text):
        new_text = pattern.sub(generated, text)
    else:
        # First run: insert right after "## Field types", before "## Optional fields".
        anchor = '\n---\n\n## Optional fields\n'
        if anchor not in text:
            raise RuntimeError('could not find insertion anchor in docs/recipes.md')
        new_text = text.replace(anchor, f'\n---\n\n{generated}\n---\n\n## Optional fields\n')

    RECIPES_PATH.write_text(new_text, encoding='utf-8')


if __name__ == '__main__':
    update_recipes()
    print(f'Updated {RECIPES_PATH}')
