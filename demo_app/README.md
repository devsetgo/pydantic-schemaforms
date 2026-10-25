# Demo App (Monorepo Consolidation)

This folder is the in-repo home for demo app assets after deprecating the standalone demo repository.

## Current layout

- `Dockerfile`: default release image definition. It intentionally runs the canonical app from `examples/main.py` to minimize sync drift.
- `requirements.template.txt`: minimal runtime dependency template, rendered to `requirements.txt` with the release version pin.
- `src/`, `migrations/`, `alembic.ini`, `requirements-demo.txt`, `scripts/docker_entrypoint.sh`: imported demo runtime snapshot from the retired standalone repo.

## Why both exist right now

The release path now prioritizes building the demo image from canonical `examples` code. The imported runtime snapshot is kept in-repo to continue migration work and to avoid dependence on the old repository.

## Build locally

```bash
make docker-build   # build + smoke-test
make docker-push    # push the last build (version tag + latest)
make docker-all     # both
```

`docker-build` renders `demo_app/requirements.txt` (pinning `pydantic-schemaforms` to the makefile's `APP_VERSION`; override with `VERSION=<version>`) and tags the image `mikeryan56/pydantic-schemaforms-demo:<YY.MM.DD.HHMM>` and `:latest`.
The image installs the published package from PyPI, not your local checkout, so that version must already be released.

## Run locally

```bash
docker run --rm -p 8000:8000 mikeryan56/pydantic-schemaforms-demo:latest
```

Then open http://localhost:8000.

## Full release

```bash
make release
```

Runs `release-check`, `docs-deploy`, `package`, and `docker-all` in order, stopping at the first failure.

## Privacy-first defaults

The copied demo runtime in `demo_app/src/` now defaults to **bad-actor handling only**:

- `ANALYTICS_CAPTURE_ENABLED=0` (default): disables persistent request/IP/user capture storage.
- `ANALYTICS_DASHBOARD_ENABLED=0` (default): disables dashboard/API analytics endpoints.
- `ANTISCAN_ENABLED=1` (default): keeps anti-scan tarpit/rate-limiting behavior active.

If you intentionally want legacy capture/dashboard behavior for troubleshooting, set both analytics flags to `1`.
