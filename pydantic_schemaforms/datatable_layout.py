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
entry point -- the embedding FormModel's own ``render_form_html()`` call and
its one submit button (which saves edits made in the table's own editable
cells; see ``parse_submitted_rows()``) are all there is. CSV upload is a
deliberately *separate*, small ``FormModel`` (a single file field) rather
than nested inside this one: browsers silently drop a ``<form>`` nested
inside another ``<form>``, and this table's own render sits inside whatever
``<form>`` the embedding FormModel provides. See ``docs/recipes.md`` for the
full pattern.
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
    'style': dict(_DATATABLE_STYLE_DEFAULTS),
}


@dataclass
class RowError:
    """Per-row validation failure from ``DataTableLayout.parse_csv_rows``."""

    row_index: int
    errors: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


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
            submit_url="/contacts/save",  # saves edits made in the table's own cells
        )
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
    def as_layout_value(
        cls,
        rows: list[dict[str, Any]] | None = None,
        row_errors: dict[int, dict[str, str]] | None = None,
        *,
        table_id: str | None = None,
        asset_mode: str = 'vendored',
        include_assets: bool = True,
    ) -> dict[str, Any]:
        """Build the value for a layout field embedding this table
        (``input_type="layout", layout_handler="datatable"`` -- see the
        module docstring). Bundles this class alongside the current rows/
        row_errors so ``render_datatable_layout_field`` knows which row
        schema/columns to render.
        """
        return {
            'model_cls': cls,
            'rows': rows,
            'row_errors': row_errors,
            'table_id': table_id or f'{cls.__name__.lower()}_datatable',
            'asset_mode': asset_mode,
            'include_assets': include_assets,
        }
