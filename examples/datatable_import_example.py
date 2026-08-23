#!/usr/bin/env python3
"""
DataTableLayout Example - CSV Import to Table
==============================================

Mounted into main.py's showcase app (see the "CSV Import (DataTableLayout)"
tag) demonstrating DataTableLayout: a FormModel subclass whose fields
describe table columns, rendered as an HTML <table> progressively enhanced
client-side by DataTables.js (search/sort/paging/csv+copy export) -- with a
built-in CSV import UI (file input, "Load CSV"/"Submit" buttons) that's part
of the table's own rendered output, not something this file hand-builds.

Each field is a table column. A column declared with FormField(...,
input_type=...) renders as a real editable widget per cell (dropdown for
Enum, etc.); plain fields render read-only. CSV rows are parsed and
validated server-side against the same Pydantic model used for the columns,
so a bad cell surfaces a normal per-row validation error instead of silently
corrupting the table.

EmployeeImportForm below has exactly one field -- the file input, "Load
CSV"/"Submit" buttons, and the "reviewing" banner are all part of
EmployeeImport's own rendered output (model_config['csv_upload'] defaults
to True; see DataTableLayout's module docstring for why that's safe
without a nested <form>, and pass include_submit_button=False here since
EmployeeImport renders its own Submit). Loading a CSV is deliberately a
separate step from saving it -- "Submit" always saves whatever the table
is currently showing (parse_submitted_rows()), whether that's a freshly
loaded (and possibly hand-corrected) CSV import or just a cell edited
directly in already-committed data -- so a bad row never lands in "the
database" just because a file was chosen.

handle_import_post() on the model itself figures out which button was
clicked and parses/merges accordingly -- see the one POST route below.

Run directly to print the rendered HTML to stdout, or mount `router` in a
FastAPI app to try the upload flow in a browser.
"""

import asyncio
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import EmailStr

from examples.fastapi_routes import log_timing, templates
from pydantic_schemaforms import render_form_html_async
from pydantic_schemaforms.datatable_layout import DataTableLayout
from pydantic_schemaforms.schema_form import Field as FormField
from pydantic_schemaforms.schema_form import FormModel


class Department(str, Enum):
    engineering = 'engineering'
    sales = 'sales'
    support = 'support'


class EmployeeImport(DataTableLayout):
    """Row schema for a CSV of employees -- also the table's columns, and
    (via the built-in csv_upload UI) the whole import page's controls.

    Every column is declared with FormField(..., input_type=...), so every
    cell renders as a real, editable widget -- not just department. Without
    input_type, a column renders read-only (see DataTableLayout's own
    docstring), which is the wrong default here: this demo lets you fix a
    typo'd name/email/project field directly in the table.
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
    """One field -- EmployeeImport's own rendered output already includes
    the file input and Load/Submit buttons (model_config['csv_upload']
    defaults to True)."""

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
_IMPORT_URL = '/employees/import'


router = APIRouter(prefix='/employees', tags=['CSV Import (DataTableLayout)'])


_TITLE = 'Employee Import - DataTableLayout'
_DESCRIPTION = (
    'One form field -- EmployeeImport (a DataTableLayout) renders its own '
    'file input and Load/Submit buttons; this file never hand-builds that '
    'markup. "Load CSV" only previews a chosen file in the table below; '
    'nothing is saved until you review it and click "Submit". Rows are '
    'validated row-by-row against the same Pydantic model used for the '
    'columns, and the table is enhanced client-side by DataTables.js '
    '(search, sort, csv/copy export).'
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


async def _render_page(
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
    currently committed data."""
    display_rows = _IMPORTED_ROWS if rows is None else rows
    display_errors = _LAST_ROW_ERRORS if row_errors is None else row_errors

    with log_timing('render_form_html_async', rows=len(display_rows)):
        form_html = await render_form_html_async(
            EmployeeImportForm,
            framework=style,
            form_data={
                'employees': EmployeeImport.as_layout_value(
                    rows=display_rows,
                    row_errors=display_errors,
                    table_id=_TABLE_ID,
                    reviewing=reviewing,
                    notice=notice,
                    discard_url=_IMPORT_URL,
                )
            },
            submit_url=_IMPORT_URL,
            debug=debug,
            show_timing=show_timing,
            enable_logging=True,
            include_submit_button=False,  # EmployeeImport renders its own Submit
        )
    form_html = _sample_links_html() + form_html

    with log_timing('TemplateResponse form.html', rows=len(display_rows)):
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
async def show_import_page(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    return await _render_page(request, style=style, debug=debug, show_timing=show_timing)


@router.post('/import', response_class=HTMLResponse)
async def import_or_save(
    request: Request, style: str = 'bootstrap', debug: bool = False, show_timing: bool = True
):
    """One call replaces the load-vs-submit branching and row-merge dance
    every DataTableLayout CSV-import route needs -- see
    DataTableLayout.handle_import_post()."""
    global _LAST_ROW_ERRORS

    with log_timing('request.form()'):
        form = await request.form()

    with log_timing('EmployeeImport.handle_import_post', action=form.get('datatable_action')):
        result = await EmployeeImport.handle_import_post(form)

    if result.action == 'load':
        return await _render_page(
            request,
            style=style,
            debug=debug,
            show_timing=show_timing,
            rows=result.rows,
            row_errors=result.row_errors,
            reviewing=True,
            notice=result.notice,
        )

    _IMPORTED_ROWS[:] = result.rows
    _LAST_ROW_ERRORS = result.row_errors

    if result.has_errors:
        # Still errors after Submit -- stay on the table so they can keep
        # fixing highlighted cells and submit again (never show a "success"
        # page for data that didn't actually all validate).
        return await _render_page(request, style=style, debug=debug, show_timing=show_timing)

    with log_timing('TemplateResponse success.html', rows=len(result.rows)):
        return templates.TemplateResponse(
            request,
            'success.html',
            {
                'request': request,
                'title': 'Employees Saved',
                'message': f'{len(result.rows)} employee(s) saved.',
                'data': result.rows,
                'framework': 'fastapi',
                'framework_name': 'FastAPI (Async)',
                'try_again_url': _IMPORT_URL,
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


async def _print_standalone_html() -> None:
    print(
        await render_form_html_async(
            EmployeeImportForm,
            form_data={'employees': EmployeeImport.as_layout_value(rows=_IMPORTED_ROWS)},
            submit_url=_IMPORT_URL,
            include_submit_button=False,
        )
    )


if __name__ == '__main__':
    asyncio.run(_print_standalone_html())
