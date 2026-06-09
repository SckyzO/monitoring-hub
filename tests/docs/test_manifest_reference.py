"""The shipped manifest reference must always parse under the current schema."""

from __future__ import annotations

from pathlib import Path

from forge.domain.manifest import ExporterManifest, parse_manifest
from forge.sources.resolver import load_yaml_mapping

_REFERENCE = Path(__file__).resolve().parents[2] / "docs" / "user-guide" / "manifest.reference.yaml"


def test_manifest_reference_is_a_valid_exporter() -> None:
    manifest = parse_manifest(load_yaml_mapping(_REFERENCE))
    assert isinstance(manifest, ExporterManifest)
    assert manifest.name
    assert manifest.spec.artifacts.rpm is not None
    assert manifest.spec.artifacts.deb is not None
    assert manifest.spec.artifacts.docker is not None
