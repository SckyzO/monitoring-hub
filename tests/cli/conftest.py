"""CLI test fixtures: a tmp catalogue tree and a fake producer (no real builds)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.manifest import Manifest
from forge.kinds.base import BuildContext, BuildResult

_EXPORTER = {
    "kind": "exporter",
    "name": "node_exporter",
    "description": "Hardware and OS metrics exporter",
    "category": "System",
    "version": "1.0.0",
    "spec": {
        "upstream": {"type": "github", "repo": "prometheus/node_exporter"},
        "build": {"method": "binary_repack", "binary_name": "node_exporter"},
        "artifacts": {"rpm": {"enabled": True, "targets": ["el9"]}},
    },
}


@pytest.fixture
def catalog_root(tmp_path: Path) -> Path:
    """A minimal catalogue with one valid exporter manifest."""
    item = tmp_path / "catalog" / "exporters" / "node_exporter"
    item.mkdir(parents=True)
    (item / "manifest.yaml").write_text(yaml.safe_dump(_EXPORTER), encoding="utf-8")
    return tmp_path / "catalog"


class FakeProducer:
    """A producer that emits a fixed artifact without touching nfpm/docker/network."""

    kind = "exporter"

    def validate(self, manifest: Manifest) -> None:
        return None

    def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult:
        entry = CatalogEntry(
            kind=manifest.kind,
            name=manifest.name,
            version=manifest.version,
            category=manifest.category,
            description=manifest.description,
        )
        artifact = Artifact(type="rpm", target="el9", arch="amd64", sha256="abc")
        return BuildResult(artifacts=[artifact], entry=entry)
