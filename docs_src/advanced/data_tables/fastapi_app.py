from enum import Enum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import EmailStr

from pydantic_schemaforms import DataTableLayout, Field, FormModel, html, render_form_html_async


class Department(str, Enum):
    engineering = 'engineering'
    sales = 'sales'
    support = 'support'


class EmployeeImport(DataTableLayout):
    name: str = Field(..., input_type='text')
    email: EmailStr = Field(..., input_type='email')
    department: Department = Field(Department.engineering, input_type='select')

    model_config = {
        'buttons': ['csv', 'copy'],
        'page_length': 25,
        'csv_template': True,
        'style': {'striped': True, 'bordered': True},
    }


class EmployeeImportForm(FormModel):
    employees: Any = Field(
        default_factory=dict,
        title='Employees',
        input_type='layout',
        layout_handler='datatable',
    )


saved_rows: list[dict] = []  # stand-in for a database
app = FastAPI()


async def render_page(*, rows=None, row_errors=None, reviewing=False, notice='') -> str:
    table = EmployeeImport.as_layout_value(
        rows=saved_rows if rows is None else rows,
        row_errors=row_errors,
        reviewing=reviewing,
        notice=notice,
        discard_url='/employees/import',
    )
    return await render_form_html_async(
        EmployeeImportForm,
        form_data={'employees': table},
        submit_url='/employees/import',
        include_submit_button=False,  # the table has its own Submit
        include_framework_assets=True,
        asset_mode='cdn',
    )


@app.get('/employees/import', response_class=HTMLResponse)
async def show_import():
    return await render_page()


@app.post('/employees/import', response_class=HTMLResponse)
async def import_or_save(request: Request):
    result = await EmployeeImport.handle_import_post(await request.form(max_fields=200_000))

    if result.action == 'load':  # a CSV was loaded for review; nothing saved yet
        return await render_page(
            rows=result.rows, row_errors=result.row_errors, reviewing=True, notice=result.notice
        )
    if result.has_errors:  # keep reviewing until every row is valid
        return await render_page(rows=result.rows, row_errors=result.row_errors)

    saved_rows[:] = result.rows
    count = len(result.rows)
    return html(t'<p>Saved {count} rows.</p>')


@app.get('/employees/import/template.csv')
def download_template() -> Response:
    return Response(
        content=EmployeeImport.csv_template_bytes(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="employees_template.csv"'},
    )
