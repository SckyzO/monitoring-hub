.PHONY: build-image sync shell lint format format-fix typecheck test security pre-commit ci check-update update

build-image:
	./dev build

sync:
	./dev run uv sync

shell:
	./dev shell

lint:
	./dev run uv run ruff check .

format:
	./dev run uv run ruff format --check .

format-fix:
	./dev run uv run ruff format .

typecheck:
	./dev run uv run mypy

test:
	./dev run uv run pytest

security:
	./dev run uv run bandit -c pyproject.toml -r src
	./dev run uv run pip-audit

pre-commit:
	./dev run uv run pre-commit run --all-files

ci: lint format typecheck test security

# Report dependencies/binaries behind their latest version (read-only).
check-update: sync
	@echo ">> Python dependencies (uv):"
	./dev run uv pip list --outdated
	@echo ">> Dev-image binary pins (Dockerfile.dev):"
	./dev run uv run python scripts/check_update.py

# Upgrade the lockfile to the latest allowed versions, then report binary pins
# to bump by hand (a binary bump needs an image rebuild + test).
update:
	./dev run uv lock --upgrade
	@echo ">> Apply any Dockerfile ARG bumps below, then 'make build-image' && 'make ci':"
	-./dev run uv run python scripts/check_update.py
