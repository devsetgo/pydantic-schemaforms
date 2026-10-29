# Data Tables (CSV Import)

`DataTableLayout` is a `FormModel` whose fields describe table columns
instead of one instance's inputs: fields declared with
`Field(..., input_type=...)` render as real, editable widgets per cell
(a dropdown for an `Enum`, etc.); plain fields render as read-only,
formatted text. The table is progressively enhanced client-side by a
vendored copy of [DataTables.js](https://datatables.net) (MIT-licensed, no
jQuery required) for search/sort/paging, plus optional `csv`/`copy` export
buttons. Since CSV import is what this class is *for*,
`model_config["csv_upload"]` defaults to `True`: the rendered table already
comes with a file input and "Load CSV"/"Submit" buttons built in — nobody
declares a separate file field or hand-builds that markup.

```python
from enum import Enum
from pydantic_schemaforms import DataTableLayout
from pydantic_schemaforms import Field

class Color(str, Enum):
    red = "red"
    blue = "blue"
    green = "green"

class ContactImport(DataTableLayout):
    name: str
    address: str
    favorite_color: Color = Field(Color.red, input_type="select")

    model_config = {"buttons": ["csv", "copy"], "search": True, "csv_template": True}
```

It is **not** rendered on its own — it's embedded as one *layout field* on
a plain `FormModel` (see [Plugin Hooks](plugin-hooks.md)), and rendered through the same
`render_form_html_async()` call every other form in this library uses.
That embedding `FormModel` needs nothing but the one field:

```python
from typing import Any
from pydantic_schemaforms import render_form_html_async
from pydantic_schemaforms import Field, FormModel

class ContactsPage(FormModel):
    rows: Any = Field(
        default_factory=dict, title="Contacts",
        input_type="layout", layout_handler="datatable",
    )

html = await render_form_html_async(
    ContactsPage,
    form_data={"rows": ContactImport.as_layout_value(rows=current_rows, row_errors=row_errors)},
    submit_url="/contacts/import",
    include_submit_button=False,  # ContactImport renders its own Submit -- see below
)
```

`layout_handler="datatable"` is registered automatically the moment you
import anything from `pydantic_schemaforms.datatable_layout` — no manual
registration step needed. The embedding `FormModel`'s framework
(`bootstrap`/`material`/`none`), `debug`, and `show_timing` all apply to the
table automatically — there's nothing DataTableLayout-specific to configure
for those; they're just `render_form_html_async()`'s own parameters, same
as any other form.

## Why `include_submit_button=False`?

Because `csv_upload` is on, `ContactImport`'s own rendered output already
includes a "Submit" button right below the table — pass
`include_submit_button=False` so the embedding form doesn't *also* render
its own generic one, which would leave two redundant "Submit"-ish controls
on the page. This is safe without a nested `<form>`: a `<button
type="submit">`/`<input type="file">` living inside this field's own slot
still submits/attaches to whatever `<form>` the *embedding* FormModel
opened — only a `<form>` nested inside another `<form>` is silently
dropped by the browser's HTML parser, and DataTableLayout never renders
one of its own (calling `ContactImport.render_form()` directly raises
`NotImplementedError`, inherited from `CompositeLayoutModel` — see
[Plugin Hooks](plugin-hooks.md) if you're building a similar composite of your own).

If you don't want the built-in upload UI at all (e.g. a read-only display
table, or your own custom upload flow), set `"csv_upload": False` in
`model_config` — the embedding form's own default submit button then
becomes "Submit" for the table's own editable cells, exactly like any other
layout field.

## Load, review, then Submit — don't commit a CSV on one click

A single submit button that immediately saves whatever CSV you chose gives
you no chance to catch and fix bad rows (a typo'd address, an invalid
color) before they land in your database. So the built-in UI is **two**
buttons: "Load CSV" parses the chosen file and re-renders the table with
those rows *for review* — validation errors show up highlighted, nothing
is saved yet — and "Submit" saves whatever the table is currently showing.

`handle_import_post()` on the model itself replaces hand-rolled
load-vs-submit branching: it reads which button was clicked, parses
accordingly (`parse_csv_rows()` for "Load", `parse_submitted_rows()` for
"Submit" — the same default a plain fallback submit uses, so nothing is
silently ignored), and returns an `ImportResult` with rows/row_errors
already merged back into their original order (`merge_rows()` — an invalid
row keeps its raw, as-typed values instead of vanishing):

```python
form = await request.form()
result = await ContactImport.handle_import_post(form)

if result.action == "load":
    # Preview only -- nothing committed. Re-render with reviewing=True so
    # "Load CSV" relabels to "Reload CSV" and an info banner explains that.
    return render_page(rows=result.rows, row_errors=result.row_errors, reviewing=True, notice=result.notice)

save_to_database(result.rows)  # only "Submit" (result.action == "submit") ever gets here
if result.has_errors:
    return render_page(rows=result.rows, row_errors=result.row_errors)  # keep reviewing
return show_success_page(result.rows)
```

`handle_import_post()` reports what was actually submitted, with no opinion on whether an
empty result is meaningful — a `"submit"` with zero rows and no errors (e.g. Submit clicked
before any CSV was ever loaded) comes back looking like a valid, empty save. Decide for
yourself whether that's acceptable for your app; if not, check `not result.rows and not
result.has_errors` before calling `save_to_database()` and show a "nothing to submit" message
instead.

Several tables can share one page, even in one form: each table's cells,
file input and buttons are named under its own embedding field, so a
"Load CSV" click on one table leaves the others alone (they report
`"submit"` with their current rows). `handle_import_post()` finds its own
table on its own. Only when two tables use the *same* row model does it need
to be told which one to read, by the embedding field's name:

```python
class TeamTransferForm(FormModel):
    leaving: Any = Field(default_factory=dict, input_type="layout", layout_handler="datatable")
    joining: Any = Field(default_factory=dict, input_type="layout", layout_handler="datatable")

form = await request.form(max_fields=200_000)
leaving = await EmployeeImport.handle_import_post(form, field="leaving")
joining = await EmployeeImport.handle_import_post(form, field="joining")
```

Pass `include_assets=False` to every table's `as_layout_value()` but the
first, so the DataTables scripts load once. The example app's
`/employees/teams` page runs this end to end.

Every cell renders as its own named `<input>` (read-only columns get a
hidden one too, see below), so a submit's field count is *rows times
columns*, not row count. Starlette/FastAPI's `Request.form()` rejects a
request over its default `max_fields=1000` with a 400 ("Too many fields") —
a plain 5-column table already exceeds that at 200 rows. Size a higher
`max_fields` to your largest expected import: `await
request.form(max_fields=200_000)`.

No server-side "staging" storage is needed to connect Load and Submit: the
rows a CSV load rendered for review are already sitting in the table's own
form fields (both the editable cells and the read-only cells' hidden
inputs — see below), so whatever the browser submits on the *next* click
already reflects any hand-fixes made in between.

Every read-only column also carries forward a hidden input with its
current value, alongside its escaped display text — without that, a real
browser submit would only include genuinely-editable cells' own inputs,
and any read-only *required* field (like `name` above) would vanish from
the submission and fail that row's validation on every save.

`as_layout_value()`'s `reviewing`/`notice`/`discard_url` parameters only
affect the built-in upload UI: `reviewing=True` relabels the button and
shows the info banner described above; `notice=` shows a one-off warning
banner instead (`handle_import_post()` returns one in `result.notice` when
"Load" is clicked with no file chosen); `discard_url=` adds a "discard and
start over" link to the reviewing banner.

## `model_config` keys

Recognized by `DataTableLayout` (any other key is ignored — pydantic does
not reject unknown `model_config` keys at runtime):

| Key | Default | Meaning |
|---|---|---|
| `buttons` | `[]` | Export buttons: `"csv"`, `"copy"`. `"pdf"` is accepted but raises `NotImplementedError` at render time (pdfmake isn't vendored yet). |
| `search` | `True` | Show the DataTables search box. |
| `paging` | `True` | Enable client-side paging. |
| `page_length` | `10` | Default rows per page. Always included as a choice in the "entries per page" dropdown, even if not listed in `length_menu`. |
| `length_menu` | `[10, 25, 50, 100]` | Choices offered in the "entries per page" dropdown. |
| `csv_template` | `False` | Render a "Download CSV template" link above the table, as a `data:` URI built from `ContactImport.csv_template_bytes()` — no server route needed. |
| `csv_upload` | `True` | Render the built-in file input + "Load CSV"/"Submit" buttons described above. Set `False` for a bare table with no upload UI (see above). |
| `editable` | `True` | Whether cells declared with `Field(..., input_type=...)` actually render as editable widgets. Set `False` to force every cell read-only regardless of its own `input_type` — see below. |
| `style` | see below | Table-appearance flags (dict) — see next section. |

## `editable: False` — a bulk-replace-only table, no in-place edits

Set `model_config["editable"] = False` when the table should only ever be
replaced wholesale by re-uploading a CSV — every cell renders read-only no
matter what `input_type` a column declares, and the built-in UI drops
"Submit" entirely, leaving one "Reload CSV" button that both parses *and*
commits in a single click (`handle_import_post()` returns
`action="reload"`) — there's no separate review-then-Submit step to wait on
when nothing in the table can be hand-corrected anyway:

```python
class ReadOnlyImport(DataTableLayout):
    name: str
    favorite_color: Color = Field(Color.red, input_type="select")  # ignored -- always read-only

    model_config = {"editable": False}
```

```python
result = await ReadOnlyImport.handle_import_post(await request.form())
# result.action is always "reload" here -- treat it the same as "submit":
save_to_database(result.rows)
```

**Performance:** every editable cell (a column declared with `input_type=`,
with `editable` left at its default `True`) renders as a real `<select>`/
`<input>` widget, with no virtualization — row count drives DOM size
directly. Past roughly 100 rows this gets noticeably slower to render,
paginate, and submit than plain read-only cells (escaped text plus a
lightweight hidden input for round-tripping). For imports past that size,
prefer a read-only presentation — either `model_config["editable"] = False`
if a bulk-replace-only flow fits (above), or declare the columns without
`input_type` if you still want the normal Load-then-Submit review step, just
without any cell being hand-editable.

## Table appearance (`style`)

`model_config["style"]` maps to Bootstrap's own `table-*` utility classes.
It's a partial dict — any flag you omit keeps its default, so
`{"striped": True}` alone only changes striping and leaves the rest as-is:

| Style flag | Default | Bootstrap class added |
|---|---|---|
| `striped` | `False` | `table-striped` |
| `bordered` | `False` | `table-bordered` |
| `hover` | `True` | `table-hover` |
| `compact` | `False` | `table-sm` |

```python
model_config = {"style": {"striped": True, "bordered": True, "compact": True}}
```

These are Bootstrap-specific classes: they have no visible effect under
`framework="none"` (a deliberately bare table) and there's no dedicated
Material variant yet — `framework="material"` currently gets the same
Bootstrap-ish classes as `framework="bootstrap"`.

## Performance: large imports

> **Note:** imports over roughly 10,000 rows can feel slow. Rendering
> (not CSV parsing) dominates at that scale — every editable cell (any
> column declared with `Field(..., input_type=...)`) instantiates and
> renders its own input widget class, so cost scales with
> `rows × editable columns`, not just row count. Representative numbers
> from `tests/test_benchmarks.py` (one editable `select` column out of
> three, plain Bootstrap styling, buttons enabled), measured server-side
> only:
>
> | Rows | `parse_csv_rows` | table render |
> |---|---|---|
> | 10 | ~0.03 ms | ~0.2 ms |
> | 100 | ~0.3 ms | ~1.9 ms |
> | 1,000 | ~4 ms | ~21 ms |
> | 10,000 | ~45 ms | ~220 ms |
>
> That's server render time alone — a 10,000-row table is also several MB
> of HTML, and the *browser* then has to parse that markup, build
> 10,000+ DOM rows, and hand them to DataTables for client-side
> sort/search/paging, which is usually the slower part in practice. Run
> `pytest tests/test_benchmarks.py -k datatable` yourself to reproduce
> these numbers on your own hardware/model shape.
>
> If you regularly expect imports in this range: keep as many columns
> read-only (plain fields, no `Field(input_type=...)`) as your UI can
> tolerate — read-only cells are a cheap `str()`/escape, not a full widget
> render; and consider validating/importing in a background task instead
> of inline in the request/response cycle for the largest files.

## Complete example

A trimmed copy of `examples/datatable_import_example.py`. Notice how little of
it is about CSV import: no file field, no button HTML, no load-or-submit
branching and no merge logic. `EmployeeImport` and `handle_import_post()` do
all of that.

```python
--8<-- "docs_src/advanced/data_tables/fastapi_app.py"
```

The example app's `/employees/import` page runs it with sample CSV files of
10 to 10,000 rows, `/employees/directory` shows a read-only table, and
`/employees/teams` has two tables in one form.
