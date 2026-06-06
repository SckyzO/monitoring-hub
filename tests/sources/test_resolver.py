"""Item-reference resolution: load + path/name lookup + orchestration (spec §13)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.domain.errors import SourceResolutionError
from forge.sources.resolver import load_yaml_mapping, resolve_manifest_path


def test_load_yaml_mapping_reads_mapping(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text("kind: exporter\nname: node_exporter\n", encoding="utf-8")
    assert load_yaml_mapping(path) == {"kind": "exporter", "name": "node_exporter"}


def test_load_yaml_mapping_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError):
        load_yaml_mapping(tmp_path / "nope.yaml")


def test_load_yaml_mapping_invalid_yaml_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("kind: [unterminated\n", encoding="utf-8")
    with pytest.raises(SourceResolutionError):
        load_yaml_mapping(path)


def test_load_yaml_mapping_non_mapping_root_raises(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(SourceResolutionError):
        load_yaml_mapping(path)


def _write_catalog_item(catalog_root: Path, kind_dir: str, name: str) -> Path:
    item_dir = catalog_root / kind_dir / name
    item_dir.mkdir(parents=True)
    manifest = item_dir / "manifest.yaml"
    manifest.write_text(f"kind: x\nname: {name}\n", encoding="utf-8")
    return manifest


def test_resolve_path_accepts_direct_file(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text("kind: exporter\n", encoding="utf-8")
    assert resolve_manifest_path(str(path), catalog_root=tmp_path) == path


def test_resolve_path_accepts_directory(tmp_path: Path) -> None:
    item_dir = tmp_path / "node_exporter"
    item_dir.mkdir()
    manifest = item_dir / "manifest.yaml"
    manifest.write_text("kind: exporter\n", encoding="utf-8")
    assert resolve_manifest_path(str(item_dir), catalog_root=tmp_path) == manifest


def test_resolve_path_directory_without_manifest_raises(tmp_path: Path) -> None:
    item_dir = tmp_path / "empty"
    item_dir.mkdir()
    with pytest.raises(SourceResolutionError):
        resolve_manifest_path(str(item_dir), catalog_root=tmp_path)


def test_resolve_path_by_catalogue_name(tmp_path: Path) -> None:
    manifest = _write_catalog_item(tmp_path, "exporters", "node_exporter")
    assert resolve_manifest_path("node_exporter", catalog_root=tmp_path) == manifest


def test_resolve_path_ambiguous_name_raises(tmp_path: Path) -> None:
    _write_catalog_item(tmp_path, "exporters", "shared")
    _write_catalog_item(tmp_path, "dashboards", "shared")
    with pytest.raises(SourceResolutionError, match="ambiguous"):
        resolve_manifest_path("shared", catalog_root=tmp_path)


def test_resolve_path_unknown_name_raises(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError, match="not found"):
        resolve_manifest_path("ghost", catalog_root=tmp_path)
