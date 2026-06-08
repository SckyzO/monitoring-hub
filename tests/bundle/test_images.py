"""Image acquisition for the offline bundler (spec §5.5, SP3.5)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.bundle.images import LocalImageSource, RegistryImageSource, save_images
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


def test_local_source_builds_and_pushes_present_arches(tmp_path: Path) -> None:
    contexts = tmp_path / "ctx"
    (contexts / "node_exporter").mkdir(parents=True)
    (contexts / "node_exporter" / "node_exporter-amd64").write_text("bin", encoding="utf-8")
    runner = FakeRunner()
    out_dir = tmp_path / "images"

    written = LocalImageSource(contexts_root=contexts, runner=runner).save(
        _img(), out_dir, arches=["amd64", "arm64"]
    )

    assert written == [out_dir / "node_exporter-1.9.1-amd64.tar"]  # arm64 has no binary → skipped
    ctx = contexts / "node_exporter"
    assert cast("list[str]", runner.calls[0]["args"]) == [
        "buildah",
        "bud",
        "--arch",
        "amd64",
        "-t",
        "node_exporter:1.9.1-amd64",
        str(ctx),
    ]
    assert cast("list[str]", runner.calls[1]["args"]) == [
        "buildah",
        "push",
        "node_exporter:1.9.1-amd64",
        f"docker-archive:{out_dir / 'node_exporter-1.9.1-amd64.tar'}:node_exporter:1.9.1",
    ]


def test_local_source_missing_context_raises(tmp_path: Path) -> None:
    with pytest.raises(BundleError, match="context not found"):
        LocalImageSource(contexts_root=tmp_path, runner=FakeRunner()).save(
            _img(), tmp_path / "o", arches=["amd64"]
        )


class _RecordingSource:
    def __init__(self) -> None:
        self.seen: list[tuple[str, list[str]]] = []

    def save(self, artifact: ResolvedArtifact, dest_dir: Path, *, arches: list[str]) -> list[Path]:
        self.seen.append((artifact.name, arches))
        return [dest_dir / f"{artifact.name}.tar"]


def test_save_images_only_docker_and_defaults_arches(tmp_path: Path) -> None:
    rpm = ResolvedArtifact(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        artifact=Artifact(type="rpm", target="el9", arch="amd64", sha256="b" * 64),
        filename="node_exporter-1.9.1-1.el9.x86_64.rpm",
    )
    src = _RecordingSource()
    written = save_images([rpm, _img()], dest_dir=tmp_path, source=src, arches=None)
    assert src.seen == [("node_exporter", ["amd64", "arm64"])]
    assert written == [tmp_path / "node_exporter.tar"]
