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
from .themes import RendererTheme

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


_DEFAULT_THEME = RendererTheme()


def _theme(engine: LayoutEngine) -> RendererTheme:
    theme = getattr(engine._renderer, 'theme', None)  # noqa: SLF001
    return theme if isinstance(theme, RendererTheme) else _DEFAULT_THEME


def _render_error(theme: RendererTheme, message: str | None) -> SafeHTML:
    if not message:
        return SafeHTML('')
    alert_class = f'{theme.alert_class("danger")} nested-model-error'  # NOSONAR
    return html(t'<div class="{alert_class}" role="alert">{message}</div>')


def _render_sub_fields(
    field_name: str,
    field_schema: dict[str, Any],
    schema_def: dict[str, Any],
    value: Any,
    context: 'RenderContext',
    engine: LayoutEngine,
) -> list[str]:
    data = _normalize_value(value)
    child_errors = context.child_errors or {}
    # An optional sub-form (``Address | None``) can be left blank, so the
    # browser must not insist on its fields; validation turns it into None.
    optional = any(o.get('type') == 'null' for o in field_schema.get('anyOf') or [])
    required = set() if optional else set(schema_def.get('required') or [])
    renderer = engine._renderer  # noqa: SLF001 - composite renderers render children through it

    def render_one(key: str, sub_schema: dict[str, Any]) -> str:
        input_name = f'{field_name}.{key}'
        return renderer._render_field(  # noqa: SLF001
            input_name,
            sub_schema,
            data.get(key),
            child_errors.get(key),
            [input_name] if key in required else [],
            context,
            'vertical',
        )

    return engine.render_fields(
        ordered_properties(schema_def),
        render_one,
        context,
        prefix=f'{field_name}.',
        errors=child_errors,
    )


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

    child_errors = context.child_errors or {}
    theme = _theme(engine)
    body = '\n'.join(
        [
            str(_render_error(theme, context.error)),
            *_render_sub_fields(field_name, field_schema, schema_def, value, context, engine),
        ]
    )

    if ui_info.get(IN_GROUP_FLAG):
        return html(
            t'<div class="nested-model-fields" data-field-name="{field_name}">{SafeHTML(body)}</div>'
        )

    title = field_schema.get('title') or field_name.replace('_', ' ').title()
    help_text = ui_info.get('help_text') or field_schema.get('description') or ''

    if ui_info.get('collapsible'):
        has_errors = bool(context.error) or bool(child_errors)
        return theme.render_collapsible_section(
            title=title,
            body_html=body,
            is_open=not bool(ui_info.get('collapsed')) or has_errors,
            field_name=field_name,
        )

    return engine._render_layout_card(title, body, help_text)  # noqa: SLF001
