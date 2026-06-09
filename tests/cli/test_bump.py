"""mh bump: CLI wiring over forge.detect.bump (spec §8)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from forge.cli.main import cli
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
"""


def _seed(tmp_path: Path) -> Path:
    item_dir = tmp_path / "exporters" / "node_exporter"
    item_dir.mkdir(parents=True)
    manifest = item_dir / "manifest.yaml"
    manifest.write_text(_MANIFEST, encoding="utf-8")
    return manifest


def test_bump_by_name_updates_version(tmp_path: Path) -> None:
    manifest = _seed(tmp_path)
    result = CliRunner().invoke(
        cli, ["bump", "node_exporter", "--to", "v1.12.0", "--catalog-root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert "node_exporter" in result.output
    assert "v1.12.0" in result.output
    assert load_yaml_mapping(manifest)["version"] == "v1.12.0"


def test_bump_by_path_updates_version(tmp_path: Path) -> None:
    manifest = _seed(tmp_path)
    result = CliRunner().invoke(cli, ["bump", str(manifest), "--to", "v1.12.0"])
    assert result.exit_code == 0, result.output
    assert load_yaml_mapping(manifest)["version"] == "v1.12.0"


def test_bump_unknown_ref_exits_nonzero(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli, ["bump", "does_not_exist", "--to", "v1.0.0", "--catalog-root", str(tmp_path)]
    )
    assert result.exit_code != 0
    assert "does_not_exist" in result.output


def test_bump_invalid_version_exits_nonzero_without_writing(tmp_path: Path) -> None:
    manifest = _seed(tmp_path)
    before = manifest.read_text(encoding="utf-8")
    result = CliRunner().invoke(
        cli, ["bump", "node_exporter", "--to", "", "--catalog-root", str(tmp_path)]
    )
    assert result.exit_code != 0
    assert manifest.read_text(encoding="utf-8") == before
