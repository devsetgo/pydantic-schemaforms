"""Markup of one repeating sub-form item (model_list), shared by the themes.

`RendererTheme.render_model_list_item` renders an item through this module by
default; a theme overrides that hook to give items its own markup. Kept apart
from `model_list_renderer` so `rendering.themes` can import it without a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_schemaforms.tstring import SafeHTML, html


@dataclass(frozen=True, slots=True)
class ModelListItem:
    index: int
    field_name: str
    title_template: str
    item_title: str
    collapsible: bool
    expanded: bool
    collapse_id: str
    # (rendered field, spans the full row) per item field, in order.
    cells: tuple[tuple[str, bool], ...]


def _render_item_toggle(item: ModelListItem) -> SafeHTML:
    # The title sits in its own element so the model-list script can update
    # it with textContent as the user types, never as HTML.
    title = html(
        t'<span class="model-list-item-title" data-model-list-title>{item.item_title}</span>'
    )
    if not item.collapsible:
        return html(t"""
                <span>
                    <i class="bi bi-card-list me-2"></i>
                    {title}
                </span>""")

    # NOSONAR comments below: each variable is read via {expr} interpolation
    # in the t-string return statement -- Sonar's Python analyzer doesn't
    # parse PEP 750 t-strings yet, so it can't see the reference and flags a
    # false-positive "unused local variable".
    collapse_id = item.collapse_id  # NOSONAR
    chevron_class = 'down' if item.expanded else 'right'  # NOSONAR
    expanded_attr = str(item.expanded).lower()  # NOSONAR
    return html(t'''
                <button class="btn btn-link text-decoration-none p-0 text-start"
                        type="button"
                        data-bs-toggle="collapse"
                        data-bs-target="#{collapse_id}"
                        aria-expanded="{expanded_attr}"
                        aria-controls="{collapse_id}">
                    <i class="bi bi-chevron-{chevron_class} me-2"></i>
                    <i class="bi bi-card-list me-2"></i>
                    {title}
                </button>''')


def _column_class_for_field_count(field_count: int) -> str:
    if field_count <= 2:
        return 'col-12'
    if field_count <= 4:
        return 'col-md-6'
    return 'col-lg-4 col-md-6'


def _render_cells(item: ModelListItem) -> str:
    col_class = _column_class_for_field_count(len(item.cells))
    parts = []
    for cell_html, full_row in item.cells:
        field_col_class = 'col-12' if full_row else col_class  # NOSONAR
        nested_field_html = SafeHTML(cell_html)  # NOSONAR
        parts.append(
            str(
                html(t'''
            <div class="{field_col_class}">
                {nested_field_html}
            </div>''')
            )
        )
    return ''.join(parts)


def _render_item_body_wrapper(item: ModelListItem, fields_html: str) -> str:
    if item.collapsible:
        collapse_id = item.collapse_id  # NOSONAR
        show_class = 'show' if item.expanded else ''  # NOSONAR
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


def render_default_model_list_item(item: ModelListItem) -> str:
    """The card-style item every framework has used (Bootstrap markup)."""
    index = item.index  # NOSONAR
    title_template = item.title_template  # NOSONAR
    field_name = item.field_name  # NOSONAR
    item_html = html(t'''
    <div class="model-list-item card border mb-3"
         data-index="{index}"
         data-title-template="{title_template}"
         data-field-name="{field_name}">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">''')
    item_html += _render_item_toggle(item)
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
    item_html += _render_item_body_wrapper(item, _render_cells(item))
    item_html += """
    </div>"""
    return item_html
