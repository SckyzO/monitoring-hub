"""catalog.builder: assemble catalog.json + new/updated diff (spec §10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.catalog.builder import assemble_catalog, build_catalog, load_catalog, write_catalog
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import ForgeError


def _entry(name: str, version: str) -> CatalogEntry:
    return CatalogEntry(
        kind="exporter", name=name, version=version, category="System", description="d"
    )


def test_build_catalog_marks_new_when_absent_from_previous() -> None:
    cat = build_catalog([_entry("a", "1")], previous=None, generated_at="t")
    assert cat.schema_version == 1
    assert cat.generated_at == "t"
    assert cat.items[0].new is True
    assert cat.items[0].updated is False


def test_build_catalog_marks_updated_on_version_change() -> None:
    prev = Catalog(generated_at="t0", items=[_entry("a", "1")])
    cat = build_catalog([_entry("a", "2")], previous=prev, generated_at="t1")
    assert cat.items[0].new is False
    assert cat.items[0].updated is True


def test_build_catalog_unchanged_entry_has_no_flags() -> None:
    prev = Catalog(generated_at="t0", items=[_entry("a", "1")])
    cat = build_catalog([_entry("a", "1")], previous=prev, generated_at="t1")
    assert cat.items[0].new is False
    assert cat.items[0].updated is False


def test_build_catalog_generated_at_defaults_to_utc() -> None:
    cat = build_catalog([], previous=None)
    assert cat.generated_at.endswith("Z")


def test_load_catalog_missing_returns_none(tmp_path: Path) -> None:
    assert load_catalog(tmp_path / "nope.json") is None


def test_load_catalog_corrupt_raises(tmp_path: Path) -> None:
    bad = tmp_path / "catalog.json"
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(ForgeError, match="cannot read catalog"):
        load_catalog(bad)


def test_write_then_load_round_trips(tmp_path: Path) -> None:
    cat = build_catalog([_entry("a", "1")], previous=None, generated_at="t")
    out = tmp_path / "sub" / "catalog.json"
    write_catalog(cat, out)
    again = load_catalog(out)
    assert again is not None
    assert again.items[0].name == "a"
    assert again.items[0].new is True


def test_write_catalog_leaves_no_temp_file(tmp_path: Path) -> None:
    cat = build_catalog([_entry("a", "1")], previous=None, generated_at="t")
    out = tmp_path / "catalog.json"
    write_catalog(cat, out)
    assert out.is_file()
    assert list(tmp_path.glob("*.tmp")) == []


def test_write_catalog_failure_preserves_existing(tmp_path: Path, monkeypatch) -> None:
    import forge.catalog.builder as builder_mod  # noqa: PLC0415

    out = tmp_path / "catalog.json"
    write_catalog(build_catalog([_entry("a", "1")], generated_at="t0"), out)
    original = out.read_text(encoding="utf-8")

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(builder_mod.os, "replace", boom)
    with pytest.raises(OSError, match="disk full"):
        write_catalog(build_catalog([_entry("a", "2")], generated_at="t1"), out)

    assert out.read_text(encoding="utf-8") == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_assemble_keeps_unbuilt_previous_items() -> None:
    prev = Catalog(generated_at="t0", items=[_entry("a", "1"), _entry("b", "1")])
    cat = assemble_catalog([_entry("a", "2")], previous=prev, generated_at="t1")
    by_name = {e.name: e for e in cat.items}
    assert by_name["a"].version == "2"
    assert by_name["a"].updated is True
    assert by_name["b"].version == "1"  # carried over
    assert by_name["b"].new is False and by_name["b"].updated is False


def test_assemble_adds_new_item_alongside_previous() -> None:
    prev = Catalog(generated_at="t0", items=[_entry("a", "1")])
    cat = assemble_catalog([_entry("c", "1")], previous=prev, generated_at="t1")
    by_name = {e.name: e for e in cat.items}
    assert set(by_name) == {"a", "c"}
    assert by_name["c"].new is True


def test_assemble_no_previous_equals_build() -> None:
    cat = assemble_catalog([_entry("a", "1")], previous=None, generated_at="t")
    assert [e.name for e in cat.items] == ["a"]
    assert cat.items[0].new is True


def test_assemble_items_sorted_by_kind_name() -> None:
    prev = Catalog(generated_at="t0", items=[_entry("b", "1")])
    cat = assemble_catalog([_entry("a", "1")], previous=prev, generated_at="t1")
    assert [e.name for e in cat.items] == ["a", "b"]
