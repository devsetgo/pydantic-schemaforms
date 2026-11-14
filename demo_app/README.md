# Demo App (Monorepo Consolidation)

This folder is the in-repo home for demo app assets after deprecating the standalone demo repository.

## Current layout

- `Dockerfile`: default release image definition. It intentionally runs the canonical app from `examples/main.py` to minimize sync drift.
- `requirements.template`: minimal runtime dependency template, rendered to `requirements.txt` with the release version pin.
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

## Published on every release

Publishing a GitHub release runs `.github/workflows/pythonpublish.yml`, which
publishes to PyPI, then deploys the docs, then builds the demo image with
`.github/workflows/docker-demo.yml`. Each step waits for the one before, so a
failed docs deploy pushes no image. The image job waits until the new version
is on PyPI, smoke-tests the image, checks it has that version installed, and
pushes `mikeryan56/pydantic-schemaforms-demo:<YY.MM.DD.HHMM>` and `:latest`.
Like `make docker-build`, the tag is the build time (New York time), not the
library version, so a fix to the demo can ship without a new PyPI release.
It needs the repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
(a Docker Hub access token with read and write access).

To rebuild the image, for example after a fix to the demo app, run **Demo
Docker Image** from the Actions tab: pick the branch to build the demo from
(usually `main`) and the library version to install from PyPI. A release
builds from its own tag.

## Full manual release

```bash
make release
```

Runs `release-check`, `docs-deploy`, `package`, and `docker-all` in order, stopping at the first failure.
Only for releasing without GitHub Actions; a published GitHub release already does all of this.

## Privacy-first defaults

The copied demo runtime in `demo_app/src/` now defaults to **bad-actor handling only**:

- `ANALYTICS_CAPTURE_ENABLED=0` (default): disables persistent request/IP/user capture storage.
- `ANALYTICS_DASHBOARD_ENABLED=0` (default): disables dashboard/API analytics endpoints.
- `ANTISCAN_ENABLED=1` (default): keeps anti-scan tarpit/rate-limiting behavior active.

If you intentionally want legacy capture/dashboard behavior for troubleshooting, set both analytics flags to `1`.
