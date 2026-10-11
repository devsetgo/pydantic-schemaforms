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

Every one of the four moved methods takes the owning `FieldRenderer`
instance as its first argument (`field_renderer`) and calls back through
`field_renderer.<method_name>(...)` for any cross-reference to another one
of the four, rather than calling the sibling free function directly --
this keeps existing test suites that `monkeypatch.setattr(field_renderer,
'<method_name>', ...)` or `patch.object(field_renderer, ...)` working
unchanged, since `FieldRenderer` keeps thin delegator methods of the same
name that forward here.

Errors arrive as a nested error tree (see `pydantic_schemaforms.error_tree`):
the list field's own child errors are a dict keyed by item index, and each
item's errors are a dict keyed by that item's field names.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic_schemaforms.tstring import SafeHTML, html

from .layout_engine import LayoutEngine
from .schema_parser import (
    GROUP_ELEMENTS,
    ordered_properties,
    resolve_list_item_ref,
    resolve_ui_element,
)

if TYPE_CHECKING:
    from .context import RenderContext
    from .field_renderer import FieldRenderer


@runtime_checkable
class _ModelDumpable(Protocol):
    """Anything with a `model_dump()` method -- not narrowed to
    pydantic's `BaseModel` specifically, since `_normalize_model_list_value`
    deliberately accepts any model-dump-able object (see its docstring).
    A `hasattr(item, 'model_dump')` check does the same thing at runtime but
    pyright can't narrow through it; isinstance against a runtime_checkable
    Protocol gets the same duck typing with real narrowing."""

    def model_dump(self) -> dict[str, Any]: ...


def _normalize_model_list_value(value: Any) -> list[dict[str, Any]]:
    """Coerce whatever a model_list field's raw value is (a list of model
    instances/dicts, a single instance/dict, or empty) into a plain list of
    dicts for rendering. Anything that's neither model-dump-able nor a dict
    is silently skipped -- this mirrors submitted/prefilled data shapes, not
    arbitrary user input, so there's nothing meaningful to surface as an
    error for an unrecognized item shape."""
    if not value:
        return []
    if isinstance(value, list):
        return [
            item.model_dump() if isinstance(item, _ModelDumpable) else item
            for item in value
            if isinstance(item, (_ModelDumpable, dict))
        ]
    if isinstance(value, _ModelDumpable):
        return [value.model_dump()]
    if isinstance(value, dict):
        return [value]
    return []


def render_model_list_field(
    field_renderer: 'FieldRenderer',
    field_name: str,
    field_schema: dict[str, Any],
    value: Any,
    error: str | None,
    required_fields: list[str] | None,
    ui_info: dict[str, Any],
    context: 'RenderContext',
    list_errors: dict[Any, Any] | None,
) -> str:
    # The item model is always resolved from the list[ItemModel] type
    # annotation's $ref -- there is no separate model_class override.
    model_name = resolve_list_item_ref(field_schema)
    if not model_name:
        return html(
            t"<!-- Error: model_list field '{field_name}' must be typed as list[ItemModel] -->"
        )

    schema_defs = context.schema_defs or {}
    schema_def = schema_defs.get(model_name)
    if not schema_def:
        return html(
            t"<!-- Error: Could not resolve model reference '{model_name}' "
            t"for field '{field_name}' -->"
        )

    list_values = _normalize_model_list_value(value)

    return field_renderer.render_model_list_from_schema(
        field_name=field_name,
        field_schema=field_schema,
        schema_def=schema_def,
        values=list_values,
        error=error,
        ui_info=ui_info,
        required_fields=required_fields or [],
        context=context,
        list_errors=list_errors,
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
    list_errors: dict[Any, Any] | None = None,
) -> str:
    list_errors = list_errors or {}
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
                item_errors(list_errors, i),
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
                    item_errors(list_errors, i),
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
                item_errors(list_errors, 0),
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
        {},
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


def item_errors(list_errors: dict[Any, Any], index: int) -> dict[Any, Any]:
    """One item's error sub-tree. Index keys are ints from Pydantic, or
    strings when the tree round-tripped through JSON."""
    node = list_errors.get(index, list_errors.get(str(index)))
    return node if isinstance(node, dict) else {}


def _resolve_item_title(title_template: str, index: int, item_data: dict[str, Any]) -> str:
    title_vars = {'index': index + 1, **item_data}
    try:
        return title_template.format(**title_vars)
    except (KeyError, ValueError):  # fmt: skip  # pragma: no cover - best effort rendering
        return f'Item #{index + 1}'


def _render_item_toggle(
    *,
    collapsible: bool,
    expanded: bool,
    # NOSONAR comments below: collapse_id/item_title are read via {expr}
    # interpolation in the t-strings below -- see the note further down in
    # this function on false-positive "unused variable" warnings.
    collapse_id: str,  # NOSONAR
    item_title: str,  # NOSONAR
) -> SafeHTML:
    if not collapsible:
        return html(t"""
                <span>
                    <i class="bi bi-card-list me-2"></i>
                    {item_title}
                </span>""")

    # NOSONAR comments below: each variable is read via {expr} interpolation
    # in the t-string return statement -- Sonar's Python analyzer doesn't
    # parse PEP 750 t-strings yet, so it can't see the reference and flags a
    # false-positive "unused local variable".
    chevron_class = 'down' if expanded else 'right'  # NOSONAR
    expanded_attr = str(expanded).lower()  # NOSONAR
    return html(t'''
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


def _column_class_for_field_count(field_count: int) -> str:
    if field_count <= 2:
        return 'col-12'
    if field_count <= 4:
        return 'col-md-6'
    return 'col-lg-4 col-md-6'


def _render_item_field_cell(
    field_renderer: 'FieldRenderer',
    *,
    field_name: str,
    index: int,
    field_key: str,
    nested_schema: dict[str, Any],
    item_data: dict[str, Any],
    nested_errors: dict[Any, Any],
    context: 'RenderContext',
    col_class: str,
) -> SafeHTML:
    field_value = item_data.get(field_key, '')
    input_name = f'{field_name}[{index}].{field_key}'
    field_error = nested_errors.get(field_key)

    # NOSONAR comments below: field_col_class/nested_field_html are read via
    # {expr} interpolation further down -- see the note in
    # _render_item_toggle above.
    field_col_class = (  # NOSONAR
        'col-12' if resolve_ui_element(nested_schema) in GROUP_ELEMENTS else col_class
    )

    nested_field_html = SafeHTML(  # NOSONAR
        str(
            field_renderer.render_field(
                input_name,
                nested_schema,
                field_value,
                field_error,
                [],
                context,
                'vertical',
            )
        )
    )
    return html(t'''
            <div class="{field_col_class}">
                {nested_field_html}
            </div>''')


def _render_item_body_wrapper(
    *,
    collapsible: bool,
    expanded: bool,
    # NOSONAR comment below: collapse_id is read via {collapse_id}
    # interpolation in the t-string further down -- see the note in
    # _render_item_toggle above.
    collapse_id: str,  # NOSONAR
    fields_html: str,
) -> str:
    if collapsible:
        show_class = 'show' if expanded else ''  # NOSONAR
        opening = html(t'''
        <div class="collapse {show_class}" id="{collapse_id}">
            <div class="card-body">''')
        closing = """
            </div>
        </div>"""
    else:
        opening = """
        <div class="card-body">"""
        closing = """
        </div>"""
    return f'{opening}<div class="row">{fields_html}</div>{closing}'


def render_schema_list_item(
    field_renderer: 'FieldRenderer',
    field_name: str,
    schema_def: dict[str, Any],
    index: int,
    item_data: dict[str, Any],
    context: 'RenderContext',
    ui_info: dict[str, Any] | None = None,
    nested_errors: dict[Any, Any] | None = None,
) -> str:
    ui_info = ui_info or {}
    nested_errors = nested_errors or {}
    collapsible = ui_info.get('collapsible_items', True)
    expanded = ui_info.get('items_expanded', True)
    title_template = ui_info.get('item_title_template', 'Item #{index}')
    item_title = _resolve_item_title(title_template, index, item_data)

    safe_field_name = re.sub(r'[^a-zA-Z0-9_-]', '_', field_name)
    collapse_id = f'{safe_field_name}_item_{index}_content'

    item_html = html(t'''
    <div class="model-list-item card border mb-3"
         data-index="{index}"
         data-title-template="{title_template}"
         data-field-name="{field_name}">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">''')
    item_html += _render_item_toggle(
        collapsible=collapsible, expanded=expanded, collapse_id=collapse_id, item_title=item_title
    )
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

    properties = dict(ordered_properties(schema_def))
    field_count = len([key for key in properties.keys() if not key.startswith('_')])
    col_class = _column_class_for_field_count(field_count)

    fields_html = ''.join(
        str(
            _render_item_field_cell(
                field_renderer,
                field_name=field_name,
                index=index,
                field_key=field_key,
                nested_schema=nested_schema,
                item_data=item_data,
                nested_errors=nested_errors,
                context=context,
                col_class=col_class,
            )
        )
        for field_key, nested_schema in properties.items()
        if not field_key.startswith('_')
    )
    item_html += _render_item_body_wrapper(
        collapsible=collapsible, expanded=expanded, collapse_id=collapse_id, fields_html=fields_html
    )

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
    child_errors trio `FieldRenderer.render_field` stashes on `context` right
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
        context.child_errors,
    )
