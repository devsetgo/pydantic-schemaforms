# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased (since untagged-bfb3bb98aa31ca386d88)

### Breaking Changes

- `submit_url` is now explicit across public form render APIs and no longer defaults silently.
- Calls that omit `submit_url` now raise a clear error, enforcing app-owned routing boundaries.

### Added

- Async-first rendering flow improvements and examples.
- FastAPI form/style GET+POST matrix testing to validate route and style combinations.
- Expanded coverage suites for renderer/input modules and validation pathways.

### Changed

- Layout rendering internals refactored for maintainability and reduced cognitive complexity.
- Reliability and maintainability improvements to satisfy SonarCloud findings.
- Improved nested/collapsible form behavior when multiple forms are rendered on a page.
- Better timing/logging support in examples and diagnostics.

### Fixed

- Removed implicit default submit target behavior (`/submit`) and aligned all call sites/tests.
- Fixed FastAPI showcase POST re-render path by passing explicit submit target in error flows.
- Fixed datetime/month/week conversion edge cases (`datetime` vs `date` branch ordering).
- Fixed model-list and nested rendering edge behavior across schema and runtime paths.

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
