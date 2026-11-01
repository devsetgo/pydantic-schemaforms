# Roadmap

The order to work through open enhancements and known bugs. Work top to bottom:
each phase sets up the ones after it, and each ships as its own release. GitHub
issues hold the design detail for each item. This file only sets the order and
says why.

Every item follows the "Examples must cover every layout, input, and
validation" rule in `CLAUDE.md`: a feature isn't done until it's demonstrated
on an example page under both Bootstrap and Material.

Last updated: 2026-11-01.

## Phase 1: Clear the ground

Small fixes and decisions that the later phases build on. Do these first so new
features aren't layered on known bugs.

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

## Shipped in 26.4.4

| # | Item | Status | Why then |
|---|---|---|---|
| 8 | [#265](https://github.com/devsetgo/pydantic-schemaforms/issues/265) Rebuild the Material style on the shared rendering path | Done ([#272](https://github.com/devsetgo/pydantic-schemaforms/pull/272)) | Material renders through its own parallel code path, so every widget and fix is done twice and Material keeps lagging (the Enum, constraint and step bugs fixed for #258 were all Material-only or Material-too). Do it before the phase 2 features so conditional fields, groups and display mode are built once. Also removes the vendored Materialize files it no longer uses. |
| 9 | [#273](https://github.com/devsetgo/pydantic-schemaforms/issues/273) `Literal[True]` checkbox always fails validation | Done ([#283](https://github.com/devsetgo/pydantic-schemaforms/pull/283)) | A bug: there's no straightforward way to require acceptance of terms. Small, stands alone, and #274's consent field needs it. |

## Phase 2: Display-only content

Forms and pages gain content that isn't an input. Content blocks and display mode need the same new theme markup, so they're built together, after two small cleanups so that markup is added once.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 10 | [#280](https://github.com/devsetgo/pydantic-schemaforms/issues/280) Remove the double `mb-3` on Bootstrap select fields | Done ([#301](https://github.com/devsetgo/pydantic-schemaforms/pull/301)) | Small cleanup, so every field has the same spacing before new markup is added. |
| 11 | [#281](https://github.com/devsetgo/pydantic-schemaforms/issues/281) Retire the `FRAMEWORKS` config dict | Done ([#302](https://github.com/devsetgo/pydantic-schemaforms/pull/302)) | Moves each style's settings into its theme before this phase adds new theme hooks. Rendered output doesn't change. |
| 12 | [#274](https://github.com/devsetgo/pydantic-schemaforms/issues/274) Content blocks and a consent field | Done ([#303](https://github.com/devsetgo/pydantic-schemaforms/pull/303)) | Forms can't hold text that isn't a field. The consent field builds on #273. |
| 13 | [#238](https://github.com/devsetgo/pydantic-schemaforms/issues/238) Read-only display mode | Not started | Replaces the f-string confirmation pages users write today, which are an XSS risk, and supplies the display templates the wizard review step (#250) needs. Must decide how a content block from #274 appears in display mode. |

## Phase 3: Form structure

Both items change the layout engine, and both must work with the display mode from phase 2.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 14 | [#237](https://github.com/devsetgo/pydantic-schemaforms/issues/237) Conditional show/hide rules | Not started | The most common missing form feature. Fields hidden by a rule must also stay out of display mode (#238). |
| 15 | [#241](https://github.com/devsetgo/pydantic-schemaforms/issues/241) Field groups and grid widths in one model | Not started | After #237, so show/hide rules can target a whole group. Display mode (#238) must render groups as well. |

## Phase 4: Long forms and the wizard

Everything a long form needs, finished by a complete job application as a realistic test.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 16 | [#242](https://github.com/devsetgo/pydantic-schemaforms/issues/242) Server-side upload validation | Not started | Size, count and type checks on the server. Comes first because a resume upload in #276 needs them, and so a step in #275 can upload a file on its own. |
| 17 | [#275](https://github.com/devsetgo/pydantic-schemaforms/issues/275) Opt-in step-by-step saving for the wizard | Not started | An option for each step to be validated and saved on the server. Before #250, whose review step would read saved data in this mode. |
| 18 | [#250](https://github.com/devsetgo/pydantic-schemaforms/issues/250) Wizard review step | Not started | Adds an opt-in final wizard step that shows everything entered before Submit. Builds on #238: reuse its per-input display formatting and escaping rather than writing a second set. |
| 19 | [#295](https://github.com/devsetgo/pydantic-schemaforms/issues/295) Confirmation step before submit | Not started | Sits beside the review step as the other way to check before submitting. Reuses the existing modal code. |
| 20 | [#296](https://github.com/devsetgo/pydantic-schemaforms/issues/296) Form progress indicator | Not started | The count of completed fields depends on which fields #237 hides, and it must not compete with the wizard's step display. |
| 21 | [#243](https://github.com/devsetgo/pydantic-schemaforms/issues/243) Draft autosave and unsaved-changes warning | Not started | Small vanilla-JS feature. Most useful once long forms and the wizard have conditional fields and groups. |
| 22 | [#276](https://github.com/devsetgo/pydantic-schemaforms/issues/276) Job application example | Not started | A realistic test of everything above, built up in stages as each dependency lands. Sign-in stays a separate page outside the wizard. |

## Phase 5: New small inputs

Small, independent widgets that make a quick release. All of them get checked by the accessibility gate from phase 1.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 23 | [#291](https://github.com/devsetgo/pydantic-schemaforms/issues/291) One-time code (OTP) input | Not started | Common on sign-in and verification forms. |
| 24 | [#292](https://github.com/devsetgo/pydantic-schemaforms/issues/292) Password strength meter | Not started | The scoring rules already exist on the server, so this mostly adds the display. |
| 25 | [#293](https://github.com/devsetgo/pydantic-schemaforms/issues/293) Year picker | Not started | Small gap next to the existing month and week inputs. |
| 26 | [#294](https://github.com/devsetgo/pydantic-schemaforms/issues/294) E.164 phone numbers | Not started | Builds on the phone input's live formatting, and gives apps a consistent value to store. |

## Phase 6: Rich pickers

Custom option lists and pickers that replace the browser's own menus, sharing their surface styling.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 27 | [#239](https://github.com/devsetgo/pydantic-schemaforms/issues/239) Remote options for select and combobox | Not started | Reuses the HTMX plumbing from live validation. Can move earlier if a user needs it. |
| 28 | [#277](https://github.com/devsetgo/pydantic-schemaforms/issues/277) MD3 menu for select fields | Not started | Native selects open the browser's own menu, so only the closed field looks like MD3. Opt-in, with the native select as the fallback. |
| 29 | [#278](https://github.com/devsetgo/pydantic-schemaforms/issues/278) MD3 date and time picker | Not started | Same gap for date and time inputs. Opt-in, after #277 so both menus share their surface styling. |

## Phase 7: Look and feedback

How forms look and how they report back. A new style multiplies the work for every widget, so this comes once the widget set has settled.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 30 | [#266](https://github.com/devsetgo/pydantic-schemaforms/issues/266) Review other UI frameworks | Not started | Research only: pick which styles to add (for example Tailwind/daisyUI, Bulma, Pico) against criteria such as maintenance, licence and asset size. Feeds #247, so do it first. |
| 31 | [#247](https://github.com/devsetgo/pydantic-schemaforms/issues/247) Color schemes and a framework-free CSS-variables theme | Not started | Named color schemes plus custom ones, covering light and dark, and a new style built on the same tokens. |
| 32 | [#279](https://github.com/devsetgo/pydantic-schemaforms/issues/279) Opt out of inlining Material CSS on every form | Not started | Also about how Material's CSS reaches the page, so it's decided alongside the color work in #247. |
| 33 | [#271](https://github.com/devsetgo/pydantic-schemaforms/issues/271) Toast notifications and other ways to show form feedback | Not started | Choices for how a form shows its errors and success messages, with today's summary as the default. Before #240, so its messages are translated along with everything else. |

## Phase 8: Reach and developer tools

Features that widen who can use the library, once the features they have to cover exist.

| # | Item | Status | Why in this order |
|---|---|---|---|
| 34 | [#245](https://github.com/devsetgo/pydantic-schemaforms/issues/245) Testing helpers for app authors | Not started | After the new inputs and layout features, so the submission builders cover them from the start. |
| 35 | [#235](https://github.com/devsetgo/pydantic-schemaforms/issues/235) Build a FormModel from JSON Schema | Not started | The library-sized answer to [#190](https://github.com/devsetgo/pydantic-schemaforms/issues/190). With `FormBuilder` removed (#255), this is the friendly way to build a form at runtime; until it ships, the `create_model(..., __base__=FormModel)` recipe in `docs/advanced/runtime-forms.md` covers it. |
| 36 | [#244](https://github.com/devsetgo/pydantic-schemaforms/issues/244) Litestar and Django adapters | Not started | Independent of everything above and can be picked up any time, for example by an outside contributor. |
| 37 | [#240](https://github.com/devsetgo/pydantic-schemaforms/issues/240) Internationalization | Not started | Wraps every library-generated string and display format, so it comes last and is done once. |

## Parked

| Item | Why parked |
|---|---|
| [#147](https://github.com/devsetgo/pydantic-schemaforms/issues/147) Replace MkDocs Material | Waiting on Zensical to leave alpha; migrate spring 2027, before MkDocs Material's end of life on 2027-05-05. Research is done: Zensical builds our `mkdocs.yml` as-is (tested), and a non-blocking CI job builds the docs with it on every PR. Docs aren't part of the package, so this doesn't hold up a release. |
| [#251](https://github.com/devsetgo/pydantic-schemaforms/issues/251) Dynamic step wizard (steps built from earlier answers, such as a car or product configurator or a BOM builder) | A complex addition that needs design before it's scheduled, and it's out of scope for the current wizard work. Revisit after #237, #238, #239 and #250 have shipped. It probably needs a wizard mode where the server keeps state between steps. |
| [#236](https://github.com/devsetgo/pydantic-schemaforms/issues/236) Form versioning with a migration chain | Wait until a real user asks. The library doesn't store data, so most of the value comes from a documented recipe. |
| [#297](https://github.com/devsetgo/pydantic-schemaforms/issues/297) Drawing inputs: signature pad, drawing canvas and image annotation | No place on the roadmap decided yet. Stateful canvas work that needs an accessible alternative. |
| [#298](https://github.com/devsetgo/pydantic-schemaforms/issues/298) Rich content and structured choice inputs | A tracking issue with no place on the roadmap yet. Each input needs a design decision, especially whether it can stay dependency-free. |
| [#190](https://github.com/devsetgo/pydantic-schemaforms/issues/190) Form builder | A far-future idea that depends on the library gaining a larger user base. It may become part of the demo site (pydantic-schemaforms.devsetgo.com) or DevSetGo.com rather than the library, so it stays open after #235 ships. |

## Not planned

- **A visual drag-and-drop form builder.** It needs persistence, auth and a
  design surface, which makes it a product, not a library feature. JSON Schema
  import (#235) is the library's part of #190.
- **Tier 5 inputs from #178.** Map pickers, barcode scanners, camera
  recording, voice input, passkeys and hosted CAPTCHA all need external services
  or API keys.
