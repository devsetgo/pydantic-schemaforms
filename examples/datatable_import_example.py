#!/usr/bin/env python3
"""
DataTableLayout Example - CSV Import to Table
==============================================

Standalone example (not wired into main.py's showcase app) demonstrating
DataTableLayout: a FormModel subclass whose fields describe table columns,
rendered as an HTML <table> progressively enhanced client-side by
DataTables.js (search/sort/paging/csv+copy export).

Each field is a table column. A column declared with FormField(...,
input_type=...) renders as a real editable widget per cell (dropdown for
Enum, etc.); plain fields render read-only. CSV rows are parsed and
validated server-side against the same Pydantic model used for the columns,
so a bad cell surfaces a normal per-row validation error instead of silently
corrupting the table.

The file input and the table are integrated into *one* form
(EmployeeImportForm below), rendered with the same single render_form_html()
call every other form in this app uses (see date_time_formats_example.py):

- csv_file: a plain file field -- present alongside the table, not in a
  separate form.
- employees: DataTableLayout embedded as a single layout field
  (input_type="layout", layout_handler="datatable" -- see
  pydantic_schemaforms/datatable_layout.py).

Loading a CSV is deliberately a *separate* step from saving it: a single
"Submit" button that immediately committed whatever CSV you'd chosen would
give you no chance to catch and fix bad rows (a typo'd email, an invalid
department) before they landed in "the database." So there are two submit
buttons instead of one (include_submit_button=False suppresses the
library's own single button; two plain <button type="submit"
name="datatable_action" value="...">s are appended before </form>):

- "Load CSV" (datatable_action=load): parses the chosen file and re-renders
  the table with those rows for review -- highlighting any row that failed
  validation -- without touching the committed data at all.
- "Submit" (datatable_action=submit): saves whatever the table is currently
  showing, whether that's a freshly loaded (and possibly hand-corrected)
  CSV import or just a cell edited directly in already-committed data.

No server-side "staging" storage is needed to connect those two steps --
the loaded rows are already sitting in the table's own form fields (both
the editable cells and the read-only cells' hidden inputs), so whatever the
browser submits on the next click *is* the reviewed state.

Run directly to print the rendered HTML to stdout, or mount `router` in a
FastAPI app to try the upload flow in a browser.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import EmailStr

from examples.fastapi_routes import templates
from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.datatable_layout import DataTableLayout, RowError
from pydantic_schemaforms.schema_form import Field as FormField
from pydantic_schemaforms.schema_form import FormModel


class Department(str, Enum):
    engineering = 'engineering'
    sales = 'sales'
    support = 'support'


class EmployeeImport(DataTableLayout):
    """Row schema for a CSV of employees -- also the table's columns.

    Every column is declared with FormField(..., input_type=...), so every
    cell renders as a real, editable widget -- not just department. Without
    input_type, a column renders read-only (see DataTableLayout's own
    docstring), which is the wrong default here: this demo lets you fix a
    typo'd name/email/project field directly in the table, not just swap
    the whole CSV to change anything but the dropdown.
    """

    name: str = FormField(..., input_type='text')
    email: EmailStr = FormField(..., input_type='email')
    department: Department = FormField(Department.engineering, input_type='select')
    project_team_name: str = FormField('', input_type='text')
    project_description: str = FormField('', input_type='text')

    model_config = {
        'buttons': [
            'csv',
            'copy',
        ],  # 'pdf' accepted too, but raises NotImplementedError (pdfmake not vendored)
        'search': True,
        'paging': True,
        'page_length': 25,
        'csv_template': True,
        'style': {'striped': True, 'bordered': True, 'hover': True, 'compact': False},
    }


class EmployeeImportForm(FormModel):
    """One form: a file field for bulk CSV import, sitting right above the
    table itself (DataTableLayout embedded as a layout field). "Load CSV"
    previews the file's rows in the table below without saving anything;
    "Submit" saves whatever the table currently shows -- see
    import_or_save() below.
    """

    csv_file: str = FormField(
        '',
        title='Import CSV (optional)',
        input_type='file',
        ui_help_text=(
            'Upload a CSV with name,email,department,project_team_name,'
            'project_description columns, then click "Load CSV" to preview '
            'it in the table below -- nothing is saved until you review it '
            'and click "Submit". To just edit existing rows, skip this and '
            'edit cells directly, then click "Submit".'
        ),
    )
    employees: Any = FormField(
        default_factory=dict,
        title='Employees',
        input_type='layout',
        layout_handler='datatable',
    )


# In-memory demo store standing in for a real database.
_IMPORTED_ROWS: list[dict[str, str]] = [
    {
        'name': 'Alice Chen',
        'email': 'alice@example.com',
        'department': 'engineering',
        'project_team_name': 'Platform Team',
        'project_description': 'Rebuild the customer portal',
    },
    {
        'name': 'Bob Diaz',
        'email': 'bob@example.com',
        'department': 'sales',
        'project_team_name': 'Growth Team',
        'project_description': 'Expand into new markets',
    },
]
_LAST_ROW_ERRORS: dict[int, dict[str, str]] = {}

_TABLE_ID = 'employee_datatable'


router = APIRouter(prefix='/employees', tags=['CSV Import (DataTableLayout)'])


_TITLE = 'Employee Import - DataTableLayout'
_DESCRIPTION = (
    'One form -- a file input integrated directly above the table, both '
    'rendered by a single render_form_html() call, the same pattern every '
    'other form in this app uses. "Load CSV" only previews a chosen file '
    'in the table below; nothing is saved until you review it and click '
    '"Submit". Rows are validated row-by-row against the same Pydantic '
    'model used for the columns, and the table is enhanced client-side by '
    'DataTables.js (search, sort, csv/copy export).'
)

# Pre-generated by generate_sample_csv.py -- for exercising the import
# pipeline at different scales. Two of every generated file's rows are
# intentionally invalid (a bad email, a bad department) to demonstrate the
# per-row validation-error highlighting.
_SAMPLE_DIR = Path(__file__).resolve().parent / 'sample_data'
_SAMPLE_SIZES = (10, 100, 1000, 10000)


def _sample_links_html() -> str:
    links = ''.join(
        f'<a href="/employees/samples/{size}" class="btn btn-outline-secondary btn-sm me-2 mb-2">'
        f'{size:,} rows</a>'
        for size in _SAMPLE_SIZES
    )
    return (
        '<div class="mb-3">'
        '<div class="text-muted small mb-1">Sample CSV files to test different scales:</div>'
        f'{links}'
        '</div>'
    )


def _merge_rows_in_original_order(
    rows: list[EmployeeImport], row_errors: list[RowError]
) -> list[dict[str, str]]:
    """Merge valid + invalid rows back into their original order so every
    submitted row stays visible -- an invalid row keeps its raw, as-typed
    values (instead of silently vanishing) and is flagged via row_errors."""
    errors_by_index = {err.row_index: err for err in row_errors}
    valid_rows = iter(row.model_dump(mode='json') for row in rows)
    return [
        errors_by_index[i].raw if i in errors_by_index else next(valid_rows)
        for i in range(len(rows) + len(row_errors))
    ]


# Marks the start of the "employees" layout field's own wrapper -- generic
# markup emitted for *any* layout field (see rendering/themes.py), not
# specific to DataTableLayout, so it's a stable anchor for "everything
# before the table" regardless of which columns/config this row model uses.
_LAYOUT_FIELD_MARKER = '<section class="layout-field-section'


def _load_button_html(*, reviewing: bool) -> str:
    load_label = 'Reload CSV' if reviewing else 'Load CSV'
    return (
        '<div class="mb-3">'
        f'<button type="submit" name="datatable_action" value="load" '
        f'class="btn btn-outline-primary">{load_label}</button>'
        '</div>'
    )


def _submit_button_html() -> str:
    return (
        '<div class="mt-3">'
        '<button type="submit" name="datatable_action" value="submit" '
        'class="btn btn-primary">Submit</button>'
        '</div>'
    )


def _render_page(
    request: Request,
    *,
    style: str,
    debug: bool,
    show_timing: bool,
    rows: list[dict[str, str]] | None = None,
    row_errors: dict[int, dict[str, str]] | None = None,
    reviewing: bool = False,
    notice: str = '',
):
    """Render the page from an explicit (rows, row_errors) pair when given
    (a CSV just parsed for review -- not yet committed), otherwise from the
    currently committed data. Either way the result is the *same* table,
    editable the same way -- reviewing only changes the banner/button label
    above it, not how the table itself behaves.
    """
    display_rows = _IMPORTED_ROWS if rows is None else rows
    display_errors = _LAST_ROW_ERRORS if row_errors is None else row_errors

    form_html = render_form_html(
        EmployeeImportForm,
        framework=style,
        form_data={
            'employees': EmployeeImport.as_layout_value(
                rows=display_rows, row_errors=display_errors, table_id=_TABLE_ID
            )
        },
        submit_url='/employees/import',
        debug=debug,
        show_timing=show_timing,
        enable_logging=True,
        include_submit_button=False,
    )
    # "Load CSV" sits right next to the file input it acts on, immediately
    # above the table -- not stranded below the table next to "Submit",
    # which acts on the table instead.
    load_button = _load_button_html(reviewing=reviewing)
    if _LAYOUT_FIELD_MARKER in form_html:
        form_html = form_html.replace(_LAYOUT_FIELD_MARKER, load_button + _LAYOUT_FIELD_MARKER, 1)
    else:
        form_html = load_button + form_html
    form_html = form_html.replace('</form>', _submit_button_html() + '</form>', 1)

    banner = ''
    if notice:
        banner = f'<div class="alert alert-warning">{notice}</div>'
    elif reviewing:
        banner = (
            '<div class="alert alert-info">Reviewing rows loaded from CSV -- '
            'nothing is saved yet. Fix any highlighted cells below, then '
            'click <strong>Submit</strong> to save, or '
            '<a href="/employees/import">discard and start over</a>.</div>'
        )

    form_html = _sample_links_html() + banner + form_html

    return templates.TemplateResponse(
        request,
        'form.html',
        {
            'request': request,
            'title': _TITLE,
            'description': _DESCRIPTION,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'framework_type': style,
            'form_html': form_html,
        },
    )


@router.get('/import', response_class=HTMLResponse)
def show_import_page(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    return _render_page(request, style=style, debug=debug, show_timing=show_timing)


@router.post('/import', response_class=HTMLResponse)
async def import_or_save(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """Two distinct submit buttons (see _action_buttons_html), told apart by
    the datatable_action field the clicked one carries:

    - "load": parse the chosen CSV and show it in the table for review --
      this never touches _IMPORTED_ROWS ("the database"), so a bad import
      can't land there just because a file was chosen.
    - "submit" (default, for safety): save whatever the table is currently
      showing -- parse_submitted_rows() reads the same rows[i].field
      inputs the table always renders, regardless of whether their values
      came from a CSV just loaded for review or a directly edited cell.
    """
    global _LAST_ROW_ERRORS

    form = await request.form()
    action = form.get('datatable_action', 'submit')

    if action == 'load':
        csv_upload = form.get('csv_file')
        raw = await csv_upload.read() if hasattr(csv_upload, 'read') else b''
        if not raw:
            return _render_page(
                request,
                style=style,
                debug=debug,
                show_timing=show_timing,
                notice='Choose a CSV file first, then click "Load CSV".',
            )
        rows, row_errors = EmployeeImport.parse_csv_rows(raw)
        preview_rows = _merge_rows_in_original_order(rows, row_errors)
        preview_errors = {err.row_index: err.errors for err in row_errors}
        return _render_page(
            request,
            style=style,
            debug=debug,
            show_timing=show_timing,
            rows=preview_rows,
            row_errors=preview_errors,
            reviewing=True,
        )

    rows, row_errors = EmployeeImport.parse_submitted_rows(form)
    merged_rows = _merge_rows_in_original_order(rows, row_errors)
    _IMPORTED_ROWS[:] = merged_rows
    _LAST_ROW_ERRORS = {err.row_index: err.errors for err in row_errors}

    if row_errors:
        # Still errors after Submit -- stay on the table so they can keep
        # fixing highlighted cells and submit again, same as every other
        # DataTableLayout error path (never show a "success" page for data
        # that didn't actually all validate).
        return _render_page(request, style=style, debug=debug, show_timing=show_timing)

    return templates.TemplateResponse(
        request,
        'success.html',
        {
            'request': request,
            'title': 'Employees Saved',
            'message': f'{len(merged_rows)} employee(s) saved.',
            'data': merged_rows,
            'framework': 'fastapi',
            'framework_name': 'FastAPI (Async)',
            'try_again_url': '/employees/import',
        },
    )


@router.get('/import/template.csv')
def download_csv_template() -> Response:
    if not EmployeeImport.datatable_options()['csv_template']:
        raise HTTPException(status_code=404, detail='CSV template not enabled for this form')
    return Response(
        content=EmployeeImport.csv_template_bytes(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="employee_import_template.csv"'},
    )


@router.get('/samples/{size}')
def download_sample_csv(size: int) -> FileResponse:
    # size is constrained to a fixed whitelist (not an arbitrary filename),
    # so this can't be used to read other files off disk.
    if size not in _SAMPLE_SIZES:
        raise HTTPException(status_code=404, detail=f'No sample file for size {size}')
    path = _SAMPLE_DIR / f'employees_{size}.csv'
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail='Sample file not generated -- run `python examples/generate_sample_csv.py`',
        )
    return FileResponse(path, media_type='text/csv', filename=path.name)


if __name__ == '__main__':
    print(
        render_form_html(
            EmployeeImportForm,
            form_data={'employees': EmployeeImport.as_layout_value(rows=_IMPORTED_ROWS)},
            submit_url='/employees/import',
        )
    )
