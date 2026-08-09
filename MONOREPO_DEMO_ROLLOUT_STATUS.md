# Monorepo Demo Rollout Status

Date: 2026-08-08

## Locked Decisions

- Deprecate standalone `demo-pydantic-schemaforms` repository.
- No history preservation required; straight copy into main repository is acceptable.
- Manual Makefile orchestration is preferred over a tightly-coupled GitHub Actions release chain.
- Demo image must install the published package version (no editable `pip -e` install).
- Demo container must use dedicated demo requirements, not the library-wide requirements.
- With Plausible as primary analytics, persistent IP/user capture in the app should be disabled by default.

## Implemented in `pydantic-schemaforms`

### Release orchestration

- Updated `makefile` with manual release targets:
  - `release-prepare`
  - `release-docs`
  - `release-package`
  - `release-demo-image`
  - `release-verify`
  - `release-manual`
  - retry targets
- Added `demo-requirements` target to render `demo_app/requirements.txt` from template using `RELEASE_VERSION`.
- `release-demo-image` now:
  - renders demo requirements from template
  - enforces `CONFIRM_RELEASE=1` before push
- `release-verify` now validates version alignment across:
  - `pyproject.toml`
  - `makefile` `APP_VERSION`
  - `pydantic_schemaforms/__init__.py`
  - `demo_app/requirements.txt` package pin

### Script

- Added `scripts/release_manual.sh`:
  - runs release steps in order
  - records per-step PASS/FAIL in `.release-status/<version>.txt`
  - supports independent retry workflow

### Demo app consolidation

- Added `demo_app/` in monorepo.
- Added `demo_app/Dockerfile` that runs canonical app from `examples/main.py`.
- Added `demo_app/requirements.template.txt` with:
  - `pydantic-schemaforms[fastapi,email]==__APP_VERSION__`
  - minimal runtime dependencies
- Added `demo_app/README.md` with build/release instructions.
- Imported runtime snapshot from old demo repo into `demo_app/` for transition:
  - `src/`
  - `migrations/`
  - `alembic.ini`
  - `scripts/docker_entrypoint.sh`
  - `requirements-demo.txt`

## Privacy-First Analytics Defaults (implemented in copied runtime)

- `demo_app/src/middleware.py`
  - added `ANALYTICS_CAPTURE_ENABLED` gate (default off)
  - persistent request/IP/user capture disabled unless explicitly enabled
  - user tracking cookie disabled unless capture enabled
  - anti-scan logic remains active
- `demo_app/src/resources.py`
  - DB init/seed and IP-geo worker only run when capture is enabled
- `demo_app/src/app_routes.py`
  - added `ANALYTICS_DASHBOARD_ENABLED` gate (default off)
  - dashboard endpoints/auth return 404 when disabled
  - unhandled exception persistence (`record_error`) gated by capture flag

## Validations Completed

- `python3 -m compileall demo_app/src` passed.
- `make demo-requirements RELEASE_VERSION=26.3.3` passed.
- `make release-verify RELEASE_VERSION=26.3.3` passed.
- Dry-run behavior for image release target verified.

## Current Git State (at time of note)

- Modified: `makefile`
- Untracked: `demo_app/`
- Untracked: `scripts/release_manual.sh`

## Resume Checklist (next session)

1. Commit current consolidation and release-flow changes to a checkpoint branch.
2. Decide whether to keep or remove legacy analytics dashboard templates/routes in copied runtime.
3. Add a short operator runbook target/checklist to Makefile.
4. Integrate Plausible script into target demo runtime templates when ready.
5. Finalize standalone demo repo deprecation communication once monorepo path is stable.
