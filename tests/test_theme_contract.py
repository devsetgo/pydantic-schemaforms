"""Guard rails for the one-rendering-path design (#265).

Framework-specific markup belongs in the themes (`rendering/themes.py`) and the
field shells (`rendering/field_shell.py`). Inputs and renderers must not branch
on the framework string; if a widget needs different markup per framework, it
gets a theme hook instead.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / 'pydantic_schemaforms'

# Where framework-specific decisions are supposed to live.
_THEME_MODULES = {
    'rendering/themes.py',
    'rendering/field_shell.py',
    'rendering/form_style.py',
    'rendering/frameworks.py',
    'assets/runtime.py',
    'icon_mapping.py',
}

# Never add an entry: a widget or renderer that needs framework-specific
# markup gets a theme hook instead.
_ALLOWED: dict[str, int] = {}


def _is_framework_name(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return node.id in {'framework', 'fw'}
    if isinstance(node, ast.Attribute):
        return node.attr == 'framework'
    return False


def _framework_comparisons(tree: ast.AST) -> list[int]:
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        if any(_is_framework_name(op) for op in operands) and any(
            isinstance(op, ast.Constant)
            and isinstance(op.value, str)
            or isinstance(op, (ast.Set, ast.Tuple, ast.List))
            for op in operands
        ):
            lines.append(node.lineno)
    return lines


def test_inputs_and_renderers_do_not_branch_on_the_framework() -> None:
    found: dict[str, list[int]] = {}
    for path in PACKAGE.rglob('*.py'):
        relative = path.relative_to(PACKAGE).as_posix()
        if relative in _THEME_MODULES:
            continue
        lines = _framework_comparisons(ast.parse(path.read_text(encoding='utf-8')))
        if lines:
            found[relative] = lines

    unexpected = {
        name: lines for name, lines in found.items() if len(lines) > _ALLOWED.get(name, 0)
    }
    assert not unexpected, (
        'Framework-string branches outside the theme modules (use a theme hook instead): '
        f'{unexpected}'
    )
    stale = {name: count for name, count in _ALLOWED.items() if len(found.get(name, [])) < count}
    assert not stale, f'Lower these allowances in _ALLOWED, the branches are gone: {stale}'


def test_widget_css_takes_colors_from_tokens() -> None:
    hard_coded = re.compile(
        r'(?:color|background|border|box-shadow)[^;\n]*?(?<!, )#[0-9a-fA-F]{3,8}\b'
    )
    found = {
        path.name: hard_coded.findall(path.read_text(encoding='utf-8'))
        for path in (PACKAGE / 'inputs').glob('*.py')
    }
    assert not {name: hits for name, hits in found.items() if hits}


def test_md3_css_has_no_important_and_no_hex() -> None:
    css = (PACKAGE / 'assets' / 'material' / 'md3.css').read_text(encoding='utf-8')
    assert '!important' not in css
    assert not re.findall(r'#[0-9a-fA-F]{3,8}\b', css)


def test_material_output_has_no_bootstrap_classes() -> None:
    from examples.shared_models import WidgetGalleryForm
    from pydantic_schemaforms import render_form_html

    rendered = render_form_html(WidgetGalleryForm, framework='material', submit_url='/x')
    markup = re.sub(r'<(style|script)\b.*?</\1>', '', rendered, flags=re.S)
    classes = ' '.join(re.findall(r'class="([^"]*)"', markup)).split()
    bootstrap = {'form-control', 'form-select', 'form-label', 'form-text', 'btn', 'card', 'alert'}
    assert not bootstrap & set(classes)
    assert not [name for name in classes if name.startswith('bi-')]


def test_every_registered_input_alias_gets_its_canonical_material_kind() -> None:
    from pydantic_schemaforms.inputs.registry import get_input_component_map
    from pydantic_schemaforms.rendering.field_shell import material_field_kind

    wrong = {
        name: (material_field_kind(name), cls.ui_element)
        for name, cls in get_input_component_map().items()
        if material_field_kind(name) != material_field_kind(cls.ui_element)
    }
    assert not wrong
