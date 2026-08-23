"""Shared base for FormModel subclasses that ARE a composite control's own
structure (table columns, wizard steps, ...) rather than one instance's
inputs -- meant to be embedded as a single *layout field* on a plain
FormModel (``input_type='layout', layout_handler=...``) rather than
rendered through ``FormModel.render_form()``'s single-instance
data/errors/submit_url shape, which doesn't apply to them.

``DataTableLayout`` (see ``datatable_layout.py``) is the reference example.
See ``docs/plugin_hooks.md`` for the ``layout_handler``/
``LayoutEngine.register_layout_renderer`` mechanism this relies on, and
``LayoutEngine.layout_renderer`` for the registration decorator a composite's
renderer module uses to hook itself up at import time.

Not every composite field type needs this base -- it's specifically for the
"a class's own fields define the composite's structure" shape. model_list,
for example, doesn't use it: a model_list field's item type is just an
ordinary, unmodified FormModel referenced via a ``list[ItemModel]``
annotation, not a class that needs its own ``render_form()`` disabled.
"""

from __future__ import annotations

from typing import Any

from .schema_form import FormModel


class CompositeLayoutModel(FormModel):
    """Base for a FormModel subclass meant to be embedded as one layout
    field, never rendered on its own. Subclasses are expected to provide
    their own ``as_layout_value()`` classmethod bundling whatever their
    registered ``LayoutRenderer`` needs to render it.
    """

    @classmethod
    def render_form(cls, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError(
            f'{cls.__name__}.render_form() is not supported -- {cls.__name__} is a composite '
            "layout field meant to be embedded on a plain FormModel (input_type='layout', "
            f'layout_handler=...), not rendered on its own. See {cls.__name__}.as_layout_value().'
        )
