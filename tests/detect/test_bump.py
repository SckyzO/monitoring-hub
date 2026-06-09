"""forge.detect.bump.bump_manifest: validated atomic version write (spec §8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.detect.bump import bump_manifest
from forge.domain.errors import ManifestError, SourceResolutionError
from forge.domain.manifest import ExporterManifest
from forge.sources.resolver import load_yaml_mapping

_MANIFEST = """\
kind: exporter
name: node_exporter
description: Hardware and OS metrics exporter for Prometheus
category: System
version: v1.11.1
spec:
  upstream:
    type: github
    repo: prometheus/node_exporter
    strategy: latest_release
  build:
    method: binary_repack
    binary_name: node_exporter
  artifacts:
    rpm:
      enabled: true
      targets:
      - el9
      - el10
"""


def _write(tmp_path: Path, text: str = _MANIFEST) -> Path:
    path = tmp_path / "manifest.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_bump_sets_version_and_returns_manifest(tmp_path: Path) -> None:
    path = _write(tmp_path)
    manifest = bump_manifest(path, to="v1.12.0")
    assert isinstance(manifest, ExporterManifest)
    assert manifest.version == "v1.12.0"
    assert load_yaml_mapping(path)["version"] == "v1.12.0"


def test_bump_writes_value_verbatim_no_normalization(tmp_path: Path) -> None:
    path = _write(tmp_path)
    bump_manifest(path, to="2.0.0")
    assert load_yaml_mapping(path)["version"] == "2.0.0"


def test_bump_preserves_other_fields(tmp_path: Path) -> None:
    path = _write(tmp_path)
    bump_manifest(path, to="v1.12.0")
    data = load_yaml_mapping(path)
    assert data["name"] == "node_exporter"
    assert data["spec"]["upstream"]["repo"] == "prometheus/node_exporter"
    assert data["spec"]["artifacts"]["rpm"]["targets"] == ["el9", "el10"]


def test_bump_invalid_result_raises_and_leaves_file_untouched(tmp_path: Path) -> None:
    path = _write(tmp_path)
    before = path.read_text(encoding="utf-8")
    with pytest.raises(ManifestError):
        bump_manifest(path, to="")
    assert path.read_text(encoding="utf-8") == before


def test_bump_unknown_extra_field_still_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, _MANIFEST + "bogus: nope\n")
    with pytest.raises(ManifestError):
        bump_manifest(path, to="v1.12.0")


def test_bump_missing_file_raises_source_error(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError):
        bump_manifest(tmp_path / "nope.yaml", to="v1.12.0")
