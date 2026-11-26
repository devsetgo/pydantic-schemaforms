"""Content-Security-Policy compatibility of rendered output.

A strict ``script-src`` never runs inline event-handler attributes, nonce or not,
so the library's markup must wire its behavior up from its own scripts.
"""

from __future__ import annotations

import re

import pytest

from examples.shared_models import LayoutDemonstrationForm, WidgetGalleryForm
from pydantic_schemaforms import ModalLayout
from pydantic_schemaforms.rendering.layout_engine import LAYOUTS

FRAMEWORKS = ('bootstrap', 'material', 'none')
_HANDLER_ATTR = re.compile(r'<[a-zA-Z][^>]*\son[a-z]+\s*=', re.IGNORECASE)


def _handlers(markup: str) -> list[str]:
    return [match.group(0)[:120] for match in _HANDLER_ATTR.finditer(markup)]


@pytest.mark.parametrize('framework', FRAMEWORKS)
@pytest.mark.parametrize('layout', sorted(LAYOUTS))
def test_layouts_render_no_inline_event_handlers(framework: str, layout: str) -> None:
    markup = LayoutDemonstrationForm.render_form(
        framework=framework, submit_url='/x', layout=layout
    )
    assert _handlers(markup) == []


@pytest.mark.parametrize('framework', FRAMEWORKS)
def test_every_widget_renders_no_inline_event_handlers(framework: str) -> None:
    markup = WidgetGalleryForm.render_form(
        framework=framework, submit_url='/x', include_framework_assets=True
    )
    assert _handlers(markup) == []


def test_modal_layout_renders_no_inline_event_handlers() -> None:
    assert _handlers(ModalLayout('m1', 'Title', 'Body').render()) == []
