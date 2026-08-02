# Variables
REPONAME = pydantic-schemaforms
APP_VERSION = 26.3.2
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

.PHONY: autoflake black bump bump-beta bump-undo cleanup create-docs flake8 git-cleanup help install isort rebase run-example run-example-dev speedtest test ex-run ex-test

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

create-docs: ## Build and publish versioned docs with mike (make create-docs VERSION=26.4.0)

	python3 scripts/changelog.py
	python3 scripts/update_docs.py
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
	cd examples && $(PYTHON) -m uvicorn main:app --port $(PORT) --reload --reload-dir .. --log-level debug

ex-test: ## Test that the FastAPI example can be imported successfully
	cd examples && $(PYTHON) -c "import main; print('✅ FastAPI example imports correctly')"
	@echo "🎉 FastAPI example is ready to run!"

kill:  # Kill any process running on the app port
	@echo "Stopping any process running on port ${PORT}..."
	@set -e; \
	# Prefer lsof, then fuser, then ss/netstat, then fallback to pgrep pattern
	if command -v lsof >/dev/null 2>&1; then \
		pids=$$(lsof -ti tcp:${PORT} 2>/dev/null || true); \
	elif command -v fuser >/dev/null 2>&1; then \
		pids=$$(fuser -n tcp ${PORT} 2>/dev/null || true); \
	elif command -v ss >/dev/null 2>&1; then \
		pids=$$(ss -ltnp 2>/dev/null | grep -F ":${PORT}" || true | grep -o 'pid=[0-9]*' | sed 's/pid=//' | sort -u || true); \
	else \
		pids=$$(pgrep -f "uvicor[n] main:app.*--port ${PORT}" || true); \
	fi; \
	# Normalize and deduplicate
	pids=$$(echo "$$pids" | tr ' ' '\n' | sed '/^$$/d' | sort -u || true); \
	if [ -n "$$pids" ]; then \
		echo "Found PIDs using port ${PORT}: $$pids"; \
		# Try graceful shutdown first
		echo "Sending TERM to $$pids"; echo "$$pids" | xargs -r kill -TERM || true; \
		sleep 1; \
		# Kill any remaining
		still=$$(echo "$$pids" | xargs -r ps -o pid= -p 2>/dev/null || true); \
		if [ -n "$$still" ]; then \
			echo "Forcing kill for: $$still"; echo "$$still" | xargs -r kill -9 || true; \
		else \
			echo "Processes terminated."; \
		fi; \
	else \
		echo "No process found running on port ${PORT}"; \
	fi; \
	@echo "Port ${PORT} is now free"
