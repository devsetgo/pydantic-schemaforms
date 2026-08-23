"""DataTableLayout: a FormModel whose fields describe table columns instead
of a single instance's inputs, rendered as an HTML <table> (progressively
enhanced client-side by DataTables.js) via the *same* render_form_html()/
FormModel pipeline every other form in this library uses.

Each field on a ``DataTableLayout`` subclass is a table column. Fields
declared with ``FormField(..., input_type=...)`` render as real, editable
input widgets per cell (reusing the same ``inputs/`` registry normal forms
use); plain annotated fields render as read-only, formatted text.

A ``DataTableLayout`` subclass is embedded as one *layout field* on a plain
``FormModel`` (``input_type="layout", layout_handler="datatable"`` --
registered automatically at import time, see ``rendering/datatable_renderer.py``),
built via ``as_layout_value()``, exactly like any other layout field
(``docs/plugin_hooks.md``). It is not rendered through a separate bespoke
entry point -- the embedding FormModel's own ``render_form_html_async()``
call is all there is.

CSV import is what this class is *for*, so ``model_config['csv_upload']``
defaults to ``True``: the layout field's own rendered output already
includes a file input, a "Load CSV" button (parses the file and shows it in
the table for review -- nothing is saved yet), and a "Submit" button (saves
whatever the table currently shows). Nobody declares a separate file field,
hand-builds button HTML, or string-splices the rendered form -- the
embedding ``FormModel`` needs nothing but the one layout field. Because the
layout field renders its own "Submit", pass ``include_submit_button=False``
to ``render_form_html_async()`` so there isn't a second, redundant one from
the embedding form itself. Set ``csv_upload: False`` to opt out and get a
bare, no-upload-UI table instead (e.g. a read-only display table, or a
custom upload flow of your own) -- in that case the embedding form's own
default submit button *is* "Submit".

``model_config['editable']`` (default ``True``) controls whether cells
declared with ``FormField(..., input_type=...)`` actually render as
editable widgets. Set it ``False`` to force every cell read-only regardless
of a column's own ``input_type`` -- there's then nothing to "save" via
in-place edits, so the built-in UI drops the "Submit" button entirely and
keeps just one "Reload CSV" button, which parses *and* commits in a single
click (there's no separate review step to wait on a later Submit for; see
``handle_import_post()``'s ``action='reload'``).

On the server side, ``handle_import_post()`` replaces hand-rolled
load-vs-submit branching: it reads the submitted form data, figures out
which button was clicked, parses accordingly (``parse_csv_rows()`` for
"Load", ``parse_submitted_rows()`` for "Submit"), and returns rows merged
back into their original submitted order (see ``merge_rows()`` -- an
invalid row keeps its raw, as-typed values instead of vanishing). See
``docs/recipes.md`` for the full pattern and a complete example route.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal, TypedDict

from pydantic import ValidationError

from .composite_layout import CompositeLayoutModel

# Importing this registers the 'datatable' layout_handler (LayoutEngine
# .register_layout_renderer) as a side effect at import time -- without it,
# a field declared with layout_handler='datatable' would never find a
# renderer no matter how DataTableLayout itself gets used.
from .rendering import datatable_renderer as _datatable_renderer  # noqa: F401


class DataTableStyleConfig(TypedDict, total=False):
    """Bootstrap table-appearance flags -- see ``DataTableConfig['style']``.

    These map to Bootstrap's own ``table-*`` utility classes, so they have
    no visible effect when ``framework='none'`` (which renders no framework
    classes at all) and are not yet mapped for a dedicated Material variant.
    """

    striped: bool
    bordered: bool
    hover: bool
    compact: bool


class DataTableConfig(TypedDict, total=False):
    """Recognized ``model_config`` keys for a ``DataTableLayout`` subclass.

    Purely a typing aid for editor autocomplete -- ``model_config`` stays a
    plain dict at runtime (pydantic does not reject unrecognized keys), so
    unrecognized keys are simply ignored by ``DataTableLayout``.
    """

    buttons: list[Literal['csv', 'copy', 'pdf']]
    search: bool
    paging: bool
    page_length: int
    length_menu: list[int]
    csv_template: bool
    csv_upload: bool
    editable: bool
    style: DataTableStyleConfig


_DATATABLE_STYLE_DEFAULTS: dict[str, Any] = {
    'striped': False,
    'bordered': False,
    'hover': True,
    'compact': False,
}

_DATATABLE_DEFAULTS: dict[str, Any] = {
    'buttons': [],
    'search': True,
    'paging': True,
    'page_length': 10,
    'length_menu': [10, 25, 50, 100],
    'csv_template': False,
    'csv_upload': True,
    'editable': True,
    'style': dict(_DATATABLE_STYLE_DEFAULTS),
}


@dataclass
class RowError:
    """Per-row validation failure from ``DataTableLayout.parse_csv_rows``."""

    row_index: int
    errors: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    """What ``DataTableLayout.handle_import_post()`` figured out from one
    submitted request -- which button was clicked, and the rows/row_errors
    already merged back into their original order (``merge_rows()``), ready
    to pass straight to ``as_layout_value()`` for re-display, or to commit.

    ``action`` is ``'load'`` (preview only, nothing committed -- wait for a
    later ``'submit'``), ``'submit'`` (commit if not ``has_errors``), or
    ``'reload'`` (``model_config['editable'] = False`` only: there's no
    separate review step since cells aren't editable, so the one "Reload
    CSV" button both parses *and* commits in a single click -- treat it the
    same as ``'submit'``).
    """

    action: Literal['load', 'submit', 'reload']
    rows: list[dict[str, Any]]
    row_errors: dict[int, dict[str, str]]
    notice: str = ''

    @property
    def has_errors(self) -> bool:
        return bool(self.row_errors)


class DataTableLayout(CompositeLayoutModel):
    """FormModel whose fields are table columns instead of one instance's
    inputs -- embedded as a layout field on a plain FormModel, not rendered
    on its own. See the module docstring and ``docs/recipes.md``.

    Example::

        class FileImport(DataTableLayout):
            name: str
            address: str
            favorite_color: Color

            model_config = {
                "buttons": ["csv", "copy"],
                "search": True,
                "csv_template": True,
                "style": {"striped": True, "bordered": True},
            }

        class FileImportPage(FormModel):
            rows: Any = FormField(
                default_factory=dict, title="Contacts",
                input_type="layout", layout_handler="datatable",
            )

        html = await render_form_html_async(
            FileImportPage,
            form_data={"rows": FileImport.as_layout_value(rows=current_rows)},
            submit_url="/contacts/import",
            include_submit_button=False,  # the layout field renders its own Submit
        )

        # In the POST route:
        result = await FileImport.handle_import_post(await request.form())
        # result.action == "load": preview only, nothing committed yet.
        # result.action == "submit" and not result.has_errors: commit result.rows.
    """

    __is_datatable_layout__: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__is_datatable_layout__ = True

    @classmethod
    def datatable_options(cls) -> DataTableConfig:
        recognized = DataTableConfig.__annotations__.keys()
        merged: dict[str, Any] = dict(_DATATABLE_DEFAULTS)
        merged['style'] = dict(_DATATABLE_STYLE_DEFAULTS)

        raw_config = dict(cls.model_config) if cls.model_config else {}
        for key, value in raw_config.items():
            if key not in recognized:
                continue
            if key == 'style' and isinstance(value, dict):
                # Deep-merge so a subclass can override just one style flag
                # (e.g. only {"striped": True}) without repeating the rest.
                merged['style'] = {**merged['style'], **value}
            else:
                merged[key] = value

        return merged  # type: ignore[return-value]

    @classmethod
    def _validate_rows(
        cls, records: list[dict[str, Any]]
    ) -> tuple[list['DataTableLayout'], list[RowError]]:
        """Validate a list of row dicts independently -- one bad row does
        not prevent the rest from importing/saving."""
        rows: list[DataTableLayout] = []
        row_errors: list[RowError] = []

        for index, record in enumerate(records):
            try:
                rows.append(cls.model_validate(record))
            except ValidationError as exc:
                field_errors = {
                    '.'.join(str(part) for part in err['loc']): err['msg'] for err in exc.errors()
                }
                row_errors.append(RowError(row_index=index, errors=field_errors, raw=dict(record)))

        return rows, row_errors

    @classmethod
    def parse_csv_rows(
        cls, raw: bytes, *, encoding: str = 'utf-8'
    ) -> tuple[list['DataTableLayout'], list[RowError]]:
        """Parse+validate CSV bytes against this model's row schema.

        Column headers must match field names exactly.
        """
        text = raw.decode(encoding)
        reader = csv.DictReader(io.StringIO(text))
        return cls._validate_rows(list(reader))

    @classmethod
    def parse_submitted_rows(cls, form_data: Any) -> tuple[list['DataTableLayout'], list[RowError]]:
        """Validate edited cell values posted from the table's own
        ``submit_url`` form (see ``render_form(submit_url=...)``).

        Cells are named ``rows[i].field`` -- the same bracket+dot flat-key
        convention ``model_list`` fields already use -- so this reuses
        ``parse_nested_form_data`` to reconstruct them into per-row dicts
        before validating each one independently, same as
        ``parse_csv_rows``.
        """
        from .form_data import parse_nested_form_data

        nested = parse_nested_form_data(form_data)
        records = nested.get('rows') or []
        return cls._validate_rows(records)

    @classmethod
    def csv_template_bytes(cls) -> bytes:
        """Header-only CSV matching this model's field names, for a
        "Download CSV template" link (``model_config['csv_template']``)."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(list(cls.model_fields.keys()))
        return buffer.getvalue().encode('utf-8')

    @classmethod
    def merge_rows(
        cls, rows: list['DataTableLayout'], row_errors: list[RowError]
    ) -> list[dict[str, Any]]:
        """Reconstruct the original submitted/imported row order from
        (valid rows, row errors) -- an invalid row keeps its raw, as-typed
        values (instead of silently vanishing) so every row stays visible,
        flagged via row_errors."""
        errors_by_index = {err.row_index: err for err in row_errors}
        valid_rows = iter(row.model_dump(mode='json') for row in rows)
        return [
            errors_by_index[i].raw if i in errors_by_index else next(valid_rows)
            for i in range(len(rows) + len(row_errors))
        ]

    @classmethod
    async def _read_uploaded_csv(cls, form_data: Any) -> bytes:
        csv_upload = form_data.get('csv_file')
        return await csv_upload.read() if hasattr(csv_upload, 'read') else b''

    @classmethod
    async def handle_import_post(cls, form_data: Any) -> ImportResult:
        """Figure out which button was clicked (``datatable_action`` --
        emitted automatically by the layout field's own rendered controls
        when ``model_config['csv_upload']`` is enabled, see the module
        docstring) and parse accordingly.

        When ``model_config['editable']`` is False (cells aren't editable
        in place -- see the module docstring), there's only one button
        ("Reload CSV"), and it both parses *and* commits in a single click
        (``action='reload'``) since there's no separate review step to wait
        on a later "Submit" for.

        Otherwise:

        - "load": read the uploaded ``csv_file`` and validate it with
          ``parse_csv_rows()`` -- this never commits anything, it's just
          for review.
        - "submit" (also the default, so a plain fallback submit -- e.g. the
          embedding form's own button when ``csv_upload`` is disabled --
          still saves rather than silently doing nothing): validate the
          table's current cell values with ``parse_submitted_rows()``.

        Either way, rows/row_errors come back already merged into their
        original order via ``merge_rows()``, ready to pass straight to
        ``as_layout_value()`` for re-display.
        """
        if not cls.datatable_options().get('editable', True):
            raw = await cls._read_uploaded_csv(form_data)
            if not raw:
                return ImportResult(
                    action='reload',
                    rows=[],
                    row_errors={},
                    notice='Choose a CSV file first, then click "Reload CSV".',
                )
            rows, row_errors = cls.parse_csv_rows(raw)
            merged_rows = cls.merge_rows(rows, row_errors)
            row_errors_by_index = {err.row_index: err.errors for err in row_errors}
            return ImportResult(action='reload', rows=merged_rows, row_errors=row_errors_by_index)

        action = form_data.get('datatable_action') or 'submit'

        if action == 'load':
            raw = await cls._read_uploaded_csv(form_data)
            if not raw:
                return ImportResult(
                    action='load',
                    rows=[],
                    row_errors={},
                    notice='Choose a CSV file first, then click "Load CSV".',
                )
            rows, row_errors = cls.parse_csv_rows(raw)
        else:
            action = 'submit'
            rows, row_errors = cls.parse_submitted_rows(form_data)

        merged_rows = cls.merge_rows(rows, row_errors)
        row_errors_by_index = {err.row_index: err.errors for err in row_errors}
        return ImportResult(action=action, rows=merged_rows, row_errors=row_errors_by_index)

    @classmethod
    def as_layout_value(
        cls,
        rows: list[dict[str, Any]] | None = None,
        row_errors: dict[int, dict[str, str]] | None = None,
        *,
        table_id: str | None = None,
        asset_mode: str = 'vendored',
        include_assets: bool = True,
        reviewing: bool = False,
        notice: str = '',
        discard_url: str | None = None,
    ) -> dict[str, Any]:
        """Build the value for a layout field embedding this table
        (``input_type="layout", layout_handler="datatable"`` -- see the
        module docstring). Bundles this class alongside the current rows/
        row_errors so ``render_datatable_layout_field`` knows which row
        schema/columns to render.

        ``reviewing``/``notice``/``discard_url`` only affect the built-in
        upload UI (``model_config['csv_upload']``, on by default): pass
        ``reviewing=True`` after a "Load CSV" click (relabels the button
        "Reload CSV" and shows an info banner saying nothing's saved yet),
        ``notice=`` for a one-off message (e.g. "choose a file first" --
        see ``handle_import_post()``), and ``discard_url=`` to add a
        "discard and start over" link to the reviewing banner.
        """
        return {
            'model_cls': cls,
            'rows': rows,
            'row_errors': row_errors,
            'table_id': table_id or f'{cls.__name__.lower()}_datatable',
            'asset_mode': asset_mode,
            'include_assets': include_assets,
            'reviewing': reviewing,
            'notice': notice,
            'discard_url': discard_url,
        }
