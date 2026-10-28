"""Tests for DataTableLayout: a FormModel whose fields are table columns,
embedded as a layout field on a plain FormModel and rendered through the
same render_form_html()/FormModel pipeline every other form uses (see the
module docstring in pydantic_schemaforms/datatable_layout.py for why)."""

from enum import Enum
from typing import Any

import pytest

from pydantic_schemaforms import render_form_html
from pydantic_schemaforms.datatable_layout import DataTableLayout
from pydantic_schemaforms.schema_form import Field as FormField
from pydantic_schemaforms.schema_form import FormModel


class Color(str, Enum):
    red = 'red'
    blue = 'blue'
    green = 'green'


class ContactImport(DataTableLayout):
    name: str
    address: str
    favorite_color: Color = FormField(Color.red, input_type='select')

    model_config = {'buttons': ['csv', 'copy'], 'search': True, 'csv_template': True}


class PlainImport(DataTableLayout):
    name: str
    address: str


def _page_for(model_cls: type[DataTableLayout]) -> type[FormModel]:
    """A minimal FormModel embedding model_cls as its one layout field --
    the only way a DataTableLayout subclass renders now."""

    class _Page(FormModel):
        contacts: Any = FormField(
            default_factory=dict, title='Contacts', input_type='layout', layout_handler='datatable'
        )

    return _Page


def _render(
    model_cls: type[DataTableLayout],
    *,
    rows: list[dict[str, Any]] | None = None,
    row_errors: dict[int, dict[str, str]] | None = None,
    framework: str = 'bootstrap',
    include_assets: bool = True,
    table_id: str | None = None,
    submit_url: str = '/save',
    reviewing: bool = False,
    notice: str = '',
    discard_url: str | None = None,
) -> str:
    value = model_cls.as_layout_value(
        rows=rows,
        row_errors=row_errors,
        table_id=table_id,
        include_assets=include_assets,
        reviewing=reviewing,
        notice=notice,
        discard_url=discard_url,
    )
    # The recommended pairing (see DataTableLayout's module docstring): when
    # the model's own csv_upload is enabled, it renders its own Submit
    # button, so the embedding form must not render a second, redundant one.
    csv_upload_enabled = model_cls.datatable_options().get('csv_upload', True)
    return render_form_html(
        _page_for(model_cls),
        framework=framework,
        form_data={'contacts': value},
        submit_url=submit_url,
        include_submit_button=not csv_upload_enabled,
    )


def test_datatable_options_merge_model_config_over_defaults() -> None:
    options = ContactImport.datatable_options()
    assert options['buttons'] == ['csv', 'copy']
    assert options['search'] is True
    assert options['csv_template'] is True
    # unset keys fall back to defaults
    assert options['paging'] is True
    assert options['page_length'] == 10


def test_datatable_options_defaults_when_model_config_unset() -> None:
    options = PlainImport.datatable_options()
    assert options == {
        'buttons': [],
        'search': True,
        'paging': True,
        'page_length': 10,
        'length_menu': [10, 25, 50, 100],
        'csv_template': False,
        'csv_upload': True,
        'editable': True,
        'style': {'striped': False, 'bordered': False, 'hover': True, 'compact': False},
    }


def test_datatable_options_ignores_unrecognized_model_config_keys() -> None:
    class WithExtraKey(DataTableLayout):
        name: str
        model_config = {'search': False, 'totally_unrelated_pydantic_setting': 'x'}

    options = WithExtraKey.datatable_options()
    assert options['search'] is False
    assert 'totally_unrelated_pydantic_setting' not in options


def test_datatable_options_style_deep_merges_partial_overrides() -> None:
    class PartiallyStyled(DataTableLayout):
        name: str
        model_config = {'style': {'striped': True}}

    options = PartiallyStyled.datatable_options()
    # only 'striped' was overridden -- the other three flags keep their defaults
    assert options['style'] == {
        'striped': True,
        'bordered': False,
        'hover': True,
        'compact': False,
    }


def test_parse_csv_rows_valid() -> None:
    csv_bytes = b'name,address,favorite_color\nAlice,123 Main St,blue\nBob,456 Oak Ave,green\n'
    rows, errors = ContactImport.parse_csv_rows(csv_bytes)

    assert errors == []
    assert len(rows) == 2
    assert rows[0].name == 'Alice'
    assert rows[0].favorite_color == Color.blue
    assert rows[1].favorite_color == Color.green


def test_parse_csv_rows_reports_per_row_errors_without_dropping_valid_rows() -> None:
    csv_bytes = (
        b'name,address,favorite_color\n'
        b'Alice,123 Main St,blue\n'
        b'BadRow,789 Elm St,purple\n'
        b'Carol,1 First Ave,red\n'
    )
    rows, errors = ContactImport.parse_csv_rows(csv_bytes)

    assert len(rows) == 2
    assert {r.name for r in rows} == {'Alice', 'Carol'}

    assert len(errors) == 1
    assert errors[0].row_index == 1
    assert errors[0].raw['name'] == 'BadRow'
    assert 'favorite_color' in errors[0].errors


def test_parse_csv_rows_rejects_enum_value_that_only_differs_in_case() -> None:
    # A user typing the Title Case label ("Blue") instead of the lower-case
    # enum value ("blue") must fail validation, not silently coerce.
    csv_bytes = b'name,address,favorite_color\nAlice,123 Main St,Blue\n'
    rows, errors = ContactImport.parse_csv_rows(csv_bytes)
    assert rows == []
    assert len(errors) == 1
    assert 'favorite_color' in errors[0].errors


def test_csv_template_bytes_has_header_only() -> None:
    template = ContactImport.csv_template_bytes()
    lines = template.decode('utf-8').splitlines()
    assert lines == ['name,address,favorite_color']


def test_parse_submitted_rows_reconstructs_bracket_dot_keys() -> None:
    form_data = {
        'contacts.datatable_model': 'ContactImport',
        'contacts.rows[0].name': 'Alice',
        'contacts.rows[0].address': '123 Main St',
        'contacts.rows[0].favorite_color': 'blue',
        'contacts.rows[1].name': 'Bob',
        'contacts.rows[1].address': '456 Oak Ave',
        'contacts.rows[1].favorite_color': 'green',
    }
    rows, errors = ContactImport.parse_submitted_rows(form_data)
    assert errors == []
    assert [r.name for r in rows] == ['Alice', 'Bob']
    assert rows[0].favorite_color == Color.blue


def test_parse_submitted_rows_reports_per_row_errors() -> None:
    form_data = {
        'contacts.datatable_model': 'ContactImport',
        'contacts.rows[0].name': 'Alice',
        'contacts.rows[0].address': '123 Main St',
        'contacts.rows[0].favorite_color': 'not-a-real-color',
    }
    rows, errors = ContactImport.parse_submitted_rows(form_data)
    assert rows == []
    assert len(errors) == 1
    assert errors[0].row_index == 0
    assert 'favorite_color' in errors[0].errors


def test_read_only_cells_carry_a_hidden_input_so_saving_edits_does_not_lose_them() -> None:
    # A real browser submit only sends fields with a name= attribute. Only
    # favorite_color has one of its own (input_type='select'); name/address
    # are read-only display text with no <input> at all. Without a hidden
    # input carrying their current value forward too, saving *any* edit
    # would submit just {'favorite_color': ...} for every row, and
    # name/address (both required) would vanish -- failing every row's
    # validation and wiping the whole table on save.
    html_out = _render(
        ContactImport,
        rows=[{'name': 'Alice', 'address': '123 Main St', 'favorite_color': 'blue'}],
        include_assets=False,
    )
    assert '<input type="hidden" name="contacts.rows[0].name" value="Alice">' in html_out
    assert '<input type="hidden" name="contacts.rows[0].address" value="123 Main St">' in html_out

    # Simulate exactly what a browser sends: the select's own value plus
    # the hidden inputs -- must validate successfully, not fail on missing
    # name/address.
    submitted = {
        'contacts.rows[0].name': 'Alice',
        'contacts.rows[0].address': '123 Main St',
        'contacts.rows[0].favorite_color': 'green',  # the one "edited" field
    }
    rows, errors = ContactImport.parse_submitted_rows(
        {**submitted, 'contacts.datatable_model': 'ContactImport'}
    )
    assert errors == []
    assert rows[0].name == 'Alice'
    assert rows[0].favorite_color == Color.green


def test_as_layout_value_bundles_model_cls_and_rows() -> None:
    value = ContactImport.as_layout_value(rows=[{'name': 'Alice'}], table_id='custom_id')
    assert value['model_cls'] is ContactImport
    assert value['rows'] == [{'name': 'Alice'}]
    assert value['table_id'] == 'custom_id'


def test_default_table_id_comes_from_the_embedding_field_name() -> None:
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}], include_assets=False)
    assert '<table id="contacts_datatable"' in html_out


def test_render_form_raises_not_implemented() -> None:
    # DataTableLayout renders many rows, not one instance -- calling the
    # inherited FormModel.render_form() directly would silently produce
    # wrong/misleading output, so it's disabled with a clear pointer to
    # as_layout_value() instead.
    with pytest.raises(NotImplementedError, match='as_layout_value'):
        ContactImport.render_form(submit_url='/x')


def test_datatable_layout_is_still_a_form_model_subclass() -> None:
    assert issubclass(ContactImport, FormModel)
    assert ContactImport.__is_datatable_layout__ is True


def test_registered_renderer_ignores_render_contexts_error_and_required_fields() -> None:
    """RenderContext grew error/required_fields/child_errors fields so
    model_list's registered renderer could read its own field's error/
    required-ness/nested errors (see rendering/context.py). Datatable's own
    registered renderer never reads context.* at all, so populating those
    new fields must not change its output one bit."""
    from pydantic_schemaforms.rendering.datatable_renderer import render_datatable_layout_field
    from pydantic_schemaforms.rendering.layout_engine import LayoutEngine
    from pydantic_schemaforms.rendering.context import RenderContext

    value = ContactImport.as_layout_value(
        rows=[{'name': 'Alice', 'favorite_color': 'blue'}], include_assets=False
    )
    engine = LayoutEngine(renderer=None)

    bare_context = RenderContext(form_data={}, schema_defs={})
    enriched_context = RenderContext(
        form_data={},
        schema_defs={},
        error='unrelated error',
        required_fields=('some_other_field',),
        child_errors={'some_other_field': 'bad'},
    )

    bare_output = render_datatable_layout_field('contacts', {}, value, {}, bare_context, engine)
    enriched_output = render_datatable_layout_field(
        'contacts', {}, value, {}, enriched_context, engine
    )

    assert bare_output == enriched_output


# ---------------------------------------------------------------------------
# Rendering, via the layout_handler embedding path
# ---------------------------------------------------------------------------


def test_no_nested_forms_when_embedded_in_a_formmodel() -> None:
    # The whole point of this architecture: exactly one <form> wraps
    # everything (the embedding FormModel's own), opened before the table
    # and closed only at the very end (after its one submit button) --
    # never a second <form> nested inside it, which browsers would
    # silently break (a nested <form> tag is dropped by the HTML parser).
    html_out = _render(ContactImport, rows=[{'name': 'Alice', 'favorite_color': 'blue'}])
    assert html_out.count('<form') == 1
    assert html_out.count('</form>') == 1
    assert html_out.index('<form') < html_out.index('<table')
    assert html_out.index('<table') < html_out.index('</form>')


def test_render_emits_table_with_header_and_cells() -> None:
    html_out = _render(
        ContactImport,
        rows=[{'name': 'Alice', 'address': '123 Main St', 'favorite_color': 'blue'}],
        table_id='contactimport_datatable',
        include_assets=False,
    )
    assert '<table id="contactimport_datatable"' in html_out
    assert '<th>Name</th>' in html_out
    # Read-only cell: escaped display text plus a same-value hidden input
    # (see test_read_only_cells_carry_a_hidden_input... for why)
    assert '<td class="datatable-cell" title="">Alice<input type="hidden"' in html_out
    # Enum column was declared with input_type='select' -> real editable widget
    assert '<select name="contacts.rows[0].favorite_color"' in html_out
    assert 'option value="blue" selected' in html_out


def test_render_read_only_column_without_form_field() -> None:
    html_out = _render(
        PlainImport, rows=[{'name': 'Alice', 'address': '123 Main St'}], include_assets=False
    )
    assert '<td class="datatable-cell" title="">Alice<input type="hidden"' in html_out
    assert '<td class="datatable-cell" title="">123 Main St<input type="hidden"' in html_out


def test_render_marks_rows_with_errors() -> None:
    html_out = _render(
        ContactImport,
        rows=[{'name': 'BadRow', 'address': '789 Elm St', 'favorite_color': 'purple'}],
        row_errors={0: {'favorite_color': "Input should be 'red', 'blue' or 'green'"}},
        include_assets=False,
    )
    assert 'datatable-row-error' in html_out
    assert 'datatable-cell-error' in html_out
    # error rows must be visually distinguishable, not just class-tagged --
    # a bare class with no matching CSS rule looks identical to a valid row
    assert '.datatable-row-error' in html_out
    assert 'background-color' in html_out
    assert 'title="Input should be' in html_out


def test_render_escapes_untrusted_cell_values() -> None:
    html_out = _render(
        PlainImport,
        rows=[{'name': '<script>alert(1)</script>', 'address': 'x'}],
        include_assets=False,
    )
    assert '<script>alert(1)</script>' not in html_out
    assert '&lt;script&gt;' in html_out


def test_render_applies_style_classes_to_table() -> None:
    class StyledImport(DataTableLayout):
        name: str
        model_config = {'style': {'striped': True, 'bordered': True, 'compact': True}}

    html_out = _render(StyledImport, rows=[{'name': 'Alice'}], include_assets=False)
    assert (
        'class="table table-striped table-bordered table-hover table-sm datatable-table"'
        in html_out
    )


def test_render_style_classes_dropped_when_framework_none() -> None:
    class StyledImport(DataTableLayout):
        name: str
        model_config = {'style': {'striped': True, 'bordered': True}}

    html_out = _render(
        StyledImport, rows=[{'name': 'Alice'}], include_assets=False, framework='none'
    )
    assert 'class="datatable-table"' in html_out
    assert 'table-striped' not in html_out


def test_datatable_field_tracks_embedding_forms_framework() -> None:
    # The table's own styling must follow whatever framework the embedding
    # FormModel is rendered with -- read off the layout engine's active
    # renderer, not a separately-passed value, since there's no separate
    # render call to pass one to anymore.
    bootstrap_html = _render(
        ContactImport, rows=[{'name': 'Alice'}], include_assets=False, framework='bootstrap'
    )
    assert 'class="table table-hover datatable-table"' in bootstrap_html

    none_html = _render(
        ContactImport, rows=[{'name': 'Alice'}], include_assets=False, framework='none'
    )
    assert 'class="datatable-table"' in none_html
    assert 'class="table datatable-table"' not in none_html


def test_export_buttons_extract_live_control_value_not_option_text() -> None:
    # DataTables' default HTML5 export strips a cell's HTML tags, which for
    # a <select> concatenates every <option>'s label instead of reading the
    # selected value -- the init script must override this per export button.
    html_out = _render(
        ContactImport, rows=[{'name': 'Alice', 'address': '123 Main St', 'favorite_color': 'blue'}]
    )
    assert 'function _dtCellExportValue(node)' in html_out
    assert 'select.value' in html_out
    assert "extend: 'csvHtml5'" in html_out
    assert "extend: 'copyHtml5'" in html_out
    assert '_dtCellExportValue(node)' in html_out.split('dtConfig.buttons')[1]


def test_length_menu_defaults_and_includes_page_length() -> None:
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}])
    assert '"lengthMenu": [10, 25, 50, 100]' in html_out


def test_length_menu_custom_value_still_includes_page_length_default() -> None:
    class Custom(DataTableLayout):
        name: str
        model_config = {'length_menu': [5, 20], 'page_length': 5}

    html_out = _render(Custom, rows=[{'name': 'Alice'}])
    assert '"lengthMenu": [5, 20]' in html_out
    assert '"pageLength": 5' in html_out


def test_layout_includes_length_menu_control_even_with_buttons_enabled() -> None:
    # A legacy `dom` string of 'Bfrtip' would silently drop the 'l'
    # (length-menu / "entries per page") control whenever buttons were on --
    # the `layout` option keeps buttons and pageLength grouped together.
    html_out = _render(ContactImport, rows=[{'name': 'Alice'}])
    assert '"topStart": ["buttons", "pageLength"]' in html_out
    assert '"topEnd": "search"' in html_out
    assert '"bottomEnd": "paging"' in html_out


def test_layout_omits_length_menu_and_pagination_when_paging_disabled() -> None:
    class NoPaging(DataTableLayout):
        name: str
        model_config = {'paging': False}

    html_out = _render(NoPaging, rows=[{'name': 'Alice'}])
    assert '"topStart"' not in html_out
    assert '"bottomEnd"' not in html_out
    assert '"topEnd": "search"' in html_out
    assert '"bottomStart": "info"' in html_out


def test_init_script_stashes_datatable_instance_on_element() -> None:
    # Needed so a page embedding this table (e.g. inside a hidden Bootstrap
    # tab pane) can look up the live instance later and call
    # el.dtInstance.columns.adjust().draw(false) once it becomes visible --
    # DataTables can miscalculate column widths initializing on a
    # zero-width hidden element.
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}])
    assert 'el.dtInstance = new DataTable(el, dtConfig);' in html_out


def test_init_script_forces_all_rows_visible_before_submit() -> None:
    # Client-side paging detaches off-page rows' <input>s from the DOM, so a
    # native form submit would only serialize the currently displayed page --
    # e.g. selecting "10 rows per page" on a 10,000-row import would silently
    # submit only 10 rows. The init script must re-expand to all rows on the
    # enclosing form's submit event before the browser reads the fields.
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}])
    assert "el.closest('form')" in html_out
    assert "form.addEventListener('submit'" in html_out
    assert 'current.dtInstance.page.len(-1).draw(false);' in html_out


def test_scripts_run_immediately_if_dom_already_ready_not_only_on_domcontentloaded() -> None:
    # This script re-runs whenever the embedding page swaps/re-renders it,
    # long after 'DOMContentLoaded' already fired once -- a listener added
    # post-facto would never run again.
    html_out = _render(ContactImport, rows=[{'name': 'Alice'}])
    assert "document.readyState === 'loading'" in html_out


def test_pdf_button_not_implemented_surfaces_as_layout_error() -> None:
    # LayoutEngine._build_layout_body() catches exceptions raised by a
    # layout_handler and renders them inline (see _layout_error_message)
    # rather than letting them propagate -- so the NotImplementedError
    # this raises shows up as rendered error markup, not a raised exception.
    class WithPdf(DataTableLayout):
        name: str
        model_config = {'buttons': ['pdf']}

    html_out = _render(WithPdf, rows=[], include_assets=False)
    assert 'layout-field-error' in html_out
    assert 'pdfmake' in html_out


def test_datatable_assets_included_by_default() -> None:
    html_out = _render(PlainImport, rows=[])
    assert 'DataTable' in html_out


def test_datatable_assets_excluded_when_disabled() -> None:
    html_out = _render(PlainImport, rows=[], include_assets=False)
    assert 'DataTables 3.0.2' not in html_out


# ---------------------------------------------------------------------------
# Built-in CSV upload UI (model_config['csv_upload'], on by default)
# ---------------------------------------------------------------------------


def test_csv_upload_ui_included_by_default() -> None:
    # No separate file field, no hand-built button HTML -- the layout
    # field's own output already has everything a CSV-import page needs.
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}], include_assets=False)
    assert 'name="contacts.csv_file"' in html_out
    assert 'type="file"' in html_out
    assert '<button type="submit" name="contacts.datatable_action" value="load"' in html_out
    assert '>Load CSV<' in html_out
    assert '<button type="submit" name="contacts.datatable_action" value="submit"' in html_out


def test_csv_upload_ui_has_exactly_one_submit_and_one_load_button() -> None:
    # Recommended pairing (include_submit_button=False) must not leave a
    # redundant second "Submit"-labeled control from the embedding form.
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}], include_assets=False)
    assert html_out.count('name="contacts.datatable_action" value="load"') == 1
    assert html_out.count('name="contacts.datatable_action" value="submit"') == 1


def test_csv_upload_ui_sets_multipart_enctype_on_the_embedding_form() -> None:
    # The <input type="file"> here lives inside this layout field's own
    # rendered output, not as a literal field on the embedding FormModel --
    # the form's generic file-field scan can't see it from the schema
    # alone, so this regression-guards LayoutEngine's requires_multipart
    # hook (see rendering/layout_engine.py) actually firing. Without it, a
    # real browser submit would silently send only the chosen file's name,
    # never its contents, and "Load CSV"/"Reload CSV" would always look
    # like no file was chosen.
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}], include_assets=False)
    assert 'enctype="multipart/form-data"' in html_out


def test_csv_upload_ui_opt_out() -> None:
    class NoUpload(DataTableLayout):
        name: str
        model_config = {'csv_upload': False}

    html_out = _render(NoUpload, rows=[{'name': 'Alice'}], include_assets=False)
    assert 'name="contacts.csv_file"' not in html_out
    assert 'datatable_action' not in html_out
    # No file input anywhere -- multipart encoding would be pointless.
    assert 'enctype' not in html_out


# ---------------------------------------------------------------------------
# model_config['editable'] -- force cells read-only, drop Submit entirely
# ---------------------------------------------------------------------------


class NonEditableImport(DataTableLayout):
    name: str
    favorite_color: Color = FormField(Color.red, input_type='select')
    model_config = {'editable': False}


def test_editable_false_forces_cells_read_only_even_with_input_type() -> None:
    # favorite_color is declared input_type='select', but editable=False
    # must still force it to a read-only cell, same as a plain field.
    html_out = _render(
        NonEditableImport,
        rows=[{'name': 'Alice', 'favorite_color': 'blue'}],
        include_assets=False,
    )
    assert '<select name="contacts.rows[0].favorite_color"' not in html_out
    assert '<td class="datatable-cell" title="">blue<input type="hidden"' in html_out


def test_editable_false_drops_submit_button_keeps_only_reload() -> None:
    html_out = _render(NonEditableImport, rows=[{'name': 'Alice'}], include_assets=False)
    assert 'name="contacts.datatable_action" value="submit"' not in html_out
    assert '>Submit<' not in html_out
    assert 'name="contacts.datatable_action" value="reload"' in html_out
    assert '>Reload CSV<' in html_out


def test_editable_false_label_is_always_reload_even_before_any_load() -> None:
    # Unlike the editable=True case (which starts as "Load CSV" and only
    # relabels to "Reload CSV" after reviewing=True), editable=False always
    # says "Reload CSV" -- there's no separate review step to distinguish.
    html_out = _render(NonEditableImport, rows=[], include_assets=False)
    assert '>Load CSV<' not in html_out
    assert '>Reload CSV<' in html_out


@pytest.mark.asyncio
async def test_handle_import_post_editable_false_reload_commits_in_one_click() -> None:
    csv_bytes = b'name,favorite_color\nAlice,blue\nBadRow,purple\n'
    form_data = {
        'contacts.datatable_model': 'NonEditableImport',
        'contacts.csv_file': _FakeUpload(csv_bytes),
    }
    result = await NonEditableImport.handle_import_post(form_data)

    assert result.action == 'reload'
    assert [row['name'] for row in result.rows] == ['Alice', 'BadRow']
    assert result.has_errors
    assert 'favorite_color' in result.row_errors[1]


@pytest.mark.asyncio
async def test_handle_import_post_editable_false_with_no_file_returns_notice() -> None:
    result = await NonEditableImport.handle_import_post({})
    assert result.action == 'reload'
    assert result.rows == []
    assert 'Choose a CSV file' in result.notice


def test_reviewing_relabels_load_button_and_shows_banner() -> None:
    html_out = _render(PlainImport, rows=[{'name': 'Alice'}], include_assets=False, reviewing=True)
    assert '>Reload CSV<' in html_out
    assert 'Reviewing rows loaded from CSV' in html_out
    assert 'nothing is' in html_out


def test_reviewing_banner_includes_discard_link_when_given() -> None:
    html_out = _render(
        PlainImport,
        rows=[{'name': 'Alice'}],
        include_assets=False,
        reviewing=True,
        discard_url='/employees/import',
    )
    assert '<a href="/employees/import">discard and start over</a>' in html_out


def test_notice_banner_takes_priority_over_reviewing_banner() -> None:
    html_out = _render(
        PlainImport,
        rows=[],
        include_assets=False,
        reviewing=True,
        notice='Choose a CSV file first, then click "Load CSV".',
    )
    assert 'alert-warning' in html_out
    assert 'Choose a CSV file first' in html_out
    assert 'Reviewing rows loaded from CSV' not in html_out


# ---------------------------------------------------------------------------
# merge_rows() / handle_import_post()
# ---------------------------------------------------------------------------


def test_merge_rows_preserves_original_order_for_valid_and_invalid_rows() -> None:
    rows, row_errors = ContactImport.parse_csv_rows(
        b'name,address,favorite_color\n'
        b'Alice,123 Main St,blue\n'
        b'BadRow,789 Elm St,purple\n'
        b'Carol,1 First Ave,red\n'
    )
    merged = ContactImport.merge_rows(rows, row_errors)
    assert [row['name'] for row in merged] == ['Alice', 'BadRow', 'Carol']


class _FakeUpload:
    def __init__(self, data: bytes) -> None:
        self._data = data

    async def read(self) -> bytes:
        return self._data


@pytest.mark.asyncio
async def test_handle_import_post_load_parses_and_merges_csv() -> None:
    csv_bytes = b'name,address,favorite_color\nAlice,123 Main St,blue\nBadRow,789 Elm St,purple\n'
    form_data = {
        'contacts.datatable_model': 'ContactImport',
        'contacts.datatable_action': 'load',
        'contacts.csv_file': _FakeUpload(csv_bytes),
    }
    result = await ContactImport.handle_import_post(form_data)

    assert result.action == 'load'
    assert [row['name'] for row in result.rows] == ['Alice', 'BadRow']
    assert result.has_errors
    assert 'favorite_color' in result.row_errors[1]
    assert result.notice == ''


@pytest.mark.asyncio
async def test_handle_import_post_load_with_no_file_returns_notice() -> None:
    result = await ContactImport.handle_import_post(
        {'contacts.datatable_model': 'ContactImport', 'contacts.datatable_action': 'load'}
    )
    assert result.action == 'load'
    assert result.rows == []
    assert not result.has_errors
    assert 'Choose a CSV file' in result.notice


@pytest.mark.asyncio
async def test_handle_import_post_submit_parses_edited_cells() -> None:
    form_data = {
        'contacts.datatable_model': 'ContactImport',
        'contacts.datatable_action': 'submit',
        'contacts.rows[0].name': 'Alice',
        'contacts.rows[0].address': '123 Main St',
        'contacts.rows[0].favorite_color': 'green',
    }
    result = await ContactImport.handle_import_post(form_data)

    assert result.action == 'submit'
    assert not result.has_errors
    assert result.rows[0]['favorite_color'] == 'green'


@pytest.mark.asyncio
async def test_handle_import_post_defaults_to_submit_when_action_is_missing() -> None:
    # The embedding form's own plain submit button (used when csv_upload is
    # disabled) carries no datatable_action field at all -- must still save
    # rather than silently doing nothing.
    form_data = {
        'contacts.datatable_model': 'PlainImport',
        'contacts.rows[0].name': 'Alice',
        'contacts.rows[0].address': '123 Main St',
    }
    result = await PlainImport.handle_import_post(form_data)
    assert result.action == 'submit'
    assert result.rows[0]['name'] == 'Alice'


# ---------------------------------------------------------------------------
# Several tables on one page (#253)
# ---------------------------------------------------------------------------


class _TwoTablePage(FormModel):
    first: Any = FormField(
        default_factory=dict, title='First', input_type='layout', layout_handler='datatable'
    )
    second: Any = FormField(
        default_factory=dict, title='Second', input_type='layout', layout_handler='datatable'
    )


def _render_two(first_cls: type[DataTableLayout], second_cls: type[DataTableLayout]) -> str:
    return render_form_html(
        _TwoTablePage,
        form_data={
            'first': first_cls.as_layout_value(rows=[{'name': 'Alice'}], include_assets=False),
            'second': second_cls.as_layout_value(rows=[{'name': 'Bob'}], include_assets=False),
        },
        submit_url='/save',
        include_submit_button=False,
    )


def test_two_tables_on_one_page_get_distinct_names_and_ids() -> None:
    html_out = _render_two(PlainImport, PlainImport)
    for field in ('first', 'second'):
        assert f'<table id="{field}_datatable"' in html_out
        assert f'name="{field}.rows[0].name"' in html_out
        assert f'name="{field}.csv_file" id="{field}.csv_file"' in html_out
        assert f'<label for="{field}.csv_file"' in html_out
        assert f'name="{field}.datatable_action" value="load"' in html_out
    assert 'name="rows[' not in html_out
    assert 'name="csv_file"' not in html_out


def test_init_script_binds_submit_per_table_not_once_per_form() -> None:
    html_out = _render_two(PlainImport, PlainImport)
    assert 'form._dtSubmitBound[tableId]' in html_out
    assert 'var tableId = "first_datatable";' in html_out
    assert 'var tableId = "second_datatable";' in html_out


def _two_table_submission(first_model: str, second_model: str) -> dict[str, Any]:
    return {
        'first.datatable_model': first_model,
        'first.datatable_action': 'load',
        'first.csv_file': _FakeUpload(b'name,address\nCarol,1 First Ave\n'),
        'second.datatable_model': second_model,
        'second.rows[0].name': 'Bob',
        'second.rows[0].address': '456 Oak Ave',
    }


@pytest.mark.asyncio
async def test_handle_import_post_reads_only_its_own_table_by_field() -> None:
    form_data = _two_table_submission('PlainImport', 'PlainImport')

    first = await PlainImport.handle_import_post(form_data, field='first')
    second = await PlainImport.handle_import_post(form_data, field='second')

    assert first.action == 'load'
    assert [row['name'] for row in first.rows] == ['Carol']
    assert second.action == 'submit'
    assert [row['name'] for row in second.rows] == ['Bob']


@pytest.mark.asyncio
async def test_handle_import_post_finds_its_table_by_row_model_without_field() -> None:
    class OtherImport(DataTableLayout):
        name: str
        address: str

    form_data = _two_table_submission('PlainImport', 'OtherImport')

    first = await PlainImport.handle_import_post(form_data)
    second = await OtherImport.handle_import_post(form_data)

    assert [row['name'] for row in first.rows] == ['Carol']
    assert [row['name'] for row in second.rows] == ['Bob']


@pytest.mark.asyncio
async def test_handle_import_post_asks_for_field_when_same_model_appears_twice() -> None:
    form_data = _two_table_submission('PlainImport', 'PlainImport')
    with pytest.raises(ValueError, match='field='):
        await PlainImport.handle_import_post(form_data)


@pytest.mark.asyncio
async def test_handle_import_post_finds_a_table_inside_a_sub_form() -> None:
    form_data = {
        'section.contacts.datatable_model': 'PlainImport',
        'section.contacts.rows[0].name': 'Alice',
        'section.contacts.rows[0].address': '123 Main St',
    }
    result = await PlainImport.handle_import_post(form_data)
    assert [row['name'] for row in result.rows] == ['Alice']


def test_editable_cells_have_an_accessible_name() -> None:
    # The column header is a <th>, not a <label>, so each cell names itself.
    html_out = _render(
        ContactImport,
        rows=[{'name': 'Alice', 'address': '1 Main St', 'favorite_color': 'blue'}],
        include_assets=False,
    )
    assert 'name="contacts.rows[0].favorite_color"' in html_out
    assert 'aria-label="Favorite Color, row 1"' in html_out
