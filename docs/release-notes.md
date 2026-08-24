# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

Versions follow **CalVer**: `YY.Quarter.Build` — e.g. `26.2.1` = year 2026, quarter 2, build 1.
Beta releases append `.beta` (e.g. `26.2.1.beta`); production releases have no suffix.

## [26.2.3] — 2026-06-28

### Fixed

- **`LiveValidator.register_model_validator` partial-validation bug** — previously called
  `model_class.model_validate({field: value})` with only one field's data; if the model
  had other required fields, Pydantic raised `ValidationError` for them, causing all
  unrelated fields to produce `is_valid=False` with no errors even when the value was valid.
  Now uses `__pydantic_validator__.validate_assignment(model_construct(), field_name, value)`
  to validate each field in isolation, independent of sibling required fields.

- **`LiveValidator.render_field_with_live_validation` single-trigger limitation** — the
  `if/elif/elif` chain for `validate_on_blur` / `validate_on_input` / `validate_on_change`
  silently dropped every trigger after the first truthy one. Changed to independent `if`
  checks so all enabled triggers combine into a single `hx-trigger` attribute
  (e.g. `hx-trigger="blur, change"` when both are `True`).

### Added

- **Live-validation example** — `GET /live-validation` demo route in the FastAPI example
  app shows a contact form with per-field HTMX validation on blur. Includes
  `POST /validate/{field_name}` HTMX endpoint using `validation_response_headers()` and
  `GET /vendor/htmx.min.js` to serve the vendored HTMX asset.

---

## [26.2.2] — 2026-06-28

### Added

- **`FormModel.as_api_model()`** — new class method that returns a pure Pydantic `BaseModel`
  with `ui_*` rendering metadata stripped from `json_schema_extra`. Allows the same model
  class to serve both as an HTML form and as a typed FastAPI body / `response_model` without
  `ui_element`, `ui_placeholder`, etc. appearing in the OpenAPI/Swagger docs.
  `Field(title=...)`, `Field(examples=[...])`, descriptions, and all validation constraints
  (`min_length`, `ge`, `pattern`, …) are fully preserved. Result is cached per subclass and
  safe to assign at module level (`ContactSchema = ContactForm.as_api_model()`).

### Changed

- Reduced SonarCloud code smells: extracted duplicate magic strings to named constants,
  prefixed unused parameters with `_`, renamed methods that shadowed class attributes,
  and merged nested `if` statements into compound conditions across multiple modules.

---

## [26.2.1] — 2026-05-17

First production release. All public Quick Start code paths verified working end-to-end.

### Breaking Changes

- `submit_url` is now explicit across public form render APIs and no longer defaults silently.
  Calls that omit `submit_url` raise a clear `ValueError`, enforcing app-owned routing boundaries.

### Added

- **HTMX live validation** — `LiveValidator`, `HTMXValidationConfig`, and `validation_response_headers()`
  provide server-side field validation triggered by blur/input events via HTMX without page reloads.
- **Branch coverage** — `branch = true` added to coverage configuration for deeper test quality.
- **HTML structural validation** — `tests/test_html_structural.py` validates tag balance across all
  frameworks and field types.
- **HTTP integration tests** — FastAPI `TestClient` and Flask `test_client` round-trip tests.
- **Property-based tests** — Hypothesis suite covering arbitrary field names, labels, and frameworks.
- **Performance benchmarks** — `pytest-benchmark` suite for small, medium, and large form rendering.
- **Playwright browser tests** — End-to-end HTMX validation tests against a live FastAPI server
  (`tests/playwright/`), running in CI on Chromium.
- **macOS in CI matrix** — Tests now run on ubuntu-latest, windows-latest, and macos-latest.
- `py.typed` marker for PEP 561 compatibility.
- Vendored assets (htmx, Bootstrap, Materialize, iMask) with sha256 manifest verification.
- `.gitattributes` forcing LF line endings on vendored assets for cross-platform checksum stability.

### Fixed

- **`create_form_from_model` crashed with any Pydantic model** — `AutoFormBuilder._build_from_model`
  used the wrong parameter name (`default_value` instead of `value`) and compared against `...`
  instead of `PydanticUndefined`; the sentinel leaked into `json_schema_extra`, causing
  `PydanticSerializationError` on every render call.
- Windows path separator in test assertion caused CI failure on win32.
- Dependabot config used unsupported `interval: "cron"` — silently ignored, causing weekly runs.
  Replaced with `interval: "monthly"`.
- HTMX live validation JS used `JSON.parse(responseText)` on HTML responses; replaced with
  the idiomatic `HX-Trigger: validationResult` header pattern so CSS classes are applied correctly.
- `except A, B:` tuple syntax preserved via `# fmt: skip` to prevent ruff from removing parentheses
  that pyright requires.

### Changed

- Layout rendering internals refactored for maintainability and reduced cognitive complexity.
- Reliability and maintainability improvements to satisfy SonarCloud quality gate.
- Improved nested/collapsible form behavior when multiple forms are rendered on a page.
- Pre-commit ruff version pinned to match `requirements.txt` to eliminate local/CI formatting drift.
- Pyright added to `make tests` so type errors surface before commit.

### Dependencies

- `fastapi[all]`: `0.121.2` → `0.128.4`
- `ruff`: `0.14.14` → `0.15.0`
- `tqdm`: `4.67.1` → `4.67.3`
- `pytest-html`: `4.1.1` → `4.2.0`
- `packaging`: `25.0` → `26.0`
- `black`: `25.12.0` → `26.1.0`
- `mkdocstrings[python]`: `1.0.0` → `1.0.1`
- `pymdown-extensions`: `10.20` → `10.20.1`

## Latest Changes

#### Production Releases

### <span style='color:blue'>Bug Fix: CSV Import</span> ([26.3.5](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.5))

## Changes
## Bug Fixes

- Fix DataTableLayout to submit all pages during large data imports (#215) (@devsetgo)

## Documentation

- Fix DataTableLayout to submit all pages during large data imports (#215) (@devsetgo)

## Maintenance

- Fix DataTableLayout to submit all pages during large data imports (#215) (@devsetgo)

## Contributors
@devsetgo and @claude


Published Date: 2026 August 23, 20:54

### <span style='color:blue'>Enhancement: CSV Import</span> ([26.3.4](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.4))

## Changes
## Documentation

- Deep documentation pass across library, examples, and docs (#213) (@devsetgo)
- Add DataTableLayout composite control for CSV import to table (#212) (@devsetgo)
- Demo Application and MonoRepo (#207) (@devsetgo)

## Maintenance

- Bump of Version to 26.3.4 (#214) (@devsetgo)
- Deep documentation pass across library, examples, and docs (#213) (@devsetgo)
- Add DataTableLayout composite control for CSV import to table (#212) (@devsetgo)
- Demo Application and MonoRepo (#207) (@devsetgo)

## Contributors
@devsetgo and @claude


Published Date: 2026 August 23, 19:08

### <span style='color:blue'>Enhancements to JSON output and new input types</span> ([26.3.3](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.3))

## Changes
## Features

- Fix register\_input\_class registry and expand AI-assistant instructions (#202) (@devsetgo)

## Documentation

- Add code/data mode to TextArea: format + optional syntax highlighting (#205) (@devsetgo)
- Refactoring Live Validation to Simplify (#204) (@devsetgo)
- Add option for DNS and MX email deliverability validation (#203) (@devsetgo)
- Fix register\_input\_class registry and expand AI-assistant instructions (#202) (@devsetgo)
- 187 enhance date datetime and time (#192) (@devsetgo)
- 189 enhancement json schema model output (#191) (@devsetgo)
- Dev (#185) (@devsetgo)

## GitHub Actions

- Refactoring Live Validation to Simplify (#204) (@devsetgo)
- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.2.0 to 8.2.1 (#193) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/labeler from 6 to 7 (#194) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.5.1 to 7.7.0 (#195) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/setup-python from 6 to 7 (#196) (@[dependabot[bot]](https://github.com/apps/dependabot))
- Dev (#185) (@devsetgo)

## Maintenance

- Bump version to 26.3.3 (#206) (@devsetgo)
- Add code/data mode to TextArea: format + optional syntax highlighting (#205) (@devsetgo)
- Refactoring Live Validation to Simplify (#204) (@devsetgo)
- Add option for DNS and MX email deliverability validation (#203) (@devsetgo)
- Fix register\_input\_class registry and expand AI-assistant instructions (#202) (@devsetgo)
- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.2.0 to 8.2.1 (#193) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/labeler from 6 to 7 (#194) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.5.1 to 7.7.0 (#195) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/setup-python from 6 to 7 (#196) (@[dependabot[bot]](https://github.com/apps/dependabot))
- 187 enhance date datetime and time (#192) (@devsetgo)
- pip(deps): bump pymdown-extensions from 11.0 to 11.0.1 (#201) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump hatchling from 1.30.1 to 1.31.0 (#200) (@[dependabot[bot]](https://github.com/apps/dependabot))
- 189 enhancement json schema model output (#191) (@devsetgo)
- Dev (#185) (@devsetgo)

## Contributors
@devsetgo, [@dependabot[bot]](https://github.com/apps/dependabot) and @claude


Published Date: 2026 August 07, 21:33

### <span style='color:blue'>New Input Types and Bug Fixes</span> ([26.3.2](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.2))

## Changes
## Bug Fixes

- Feature: Fix ui\_element registry collisions; expand AI assistant docs with a verified example (#180) (@devsetgo)

## Documentation

- Dev (#183) (@devsetgo)
- Add Tier-2 input widgets and Widget Gallery example, fix Material bugs (#181) (@devsetgo)
- Feature: Fix ui\_element registry collisions; expand AI assistant docs with a verified example (#180) (@devsetgo)

## GitHub Actions

- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.1.0 to 8.2.0 (#172) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/checkout from 5 to 7 (#169) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.3.1 to 7.5.1 (#170) (@[dependabot[bot]](https://github.com/apps/dependabot))

## Maintenance

- Dev (#183) (@devsetgo)
- Dev (#182) (@devsetgo)
- Add Tier-2 input widgets and Widget Gallery example, fix Material bugs (#181) (@devsetgo)
- Feature: Fix ui\_element registry collisions; expand AI assistant docs with a verified example (#180) (@devsetgo)
- github-actions(deps): bump SonarSource/sonarqube-scan-action from 8.1.0 to 8.2.0 (#172) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest-asyncio from 1.3.0 to 1.4.0 (#173) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi from 0.138.1 to 0.139.0 (#171) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest from 9.0.3 to 9.1.1 (#174) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/checkout from 5 to 7 (#169) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 7.3.1 to 7.5.1 (#170) (@[dependabot[bot]](https://github.com/apps/dependabot))

## Contributors
@dependabot[bot], @devsetgo and [dependabot[bot]](https://github.com/apps/dependabot)


Published Date: 2026 July 19, 18:46

### <span style='color:blue'>America 250 Release: Adding AI Help Instructions and Clean Up.</span> ([26.3.1](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.3.1))

## Changes

Happy 250th Birthday USA!!!!

## Features

- Enhancement: Adding AI Helper Documentation (#177) (@devsetgo)
- Fix: Live Validation (#167) (@devsetgo)

## Bug Fixes

- Fix: Live Validation (#167) (@devsetgo)

## Documentation

- Enhancement: Adding AI Helper Documentation (#177) (@devsetgo)
- Documentation Fix (#168) (@devsetgo)
- Fix: Live Validation (#167) (@devsetgo)
- Production Release - Final Edits (#166) (@devsetgo)

## GitHub Actions

- Enhancement: Adding AI Helper Documentation (#177) (@devsetgo)
- Documentation Fix (#168) (@devsetgo)

## Maintenance

- Enhancement: Adding AI Helper Documentation (#177) (@devsetgo)
- Fix: Live Validation (#167) (@devsetgo)
- Production Release - Final Edits (#166) (@devsetgo)

## Contributors
@devsetgo


Published Date: 2026 July 03, 23:12

### <span style='color:blue'>Live Validation Fix, Example, and Doc Updates</span> ([26.2.4](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.2.4))

## Changes
## Features

- Fix: Live Validation (#167) (@devsetgo)

## Bug Fixes

- Fix: Live Validation (#167) (@devsetgo)

## Documentation

- Fix: Live Validation (#167) (@devsetgo)

## Maintenance

- Fix: Live Validation (#167) (@devsetgo)

## Contributors
@devsetgo


Published Date: 2026 June 28, 14:32

### <span style='color:blue'>CSRF Feature Release</span> ([26.2.1.beta](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.2.1.beta))

## Changes
- Documentation Updates (#116) (@devsetgo)

## Features

- bump to v26.2.1.beta (#117) (@devsetgo)
- CSRF Feature (#114) (@devsetgo)

## Maintenance

- feat(csrf): add CSRFMode enum with backward-compatible mode handling (#115) (@devsetgo)
- pip(deps): bump tox from 4.52.0 to 4.52.1 (#104) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump python-multipart from 0.0.24 to 0.0.26 (#106) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/upload-pages-artifact from 4 to 5 (#107) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mike from 2.1.4 to 2.2.0 (#108) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi from 0.134.0 to 0.135.3 (#97) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest-cov from 7.0.0 to 7.1.0 (#98) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pydantic-extra-types from 2.11.1 to 2.11.2 (#99) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump python-multipart from 0.0.22 to 0.0.24 (#100) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest from 9.0.1 to 9.0.3 (#101) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump actions/github-script from 7 to 9 (#102) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 6.2.0 to 7.2.0 (#103) (@[dependabot[bot]](https://github.com/apps/dependabot))
- dependency update and tests (#96) (@devsetgo)
- update of dependencies (#87) (@devsetgo)
- pip(deps): bump hatchling from 1.28.0 to 1.29.0 (#73) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump tox from 4.44.0 to 4.46.3 (#74) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi[all] from 0.128.4 to 0.134.0 (#75) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mkdocs-material from 9.7.2 to 9.7.3 (#76) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump ruff from 0.15.1 to 0.15.4 (#77) (@[dependabot[bot]](https://github.com/apps/dependabot))

## Contributors
@dependabot[bot], @devsetgo and [dependabot[bot]](https://github.com/apps/dependabot)


Published Date: 2026 April 26, 19:26

### <span style='color:blue'>Removing External Validation Logic</span> ([26.1.8.beta](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.8.beta))

## Changes
## Bug Fixes

- Removing validation logic outside of library. (#71) (@devsetgo)

## Contributors
@devsetgo


Published Date: 2026 February 27, 21:32

### <span style='color:blue'>Bug fix and cleanup.</span> ([26.1.7.beta](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.7.beta))

## Changes
- Move of examples (#69) (@devsetgo)

## Bug Fixes

- fix(layouts): validate nested layout submissions and restore Preferen… (#70) (@devsetgo)

## Contributors
@devsetgo


Published Date: 2026 February 22, 19:56

### <span style='color:blue'>Many fixes, enhancements, and increasing code coverage</span> ([26.1.6.beta](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.6.beta))

## Changes
- bumping version to 26.1.6.beta (#68) (@devsetgo)
- feat(examples,docs): add plain HTML style support and document render… (#67) (@devsetgo)
- improving documents (#59) (@devsetgo)
- improving test coverage (#58) (@devsetgo)
- improving reliability rating (#57) (@devsetgo)
- working on sonarcloud issue (#41) (@devsetgo)
- fixing examples (#33) (@devsetgo)

## Features

- working on example. (#65) (@devsetgo)
- Improvements - docs, examples, and bug fixes (#43) (@devsetgo)
- 34 add timing (#42) (@devsetgo)
- adding start line and end line for HTML sent to browser (#32) (@devsetgo)

## Bug Fixes

- working on material design render issues (#66) (@devsetgo)
- working on example. (#65) (@devsetgo)
- Improvements - docs, examples, and bug fixes (#43) (@devsetgo)

## Maintenance

- pip(deps): bump tox from 4.36.0 to 4.44.0 (#60) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mkdocs-material from 9.7.1 to 9.7.2 (#61) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump isort from 7.0.0 to 8.0.0 (#62) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump flask from 3.1.2 to 3.1.3 (#63) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump autoflake from 2.3.1 to 2.3.3 (#64) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pytest-html from 4.1.1 to 4.2.0 (#45) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump ruff from 0.14.14 to 0.15.0 (#44) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump tqdm from 4.67.1 to 4.67.3 (#47) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump fastapi[all] from 0.121.2 to 0.128.4 (#48) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump mkdocstrings[python] from 1.0.0 to 1.0.1 (#39) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump pymdown-extensions from 10.20 to 10.20.1 (#36) (@[dependabot[bot]](https://github.com/apps/dependabot))
- github-actions(deps): bump release-drafter/release-drafter from 6.1.0 to 6.2.0 (#35) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump black from 25.12.0 to 26.1.0 (#37) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump ruff from 0.14.11 to 0.14.14 (#38) (@[dependabot[bot]](https://github.com/apps/dependabot))
- pip(deps): bump packaging from 25.0 to 26.0 (#40) (@[dependabot[bot]](https://github.com/apps/dependabot))

## Contributors
@dependabot[bot], @devsetgo and [dependabot[bot]](https://github.com/apps/dependabot)


Published Date: 2026 February 22, 16:35

### <span style='color:blue'>Bug fixes and Improvements</span> ([26.1.2.beta](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.2.beta))

## Changes
- Publishing Improvements (#17) (@devsetgo)
- Doc (#16) (@devsetgo)
- GitHub Actions Improvements (#10) (@devsetgo)
- first release (#9) (@devsetgo)
- working on documentation (#5) (@devsetgo)
- working on coverage (#4) (@devsetgo)

## Features

- Improving Workflow (#1) (@devsetgo)

## Bug Fixes

- 18 bootstrap not included in self contained example (#24) (@devsetgo)
- Fix model-list delete for dynamically added items (#23) (@devsetgo)
- working on coverage issue (#3) (@devsetgo)
- working on publishing issue (#2) (@devsetgo)

## Maintenance

- github-actions(deps): bump actions/upload-pages-artifact from 3 to 4 (#19) (@[dependabot[bot]](https://github.com/apps/dependabot))
- updating release drafter (#11) (@devsetgo)
- Pre-Release Checks (#6) (@devsetgo)

## Contributors
@dependabot[bot], @devsetgo and [dependabot[bot]](https://github.com/apps/dependabot)


Published Date: 2026 January 09, 21:46


#### Pre-releases

### <span style='color:blue'>Initial Beta Release</span> ([26.1.1.beta](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/26.1.1.beta))

## Changes
- GitHub Actions Improvements (#10) (@devsetgo)
- first release (#9) (@devsetgo)
- working on documentation (#5) (@devsetgo)
- working on coverage (#4) (@devsetgo)

## Features

- Improving Workflow (#1) (@devsetgo)

## Bug Fixes

- working on coverage issue (#3) (@devsetgo)
- working on publishing issue (#2) (@devsetgo)

## Maintenance

- updating release drafter (#11) (@devsetgo)
- Pre-Release Checks (#6) (@devsetgo)

## Contributors
@devsetgo


Published Date: 2026 January 02, 19:13

