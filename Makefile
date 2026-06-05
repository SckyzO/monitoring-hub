.PHONY: build-image sync shell lint format format-fix typecheck test security pre-commit ci

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
