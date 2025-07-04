# Variables
REPONAME = pydantic-forms
APP_VERSION = 2025-04-18-001.beta
PYTHON = python3
PIP = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest

EXAMPLE_PATH = examples
SERVICE_PATH = pydantic_forms

TESTS_PATH = tests
SQLITE_PATH = _sqlite_db
LOG_PATH = log

PORT = 5000
WORKER = 8
LOG_LEVEL = debug

REQUIREMENTS_PATH = requirements.txt
# DEV_REQUIREMENTS_PATH = requirements/dev.txt

.PHONY: autoflake black cleanup create-docs flake8 help install isort run-example run-example-dev speedtest test

autoflake: ## Remove unused imports and unused variables from Python code
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(SERVICE_PATH)
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(TESTS_PATH)
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(EXAMPLE_PATH)

black: ## Reformat Python code to follow the Black code style
	black $(SERVICE_PATH)
	# black $(TESTS_PATH)
	# black $(EXAMPLE_PATH)

bump: ## Bump the version of the project
	bumpcalver --build

bump-beta: ## Bump the version of the project
	bumpcalver --build --beta


cleanup: isort ruff autoflake ## Run isort, ruff, autoflake

create-docs: ## Build and deploy the project's documentation

	python3 scripts/changelog.py
	python3 scripts/update_docs.py
	cp /workspaces/$(REPONAME)/README.md /workspaces/$(REPONAME)/docs/index.md
	cp /workspaces/$(REPONAME)/CONTRIBUTING.md /workspaces/$(REPONAME)/docs/contribute.md
	cp /workspaces/$(REPONAME)/CHANGELOG.md /workspaces/$(REPONAME)/docs/release-notes.md
	mkdocs build
	mkdocs gh-deploy

create-docs-local: ## Build and deploy the project's documentation

	python3 scripts/changelog.py
	python3 scripts/update_docs.py
	cp /workspaces/$(REPONAME)/README.md /workspaces/$(REPONAME)/docs/index.md
	cp /workspaces/$(REPONAME)/CONTRIBUTING.md /workspaces/$(REPONAME)/docs/contribute.md
	cp /workspaces/$(REPONAME)/CHANGELOG.md /workspaces/$(REPONAME)/docs/release-notes.md
	mkdocs build


flake8: ## Run flake8 to check Python code for PEP8 compliance
	flake8 --tee . > htmlcov/_flake8Report.txt

help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

install: ## Install the project's dependencie
	$(PIP) install -r $(REQUIREMENTS_PATH)

local-install: ## Install the project
	 pip install -e .

reinstall: ## Install the project's dependencie
	$(PIP) uninstall -r $(REQUIREMENTS_PATH) -y
	$(PIP) install -r $(REQUIREMENTS_PATH)

isort: ## Sort imports in Python code
	isort $(SERVICE_PATH)
	isort $(TESTS_PATH)
	isort $(EXAMPLE_PATH)


speedtest: ## Run a speed test
	if [ ! -f speedtest/http_request.so ]; then gcc -shared -o speedtest/http_request.so speedtest/http_request.c -lcurl -fPIC; fi
	python3 speedtest/loop.py

test: ## Run the project's tests
	pre-commit run -a
	pytest
	genbadge coverage -i /workspaces/$(REPONAME)/coverage.xml
	genbadge tests -i /workspaces/$(REPONAME)/report.xml
	sed -i "s|<source>/workspaces/$(REPONAME)</source>|<source>$(shell pwd)</source>|" coverage.xml

tests: test ## Run the project's tests

build: ## Build the project
	python -m build

ruff: ## Format Python code with Ruff
	ruff check --fix --exit-non-zero-on-fix --show-fixes $(SERVICE_PATH)
	ruff check --fix --exit-non-zero-on-fix --show-fixes $(TESTS_PATH)
	ruff check --fix --exit-non-zero-on-fix --show-fixes $(EXAMPLE_PATH)


ex-run: ## Run the example fast application
# cp /workspaces/$(REPONAME)/examples/main.py /workspaces/$(REPONAME)/ex.py
	uvicorn examples.main:app --port ${PORT} --reload  --log-level $(LOG_LEVEL)
# rm /workspaces/$(REPONAME)/ex.py

ex-f: ## Run the example flask application
	FLASK_APP=example.py python -m flask run --host 0.0.0.0 --port ${PORT} --reload

js-build: ## Install JS dependencies and build form-bundle.js with Vite
	cd PySchemaForms/static && \
	npm install --legacy-peer-deps && \
	npx vite build

clear-pycache: ## Remove all __pycache__ directories
	find . -type d -name "__pycache__" -exec rm -rf {} +
