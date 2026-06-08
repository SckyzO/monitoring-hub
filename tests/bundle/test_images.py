"""Image acquisition for the offline bundler (spec §5.5, SP3.5)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.bundle.images import RegistryImageSource
from forge.bundle.resolver import ResolvedArtifact
from forge.domain.artifact import Artifact
from forge.domain.errors import BundleError
from forge.packaging.runner import CommandResult
from tests.packaging.conftest import FakeRunner


def _img() -> ResolvedArtifact:
    return ResolvedArtifact(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        artifact=Artifact(type="docker-image", target="node_exporter:1.9.1", sha256="a" * 64),
        filename="node_exporter-1.9.1.tar",
    )


def test_registry_source_copies_one_archive_per_arch(tmp_path: Path) -> None:
    runner = FakeRunner()
    source = RegistryImageSource(registry="ghcr.io/x/mh", runner=runner)

    written = source.save(_img(), tmp_path, arches=["amd64", "arm64"])

    assert written == [
        tmp_path / "node_exporter-1.9.1-amd64.tar",
        tmp_path / "node_exporter-1.9.1-arm64.tar",
    ]
    assert cast("list[str]", runner.calls[0]["args"]) == [
        "skopeo",
        "copy",
        "--override-os",
        "linux",
        "--override-arch",
        "amd64",
        "docker://ghcr.io/x/mh/node_exporter:1.9.1",
        f"docker-archive:{tmp_path / 'node_exporter-1.9.1-amd64.tar'}:node_exporter:1.9.1",
    ]


def test_registry_source_nonzero_raises(tmp_path: Path) -> None:
    runner = FakeRunner([CommandResult(args=["skopeo"], returncode=1, stdout="", stderr="boom")])
    with pytest.raises(BundleError, match="skopeo copy"):
        RegistryImageSource(registry="ghcr.io/x/mh", runner=runner).save(
            _img(), tmp_path, arches=["amd64"]
        )
