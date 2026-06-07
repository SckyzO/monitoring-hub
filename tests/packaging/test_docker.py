"""Docker image adapter: pure Dockerfile rendering + daemonless context emit."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from forge.domain.errors import BuildError
from forge.domain.manifest import ExporterManifest
from forge.packaging.docker import emit_docker_context, render_dockerfile


def test_render_dockerfile_targetarch(manifest: ExporterManifest) -> None:
    df = render_dockerfile(manifest)
    assert "FROM registry.access.redhat.com/ubi9/ubi-minimal" in df
    assert "ARG TARGETARCH" in df
    assert "COPY node_exporter-${TARGETARCH} /usr/bin/node_exporter" in df
    assert 'ENTRYPOINT ["/usr/bin/node_exporter"]' in df


def test_render_dockerfile_includes_cmd(manifest: ExporterManifest) -> None:
    docker_target = cast(Any, manifest.spec.artifacts.docker)
    docker_target.cmd = ["--log.level=debug"]
    df = render_dockerfile(manifest)
    assert 'CMD ["--log.level=debug"]' in df


def _make_binary(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"bin")
    return path


def test_emit_docker_context_stages_per_arch_binaries(
    manifest: ExporterManifest, tmp_path: Path
) -> None:
    amd = _make_binary(tmp_path / "amd64" / "node_exporter")
    arm = _make_binary(tmp_path / "arm64" / "node_exporter")
    out = tmp_path / "ctx"
    art = emit_docker_context(manifest, binaries={"amd64": amd, "arm64": arm}, out_dir=out)

    assert art.type == "docker-image"
    assert art.target == "node_exporter:1.9.1"
    assert art.arch is None
    assert art.url is None
    assert not art.signed
    assert (out / "Dockerfile").is_file()
    assert (out / "node_exporter-amd64").is_file()
    assert (out / "node_exporter-arm64").is_file()


def test_emit_docker_context_uses_custom_dockerfile(
    manifest: ExporterManifest, tmp_path: Path
) -> None:
    manifest_dir = tmp_path / "exp"
    (manifest_dir / "templates").mkdir(parents=True)
    (manifest_dir / "templates" / "Dockerfile.j2").write_text(
        "FROM {{ artifacts.docker.base_image }}\nRUN echo {{ name }}\n", encoding="utf-8"
    )
    cast(Any, manifest.spec.artifacts.docker).dockerfile = "templates/Dockerfile.j2"
    out = tmp_path / "ctx"
    binary = _make_binary(tmp_path / "amd64" / "node_exporter")

    emit_docker_context(
        manifest, binaries={"amd64": binary}, out_dir=out, manifest_dir=manifest_dir
    )

    rendered = (out / "Dockerfile").read_text(encoding="utf-8")
    assert "RUN echo node_exporter" in rendered
    assert "FROM registry.access.redhat.com/ubi9/ubi-minimal" in rendered


def test_emit_docker_context_custom_without_manifest_dir_raises(
    manifest: ExporterManifest, tmp_path: Path
) -> None:
    cast(Any, manifest.spec.artifacts.docker).dockerfile = "templates/Dockerfile.j2"
    binary = _make_binary(tmp_path / "amd64" / "node_exporter")
    with pytest.raises(BuildError, match="manifest_dir"):
        emit_docker_context(manifest, binaries={"amd64": binary}, out_dir=tmp_path / "ctx")


def test_emit_docker_context_raises_when_disabled(
    manifest: ExporterManifest, tmp_path: Path
) -> None:
    cast(Any, manifest.spec.artifacts.docker).enabled = False
    with pytest.raises(BuildError, match="docker target"):
        emit_docker_context(manifest, binaries={}, out_dir=tmp_path / "ctx")
