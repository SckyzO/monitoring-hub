"""mh pull: copy a catalogue manifest locally for customization (spec §11)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from forge.cli.main import cli


def test_pull_copies_manifest(catalog_root: Path, tmp_path: Path) -> None:
    dest = tmp_path / "work"
    res = CliRunner().invoke(
        cli,
        ["pull", "node_exporter", "--catalog-root", str(catalog_root), "--dest", str(dest)],
    )
    assert res.exit_code == 0
    copied = dest / "node_exporter" / "manifest.yaml"
    assert copied.is_file()
    assert "node_exporter" in copied.read_text()


def test_pull_missing_item_fails(catalog_root: Path, tmp_path: Path) -> None:
    res = CliRunner().invoke(
        cli,
        ["pull", "ghost", "--catalog-root", str(catalog_root), "--dest", str(tmp_path)],
    )
    assert res.exit_code != 0
