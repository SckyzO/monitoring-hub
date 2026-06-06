"""Item-reference resolution: load + path/name lookup + orchestration (spec §13)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.domain.errors import SourceResolutionError
from forge.sources.resolver import load_yaml_mapping


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
