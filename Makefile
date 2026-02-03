.PHONY: help install test test-cov lint format type-check pre-commit clean

# Variables
PYTHON := python3
VENV := .venv
PYTEST := PYTHONPATH=$(shell pwd) pytest
RUFF := ruff
MYPY := mypy

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -r core/requirements.txt
	pre-commit install

test: ## Run tests
	$(PYTEST) -v

test-cov: ## Run tests with coverage report
	$(PYTEST) -v --cov=core --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	$(PYTEST) -v --no-cov

test-parallel: ## Run tests in parallel
	$(PYTEST) -v -n auto

lint: ## Run linting checks
	$(RUFF) check core/

lint-fix: ## Run linting and auto-fix issues
	$(RUFF) check --fix core/

format: ## Format code with ruff
	$(RUFF) format core/

format-check: ## Check code formatting without modifying
	$(RUFF) format --check core/

type-check: ## Run type checking with mypy
	$(MYPY) core/

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

clean: ## Clean up generated files
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean ## Clean everything including venv
	rm -rf $(VENV)

validate: lint type-check test ## Run all validation checks

ci: lint format-check type-check test ## Run all CI checks
