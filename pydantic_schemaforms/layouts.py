# """Deprecated layout wrappers.

# The canonical layout primitives now live in ``pydantic_schemaforms.rendering.layout_engine``.
# """

# from __future__ import annotations

# import warnings

# from .layout_base import BaseLayout
# from .rendering.layout_engine import (
#     AccordionLayout,
#     CardLayout,
#     GridLayout,
#     HorizontalLayout,
#     LayoutComposer,
#     ModalLayout,
#     ResponsiveGridLayout,
#     TabLayout,
#     VerticalLayout,
# )

# warnings.warn(
#     "pydantic_schemaforms.layouts is deprecated. Import layout primitives from "
#     "pydantic_schemaforms.rendering.layout_engine instead.",
#     DeprecationWarning,
#     stacklevel=2,
# )

# LayoutFactory = LayoutComposer
# Layout = LayoutComposer

# __all__ = [
#     "BaseLayout",
#     "AccordionLayout",
#     "CardLayout",
#     "GridLayout",
#     "HorizontalLayout",
#     "Layout",
#     "LayoutFactory",
#     "LayoutComposer",
#     "ModalLayout",
#     "ResponsiveGridLayout",
#     "TabLayout",
#     "VerticalLayout",
# ]
