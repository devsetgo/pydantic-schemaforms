"""Renders a DataTableLayout subclass's rows as an HTML <table>, with
DataTables.js wired in client-side as progressive enhancement over the
plain <table> the server emits.

This is a *layout field* renderer (see docs/plugin_hooks.md): registered
under the name 'datatable' via the @LayoutEngine.layout_renderer('datatable')
decorator (builtin=True, so it survives LayoutEngine.reset_layout_renderers()
-- this module-level registration only ever runs once per process), it
plugs into the exact same render_form_html()/FormModel pipeline every other
form in this library uses -- a DataTableLayout subclass is embedded as one
field (input_type='layout', layout_handler='datatable') on a plain
FormModel, not rendered through a separate bespoke entry point.

When model_config['csv_upload'] is enabled (the default -- see
DataTableLayout's module docstring), this renderer's own output already
includes the file input and the "Load CSV"/"Submit" buttons -- nobody
declares a separate file field or hand-builds that markup. This is safe
without a second <form>: a <button type="submit">/<input type="file">
living inside this field's own slot still submits/attaches to whatever
<form> the *embedding* FormModel opened; only a *nested* <form> tag would
be silently dropped by the browser, and this renderer never emits one.
Because of that own "Submit" button, callers should pass
include_submit_button=False to render_form_html_async() so there isn't a
second, redundant one from the embedding form itself.

See DataTableLayout.as_layout_value() for building this field's value and
DataTableLayout.handle_import_post() for the server side, and
docs/recipes.md for the full pattern.
"""

from __future__ import annotations

import base64
import enum
import json
from typing import TYPE_CHECKING, Any

from pydantic_schemaforms.assets.runtime import (
    datatables_buttons_css_tag,
    datatables_buttons_script_tag,
    datatables_css_tag,
    datatables_script_tag,
)
from pydantic_schemaforms.inputs.registry import get_input_component_map
from pydantic_schemaforms.inputs.specialized_inputs import FileInput
from pydantic_schemaforms.rendering.layout_engine import LayoutEngine
from pydantic_schemaforms.tstring import SafeHTML
from pydantic_schemaforms.tstring import html as render_html

if TYPE_CHECKING:
    from pydantic_schemaforms.datatable_layout import DataTableConfig, DataTableLayout
    from pydantic_schemaforms.rendering.context import RenderContext

# ui_element values that are SelectInput-family widgets: render(options=[...],
# **kwargs) with per-option 'selected' flags, rather than a bare `value=`
# kwarg (which a <select> doesn't have). RadioGroup/CheckboxGroup use a
# different, incompatible render() signature (a required `group_name`) and
# are intentionally not handled here -- see the try/except fallback below.
_OPTION_BASED_UI_ELEMENTS = frozenset({'select', 'multiselect', 'combobox'})

_BUTTON_NAME_MAP = {'csv': 'csvHtml5', 'copy': 'copyHtml5', 'pdf': 'pdfHtml5'}


# DataTableStyleConfig flags -> the Bootstrap utility class each one adds.
_STYLE_CLASS_MAP = {
    'striped': 'table-striped',
    'bordered': 'table-bordered',
    'hover': 'table-hover',
    'compact': 'table-sm',
}


# DataTables' own CSS (dataTables.min.css) styles the <table>/search box/
# pagination regardless of framework, so the only thing that changes here is
# whether Bootstrap's own table/button/style classes are layered on top.
# There is no dedicated Material variant yet -- 'material' falls back to the
# same Bootstrap-ish classes as 'bootstrap' rather than going unstyled, and
# framework='none' drops all of them (including the style flags) for a
# truly bare table.
def _table_classes_for_framework(framework: str, style: dict[str, Any]) -> str:
    if framework == 'none':
        return ''
    classes = ['table']
    classes.extend(css_class for flag, css_class in _STYLE_CLASS_MAP.items() if style.get(flag))
    return ' '.join(classes)


# Plain, developer-authored CSS with no interpolated values -- wrapped in
# SafeHTML(...) at each interpolation site so the html() processor passes
# it through instead of escaping it.
_ERROR_STYLES = """<style>
.datatable-row-error > td { background-color: #f8d7da; }
.datatable-cell-error { outline: 2px solid #dc3545; outline-offset: -2px; }
</style>
"""


def _field_label(field_name: str, field_info: Any) -> str:
    return field_info.title or field_name.replace('_', ' ').title()


def _resolve_editable_ui_element(field_info: Any) -> str | None:
    extra = field_info.json_schema_extra
    if not isinstance(extra, dict):
        return None
    return extra.get('input_type') or extra.get('ui_element') or extra.get('element')


def _enum_options(annotation: Any) -> list[dict[str, str]] | None:
    candidate = annotation
    for arg in getattr(annotation, '__args__', None) or ():
        if isinstance(arg, type) and issubclass(arg, enum.Enum):
            candidate = arg
            break
    if isinstance(candidate, type) and issubclass(candidate, enum.Enum):
        return [
            {'value': str(member.value), 'label': member.name.replace('_', ' ').title()}
            for member in candidate
        ]
    return None


def _render_read_only_cell(field_name: str, row_index: int, value: Any) -> SafeHTML:
    """Escaped display text plus a hidden input carrying the same value.

    The hidden input matters whenever this table sits inside a save form
    (a column declared with FormField(input_type=...) elsewhere on the same
    row -- see render_datatable_layout_field/the recipe in docs/recipes.md):
    a real browser submit only sends fields that have a name=
    attribute, so a read-only column with *no* input at all would vanish
    from the submitted data entirely, failing that row's validation for a
    field that was never meant to be editable in the first place (e.g. a
    required 'email' column disappearing because only the 'department'
    dropdown next to it was actually an <input>).
    """
    # NOSONAR comments below: each variable is read via {expr} interpolation
    # in the t-string return statement -- Sonar's Python analyzer doesn't
    # parse PEP 750 t-strings yet, so it can't see the reference and flags a
    # false-positive "unused local variable".
    display_value = '' if value is None else str(value)  # NOSONAR
    name = f'rows[{row_index}].{field_name}'  # NOSONAR
    return render_html(
        t'{display_value}<input type="hidden" name="{name}" value="{display_value}">'
    )


def _render_cell_content(
    field_name: str, field_info: Any, value: Any, row_index: int, ui_element: str | None
) -> Any:
    """Return SafeHTML for an editable input, or escaped display text plus
    a same-value hidden input for a read-only cell (see
    _render_read_only_cell)."""

    if isinstance(value, enum.Enum):
        value = value.value

    if not ui_element:
        return _render_read_only_cell(field_name, row_index, value)

    input_map = get_input_component_map()
    input_cls = input_map.get(ui_element)
    if input_cls is None:
        return _render_read_only_cell(field_name, row_index, value)

    name = f'rows[{row_index}].{field_name}'
    instance = input_cls()
    kwargs: dict[str, Any] = {'name': name, 'id': name}

    if ui_element in _OPTION_BASED_UI_ELEMENTS:
        extra = (
            field_info.json_schema_extra if isinstance(field_info.json_schema_extra, dict) else {}
        )
        raw_options = extra.get('options')
        options = raw_options if isinstance(raw_options, list) else None
        options = options or _enum_options(field_info.annotation) or []
        marked_options = [
            {**opt, 'selected': str(value) == str(opt.get('value'))} if value is not None else opt
            for opt in options
        ]
        try:
            return SafeHTML(instance.render(options=marked_options, **kwargs))
        except TypeError:
            return _render_read_only_cell(field_name, row_index, value)

    if value is not None:
        kwargs['value'] = value

    try:
        return SafeHTML(instance.render(**kwargs))
    except TypeError:
        # Some registered widgets (e.g. RadioGroup/CheckboxGroup) require
        # extra positional args (group_name, etc.) this generic per-cell
        # renderer doesn't know how to supply -- fall back to read-only
        # display (still round-trips via the hidden input) rather than
        # breaking the whole row.
        return _render_read_only_cell(field_name, row_index, value)


def _render_csv_template_link(model_cls: type['DataTableLayout'], framework: str) -> SafeHTML:
    """A "Download CSV template" link, embedded as a data: URI so it needs
    no server route of its own -- the template bytes are already fully
    determined by the model's own fields at render time."""
    encoded = base64.b64encode(model_cls.csv_template_bytes()).decode('ascii')
    # NOSONAR comments below: each variable is read via {expr} interpolation
    # in the t-string return statement -- see _render_read_only_cell above.
    href = f'data:text/csv;base64,{encoded}'  # NOSONAR
    filename = f'{model_cls.__name__.lower()}_template.csv'  # NOSONAR
    css_class = '' if framework == 'none' else 'btn btn-outline-secondary btn-sm mb-2'  # NOSONAR
    return render_html(
        t'<a href="{href}" download="{filename}" class="{css_class}">Download CSV template</a>'
    )


def _render_csv_upload_block(*, reviewing: bool) -> SafeHTML:
    """The file input + "Load"/"Reload CSV" button -- reuses FileInput for
    the same drag-drop/preview UX an ordinary input_type='file' field gets.
    Field/button names ('csv_file', 'datatable_action') are the fixed,
    documented convention DataTableLayout.handle_import_post() reads --
    intentionally not namespaced per-field, matching row cells' own fixed
    'rows[i].field' convention (this library supports one DataTableLayout
    per page today)."""
    file_input_html = SafeHTML(FileInput().render(name='csv_file', id='csv_file'))
    load_label = 'Reload CSV' if reviewing else 'Load CSV'
    return render_html(t"""
<div class="mb-3">
    <label for="csv_file" class="form-label">Import CSV (optional)</label>
    {file_input_html}
    <div class="form-text">Upload a CSV to replace the table below, or edit cells directly and click Submit.</div>
    <button type="submit" name="datatable_action" value="load" class="btn btn-outline-primary mt-2">{load_label}</button>
</div>
""")


def _render_notice_banner(notice: str) -> SafeHTML:
    if not notice:
        return SafeHTML('')
    return render_html(t'<div class="alert alert-warning">{notice}</div>')


def _render_reviewing_banner(discard_url: str | None) -> SafeHTML:
    if discard_url:
        return render_html(
            t'<div class="alert alert-info">Reviewing rows loaded from CSV -- nothing is '
            t'saved yet. Fix any highlighted cells below, then click <strong>Submit</strong> '
            t'to save, or <a href="{discard_url}">discard and start over</a>.</div>'
        )
    return render_html(
        t'<div class="alert alert-info">Reviewing rows loaded from CSV -- nothing is saved '
        t'yet. Fix any highlighted cells below, then click <strong>Submit</strong> to save.</div>'
    )


def _render_datatable_submit_button() -> SafeHTML:
    return render_html(
        t'<div class="mt-3"><button type="submit" name="datatable_action" value="submit" '
        t'class="btn btn-primary">Submit</button></div>'
    )


def render_datatable_table(
    model_cls: type['DataTableLayout'],
    *,
    rows: list[dict[str, Any]] | None = None,
    row_errors: dict[int, dict[str, str]] | None = None,
    table_id: str = 'datatable',  # NOSONAR -- read via {table_id} in the return t-string below
    framework: str = 'bootstrap',
    style: dict[str, Any] | None = None,
) -> str:
    rows = rows or []
    row_errors = row_errors or {}
    fields = model_cls.model_fields

    # NOSONAR comments below: each variable is read via {expr} interpolation
    # in a t-string -- Sonar's Python analyzer doesn't parse PEP 750
    # t-strings yet, so it can't see the reference and flags a false-
    # positive "unused local variable" (see _render_read_only_cell above).
    header_parts = []
    for field_name, field_info in fields.items():
        label = _field_label(field_name, field_info)  # NOSONAR
        header_parts.append(render_html(t'<th>{label}</th>'))
    thead_row = SafeHTML(''.join(header_parts))  # NOSONAR

    body_parts = []
    for index, row in enumerate(rows):
        errors_for_row = row_errors.get(index) or {}
        cell_parts = []
        for field_name, field_info in fields.items():
            value = row.get(field_name)
            ui_element = _resolve_editable_ui_element(field_info)
            content = _render_cell_content(
                field_name, field_info, value, index, ui_element
            )  # NOSONAR
            cell_error = errors_for_row.get(field_name) or ''
            error_class = ' datatable-cell-error' if cell_error else ''  # NOSONAR
            cell_parts.append(
                render_html(
                    t'<td class="datatable-cell{error_class}" title="{cell_error}">{content}</td>'
                )
            )
        error_message = next(iter(errors_for_row.values()), None)
        row_class = ' class="datatable-row-error"' if error_message else ''  # NOSONAR
        body_parts.append(
            render_html(
                t'<tr data-row-index="{index}"{SafeHTML(row_class)}>{SafeHTML("".join(cell_parts))}</tr>'
            )
        )
    tbody_rows = SafeHTML(''.join(body_parts))  # NOSONAR
    table_class = (  # NOSONAR
        f'{_table_classes_for_framework(framework, style or {})} datatable-table'.strip()
    )

    return render_html(t"""{SafeHTML(_ERROR_STYLES)}<table id="{table_id}" class="{table_class}">
<thead><tr>{thead_row}</tr></thead>
<tbody>{tbody_rows}</tbody>
</table>""")


def _datatables_button_name(name: str) -> str:
    if name == 'pdf':
        raise NotImplementedError(
            "The 'pdf' DataTables button requires vendoring pdfmake, which is not bundled "
            "yet. Remove 'pdf' from model_config['buttons'] for now."
        )
    if name not in _BUTTON_NAME_MAP:
        raise ValueError(f"Unknown DataTables button '{name}'. Expected one of: csv, copy, pdf.")
    return _BUTTON_NAME_MAP[name]


def _build_layout(*, has_buttons: bool, paging: bool, search: bool) -> dict[str, Any]:
    """Build DataTables' modern `layout` option (position -> feature name(s)).

    The legacy `dom` string option (DataTables <2, still accepted for
    back-compat) only produces a flexbox-arranged row of controls when the
    string uses explicit `<div>`-grouping syntax (e.g. `<"row"<"col"l><"col"f>>`)
    -- a bare string like 'Blfrtip' just places each control as an
    unwrapped sibling with no layout at all, which is why buttons/length/
    search ended up stacked instead of aligned. `layout` is the actual
    DataTables 2+ mechanism and lays each position out in a proper flex row
    automatically, matching what a normal DataTables site looks like.
    """

    layout: dict[str, Any] = {}

    top_start: list[str] = []
    if has_buttons:
        top_start.append('buttons')
    if paging:
        top_start.append('pageLength')
    if top_start:
        layout['topStart'] = top_start

    if search:
        layout['topEnd'] = 'search'

    layout['bottomStart'] = 'info'
    if paging:
        layout['bottomEnd'] = 'paging'

    return layout


def _render_init_script(table_id: str, options: 'DataTableConfig') -> SafeHTML:
    button_names = [_datatables_button_name(name) for name in options.get('buttons') or []]
    paging = bool(options.get('paging', True))
    search = bool(options.get('search', True))
    page_length = int(options.get('page_length', 10))
    # The default page_length is always offered in the "entries per page"
    # dropdown, even if it wasn't already one of length_menu's choices.
    length_menu = sorted(
        {*(int(n) for n in options.get('length_menu') or [10, 25, 50, 100]), page_length}
    )

    config: dict[str, Any] = {
        'searching': search,
        'paging': paging,
        'pageLength': page_length,
        'lengthMenu': length_menu,
        'layout': _build_layout(has_buttons=bool(button_names), paging=paging, search=search),
    }
    config_json = json.dumps(config)

    # button_names come only from _BUTTON_NAME_MAP's fixed values
    # ('csvHtml5'/'copyHtml5'/'pdfHtml5'), never from arbitrary user input,
    # so interpolating them directly into the JS array literal below is safe.
    #
    # Export buttons need a custom exportOptions.format.body: DataTables'
    # default HTML5 export reads a cell's stripped-of-tags text, which for a
    # <select> concatenates every <option>'s label instead of the selected
    # one. _dtCellExportValue reads the live form control's actual value
    # (select.value / input.value) so exported CSV/copy data matches what
    # parse_csv_rows() expects on re-import, instead of a display label or
    # every option glued together.
    buttons_js = ''
    if button_names:
        button_entries = ',\n        '.join(
            "{ extend: '%s', exportOptions: { format: { body: function (data, row, column, node) "
            '{ return _dtCellExportValue(node); } } } }' % name
            for name in button_names
        )
        buttons_js = f"""
        dtConfig.buttons = [
        {button_entries}
        ];"""

    # JS-only content (rule 4 exception): table_id/config_json/buttons_js are
    # embedded as JS identifiers/an object literal, not HTML attribute
    # values, so this stays an f-string rather than a t-string.
    #
    # Runs immediately if the DOM is already ready rather than only waiting
    # on 'DOMContentLoaded' -- that event fires once per page load, but this
    # script re-runs on every htmx swap (htmx re-executes <script> tags in
    # swapped-in content), long after the event already fired. A listener
    # added post-facto would silently never run, leaving the freshly
    # swapped-in table un-enhanced.
    return SafeHTML(f"""
<script>
function _dtCellExportValue(node) {{
    var select = node.querySelector('select');
    if (select) {{ return select.value; }}
    var input = node.querySelector('input, textarea');
    if (input) {{ return input.value; }}
    return node.textContent.trim();
}}
(function() {{
    function _dtInit() {{
        var el = document.getElementById('{table_id}');
        if (el && window.DataTable) {{
            var dtConfig = {config_json};{buttons_js}
            // Stashed on the element (not just a local variable) so a page
            // embedding this table -- e.g. inside a hidden Bootstrap tab
            // pane, where DataTables can miscalculate column widths at
            // init time -- can look it up later and call
            // el.dtInstance.columns.adjust().draw(false) once the tab
            // becomes visible.
            el.dtInstance = new DataTable(el, dtConfig);
        }}
    }}
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', _dtInit);
    }} else {{
        _dtInit();
    }}
}})();
</script>
""")


@LayoutEngine.layout_renderer('datatable')
def render_datatable_layout_field(
    field_name: str,
    field_schema: dict[str, Any],
    value: Any,
    ui_info: dict[str, Any],
    context: 'RenderContext',
    engine: LayoutEngine,
) -> str:
    """LayoutRenderer entry point registered as the 'datatable' layout_handler
    (see the bottom of this module and DataTableLayout.as_layout_value()).

    `value` is whatever DataTableLayout.as_layout_value() built: the row
    model class plus current rows/row_errors/table_id/config. This is the
    *only* rendering entry point for DataTableLayout now -- it plugs into
    the same render_form_html()/FormModel pipeline every other form uses,
    rather than a separate bespoke one. When model_config['csv_upload'] is
    enabled (the default), the file input and Load/Submit buttons are part
    of *this* function's own output -- see the module docstring for why
    that's safe without a nested <form>, and DataTableLayout.handle_import_post()
    for the matching server-side parsing.
    """
    value = value or {}
    model_cls = value.get('model_cls')
    if model_cls is None:
        return ''

    rows = value.get('rows') or []
    row_errors = value.get('row_errors') or {}
    table_id = value.get('table_id') or f'{model_cls.__name__.lower()}_datatable'
    asset_mode = value.get('asset_mode', 'vendored')
    include_assets = value.get('include_assets', True)
    reviewing = bool(value.get('reviewing'))
    notice = value.get('notice') or ''
    discard_url = value.get('discard_url')
    framework = getattr(getattr(engine, '_renderer', None), 'framework', 'bootstrap')

    options = model_cls.datatable_options()
    csv_upload_enabled = options.get('csv_upload', True)

    template_link = (
        str(_render_csv_template_link(model_cls, framework)) if options.get('csv_template') else ''
    )

    table_html = render_datatable_table(
        model_cls,
        rows=rows,
        row_errors=row_errors,
        table_id=table_id,
        framework=framework,
        style=options.get('style'),
    )
    init_script = _render_init_script(table_id, options)

    assets = ''
    if include_assets:
        asset_parts = [
            datatables_css_tag(asset_mode=asset_mode),
            datatables_script_tag(asset_mode=asset_mode),
        ]
        if options.get('buttons'):
            asset_parts.append(datatables_buttons_css_tag(asset_mode=asset_mode))
            asset_parts.append(datatables_buttons_script_tag(asset_mode=asset_mode))
        assets = '\n'.join(part for part in asset_parts if part)

    upload_block = ''
    banner = ''
    submit_block = ''
    if csv_upload_enabled:
        upload_block = str(_render_csv_upload_block(reviewing=reviewing))
        if notice:
            banner = str(_render_notice_banner(notice))
        elif reviewing:
            banner = str(_render_reviewing_banner(discard_url))
        submit_block = str(_render_datatable_submit_button())

    return '\n'.join(
        part
        for part in (
            assets,
            upload_block,
            banner,
            template_link,
            table_html,
            submit_block,
            init_script,
        )
        if part
    )
