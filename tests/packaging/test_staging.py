"""Asset staging: copy a manifest's committed assets/ into the build dir."""

from __future__ import annotations

from pathlib import Path

from forge.packaging.staging import stage_assets


def test_stage_assets_copies_tree(tmp_path: Path) -> None:
    src = tmp_path / "manifest"
    (src / "assets").mkdir(parents=True)
    (src / "assets" / "config.yml").write_text("k: v\n", encoding="utf-8")
    dest = tmp_path / "work"
    dest.mkdir()

    stage_assets(src, dest)

    assert (dest / "assets" / "config.yml").read_text(encoding="utf-8") == "k: v\n"


def test_stage_assets_noop_without_manifest_dir(tmp_path: Path) -> None:
    stage_assets(None, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_stage_assets_noop_without_assets_subdir(tmp_path: Path) -> None:
    src = tmp_path / "manifest"
    src.mkdir()
    dest = tmp_path / "work"
    dest.mkdir()

    stage_assets(src, dest)

    assert list(dest.iterdir()) == []
