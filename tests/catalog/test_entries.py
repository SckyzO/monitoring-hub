"""catalog.entries: per-item entry.json write + load (spec §5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.catalog.entries import load_entries, write_entry
from forge.domain.catalog import CatalogEntry
from forge.domain.errors import ForgeError


def _entry(name: str, version: str) -> CatalogEntry:
    return CatalogEntry(
        kind="exporter", name=name, version=version, category="System", description="d"
    )


def test_write_entry_round_trips(tmp_path: Path) -> None:
    out = write_entry(_entry("node_exporter", "1.9.1"), tmp_path)
    assert out == tmp_path / "node_exporter.entry.json"
    [loaded] = load_entries(tmp_path)
    assert loaded.name == "node_exporter"
    assert loaded.version == "1.9.1"


def test_write_entry_leaves_no_temp_file(tmp_path: Path) -> None:
    write_entry(_entry("a", "1"), tmp_path)
    assert list(tmp_path.glob("*.tmp")) == []


def test_load_entries_sorted_by_filename(tmp_path: Path) -> None:
    write_entry(_entry("b", "1"), tmp_path)
    write_entry(_entry("a", "1"), tmp_path)
    assert [e.name for e in load_entries(tmp_path)] == ["a", "b"]


def test_load_entries_empty_dir_returns_empty(tmp_path: Path) -> None:
    assert load_entries(tmp_path) == []


def test_load_entries_corrupt_raises(tmp_path: Path) -> None:
    (tmp_path / "bad.entry.json").write_text("{ not json", encoding="utf-8")
    with pytest.raises(ForgeError, match="cannot read entry"):
        load_entries(tmp_path)
