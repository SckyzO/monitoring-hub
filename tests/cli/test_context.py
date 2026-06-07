"""CLI catalogue-root resolution (forge.cli._context)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.cli._context import resolve_catalog_root


def test_resolve_prefers_explicit_option(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_CATALOG_ROOT", "/from/env")
    assert resolve_catalog_root("/explicit") == Path("/explicit")


def test_resolve_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_CATALOG_ROOT", "/from/env")
    assert resolve_catalog_root(None) == Path("/from/env")


def test_resolve_defaults_to_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORGE_CATALOG_ROOT", raising=False)
    assert resolve_catalog_root(None) == Path("catalog")
