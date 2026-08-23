"""Renders a model_list field (`FormField(..., input_type='model_list')` on
a `list[ItemModel]`-annotated field, where ItemModel is any ordinary,
unmodified FormModel) as a collapsible, indexed list of sub-forms, one per
item, plus a hidden template item so the list can be emptied and later
re-populated by the client-side add/remove JS (see `model_list.py`'s
`ModelListRenderer.get_model_list_javascript()`).

This is the dedicated rendering module for model_list, registered under the
'model_list' ui_element keyspace via `@LayoutEngine.layout_renderer(...)` at
the bottom of this file (builtin=True, so it survives
`LayoutEngine.reset_layout_renderers()`). `FieldRenderer.render_field`
dispatches any field whose ui_element has a registered renderer here -- see
field_renderer.py's generic dispatch, which still separately serves
DataTableLayout's `layout_handler`-keyed lookup unchanged (a different
keyspace: this one is looked up directly by ui_element, regardless of
whether input_type is 'layout').

Every function here takes the owning `FieldRenderer` instance as its first
argument (`field_renderer`) and calls back through
`field_renderer.<method_name>(...)` for any cross-reference to another one
of these four, rather than calling the sibling free function directly --
this keeps existing test suites that `monkeypatch.setattr(field_renderer,
'<method_name>', ...)` or `patch.object(field_renderer, ...)` working
unchanged, since `FieldRenderer` keeps thin delegator methods of the same
name that forward here.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from pydantic_schemaforms.tstring import SafeHTML, html

from .layout_engine import LayoutEngine

if TYPE_CHECKING:
    from .context import RenderContext
    from .field_renderer import FieldRenderer


def render_model_list_field(
    field_renderer: 'FieldRenderer',
    field_name: str,
    field_schema: dict[str, Any],
    value: Any,
    error: str | None,
    required_fields: list[str] | None,
    ui_info: dict[str, Any],
    context: 'RenderContext',
    all_errors: dict[str, str] | None,
) -> str:
    # The item model is always resolved from the list[ItemModel] type
    # annotation's $ref — there is no separate model_class override.
    # A model_class passed via ui_options can never reach here: Field()
    # serializes ui_options into json_schema_extra (a raw class fails
    # that), and register_field()'s dynamic-field schema builder only
    # forwards ui_-prefixed keys. One resolution path, not two.
    items_ref = field_schema.get('items', {}).get('$ref')
    if not items_ref:
        return html(
            t"<!-- Error: model_list field '{field_name}' must be typed as list[ItemModel] -->"
        )

    model_name = items_ref.split('/')[-1]
    schema_defs = context.schema_defs or {}
    schema_def = schema_defs.get(model_name)
    if not schema_def:
        return html(
            t"<!-- Error: Could not resolve model reference '{items_ref}' "
            t"for field '{field_name}' -->"
        )

    list_values: list[dict[str, Any]] = []
    if value:
        if isinstance(value, list):
            for item in value:
                if hasattr(item, 'model_dump'):
                    list_values.append(item.model_dump())
                elif isinstance(item, dict):
                    list_values.append(item)
        elif hasattr(value, 'model_dump'):
            list_values = [value.model_dump()]
        elif isinstance(value, dict):
            list_values = [value]

    return field_renderer.render_model_list_from_schema(
        field_name=field_name,
        field_schema=field_schema,
        schema_def=schema_def,
        values=list_values,
        error=error,
        ui_info=ui_info,
        required_fields=required_fields or [],
        context=context,
        all_errors=all_errors,
    )


def render_model_list_from_schema(
    field_renderer: 'FieldRenderer',
    field_name: str,
    field_schema: dict[str, Any],
    schema_def: dict[str, Any],
    values: list[dict[str, Any]],
    error: str | None,
    ui_info: dict[str, Any],
    required_fields: list[str],
    context: 'RenderContext',
    all_errors: dict[str, str] | None = None,
) -> str:
    nested_errors = field_renderer.extract_nested_errors_for_field(field_name, all_errors or {})
    items_parts: list[str] = []

    for i, item_data in enumerate(values):
        items_parts.append(
            field_renderer._render_schema_list_item(
                field_name,
                schema_def,
                i,
                item_data,
                context,
                ui_info,
                nested_errors,
            )
        )

    min_items = field_schema.get('minItems', 0)
    if not values and min_items > 0:
        for i in range(min_items):
            items_parts.append(
                field_renderer._render_schema_list_item(
                    field_name,
                    schema_def,
                    i,
                    {},
                    context,
                    ui_info,
                    nested_errors,
                )
            )

    if not values and min_items == 0:
        items_parts.append(
            field_renderer._render_schema_list_item(
                field_name,
                schema_def,
                0,
                {},
                context,
                ui_info,
                nested_errors,
            )
        )

    # Always include a hidden template item so lists can be emptied (minItems=0)
    # and still support adding new items afterwards.
    template_item_html = field_renderer._render_schema_list_item(
        field_name,
        schema_def,
        0,
        {},
        context,
        ui_info,
        nested_errors,
    )
    _template_item_html = SafeHTML(str(template_item_html))
    template_html = html(
        t'<template class="model-list-item-template">{_template_item_html}</template>'
    )

    items_html = template_html + ''.join(items_parts)
    max_items = field_schema.get('maxItems', 10)
    help_text = ui_info.get('help_text') or field_schema.get('description')
    label = field_schema.get('title', field_name.replace('_', ' ').title())
    add_button_label = ui_info.get('add_button_label') or ui_info.get('add_button_text', 'Add Item')
    is_required = field_name in (required_fields or [])

    if field_renderer.theme:
        themed_html = field_renderer.theme.render_model_list_container(
            field_name=field_name,
            label=label,
            is_required=is_required,
            min_items=min_items,
            max_items=max_items,
            items_html=items_html,
            help_text=help_text,
            error=error,
            add_button_label=add_button_label,
        )
        if themed_html:
            return themed_html

    from .themes import RendererTheme

    return RendererTheme().render_model_list_container(
        field_name=field_name,
        label=label,
        is_required=is_required,
        min_items=min_items,
        max_items=max_items,
        items_html=items_html,
        help_text=help_text,
        error=error,
        add_button_label=add_button_label,
    )


def extract_nested_errors_for_field(
    field_renderer: 'FieldRenderer', field_name: str, all_errors: dict[str, Any]
) -> dict[str, str]:
    nested_errors: dict[str, str] = {}
    field_prefix = f'{field_name}['

    for error_path, error_message in (all_errors or {}).items():
        if error_path.startswith(field_prefix):
            nested_part = error_path[len(field_prefix) :]
            if '].' in nested_part:
                simplified_path = nested_part.replace('].', '.')
                nested_errors[simplified_path] = error_message

    return nested_errors


def render_schema_list_item(
    field_renderer: 'FieldRenderer',
    field_name: str,
    schema_def: dict[str, Any],
    index: int,
    item_data: dict[str, Any],
    context: 'RenderContext',
    ui_info: dict[str, Any] | None = None,
    nested_errors: dict[str, str] | None = None,
) -> str:
    ui_info = ui_info or {}
    nested_errors = nested_errors or {}
    collapsible = ui_info.get('collapsible_items', True)
    expanded = ui_info.get('items_expanded', True)
    title_template = ui_info.get('item_title_template', 'Item #{index}')

    title_vars = {'index': index + 1, **item_data}
    try:
        item_title = title_template.format(**title_vars)
    except (KeyError, ValueError):  # fmt: skip  # pragma: no cover - best effort rendering
        item_title = f'Item #{index + 1}'

    safe_field_name = re.sub(r'[^a-zA-Z0-9_-]', '_', field_name)
    collapse_id = f'{safe_field_name}_item_{index}_content'

    item_html = html(t'''
    <div class="model-list-item card border mb-3"
         data-index="{index}"
         data-title-template="{title_template}"
         data-field-name="{field_name}">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">''')

    if collapsible:
        chevron_class = 'down' if expanded else 'right'
        expanded_attr = str(expanded).lower()
        item_html += html(t'''
                <button class="btn btn-link text-decoration-none p-0 text-start"
                        type="button"
                        data-bs-toggle="collapse"
                        data-bs-target="#{collapse_id}"
                        aria-expanded="{expanded_attr}"
                        aria-controls="{collapse_id}">
                    <i class="bi bi-chevron-{chevron_class} me-2"></i>
                    <i class="bi bi-card-list me-2"></i>
                    {item_title}
                </button>''')
    else:
        item_html += html(t"""
                <span>
                    <i class="bi bi-card-list me-2"></i>
                    {item_title}
                </span>""")

    item_html += html(t'''
            </h6>
            <button type="button"
                    class="btn btn-outline-danger btn-sm remove-item-btn"
                    data-index="{index}"
                    data-field-name="{field_name}"
                    title="Remove this item">
                <i class="bi bi-trash"></i>
            </button>
        </div>''')

    if collapsible:
        show_class = 'show' if expanded else ''
        item_html += html(t'''
        <div class="collapse {show_class}" id="{collapse_id}">
            <div class="card-body">''')
    else:
        item_html += """
        <div class="card-body">"""

    item_html += '<div class="row">'
    properties = schema_def.get('properties', {})
    field_count = len([key for key in properties.keys() if not key.startswith('_')])

    if field_count <= 2:
        col_class = 'col-12'
    elif field_count <= 4:
        col_class = 'col-md-6'
    else:
        col_class = 'col-lg-4 col-md-6'

    for field_key, nested_schema in properties.items():
        if field_key.startswith('_'):
            continue

        field_value = item_data.get(field_key, '')
        input_name = f'{field_name}[{index}].{field_key}'
        field_error = nested_errors.get(f'{index}.{field_key}')

        field_col_class = col_class
        if nested_schema.get('input_type') == 'model_list':
            field_col_class = 'col-12'

        nested_field_html = SafeHTML(
            str(
                field_renderer.render_field(
                    input_name,
                    nested_schema,
                    field_value,
                    field_error,
                    [],
                    context,
                    'vertical',
                    nested_errors,
                )
            )
        )
        item_html += html(t'''
            <div class="{field_col_class}">
                {nested_field_html}
            </div>''')

    item_html += '</div>'

    if collapsible:
        item_html += """
            </div>
        </div>"""
    else:
        item_html += """
        </div>"""

    item_html += """
    </div>"""
    return item_html


@LayoutEngine.layout_renderer('model_list')
def render_model_list_layout_field(
    field_name: str,
    field_schema: dict[str, Any],
    value: Any,
    ui_info: dict[str, Any],
    context: 'RenderContext',
    engine: LayoutEngine,
) -> str:
    """The registered entry point: reads the per-field error/required/
    all_errors trio `FieldRenderer.render_field` stashes on `context` right
    before dispatching here (see field_renderer.py's generic dispatch),
    then calls back into the owning FieldRenderer's own
    `_render_model_list_field` -- the exact same method existing tests
    patch directly on a FieldRenderer instance.
    """
    field_renderer = engine._renderer._field_renderer  # noqa: SLF001
    return field_renderer._render_model_list_field(  # noqa: SLF001
        field_name,
        field_schema,
        value,
        context.error,
        list(context.required_fields),
        ui_info,
        context,
        context.all_errors,
    )
