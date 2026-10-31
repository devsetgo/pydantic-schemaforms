# Variables
REPONAME = pydantic-schemaforms
APP_VERSION = 26.4.4
# Version used by docs, release checks, and the Docker image's package pin.
# Override on the command line, e.g. `make docs-deploy VERSION=26.4.0`
VERSION ?= $(APP_VERSION)
PYTHON = python3
PIP = $(PYTHON) -m pip

# Some devcontainers install CLI tools into ~/.local/bin which may not be on PATH.
BUMPCALVER = $(if $(wildcard $(HOME)/.local/bin/bumpcalver),$(HOME)/.local/bin/bumpcalver,bumpcalver)

SERVICE_PATH = pydantic_schemaforms
TESTS_PATH = tests
EXAMPLE_PATH = examples
REQUIREMENTS_PATH = requirements.txt
PORT = 8000

DOCS_ALIASES ?= latest stable
DOCS_BRANCH ?= gh-pages

# Demo Docker image. The tag is computed once per `make` invocation, so
# docker-build and docker-push inside `make docker-all` share it.
DEMO_APP_DIR = demo_app
DOCKER_IMAGE ?= mikeryan56/pydantic-schemaforms-demo
DOCKER_TAG := $(shell TZ=America/New_York date +%y.%m.%d.%H%M)

.PHONY: help install test tests cleanup ruff isort autoflake \
	ex-run ex-test kill \
	ai-instructions docs-build docs-deploy \
	vendor-update-htmx vendor-update-imask vendor-update-bootstrap vendor-verify \
	docker-build docker-push docker-all \
	bump bump-beta bump-undo release-check package release \
	rebase git-cleanup

help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

install: ## Install dev dependencies and the package in editable mode
	$(PIP) install -r $(REQUIREMENTS_PATH)
	$(PIP) install -e .

##@ Test and lint

test: ## Run pre-commit, pyright, pytest, and update coverage badges
	@start=$$(date +%s); \
	echo "🔍 Running pre-commit (ruff, formatting, yaml/toml checks)..."; \
	$(PYTHON) -m pre_commit run -a; \
	echo "✅ Pre-commit passed. Running type check..."; \
	$(PYTHON) -m pyright; \
	echo "✅ Type check passed. Running form-data parser regression tests..."; \
	$(PYTHON) -m pytest -q tests/test_form_data_parsing.py; \
	echo "🧪 Regression passed. Running full pytest suite..."; \
	$(PYTHON) -m pytest -n 4; \
	echo "📊 Generating coverage and test badges..."; \
	genbadge coverage -i coverage.xml 2>/dev/null || true; \
	genbadge tests -i report.xml 2>/dev/null || true; \
	sed -i "s|<source>/workspaces/$(REPONAME)</source>|<source>$$(pwd)</source>|" coverage.xml; \
	end=$$(date +%s); \
	$(PYTHON) -c "print(f'✨ Tests complete. Badges updated. Total time: {$$end - $$start:.2f} seconds')"

tests: test ## Alias for test

cleanup: isort ruff autoflake ## Run isort, ruff --fix, and autoflake

ruff: ## Apply ruff lint fixes
	$(PYTHON) -m ruff check --fix --exit-non-zero-on-fix --show-fixes $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)

isort: ## Sort imports
	$(PYTHON) -m isort $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)

autoflake: ## Remove unused imports and variables
	autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --remove-unused-variables -r $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)

##@ Example app

ex-run: ## Run the FastAPI example app with auto-reload
	# --reload-dir scoped to just the two source dirs (not --reload-dir ..,
	# which watches the whole repo root) -- otherwise every `pytest` run's
	# regenerated coverage.xml/report.xml/htmlcov/*.html/badges at the repo
	# root looks like a source change and triggers a full app reload, paying
	# the import cost again on the next request.
	cd examples && $(PYTHON) -m uvicorn main:app --port $(PORT) --reload --reload-dir . --reload-dir ../$(SERVICE_PATH) --log-level debug

ex-test: ## Check that the example app imports
	cd examples && $(PYTHON) -c "import main; print('✅ FastAPI example imports correctly')"

kill: ## Kill any process listening on PORT
	@sh scripts/kill_by_port.sh $(PORT)

##@ Docs

ai-instructions: ## Regenerate the packaged AI-assistant instruction files
	$(PYTHON) scripts/build_ai_instructions.py

docs-build: ## Regenerate generated docs and build the site locally
	$(PYTHON) scripts/changelog.py
	$(PYTHON) scripts/update_docs.py
	$(PYTHON) scripts/build_ai_instructions.py
	cp README.md docs/index.md
	cp CONTRIBUTING.md docs/contribute.md
	cp CHANGELOG.md docs/release-notes.md
	mkdocs build

docs-deploy: ## Regenerate generated docs and publish versioned docs for VERSION
	$(PYTHON) scripts/changelog.py
	$(PYTHON) scripts/update_docs.py
	$(PYTHON) scripts/build_ai_instructions.py
	cp README.md docs/index.md
	cp CONTRIBUTING.md docs/contribute.md
	cp CHANGELOG.md docs/release-notes.md
	$(PYTHON) scripts/deploy_docs.py deploy \
		--version "$(VERSION)" \
		--aliases $(DOCS_ALIASES) \
		--title "Release $(VERSION)" \
		--branch "$(DOCS_BRANCH)" \
		--ignore-remote-status \
		--push
	mike set-default stable --branch "$(DOCS_BRANCH)" --push

##@ Vendored assets

vendor-update-htmx: ## Vendor HTMX (latest, or HTMX_VERSION=2.x.y)
	$(PYTHON) scripts/vendor_assets.py update-htmx $(if $(HTMX_VERSION),--version $(HTMX_VERSION),)

vendor-update-imask: ## Vendor IMask (IMASK_VERSION=x.y.z)
	$(PYTHON) scripts/vendor_assets.py update-imask --version "$(IMASK_VERSION)"

vendor-update-bootstrap: ## Vendor Bootstrap (BOOTSTRAP_VERSION=5.x.y)
	$(PYTHON) scripts/vendor_assets.py update-bootstrap --version "$(BOOTSTRAP_VERSION)"

vendor-verify: ## Verify vendored assets match manifest checksums
	$(PYTHON) scripts/vendor_assets.py verify --require-nonempty

##@ Docker (demo image)

docker-build: ## Build the demo image (pins pydantic-schemaforms==VERSION) and smoke-test it
	sed "s/__APP_VERSION__/$(VERSION)/g" $(DEMO_APP_DIR)/requirements.template.txt > $(DEMO_APP_DIR)/requirements.txt
	docker build -f $(DEMO_APP_DIR)/Dockerfile \
		--build-arg SCHEMAFORMS_DEMO_IMAGE_VERSION=$(DOCKER_TAG) \
		--label version=$(DOCKER_TAG) \
		-t $(DOCKER_IMAGE):$(DOCKER_TAG) -t $(DOCKER_IMAGE):latest .
	docker run --rm $(DOCKER_IMAGE):latest python -c "import examples.main; print('smoke-ok')"

docker-push: ## Push the most recently built demo image (its version tag + latest)
	@tag=$$(docker inspect -f '{{index .Config.Labels "version"}}' $(DOCKER_IMAGE):latest); \
	echo "Pushing $(DOCKER_IMAGE):$$tag and :latest"; \
	docker push $(DOCKER_IMAGE):$$tag && docker push $(DOCKER_IMAGE):latest

docker-all: docker-build docker-push ## Build, smoke-test, and push the demo image

##@ Release

bump: ## Bump to the next production version
	$(BUMPCALVER) --build

bump-beta: ## Bump to the next beta version
	$(BUMPCALVER) --build --beta

bump-undo: ## Undo the last version bump
	$(BUMPCALVER) --undo

release-check: ## Fail unless the git tree is clean and every version string equals VERSION
	@set -e; \
	if [ -n "$$(git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean."; exit 2; \
	fi; \
	py_ver=$$(awk -F\" '/^version = / {print $$2; exit}' pyproject.toml); \
	mod_ver=$$(awk -F\' '/^__version__[[:space:]]*=/ {print $$2; exit}' $(SERVICE_PATH)/__init__.py); \
	echo "VERSION=$(VERSION) makefile=$(APP_VERSION) pyproject=$$py_ver package=$$mod_ver"; \
	if [ "$$py_ver" != "$(VERSION)" ] || [ "$(APP_VERSION)" != "$(VERSION)" ] || [ "$$mod_ver" != "$(VERSION)" ]; then \
		echo "ERROR: Version mismatch."; exit 3; \
	fi; \
	echo "Release check passed."

package: ## Build sdist and wheel into dist/
	rm -rf dist
	$(PYTHON) -m build --sdist --wheel

release: release-check docs-deploy package docker-all ## Full manual release: check, docs, package, demo image

##@ Git

rebase: ## Rebase the current branch onto origin/main
	git fetch origin
	git rebase origin/main

git-cleanup: ## Prune origin and delete local branches whose upstream is gone
	git fetch origin --prune
	@git branch -vv | grep ': gone\]' | sed 's/^\*//' | awk '{print $$1}' | grep -vE '^(main|master|dev)$$' | xargs -r git branch -D
