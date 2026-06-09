"""mh build --entry-out + mh catalog assemble wiring (spec §5, §8)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from forge.catalog.builder import load_catalog, write_catalog
from forge.catalog.entries import write_entry
from forge.cli.main import cli
from forge.domain.catalog import Catalog, CatalogEntry


def _entry(name: str, version: str) -> CatalogEntry:
    return CatalogEntry(
        kind="exporter", name=name, version=version, category="System", description="d"
    )


def test_catalog_assemble_merges_entries_over_previous(tmp_path: Path) -> None:
    entries_dir = tmp_path / "entries"
    write_entry(_entry("a", "2"), entries_dir)
    prev = tmp_path / "prev.json"
    write_catalog(Catalog(generated_at="t0", items=[_entry("a", "1"), _entry("b", "1")]), prev)
    out = tmp_path / "catalog.json"

    result = CliRunner().invoke(
        cli,
        [
            "catalog",
            "assemble",
            "--entries",
            str(entries_dir),
            "--previous",
            str(prev),
            "--output",
            str(out),
        ],
    )

    assert result.exit_code == 0, result.output
    catalog = load_catalog(out)
    assert catalog is not None
    by_name = {e.name: e for e in catalog.items}
    assert by_name["a"].version == "2" and by_name["a"].updated is True
    assert by_name["b"].version == "1"  # carried over


def test_catalog_assemble_without_previous(tmp_path: Path) -> None:
    entries_dir = tmp_path / "entries"
    write_entry(_entry("a", "1"), entries_dir)
    out = tmp_path / "catalog.json"

    result = CliRunner().invoke(
        cli, ["catalog", "assemble", "--entries", str(entries_dir), "--output", str(out)]
    )

    assert result.exit_code == 0, result.output
    catalog = load_catalog(out)
    assert catalog is not None
    assert [e.name for e in catalog.items] == ["a"]
    assert catalog.items[0].new is True


def test_build_writes_entry_json_on_success(tmp_path: Path, monkeypatch) -> None:
    import forge.cli.main as main_mod  # noqa: PLC0415
    from forge.kinds.base import BuildResult  # noqa: PLC0415

    entry = _entry("node_exporter", "1.9.1")

    class _FakeProducer:
        kind = "exporter"

        def validate(self, manifest) -> None:  # noqa: ANN001
            return None

        def build(self, manifest, ctx) -> BuildResult:  # noqa: ANN001
            return BuildResult(artifacts=[], entry=entry)

    class _FakeManifest:
        kind = "exporter"
        name = "node_exporter"

    monkeypatch.setattr(main_mod, "discover", lambda: None)
    monkeypatch.setattr(main_mod, "get_producer", lambda kind: _FakeProducer())
    monkeypatch.setattr(main_mod, "resolve_manifest", lambda ref, **kwargs: _FakeManifest())

    entry_out = tmp_path / "entries"
    result = CliRunner().invoke(
        cli,
        [
            "build",
            "node_exporter",
            "--work-dir",
            str(tmp_path / "build"),
            "--entry-out",
            str(entry_out),
        ],
    )

    assert result.exit_code == 0, result.output
    written = json.loads((entry_out / "node_exporter.entry.json").read_text(encoding="utf-8"))
    assert written["name"] == "node_exporter"
    assert written["version"] == "1.9.1"
