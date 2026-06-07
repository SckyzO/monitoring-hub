"""Docker image adapter: pure Dockerfile rendering + DockerBuilder."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from forge.domain.artifact import Artifact
from forge.domain.errors import BuildError
from forge.domain.manifest import ExporterManifest
from forge.packaging.docker import DockerBuilder, render_dockerfile
from forge.packaging.runner import CommandResult
from tests.packaging.conftest import FakeRunner


def test_render_dockerfile_uses_base_and_entrypoint(manifest: ExporterManifest) -> None:
    df = render_dockerfile(manifest)
    assert "FROM registry.access.redhat.com/ubi9/ubi-minimal" in df
    assert "COPY node_exporter /usr/bin/node_exporter" in df
    assert 'ENTRYPOINT ["/usr/bin/node_exporter"]' in df


def test_build_image_invokes_docker_build(manifest: ExporterManifest, tmp_path: Path) -> None:
    binary = tmp_path / "node_exporter"
    binary.write_bytes(b"bin")
    runner = FakeRunner()
    artifact = DockerBuilder(runner).build_image(
        manifest, arch="amd64", binary_src=binary, work_dir=tmp_path
    )
    assert isinstance(artifact, Artifact)
    assert artifact.type == "docker-image"
    assert artifact.arch == "amd64"
    assert (tmp_path / "Dockerfile").is_file()
    call = cast("list[str]", runner.calls[0]["args"])
    assert call[0] == "docker" and "build" in call
    assert "-t" in call
    assert any("node_exporter:1.9.1" in part for part in call)


def test_build_image_raises_on_failure(manifest: ExporterManifest, tmp_path: Path) -> None:
    binary = tmp_path / "node_exporter"
    binary.write_bytes(b"bin")
    runner = FakeRunner(
        [CommandResult(args=["docker"], returncode=1, stdout="", stderr="no daemon")]
    )
    with pytest.raises(BuildError, match="no daemon"):
        DockerBuilder(runner).build_image(
            manifest, arch="amd64", binary_src=binary, work_dir=tmp_path
        )


def test_build_image_skipped_when_docker_target_disabled(
    manifest: ExporterManifest, tmp_path: Path
) -> None:
    docker_target = cast(Any, manifest.spec.artifacts.docker)
    docker_target.enabled = False
    binary = tmp_path / "node_exporter"
    binary.write_bytes(b"bin")
    with pytest.raises(BuildError, match="docker target"):
        DockerBuilder(FakeRunner()).build_image(
            manifest, arch="amd64", binary_src=binary, work_dir=tmp_path
        )
