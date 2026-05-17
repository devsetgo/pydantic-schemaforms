"""Deprecated layout wrappers — import from rendering.layout_engine instead."""

from __future__ import annotations

import warnings

from .rendering.layout_engine import (
    AccordionLayout,
    CardLayout,
    GridLayout,
    HorizontalLayout,
    LayoutComposer,
    ModalLayout,
    ResponsiveGridLayout,
    TabLayout,
    VerticalLayout,
)

warnings.warn(
    'pydantic_schemaforms.layouts is deprecated. Import layout primitives directly from '
    'pydantic_schemaforms or pydantic_schemaforms.rendering.layout_engine instead.',
    DeprecationWarning,
    stacklevel=2,
)

LayoutFactory = LayoutComposer
Layout = LayoutComposer

__all__ = [
    'AccordionLayout',
    'CardLayout',
    'GridLayout',
    'HorizontalLayout',
    'Layout',
    'LayoutFactory',
    'LayoutComposer',
    'ModalLayout',
    'ResponsiveGridLayout',
    'TabLayout',
    'VerticalLayout',
]
