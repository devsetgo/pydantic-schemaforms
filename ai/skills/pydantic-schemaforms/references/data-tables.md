# Data tables reference

`DataTableLayout` imports a CSV file into an editable, validated table inside a form: file
upload, a review step, per-row errors, search, sorting and paging. Don't hand-build the upload
UI, per-row validation or load/submit branching.

## Complete example (FastAPI)

<!-- INCLUDE-CODE: docs_src/advanced/data_tables/fastapi_app.py -->

## Rules

- Subclass `DataTableLayout` with one field per table column. A column declared with
  `Field(..., input_type=...)` renders as a real editable widget per cell (e.g. a dropdown
  for an `Enum`); a plain field with no `input_type` renders as read-only, escaped text (still
  round-trips correctly on submit via a hidden input per cell).
- Embed it as a layout field on a plain `FormModel`: `Any = Field(default_factory=dict,
  input_type="layout", layout_handler="datatable")`, built via
  `YourImportModel.as_layout_value(rows=..., row_errors=...)`. Pass
  `include_submit_button=False` to `render_form_html_async()` — the rendered field already
  includes its own file input and "Load CSV"/"Submit" buttons when `model_config["csv_upload"]`
  is on (the default).
- Table behaviour is `model_config` on the `DataTableLayout` subclass: `csv_upload` (default
  `True`; `False` drops the file input and Load/Submit buttons for a browse-only table),
  `editable` (default `True`; see the `"reload"` action below), `search` (`True`), `paging`
  (`True`), `page_length` (`10`), `length_menu` (`[10, 25, 50, 100]`), `buttons` (`[]`;
  `"csv"` and `"copy"` add export buttons, `"pdf"` is accepted but raises `NotImplementedError`), `csv_template` (`False`;
  `True` links a downloadable header-only CSV), and `style` (`{"striped", "bordered", "hover",
  "compact"}` booleans). Per-row errors are `dict[int, dict[str, str]]` (row index →
  field → message), the shape `ImportResult.row_errors` and `as_layout_value(row_errors=...)`
  share; `RowError(row_index, errors, raw)` is the per-row record `parse_submitted_rows()`
  returns.
- `as_layout_value()`'s full signature is `as_layout_value(rows=None, row_errors=None, *,
  table_id=None, asset_mode="vendored", include_assets=True, reviewing=False, notice="",
  discard_url=None)`. The keyword-only ones control the built-in review UI specifically: pass
  `reviewing=True` after a "Load CSV" click so the button relabels to "Reload CSV" and an info
  banner explains nothing is saved yet; `notice=` shows a one-off warning banner (e.g. "Choose a
  CSV file first"); `discard_url=` adds a "discard and start over" link. `table_id` defaults to
  one derived from the embedding field's name, so you rarely need it.
- Several `DataTableLayout` fields can share one page or form: each table's inputs and buttons
  are namespaced by its own field, so loading a CSV into one leaves the others alone. If two of
  them use the *same* row model, pass the embedding field's name to tell them apart:
  `await EmployeeImport.handle_import_post(form, field="joining")` (same `field=` on
  `parse_submitted_rows()`). With one table per row model, leave `field` out.
- On POST, call `await YourImportModel.handle_import_post(await request.form(max_fields=...))`
  instead of hand-rolling load-vs-submit branching — it parses/validates, merges rows back into
  their original order (an invalid row keeps its raw values instead of vanishing), and returns
  an `ImportResult` with `action: Literal["load", "submit", "reload"]`. Handle it as: `"load"` —
  preview only, nothing committed, re-render with `reviewing=True`; `"submit"` — a normal
  Load-then-Submit commit; `"reload"` — commit exactly like `"submit"` (this is the action
  `model_config["editable"] = False` tables always return instead of `"submit"`, since there's no
  separate review step for them — see the performance note below). **Branching on only `"load"`
  vs `"submit"` and ignoring `"reload"` means an `editable=False` table's imports silently never
  get committed.**
- `handle_import_post()` is `async def`-only (it awaits the uploaded file's `.read()`), which
  assumes a Starlette/FastAPI-style async `UploadFile`. **It does not work unmodified on Flask**
  (WSGI, sync) — Flask's uploaded file is a sync `FileStorage` whose `.read()` is
  not awaitable. `DataTableLayout` is a FastAPI/Starlette-oriented feature; for a Flask app that
  needs CSV import, either run it under an ASGI adapter or handle the CSV upload/parsing
  yourself with `DataTableLayout.parse_csv_rows(raw_bytes)` (sync, safe to call directly) instead
  of `handle_import_post()`.
- Pass a real `max_fields` to `request.form()` — every cell is its own named form field, so
  field count is rows × columns, not row count; Starlette/FastAPI's default `max_fields=1000`
  rejects a plain 5-column table past ~200 rows.
- Treat a `result.action == "submit"` with zero rows and no errors as "nothing to submit," not
  as a successful save of an empty table — `handle_import_post()` reports what was submitted
  faithfully; deciding whether an empty result is meaningful is the app's job.
- Past roughly 100 rows, editable per-cell widgets (real `<select>`/`<input>` per cell, no
  virtualization) get noticeably slower to render/submit than read-only cells. For larger
  imports, prefer declaring columns without `input_type` (keeps the Load-then-Submit review
  step, just with no cell hand-editable), or `model_config["editable"] = False` for a
  bulk-replace-only table with no review step at all (single "Reload CSV" button that parses
  and commits in one click — see the `"reload"` action above).

A different kind of composite control (not a table): see the extending reference.
