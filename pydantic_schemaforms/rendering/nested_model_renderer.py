"""Renders a nested sub-model field -- ``address: Address`` where ``Address``
is an ordinary FormModel -- as a titled section whose inputs are named
``address.street``, ``address.city``, ...

This is how complex forms are composed: a parent FormModel declares other
FormModels as plain typed fields. No ``ui_element`` is needed; the schema
parser infers ``nested_model`` from the field's ``$ref`` (see
``schema_parser.resolve_ui_element``). The parent's ``layout=`` decides
whether each sub-model renders as a stacked section (default), a tab, a
column, an accordion panel, or a wizard step (see ``LayoutEngine.render_groups``).

Registered under the ``nested_model`` ui_element keyspace, exactly like
model_list, so ``FieldRenderer.render_field`` dispatches here with no
special-casing. Children render back through the owning renderer's
``_render_field``, so a sub-model containing a model_list, a DataTableLayout,
or another sub-model simply recurses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic_schemaforms.tstring import SafeHTML, html

from .layout_engine import IN_GROUP_FLAG, LayoutEngine
from .schema_parser import ordered_properties, resolve_nested_model_ref

if TYPE_CHECKING:
    from .context import RenderContext


def _normalize_value(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, 'model_dump', None)
    if callable(model_dump):
        dumped = model_dump()
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _render_error(message: str | None) -> SafeHTML:
    if not message:
        return SafeHTML('')
    return html(t'<div class="alert alert-danger nested-model-error" role="alert">{message}</div>')


def _wrap_collapsible(
    *, title: str, body: str, collapsed: bool, has_errors: bool, field_name: str
) -> SafeHTML:
    _body = SafeHTML(body)
    if collapsed and not has_errors:
        return html(t'''<details class="nested-model-section" data-field-name="{field_name}">
    <summary class="nested-model-summary">{title}</summary>
    <div class="nested-model-body">{_body}</div>
</details>''')
    return html(t'''<details class="nested-model-section" data-field-name="{field_name}" open>
    <summary class="nested-model-summary">{title}</summary>
    <div class="nested-model-body">{_body}</div>
</details>''')


@LayoutEngine.layout_renderer('nested_model')
def render_nested_model_field(
    field_name: str,
    field_schema: dict[str, Any],
    value: Any,
    ui_info: dict[str, Any],
    context: 'RenderContext',
    engine: LayoutEngine,
) -> str:
    model_name = resolve_nested_model_ref(field_schema)
    schema_def = (context.schema_defs or {}).get(model_name or '')
    if not schema_def:
        return html(t"<!-- Error: could not resolve the sub-model of field '{field_name}' -->")

    data = _normalize_value(value)
    child_errors = context.child_errors or {}
    required = set(schema_def.get('required') or [])
    renderer = engine._renderer  # noqa: SLF001 - composite renderers render children through it

    parts: list[str] = [str(_render_error(context.error))]
    for key, sub_schema in ordered_properties(schema_def):
        input_name = f'{field_name}.{key}'
        parts.append(
            renderer._render_field(  # noqa: SLF001
                input_name,
                sub_schema,
                data.get(key),
                child_errors.get(key),
                [input_name] if key in required else [],
                context,
                'vertical',
            )
        )
    body = '\n'.join(parts)

    if ui_info.get(IN_GROUP_FLAG):
        return html(
            t'<div class="nested-model-fields" data-field-name="{field_name}">{SafeHTML(body)}</div>'
        )

    title = field_schema.get('title') or field_name.replace('_', ' ').title()
    help_text = ui_info.get('help_text') or field_schema.get('description') or ''

    if ui_info.get('collapsible'):
        has_errors = bool(context.error) or bool(child_errors)
        section = _wrap_collapsible(
            title=title,
            body=body,
            collapsed=bool(ui_info.get('collapsed')),
            has_errors=has_errors,
            field_name=field_name,
        )
        return str(section)

    return engine._render_layout_card(title, body, help_text)  # noqa: SLF001
