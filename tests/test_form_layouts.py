"""The removed form-orchestration classes fail loudly with upgrade steps.

TabbedLayout/VerticalLayout/HorizontalLayout/ListLayout/SectionDesign/
FormDesign/FormLayoutBase were replaced by nesting FormModels as fields
(see tests/test_nested_model_forms.py). They stay importable so a user's
code fails with FormLayoutRemovedError -- whose message is the upgrade guide
-- rather than an opaque ImportError.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pydantic_schemaforms
from pydantic_schemaforms import FormLayoutRemovedError
from pydantic_schemaforms import form_layouts

REMOVED = [
    'TabbedLayout',
    'VerticalLayout',
    'HorizontalLayout',
    'ListLayout',
    'SectionDesign',
    'FormDesign',
    'FormLayoutBase',
]


@pytest.mark.parametrize('name', REMOVED)
def test_subclassing_a_removed_class_raises_with_upgrade_guide(name: str) -> None:
    removed_cls = getattr(form_layouts, name)
    with pytest.raises(FormLayoutRemovedError) as info:
        type('UserSubclass', (removed_cls,), {})
    message = str(info.value)
    assert f'{name} was removed' in message
    assert 'Upgrading to nested forms' in message
    assert 'layout="tabbed"' in message
    assert info.value.removed_name == name


@pytest.mark.parametrize('name', REMOVED)
def test_instantiating_a_removed_class_raises(name: str) -> None:
    removed_class = getattr(form_layouts, name)
    with pytest.raises(FormLayoutRemovedError, match=f'{name} was removed'):
        removed_class()


def test_removed_error_is_a_type_error() -> None:
    assert issubclass(FormLayoutRemovedError, TypeError)


def test_list_layout_error_points_at_list_fields() -> None:
    with pytest.raises(FormLayoutRemovedError, match=r'list\[Item\]'):
        form_layouts.ListLayout(object)


def test_top_level_names_still_import_and_raise() -> None:
    for name in ['TabbedLayout', 'ListLayout', 'FormLayoutBase', 'SectionDesign', 'FormDesign']:
        removed_class = getattr(pydantic_schemaforms, name)
        with pytest.raises(FormLayoutRemovedError):
            removed_class()


def test_top_level_vertical_and_horizontal_are_the_flex_primitives() -> None:
    from pydantic_schemaforms.rendering import layout_engine

    assert pydantic_schemaforms.VerticalLayout is layout_engine.VerticalLayout
    assert pydantic_schemaforms.HorizontalLayout is layout_engine.HorizontalLayout
    html = pydantic_schemaforms.VerticalLayout(content=['<p>a</p>']).render()
    assert '<p>a</p>' in html


def test_deprecated_layouts_shim_module_is_gone() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('pydantic_schemaforms.layouts')


def test_library_never_imports_the_examples_package() -> None:
    package_root = Path(pydantic_schemaforms.__file__).parent
    offenders = [
        str(path.relative_to(package_root))
        for path in package_root.rglob('*.py')
        if 'from examples' in path.read_text() or 'import examples' in path.read_text()
    ]
    assert offenders == []
