.PHONY: help install test test-cov lint lint-fix format format-check type-check pre-commit clean clean-all
.PHONY: build rebuild shell ci docs-serve docs-build generate-portal
.PHONY: create-exporter build-exporter test-exporter list-exporters
.PHONY: local-test local-lint local-format local-type-check

# ==============================================================================
# Monitoring Hub - Unified Makefile
# ==============================================================================
# This Makefile provides a convenient interface to the Docker-first workflow.
# Most commands delegate to ./devctl which runs everything in containers.
#
# Docker-First (Recommended):  make test, make lint, make format
# Local Python (Advanced):     make local-test, make local-lint, make local-format
# ==============================================================================

# --- Variables ---
PYTHON   := python3
VENV     := .venv
VENV_BIN := $(VENV)/bin

# Local Binaries (Use venv if it exists, fallback to system path)
RUFF     := $(shell [ -f $(VENV_BIN)/ruff ] && echo $(VENV_BIN)/ruff || echo ruff)
PYTEST   := $(shell [ -f $(VENV_BIN)/pytest ] && echo PYTHONPATH=$(shell pwd) $(VENV_BIN)/pytest || echo PYTHONPATH=$(shell pwd) pytest)
MYPY     := $(shell [ -f $(VENV_BIN)/mypy ] && echo MYPYPATH=$(shell pwd) $(VENV_BIN)/mypy || echo mypy)

# --- Help ---
help: ## Show this help message
	@echo "Monitoring Hub - Makefile Commands"
	@echo ""
	@echo "RECOMMENDED: Use ./devctl for Docker-first workflow"
	@echo "  ./devctl help          Show all available commands"
	@echo "  ./devctl build         Build development image"
	@echo "  ./devctl test          Run tests in container"
	@echo "  ./devctl shell         Open interactive shell"
	@echo ""
	@echo "Available Make commands (delegates to ./devctl):"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# Docker-First Commands (Recommended - No Python install required)
# ==============================================================================

build: ## Build the development Docker image
	@./devctl build

rebuild: ## Rebuild Docker image from scratch
	@./devctl rebuild

shell: ## Open interactive shell in container
	@./devctl shell

test: ## Run tests in Docker container
	@./devctl test

test-cov: ## Run tests with coverage in Docker container
	@./devctl test-cov

lint: ## Run linter in Docker container
	@./devctl lint

lint-fix: ## Auto-fix linting issues in Docker container
	@./devctl lint-fix

lint-css: ## Run CSS linter in Docker container
	@./devctl lint-css

format: ## Format code in Docker container
	@./devctl format

format-check: ## Check code formatting in Docker container
	@./devctl format-check

type-check: ## Run type checker in Docker container
	@./devctl type-check

ci: ## Run all CI checks in Docker container
	@./devctl ci

# --- Exporter Commands ---

create-exporter: ## Create a new exporter interactively
	@./devctl create-exporter

list-exporters: ## List all available exporters
	@./devctl list-exporters

build-exporter: ## Build specific exporter (usage: make build-exporter EXPORTER=node_exporter)
	@if [ -z "$(EXPORTER)" ]; then \
		echo "Usage: make build-exporter EXPORTER=<name>"; \
		exit 1; \
	fi
	@./devctl build-exporter $(EXPORTER)

test-exporter: ## Test build an exporter (usage: make test-exporter EXPORTER=node_exporter)
	@if [ -z "$(EXPORTER)" ]; then \
		echo "Usage: make test-exporter EXPORTER=<name>"; \
		exit 1; \
	fi
	@./devctl test-exporter $(EXPORTER)

# --- Portal & Docs ---

generate-portal: ## Generate the web portal
	@./devctl generate-portal

docs-build: ## Build MkDocs documentation
	@./devctl docs-build

docs-serve: ## Serve docs with live reload
	@./devctl docs-serve

# ==============================================================================
# Local Commands (Advanced - Requires Python 3.9+ installed locally)
# ==============================================================================

install: ## Install development dependencies locally
	$(PYTHON) -m pip install -r requirements/dev.txt
	$(PYTHON) -m pip install -r requirements/base.txt
	$(PYTHON) -m pip install -r requirements/docs.txt
	pre-commit install

local-test: ## Run tests locally (requires local Python)
	$(PYTEST) -v

local-test-cov: ## Run tests with coverage locally
	$(PYTEST) -v --cov=core --cov-report=term-missing --cov-report=html

local-lint: ## Run linter locally
	$(RUFF) check .

local-lint-fix: ## Auto-fix linting issues locally
	$(RUFF) check --fix .

local-format: ## Format code locally
	$(RUFF) format .

local-format-check: ## Check code formatting locally
	$(RUFF) format --check .

local-type-check: ## Run type checker locally
	$(MYPY) --explicit-package-bases core/

pre-commit: ## Run pre-commit hooks locally
	pre-commit run --all-files

# ==============================================================================
# Cleanup
# ==============================================================================

clean: ## Clean up generated files and caches (uses Docker to avoid permission issues)
	@./devctl clean

clean-all: ## Deep clean including site, build, dist, and venv
	@./devctl clean
	@sudo rm -rf site/ dist/ $(VENV)
