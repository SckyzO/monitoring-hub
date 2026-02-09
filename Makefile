.PHONY: help install test test-cov lint lint-fix format format-check type-check pre-commit clean docker-build docker-lint docker-lint-fix docker-format docker-type-check docker-test docker-ci docker-shell

# --- Variables ---
PYTHON   := python3
VENV     := .venv
VENV_BIN := $(VENV)/bin

# Local Binaries (Use venv if it exists, fallback to system path)
RUFF     := $(shell [ -f $(VENV_BIN)/ruff ] && echo $(VENV_BIN)/ruff || echo ruff)
PYTEST   := $(shell [ -f $(VENV_BIN)/pytest ] && echo PYTHONPATH=$(shell pwd) $(VENV_BIN)/pytest || echo PYTHONPATH=$(shell pwd) pytest)
MYPY     := $(shell [ -f $(VENV_BIN)/mypy ] && echo MYPYPATH=$(shell pwd) $(VENV_BIN)/mypy || echo mypy)

# Docker Variables
DEV_IMAGE  := monitoring-hub-dev
DOCKER_RUN := docker run --rm -v $(shell pwd):/workspace $(DEV_IMAGE)

# --- Help ---
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Local Commands ---
install: ## Install development dependencies
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -r core/requirements.txt
	pre-commit install

test: ## Run tests locally
	$(PYTEST) -v

test-cov: ## Run tests with coverage report
	$(PYTEST) -v --cov=core --cov-report=term-missing --cov-report=html

lint: ## Run linting checks locally
	$(RUFF) check .

lint-fix: ## Run linting and auto-fix locally
	$(RUFF) check --fix .

format: ## Format code with ruff locally
	$(RUFF) format .

format-check: ## Check code formatting locally
	$(RUFF) format --check .

type-check: ## Run type checking locally
	$(MYPY) --explicit-package-bases core/

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage coverage.xml .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# --- Docker Commands (No local install needed) ---
docker-build: ## Build the development Docker image
	docker build -t $(DEV_IMAGE) -f Dockerfile.dev .

docker-lint: ## Run linter inside Docker
	$(DOCKER_RUN) ruff check .

docker-lint-css: ## Run CSS linter inside Docker
	$(DOCKER_RUN) stylelint "**/*.css"

docker-lint-fix: ## Run linter and fix inside Docker
	$(DOCKER_RUN) ruff check --fix .
	$(DOCKER_RUN) stylelint "**/*.css" --fix

docker-format: ## Run formatter inside Docker
	$(DOCKER_RUN) ruff format .

docker-type-check: ## Run type checking inside Docker
	$(DOCKER_RUN) mypy --explicit-package-bases core/

docker-test: ## Run tests inside Docker
	$(DOCKER_RUN) pytest -v

docker-portal: ## Generate the web portal (index.html) inside Docker
	$(DOCKER_RUN) python3 -m core.engine.site_generator

docker-docs-build: ## Build MkDocs documentation inside Docker
	$(DOCKER_RUN) mkdocs build

docker-docs-serve: ## Serve MkDocs documentation with live reload (accessible at localhost:8000)
	docker run -it --rm -v $(shell pwd):/workspace -p 8000:8000 $(DEV_IMAGE) mkdocs serve -a 0.0.0.0:8000

docker-ci: ## Run all CI checks (lint + format + type-check + tests) inside Docker
	$(DOCKER_RUN) /bin/bash -c "ruff check . && ruff format --check . && mypy --explicit-package-bases core/ && stylelint \"**/*.css\" && pytest -v"

docker-shell: ## Open a shell inside the development container
	docker run -it --rm -v $(shell pwd):/workspace $(DEV_IMAGE) /bin/bash