# Roadmap

The order to work through open enhancements and known bugs. Work top to bottom:
each phase sets up the ones after it. GitHub issues hold the design detail for
each item. This file only sets the order and says why.

Every item follows the "Examples must cover every layout, input, and
validation" rule in `CLAUDE.md`: a feature isn't done until it's demonstrated
on an example page under both Bootstrap and Material.

Last updated: 2026-10-28.

## Phase 1: Clear the ground

Small fixes and decisions that the later phases build on. Do these first so new
features aren't layered on known bugs. Phase 1 ships as its own release.

| # | Item | Why now |
|---|---|---|
| 1 | [#252](https://github.com/devsetgo/pydantic-schemaforms/issues/252) Fix fixed element IDs in tabbed and accordion layouts | Two grouped forms on one page collide. Conditional fields (#237) and field groups (#241) both change the layout engine, so fix this before they land. Copy the wizard's ID-free, data-attribute approach. |
| 2 | [#253](https://github.com/devsetgo/pydantic-schemaforms/issues/253) Fix two DataTables on one page colliding | Cell and control names are fixed (`rows[i].col`, `csv_file`). Derive them from the embedding field's name. Small and self-contained. |
| 3 | [#254](https://github.com/devsetgo/pydantic-schemaforms/issues/254) Remove or wire up `@form_validator` | It's a top-level export that does nothing, so decorated checks never run. Removing it is breaking, so batch it with item 4 (#255) into one breaking release. |
| 4 | [#255](https://github.com/devsetgo/pydantic-schemaforms/issues/255) Decide on `FormBuilder` and the prebuilt login, registration and contact forms (left open from #248) | #248 closed when the React/Vue removal merged, but this half was never decided. The answer shapes #235 and #190: keep and document them as the "form without a model" path, or remove them and let JSON Schema import fill that role. |
| 5 | [#246](https://github.com/devsetgo/pydantic-schemaforms/issues/246) Accessibility gate with axe-core | Low effort. Landing it before the new widgets in phases 2 and 3 means each one is checked as it's built instead of fixed later. |
| 6 | [#147](https://github.com/devsetgo/pydantic-schemaforms/issues/147) Replace MkDocs Material | MkDocs 2.0 breaks MkDocs Material. Research only for now: pick a replacement before it blocks a docs deploy. Migrate when the choice is clear. |
| 7 | [#258](https://github.com/devsetgo/pydantic-schemaforms/issues/258) Reorganize the documentation | Do it with #147 or straight after it, so the new navigation is built once in the new tool. Content work (merging duplicate pages, shortening the README) can start before the tool is chosen. Docs aren't part of the package, so this doesn't hold up the phase 1 library release. |

## Phase 2: Core form features

How phase 2 and later phases are grouped into releases is not decided yet.

The features people ask for most. Each one builds on the layout engine and the
wizard that shipped in 26.4.1.

| # | Item | Why in this order |
|---|---|---|
| 8 | [#237](https://github.com/devsetgo/pydantic-schemaforms/issues/237) Conditional show/hide rules | The most common missing form feature. Needs the ID fix from phase 1. |
| 9 | [#241](https://github.com/devsetgo/pydantic-schemaforms/issues/241) Field groups and grid widths in one model | Next layout change after #237, so show/hide rules can target a whole group. |
| 10 | [#238](https://github.com/devsetgo/pydantic-schemaforms/issues/238) Read-only display mode | Supplies the display templates the wizard review step (#250) needs, and replaces the f-string confirmation pages users write today, which is an XSS risk. Must handle groups from #241. |
| 11 | [#250](https://github.com/devsetgo/pydantic-schemaforms/issues/250) Wizard review step | Adds an opt-in final wizard step that shows everything entered before Submit, for example a job application. Builds on #238: reuse its per-input display formatting and escaping rather than writing a second set. Ships with a job-application wizard example. |
| 12 | [#243](https://github.com/devsetgo/pydantic-schemaforms/issues/243) Draft autosave and unsaved-changes warning | Small vanilla-JS feature. Most useful once long forms and the wizard have conditional fields and groups. |
| 13 | [#245](https://github.com/devsetgo/pydantic-schemaforms/issues/245) Testing helpers for app authors | Comes after the phase 2 features so the submission builders handle conditional fields, groups and display mode from the start. |

## Phase 3: Inputs and data

New widgets and the server work behind them. All of them get checked by the
accessibility gate from phase 1.

| # | Item | Why in this order |
|---|---|---|
| 14 | [#178](https://github.com/devsetgo/pydantic-schemaforms/issues/178) Mobile-friendly inputs | Start by re-auditing the issue: some Tier 2 items have shipped since July. Then do the remaining Tier 2 and Tier 3 items that fit the vanilla-JS pattern: OTP code, segmented control, stepper buttons, password strength meter, year picker. Skip Tier 5. |
| 15 | [#242](https://github.com/devsetgo/pydantic-schemaforms/issues/242) Server-side upload validation and drag-and-drop | Covers the file drag-and-drop item from #178. The server half is bigger than the widget. |
| 16 | [#239](https://github.com/devsetgo/pydantic-schemaforms/issues/239) Remote options for select and combobox | Reuses the HTMX plumbing from live validation. Can move earlier if a user needs it. |

## Phase 4: Reach

Features that widen who can use the library. They come last because each one
touches every widget, so doing them after phases 2 and 3 means less retrofitting.

| # | Item | Why in this order |
|---|---|---|
| 17 | [#235](https://github.com/devsetgo/pydantic-schemaforms/issues/235) Build a FormModel from JSON Schema | The library-sized answer to [#190](https://github.com/devsetgo/pydantic-schemaforms/issues/190). Close #190 when this ships. Depends on the FormBuilder decision in item 4 (#255). |
| 18 | [#240](https://github.com/devsetgo/pydantic-schemaforms/issues/240) Internationalization | Wraps every library-generated string and display format. Doing it after the new widgets and display mode means doing it once. |
| 19 | [#247](https://github.com/devsetgo/pydantic-schemaforms/issues/247) CSS-variables theme and the Materialize decision | A new style multiplies the work for every widget, so add it once the widget set has settled. Decide Materialize's future at the same time. |
| 20 | [#244](https://github.com/devsetgo/pydantic-schemaforms/issues/244) Litestar and Django adapters | Independent of everything above and can be picked up any time, for example by an outside contributor. |

## Parked

| Item | Why parked |
|---|---|
| [#251](https://github.com/devsetgo/pydantic-schemaforms/issues/251) Dynamic step wizard (steps built from earlier answers, such as a car or product configurator or a BOM builder) | A complex addition that needs design before it's scheduled, and it's out of scope for the current wizard work. Revisit after #237, #238, #239 and #250 have shipped. It probably needs a wizard mode where the server keeps state between steps. |
| [#236](https://github.com/devsetgo/pydantic-schemaforms/issues/236) Form versioning with a migration chain | Wait until a real user asks. The library doesn't store data, so most of the value comes from a documented recipe. |

## Not planned

- **A visual drag-and-drop form builder.** It needs persistence, auth and a
  design surface, which makes it a product, not a library feature. JSON Schema
  import (#235) is the library's part of #190.
- **Tier 5 inputs from #178.** Map pickers, barcode scanners, camera
  recording, voice input, passkeys and hosted CAPTCHA all need external services
  or API keys.
