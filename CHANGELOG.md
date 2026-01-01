# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Latest Changes

### Added

- Versioned documentation publishing via MkDocs + `mike`, deployed on GitHub Releases.
- Manual GitHub Actions inputs to test docs deployment and optionally deploy to a staging Pages branch.
- SonarCloud CI workflow that generates Python coverage (`coverage.xml`) and imports it during analysis.

### Changed

- Documentation configuration now includes an explicit `site_url` for correct canonical URLs.

### Fixed

- Docs deploy workflow robustness by adding the missing repo scripts and canonical docs files it references.
- GitHub Actions permissions for PR-description automation (where the token context allows write access).
