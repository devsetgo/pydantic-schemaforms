"""Text in a form that isn't a field: content blocks and consent fields.

A content block submits nothing and is left out of validation and the returned
data (see `Field(ui_element='content')`). A consent field pairs the same text
with a required checkbox, which renders and validates as any other checkbox.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from pydantic_schemaforms.rendering.layout_engine import LayoutEngine
from pydantic_schemaforms.tstring import SafeHTML, html

if TYPE_CHECKING:
    from pydantic_schemaforms.rendering.context import RenderContext


def _body(ui_info: dict[str, Any]) -> SafeHTML:
    # Field() stores SafeHTML under its own key because JSON Schema generation
    # turns it back into a plain str, which would then be escaped.
    if 'content_html' in ui_info:
        return SafeHTML(ui_info['content_html'])
    text = ui_info.get('content', '')
    return html(t'<p>{text}</p>')


def _block(
    block_id: str, ui_info: dict[str, Any], engine: LayoutEngine, heading: str | None = None
) -> SafeHTML:
    options = ui_info.get('options')
    scrollable = bool(isinstance(options, dict) and options.get('scrollable'))
    field_renderer = engine._renderer._field_renderer  # noqa: SLF001
    theme = field_renderer.theme
    css_class = (
        theme.content_block_class(scrollable) if theme else ''
    ) or field_renderer.class_defaults.content_block_class(scrollable)
    _heading = html(t'<h3 class="h5">{heading}</h3>') if heading else SafeHTML('')
    _content = _body(ui_info)
    if scrollable:
        # tabindex lets keyboard users scroll it.
        return html(
            t'<div id="{block_id}" class="{css_class}" tabindex="0" '
            t'style="max-height: 16rem; overflow-y: auto">{_heading}{_content}</div>'
        )
    return html(t'<div id="{block_id}" class="{css_class}">{_heading}{_content}</div>')


@LayoutEngine.layout_renderer('content')
def render_content_field(
    field_name: str,
    field_schema: dict[str, Any],
    value: Any,
    ui_info: dict[str, Any],
    context: 'RenderContext',
    engine: LayoutEngine,
) -> str:
    # Pydantic fills in a title from the field name, which isn't a heading.
    title = ui_info.get('title')
    own_name = re.sub(r'\[\d+\]$', '', field_name).rsplit('.', 1)[-1]
    heading = None if title == own_name.replace('_', ' ').title() else title
    return _block(f'{field_name}-content', ui_info, engine, heading)


@LayoutEngine.layout_renderer('consent')
def render_consent_field(
    field_name: str,
    field_schema: dict[str, Any],
    value: Any,
    ui_info: dict[str, Any],
    context: 'RenderContext',
    engine: LayoutEngine,
) -> str:
    block_id = f'{field_name}-content'
    options = {k: v for k, v in (ui_info.get('options') or {}).items() if k != 'scrollable'}
    checkbox_schema = {
        **field_schema,
        'ui_element': 'checkbox',
        'ui_options': {**options, 'aria-describedby': block_id},
    }
    checkbox_schema.pop('ui', None)
    checkbox = SafeHTML(
        engine._renderer._field_renderer.render_field(  # noqa: SLF001
            field_name,
            checkbox_schema,
            value,
            context.error,
            list(context.required_fields),
            context,
        )
    )
    _block_html = _block(block_id, ui_info, engine)
    return html(t'<div class="sf-consent">{_block_html}{checkbox}</div>')
