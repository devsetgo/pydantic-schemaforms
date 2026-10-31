# Roadmap

The order to work through open enhancements and known bugs. Work top to bottom:
each phase sets up the ones after it. GitHub issues hold the design detail for
each item. This file only sets the order and says why.

Every item follows the "Examples must cover every layout, input, and
validation" rule in `CLAUDE.md`: a feature isn't done until it's demonstrated
on an example page under both Bootstrap and Material.

Last updated: 2026-10-29.

## Phase 1: Clear the ground

Small fixes and decisions that the later phases build on. Do these first so new
features aren't layered on known bugs. Phase 1 ships as its own release.

All phase 1 items are done; they ship as release 26.4.3.

| # | Item | Status | Why now |
|---|---|---|---|
| 1 | [#252](https://github.com/devsetgo/pydantic-schemaforms/issues/252) Fix fixed element IDs in tabbed and accordion layouts | Done ([#257](https://github.com/devsetgo/pydantic-schemaforms/pull/257)) | Two grouped forms on one page collide. Conditional fields (#237) and field groups (#241) both change the layout engine, so fix this before they land. Copy the wizard's ID-free, data-attribute approach. |
| 2 | [#253](https://github.com/devsetgo/pydantic-schemaforms/issues/253) Fix two DataTables on one page colliding | Done ([#260](https://github.com/devsetgo/pydantic-schemaforms/pull/260)) | Cell and control names are fixed (`rows[i].col`, `csv_file`). Derive them from the embedding field's name. Small and self-contained. |
| 3 | [#254](https://github.com/devsetgo/pydantic-schemaforms/issues/254) Remove or wire up `@form_validator` | Done ([#261](https://github.com/devsetgo/pydantic-schemaforms/pull/261)) | It's a top-level export that does nothing, so decorated checks never run. Removing it is breaking, so batch it with item 4 (#255) into one breaking release. |
| 4 | [#255](https://github.com/devsetgo/pydantic-schemaforms/issues/255) Decide on `FormBuilder` and the prebuilt login, registration and contact forms (left open from #248) | Done ([#261](https://github.com/devsetgo/pydantic-schemaforms/pull/261)) | #248 closed when the React/Vue removal merged, but this half was never decided. The answer shapes #235 and #190: keep and document them as the "form without a model" path, or remove them and let JSON Schema import fill that role. |
| 5 | [#246](https://github.com/devsetgo/pydantic-schemaforms/issues/246) Accessibility gate with axe-core | Done ([#262](https://github.com/devsetgo/pydantic-schemaforms/pull/262)) | Low effort. Landing it before the new widgets in phases 2 and 3 means each one is checked as it's built instead of fixed later. |
| 6 | [#264](https://github.com/devsetgo/pydantic-schemaforms/issues/264) Ship library skills ([library-skills.io](https://library-skills.io/)) inside the package | Done ([#269](https://github.com/devsetgo/pydantic-schemaforms/pull/269)) | Lets `uvx library-skills` install version-matched agent guidance from the installed package, so AI agents stop suggesting removed APIs. Five skills: build and fix forms, create, convert, upgrade and document. Ships with the phase 1 release, right after the breaking removals in #254 and #255. |
| 7 | [#258](https://github.com/devsetgo/pydantic-schemaforms/issues/258) Reorganize the documentation | Done ([#267](https://github.com/devsetgo/pydantic-schemaforms/pull/267)) | Do it with #147 or straight after it, so the new navigation is built once in the new tool. Content work (merging duplicate pages, shortening the README) can start before the tool is chosen. Docs aren't part of the package, so this doesn't hold up the phase 1 library release. |

## Phase 2: Core form features

How phase 2 and later phases are grouped into releases is not decided yet.

The features people ask for most. Each one builds on the layout engine and the
wizard that shipped in 26.4.1.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 8 | [#265](https://github.com/devsetgo/pydantic-schemaforms/issues/265) Rebuild the Material style on the shared rendering path | Done | Material renders through its own parallel code path, so every widget and fix is done twice and Material keeps lagging (the Enum, constraint and step bugs fixed for #258 were all Material-only or Material-too). Do it before the phase 2 features so conditional fields, groups and display mode are built once. Also removes the vendored Materialize files it no longer uses. |
| 9 | [#273](https://github.com/devsetgo/pydantic-schemaforms/issues/273) `Literal[True]` checkbox always fails validation | Not started | A bug: there's no straightforward way to require acceptance of terms. Small, stands alone, and #274's consent field needs it. |
| 10 | [#274](https://github.com/devsetgo/pydantic-schemaforms/issues/274) Content blocks and a consent field | Not started | Forms can't hold text that isn't a field. Comes before the other layout work because it changes what a form can contain. |
| 11 | [#237](https://github.com/devsetgo/pydantic-schemaforms/issues/237) Conditional show/hide rules | Not started | The most common missing form feature. Needs the ID fix from phase 1. |
| 12 | [#241](https://github.com/devsetgo/pydantic-schemaforms/issues/241) Field groups and grid widths in one model | Not started | Next layout change after #237, so show/hide rules can target a whole group. |
| 13 | [#238](https://github.com/devsetgo/pydantic-schemaforms/issues/238) Read-only display mode | Not started | Supplies the display templates the wizard review step (#250) needs, and replaces the f-string confirmation pages users write today, which is an XSS risk. Must handle groups from #241. |
| 14 | [#242](https://github.com/devsetgo/pydantic-schemaforms/issues/242) Server-side upload validation | Not started | Size, count and type checks on the server. Moved up from phase 3 because a resume upload in the job application example (#276) needs them, and before #275 so a step can upload a file on its own. |
| 15 | [#275](https://github.com/devsetgo/pydantic-schemaforms/issues/275) Opt-in step-by-step saving for the wizard | Not started | An option for each step to be validated and saved on the server. Before #250, whose review step would read saved data in this mode. |
| 16 | [#250](https://github.com/devsetgo/pydantic-schemaforms/issues/250) Wizard review step | Not started | Adds an opt-in final wizard step that shows everything entered before Submit, for example a job application. Builds on #238: reuse its per-input display formatting and escaping rather than writing a second set. Ships with a job-application wizard example. |
| 17 | [#243](https://github.com/devsetgo/pydantic-schemaforms/issues/243) Draft autosave and unsaved-changes warning | Not started | Small vanilla-JS feature. Most useful once long forms and the wizard have conditional fields and groups. |
| 18 | [#245](https://github.com/devsetgo/pydantic-schemaforms/issues/245) Testing helpers for app authors | Not started | Comes after the phase 2 features so the submission builders handle conditional fields, groups and display mode from the start. |
| 19 | [#276](https://github.com/devsetgo/pydantic-schemaforms/issues/276) Job application example | Not started | A realistic test of everything above, built up in stages as each dependency lands. Sign-in stays a separate page outside the wizard. |

## Phase 3: Inputs and data

New widgets and the server work behind them. All of them get checked by the
accessibility gate from phase 1.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 20 | [#178](https://github.com/devsetgo/pydantic-schemaforms/issues/178) Mobile-friendly inputs | Not started | Start by re-auditing the issue: some Tier 2 items have shipped since July. Then do the remaining Tier 2 and Tier 3 items that fit the vanilla-JS pattern: OTP code, segmented control, stepper buttons, password strength meter, year picker. Skip Tier 5. |
| 21 | [#239](https://github.com/devsetgo/pydantic-schemaforms/issues/239) Remote options for select and combobox | Not started | Reuses the HTMX plumbing from live validation. Can move earlier if a user needs it. |
| 22 | [#277](https://github.com/devsetgo/pydantic-schemaforms/issues/277) MD3 menu for select fields | Not started | Native selects open the browser's own menu, so only the closed field looks like MD3. Opt-in, with the native select as the fallback. |
| 23 | [#278](https://github.com/devsetgo/pydantic-schemaforms/issues/278) MD3 date and time picker | Not started | Same gap for date and time inputs, which open the browser's own picker. Opt-in, after #277 so both menus share their surface styling. |

## Phase 4: Reach

Features that widen who can use the library. They come last because each one
touches every widget, so doing them after phases 2 and 3 means less retrofitting.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 24 | [#235](https://github.com/devsetgo/pydantic-schemaforms/issues/235) Build a FormModel from JSON Schema | Not started | The library-sized answer to [#190](https://github.com/devsetgo/pydantic-schemaforms/issues/190). Close #190 when this ships. With `FormBuilder` removed (#255), this is the friendly way to build a form at runtime; until it ships, the `create_model(..., __base__=FormModel)` recipe in `docs/advanced/runtime-forms.md` covers it. |
| 25 | [#240](https://github.com/devsetgo/pydantic-schemaforms/issues/240) Internationalization | Not started | Wraps every library-generated string and display format. Doing it after the new widgets and display mode means doing it once. |
| 26 | [#266](https://github.com/devsetgo/pydantic-schemaforms/issues/266) Review other UI frameworks | Not started | Research only: pick which styles to add (for example Tailwind/daisyUI, Bulma, Pico) against criteria such as maintenance, licence and asset size. Feeds #247, so do it first. Adding a style is cheap only after #265 puts every style on one rendering path. |
| 27 | [#247](https://github.com/devsetgo/pydantic-schemaforms/issues/247) Color schemes and a framework-free CSS-variables theme | Not started | Named color schemes plus custom ones, covering light and dark, and a new style built on the same tokens. A new style multiplies the work for every widget, so do it once the widget set has settled. #265 has put every style on one rendering path, and #266 feeds which styles to add. |
| 28 | [#271](https://github.com/devsetgo/pydantic-schemaforms/issues/271) Toast notifications and other ways to show form feedback | Not started | Choices for how a form shows its errors and success messages, with today's summary as the default. After #247 so it uses the same color tokens, and after #240 so its messages can be translated. |
| 29 | [#244](https://github.com/devsetgo/pydantic-schemaforms/issues/244) Litestar and Django adapters | Not started | Independent of everything above and can be picked up any time, for example by an outside contributor. |

## Parked

| Item | Why parked |
|---|---|
| [#147](https://github.com/devsetgo/pydantic-schemaforms/issues/147) Replace MkDocs Material | Waiting on Zensical to leave alpha; migrate spring 2027, before MkDocs Material's end of life on 2027-05-05. Research is done: Zensical builds our `mkdocs.yml` as-is (tested), and a non-blocking CI job builds the docs with it on every PR. Docs aren't part of the package, so this doesn't hold up a release. |
| [#251](https://github.com/devsetgo/pydantic-schemaforms/issues/251) Dynamic step wizard (steps built from earlier answers, such as a car or product configurator or a BOM builder) | A complex addition that needs design before it's scheduled, and it's out of scope for the current wizard work. Revisit after #237, #238, #239 and #250 have shipped. It probably needs a wizard mode where the server keeps state between steps. |
| [#236](https://github.com/devsetgo/pydantic-schemaforms/issues/236) Form versioning with a migration chain | Wait until a real user asks. The library doesn't store data, so most of the value comes from a documented recipe. |
| [#279](https://github.com/devsetgo/pydantic-schemaforms/issues/279) Opt out of inlining Material CSS on every form | No place on the roadmap decided yet. |
| [#280](https://github.com/devsetgo/pydantic-schemaforms/issues/280) Remove the double `mb-3` on Bootstrap select fields | No place on the roadmap decided yet. |
| [#281](https://github.com/devsetgo/pydantic-schemaforms/issues/281) Retire the `FRAMEWORKS` config dict | No place on the roadmap decided yet. |

## Not planned

- **A visual drag-and-drop form builder.** It needs persistence, auth and a
  design surface, which makes it a product, not a library feature. JSON Schema
  import (#235) is the library's part of #190.
- **Tier 5 inputs from #178.** Map pickers, barcode scanners, camera
  recording, voice input, passkeys and hosted CAPTCHA all need external services
  or API keys.
