# Demo App (Monorepo Consolidation)

This folder is the in-repo home for demo app assets after deprecating the standalone demo repository.

## Current layout

- `Dockerfile`: default release image definition. It intentionally runs the canonical app from `examples/main.py` to minimize sync drift.
- `requirements.template.txt`: minimal runtime dependency template, rendered to `requirements.txt` with the release version pin.
- `src/`, `migrations/`, `alembic.ini`, `requirements-demo.txt`, `scripts/docker_entrypoint.sh`: imported demo runtime snapshot from the retired standalone repo.

## Why both exist right now

The release path now prioritizes building the demo image from canonical `examples` code. The imported runtime snapshot is kept in-repo to continue migration work and to avoid dependence on the old repository.

## Build locally

Render the demo requirements first (pins `pydantic-schemaforms` to your target version):

```bash
make demo-requirements RELEASE_VERSION=<version>
```

```bash
docker build -f demo_app/Dockerfile -t pydantic-schemaforms-demo:local .
```

## Run locally

```bash
docker run --rm -p 8000:8000 pydantic-schemaforms-demo:local
```

Then open http://localhost:8000.

## Manual release via root Makefile

```bash
make release-manual RELEASE_VERSION=<version> CONFIRM_RELEASE=1
```

Docs and image publishing run in one operator flow with independent pass/fail status.
The demo image install is based on the published `pydantic-schemaforms==<version>` pin in `demo_app/requirements.txt`, not an editable local install.

## Privacy-first defaults

The copied demo runtime in `demo_app/src/` now defaults to **bad-actor handling only**:

- `ANALYTICS_CAPTURE_ENABLED=0` (default): disables persistent request/IP/user capture storage.
- `ANALYTICS_DASHBOARD_ENABLED=0` (default): disables dashboard/API analytics endpoints.
- `ANTISCAN_ENABLED=1` (default): keeps anti-scan tarpit/rate-limiting behavior active.

If you intentionally want legacy capture/dashboard behavior for troubleshooting, set both analytics flags to `1`.
