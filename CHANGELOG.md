# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

Versions follow **CalVer**: `YY.Quarter.Build` — e.g. `26.2.1` = year 2026, quarter 2, build 1.
Beta releases append `.beta` (e.g. `26.2.1.beta`); production releases have no suffix.

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

### <span style='color:blue'>Additional Work for Self-Contained</span> ([untagged-bfb3bb98aa31ca386d88](https://github.com/devsetgo/pydantic-schemaforms/releases/tag/untagged-bfb3bb98aa31ca386d88))

## Changes
## Features

- Fix of self-contained and documentation updates (#31) (@devsetgo)

## Bug Fixes

- Fix of self-contained and documentation updates (#31) (@devsetgo)
- deploy docs (#28) (@devsetgo)
- working on documentation flow bugs (#27) (@devsetgo)
- working on issue to fix publishing failure (#26) (@devsetgo)

## Contributors
@devsetgo


Published Date: 2026 January 18, 13:57

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

