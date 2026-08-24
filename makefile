# Variables
REPONAME = pydantic-schemaforms
APP_VERSION = 26.3.5
# Override on the command line, e.g. `make create-docs VERSION=26.4.0`
VERSION ?= $(APP_VERSION)
ALIASES ?= latest stable
DOCS_BRANCH ?= gh-pages
PYTHON = python3
PIP = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest

# Some devcontainers install CLI tools into ~/.local/bin which may not be on PATH.
BUMPCALVER = $(if $(wildcard $(HOME)/.local/bin/bumpcalver),$(HOME)/.local/bin/bumpcalver,bumpcalver)

EXAMPLE_PATH = examples
SERVICE_PATH = pydantic_schemaforms

TESTS_PATH = tests
SQLITE_PATH = _sqlite_db
LOG_PATH = log

PORT = 8000
WORKER = 8
LOG_LEVEL = debug

REQUIREMENTS_PATH = requirements.txt
# DEV_REQUIREMENTS_PATH = requirements/dev.txt

# Demo container settings (monorepo rollout)
DEMO_APP_DIR ?= demo_app
DEMO_IMAGE_NAME ?= pydantic-schemaforms-demo
DEMO_DOCKER_REGISTRY ?= docker.io
DEMO_DOCKER_REPO ?= mikeryan56/$(DEMO_IMAGE_NAME)
DEMO_IMAGE_PORT ?= 8000
DEMO_TAG_TZ ?= America/New_York

# Manual release orchestration settings
RELEASE_VERSION ?= $(APP_VERSION)
ALLOW_DIRTY ?= 0
CONFIRM_RELEASE ?= 0
PUBLISH_LATEST ?= 0
PUBLISH_STABLE ?= 0

.PHONY: ai-instructions autoflake black bump bump-beta bump-undo cleanup create-docs flake8 git-cleanup help install isort rebase run-example run-example-dev speedtest test ex-run ex-test

.PHONY: release-prepare release-docs release-demo-image release-package release-verify release-manual release-docs-retry release-demo-image-retry demo-requirements

.PHONY: vendor-update-htmx vendor-verify

autoflake: ## Remove unused imports and unused variables from Python code
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(SERVICE_PATH)
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(TESTS_PATH)
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(EXAMPLE_PATH)

black: ## Reformat Python code to follow the Black code style
	$(PYTHON) -m black $(SERVICE_PATH)
	# black $(TESTS_PATH)
	# black $(EXAMPLE_PATH)

# Version management via BumpCalver (github.com/devsetgo/bumpcalver).
# Version format: {YY}.{quarter}.{build_count}  e.g. 26.2.1
# Use `bump` for production releases, `bump-beta` for pre-release iterations.
# `bump-undo` reverts version strings only; code changes are unaffected.
bump: ## Bump to next production version (no suffix) — use for releases
	$(BUMPCALVER) --build

bump-beta: ## Bump to next beta version
	$(BUMPCALVER) --build --beta

bump-undo: ## Undo the last version bump
	$(BUMPCALVER) --undo


cleanup: isort ruff autoflake ## Run isort, ruff, autoflake

ai-instructions: ## Regenerate the packaged AI-assistant instruction files from shared sources
	python3 scripts/build_ai_instructions.py

create-docs: ## Build and publish versioned docs with mike (make create-docs VERSION=26.4.0)

	python3 scripts/changelog.py
	python3 scripts/update_docs.py
	python3 scripts/build_ai_instructions.py
	cp /workspaces/$(REPONAME)/README.md /workspaces/$(REPONAME)/docs/index.md
	cp /workspaces/$(REPONAME)/CONTRIBUTING.md /workspaces/$(REPONAME)/docs/contribute.md
	cp /workspaces/$(REPONAME)/CHANGELOG.md /workspaces/$(REPONAME)/docs/release-notes.md
	python3 scripts/deploy_docs.py deploy \
		--version "$(VERSION)" \
		--aliases $(ALIASES) \
		--title "Release $(VERSION)" \
		--branch "$(DOCS_BRANCH)" \
		--ignore-remote-status \
		--push
	mike set-default stable --branch "$(DOCS_BRANCH)" --push

create-docs-local: ## Build and deploy the project's documentation

	python3 scripts/changelog.py
	python3 scripts/update_docs.py
	python3 scripts/build_ai_instructions.py
	cp /workspaces/$(REPONAME)/README.md /workspaces/$(REPONAME)/docs/index.md
	cp /workspaces/$(REPONAME)/CONTRIBUTING.md /workspaces/$(REPONAME)/docs/contribute.md
	cp /workspaces/$(REPONAME)/CHANGELOG.md /workspaces/$(REPONAME)/docs/release-notes.md
# 	cp /workspaces/$(REPONAME)/pydantic-schemaform-logo.png /workspaces/$(REPONAME)/docs/pydantic-schemaform-logo.png
# 	cp /workspaces/$(REPONAME)/favicon.png /workspaces/$(REPONAME)/docs/favicon.png
	mkdocs build


flake8: ## Run flake8 to check Python code for PEP8 compliance
	flake8 --tee . > htmlcov/_flake8Report.txt

help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

install: ## Install the project's dependencie
	$(PIP) install -r $(REQUIREMENTS_PATH)
	pip install -e .

local-install: ## Install the project
	 pip install -e .

reinstall: ## Install the project's dependencie
	$(PIP) uninstall -r $(REQUIREMENTS_PATH) -y
	$(PIP) install -r $(REQUIREMENTS_PATH)

rebase: ## Rebase current branch from origin/main
	git fetch origin
	git rebase origin/main

git-cleanup: ## Fetch + prune from origin, then delete local branches whose upstream is gone
	@echo "Fetching from origin and pruning stale remote-tracking branches..."
	git fetch origin --prune
	@echo "Removing local branches whose upstream branch no longer exists..."
	@git branch -vv | grep ': gone\]' | sed 's/^\*//' | awk '{print $$1}' | grep -vE '^(main|master|dev)$$' | xargs -r git branch -D
	@echo "git-cleanup complete."

isort: ## Sort imports in Python code
	$(PYTHON) -m isort $(SERVICE_PATH)
	$(PYTHON) -m isort $(TESTS_PATH)
	$(PYTHON) -m isort $(EXAMPLE_PATH)


speedtest: ## Run a speed test
	if [ ! -f speedtest/http_request.so ]; then gcc -shared -o speedtest/http_request.so speedtest/http_request.c -lcurl -fPIC; fi
	python3 speedtest/loop.py

test: ## Run the project's tests (linting + pyright + pytest + coverage badges)
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
	genbadge coverage -i /workspaces/$(REPONAME)/coverage.xml 2>/dev/null || true; \
	genbadge tests -i /workspaces/$(REPONAME)/report.xml 2>/dev/null || true; \
	sed -i "s|<source>/workspaces/$(REPONAME)</source>|<source>$$(pwd)</source>|" coverage.xml; \
	end=$$(date +%s); \
	$(PYTHON) -c "print(f'✨ Tests complete. Badges updated. Total time: {$$end - $$start:.2f} seconds')"

tests: test ## Alias for 'test' - Run the project's tests

vendor-update-htmx: ## Vendor the latest HTMX into package assets (or set HTMX_VERSION=2.x.y)
	$(PYTHON) scripts/vendor_assets.py update-htmx $(if $(HTMX_VERSION),--version $(HTMX_VERSION),)

vendor-update-imask: ## Vendor the latest IMask into package assets (or set IMASK_VERSION=2.x.y)
	$(PYTHON) scripts/vendor_assets.py update-imask --version "$(IMASK_VERSION)"

vendor-update-bootstrap: ## Vendor the latest Bootstrap into package assets (or set BOOTSTRAP_VERSION=5.x.y)
	$(PYTHON) scripts/vendor_assets.py update-bootstrap --version "$(BOOTSTRAP_VERSION)"

vendor-update-materialize: ## Vendor the latest Materialize into package assets (or set MATERIALIZE_VERSION=1.x.y)
	$(PYTHON) scripts/vendor_assets.py update-materialize --version "$(MATERIALIZE_VERSION)"

vendor-verify: ## Verify vendored assets match manifest checksums
	$(PYTHON) scripts/vendor_assets.py verify --require-nonempty


build: ## Build the project
	python -m build

ruff: ## Format Python code with Ruff
	$(PYTHON) -m ruff check --fix --exit-non-zero-on-fix --show-fixes $(SERVICE_PATH)
	$(PYTHON) -m ruff check --fix --exit-non-zero-on-fix --show-fixes $(TESTS_PATH)
	$(PYTHON) -m ruff check --fix --exit-non-zero-on-fix --show-fixes $(EXAMPLE_PATH)


ex-run: ## Run the FastAPI example (async implementation)
	# --reload-dir scoped to just the two source dirs (not --reload-dir ..,
	# which watches the whole repo root) -- otherwise every `pytest` run's
	# regenerated coverage.xml/report.xml/htmlcov/*.html/badges at the repo
	# root looks like a source change and triggers a full app reload, paying
	# the import cost again on the next request.
	cd examples && $(PYTHON) -m uvicorn main:app --port $(PORT) --reload --reload-dir . --reload-dir ../$(SERVICE_PATH) --log-level debug

ex-test: ## Test that the FastAPI example can be imported successfully
	cd examples && $(PYTHON) -c "import main; print('✅ FastAPI example imports correctly')"
	@echo "🎉 FastAPI example is ready to run!"

kill:  # Kill any process running on the app port
	@chmod +x scripts/kill_by_port.sh || true
	@scripts/kill_by_port.sh ${PORT}

release-prepare: ## Validate release prerequisites (version alignment + clean git state)
	@set -e; \
	echo "Preparing manual release for version: $(RELEASE_VERSION)"; \
	if [ "$(ALLOW_DIRTY)" != "1" ] && [ -n "$$(git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean. Commit/stash changes or run with ALLOW_DIRTY=1"; \
		exit 2; \
	fi; \
	py_ver=$$(awk -F\" '/^version = / {print $$2; exit}' pyproject.toml); \
	mk_ver=$$(awk -F= '/^APP_VERSION[[:space:]]*=/ {gsub(/[[:space:]]/,"",$$2); print $$2; exit}' makefile); \
	mod_ver=$$(awk -F\' '/^__version__[[:space:]]*=/ {print $$2; exit}' pydantic_schemaforms/__init__.py); \
	if [ "$$py_ver" != "$(RELEASE_VERSION)" ] || [ "$$mk_ver" != "$(RELEASE_VERSION)" ] || [ "$$mod_ver" != "$(RELEASE_VERSION)" ]; then \
		echo "ERROR: Version mismatch detected"; \
		echo "  pyproject.toml: $$py_ver"; \
		echo "  makefile: $$mk_ver"; \
		echo "  package module: $$mod_ver"; \
		echo "  expected RELEASE_VERSION: $(RELEASE_VERSION)"; \
		exit 3; \
	fi; \
	echo "Release preflight checks passed."

release-docs: ## Deploy versioned docs for RELEASE_VERSION
	$(MAKE) create-docs VERSION=$(RELEASE_VERSION)

release-package: ## Build package artifacts for RELEASE_VERSION
	@set -e; \
	rm -rf dist; \
	$(PYTHON) -m build --sdist --wheel; \
	echo "Package artifacts built in dist/"

demo-requirements: ## Render demo_app/requirements.txt with RELEASE_VERSION pin
	@set -e; \
	if [ ! -f "$(DEMO_APP_DIR)/requirements.template.txt" ]; then \
		echo "ERROR: Missing $(DEMO_APP_DIR)/requirements.template.txt"; \
		exit 7; \
	fi; \
	sed "s/__APP_VERSION__/$(RELEASE_VERSION)/g" "$(DEMO_APP_DIR)/requirements.template.txt" > "$(DEMO_APP_DIR)/requirements.txt"; \
	echo "Rendered $(DEMO_APP_DIR)/requirements.txt for version $(RELEASE_VERSION)"

release-demo-image: ## Build and push demo image for RELEASE_VERSION
	@set -e; \
	if [ ! -f "$(DEMO_APP_DIR)/requirements.template.txt" ]; then \
		echo "ERROR: Missing $(DEMO_APP_DIR)/requirements.template.txt"; \
		exit 7; \
	fi; \
	sed "s/__APP_VERSION__/$(RELEASE_VERSION)/g" "$(DEMO_APP_DIR)/requirements.template.txt" > "$(DEMO_APP_DIR)/requirements.txt"; \
	echo "Rendered $(DEMO_APP_DIR)/requirements.txt for version $(RELEASE_VERSION)"; \
	if [ "$(CONFIRM_RELEASE)" != "1" ]; then \
		echo "ERROR: Refusing to push image without CONFIRM_RELEASE=1"; \
		exit 4; \
	fi; \
	if [ ! -f "$(DEMO_APP_DIR)/Dockerfile" ]; then \
		echo "ERROR: Missing $(DEMO_APP_DIR)/Dockerfile"; \
		exit 5; \
	fi; \
	demo_image_version=$$(TZ="$(DEMO_TAG_TZ)" date +%y.%m.%d.%H%M); \
	local_tag="$(DEMO_IMAGE_NAME):$$demo_image_version"; \
	remote_base="$(DEMO_DOCKER_REGISTRY)/$(DEMO_DOCKER_REPO)"; \
	remote_tag="$$remote_base:$$demo_image_version"; \
	echo "Computed demo image version $$demo_image_version (tz=$(DEMO_TAG_TZ))"; \
	echo "Building $$local_tag from $(DEMO_APP_DIR)/Dockerfile"; \
	docker build -f "$(DEMO_APP_DIR)/Dockerfile" --build-arg SCHEMAFORMS_DEMO_IMAGE_VERSION="$$demo_image_version" -t "$$local_tag" .; \
	echo "Running container smoke test (import examples.main) before push"; \
	docker run --rm "$$local_tag" python -c "import examples.main; print('smoke-ok')"; \
	docker tag "$$local_tag" "$$remote_tag"; \
	docker push "$$remote_tag"; \
	if [ "$(PUBLISH_LATEST)" = "1" ]; then \
		docker tag "$$local_tag" "$$remote_base:latest"; \
		docker push "$$remote_base:latest"; \
	fi; \
	if [ "$(PUBLISH_STABLE)" = "1" ]; then \
		docker tag "$$local_tag" "$$remote_base:stable"; \
		docker push "$$remote_base:stable"; \
	fi; \
	echo "Demo image publish complete: $$remote_tag"

release-verify: ## Verify local version alignment after manual release steps
	@set -e; \
	py_ver=$$(awk -F\" '/^version = / {print $$2; exit}' pyproject.toml); \
	mk_ver=$$(awk -F= '/^APP_VERSION[[:space:]]*=/ {gsub(/[[:space:]]/,"",$$2); print $$2; exit}' makefile); \
	mod_ver=$$(awk -F\' '/^__version__[[:space:]]*=/ {print $$2; exit}' pydantic_schemaforms/__init__.py); \
	demo_req_ver=$$(awk -F'==' '/^pydantic-schemaforms\[fastapi,email\]==/ {gsub(/[[:space:]]/,"",$$2); print $$2; exit}' "$(DEMO_APP_DIR)/requirements.txt" 2>/dev/null || true); \
	echo "Version check:"; \
	echo "  RELEASE_VERSION=$(RELEASE_VERSION)"; \
	echo "  pyproject.toml=$$py_ver"; \
	echo "  makefile=$$mk_ver"; \
	echo "  package module=$$mod_ver"; \
	echo "  demo requirements pin=$${demo_req_ver:-<not rendered>}"; \
	if [ "$$py_ver" != "$(RELEASE_VERSION)" ] || [ "$$mk_ver" != "$(RELEASE_VERSION)" ] || [ "$$mod_ver" != "$(RELEASE_VERSION)" ] || [ "$$demo_req_ver" != "$(RELEASE_VERSION)" ]; then \
		echo "ERROR: release verification failed"; \
		exit 6; \
	fi; \
	echo "release-verify passed."

release-manual: ## Run manual release orchestration with independent docs/image outcomes
	@chmod +x scripts/release_manual.sh
	@RELEASE_VERSION="$(RELEASE_VERSION)" \
	ALLOW_DIRTY="$(ALLOW_DIRTY)" \
	CONFIRM_RELEASE="$(CONFIRM_RELEASE)" \
	PUBLISH_LATEST="$(PUBLISH_LATEST)" \
	PUBLISH_STABLE="$(PUBLISH_STABLE)" \
	bash scripts/release_manual.sh

release-docs-retry: ## Retry only docs deployment for RELEASE_VERSION
	$(MAKE) release-docs RELEASE_VERSION=$(RELEASE_VERSION)

release-demo-image-retry: ## Retry only demo image publish for RELEASE_VERSION
	$(MAKE) release-demo-image RELEASE_VERSION=$(RELEASE_VERSION) CONFIRM_RELEASE=$(CONFIRM_RELEASE) PUBLISH_LATEST=$(PUBLISH_LATEST) PUBLISH_STABLE=$(PUBLISH_STABLE)
