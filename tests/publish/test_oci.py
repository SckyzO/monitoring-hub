"""OciPublisher: emits buildah/skopeo commands for a multi-arch manifest list."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from forge.domain.errors import PublishError
from forge.packaging.runner import CommandResult
from forge.publish.oci import OciPublisher


class RecordingRunner:
    """Records every command; returns a configurable returncode."""

    def __init__(self, returncode: int = 0, stderr: str = "") -> None:
        self.calls: list[list[str]] = []
        self._returncode = returncode
        self._stderr = stderr

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        argv = list(args)
        self.calls.append(argv)
        return CommandResult(args=argv, returncode=self._returncode, stdout="", stderr=self._stderr)


def _context(staging: Path, name: str, arches: tuple[str, ...]) -> None:
    ctx = staging / name
    ctx.mkdir(parents=True)
    (ctx / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    for arch in arches:
        (ctx / f"{name}-{arch}").write_bytes(b"x")


def test_oci_publisher_builds_manifest_list(tmp_path: Path) -> None:
    staging = tmp_path / "docker"
    _context(staging, "node_exporter", ("amd64", "arm64"))
    runner = RecordingRunner()

    OciPublisher(
        registry="ghcr.io/sckyzo/monitoring-hub",
        versions={"node_exporter": "1.9.1"},
        runner=runner,
    ).publish(staging)

    flat = [" ".join(c) for c in runner.calls]
    ref = "ghcr.io/sckyzo/monitoring-hub/node_exporter:1.9.1"
    assert any(f"buildah bud --arch amd64 -t {ref}-amd64" in c for c in flat)
    assert any(f"buildah bud --arch arm64 -t {ref}-arm64" in c for c in flat)
    assert any(f"buildah manifest create {ref}" in c for c in flat)
    assert any(f"buildah manifest add {ref} {ref}-amd64" in c for c in flat)
    assert any(f"buildah manifest add {ref} {ref}-arm64" in c for c in flat)
    assert any(f"buildah manifest push --all {ref} docker://{ref}" in c for c in flat)
    assert any(
        "skopeo copy" in c
        and f"docker://{ref}" in c
        and "docker://ghcr.io/sckyzo/monitoring-hub/node_exporter:latest" in c
        for c in flat
    )


def test_oci_publisher_single_arch_skips_missing(tmp_path: Path) -> None:
    staging = tmp_path / "docker"
    _context(staging, "single", ("amd64",))
    runner = RecordingRunner()

    OciPublisher(registry="r", versions={"single": "2.0.0"}, runner=runner).publish(staging)

    flat = [" ".join(c) for c in runner.calls]
    assert any("--arch amd64" in c for c in flat)
    assert not any("--arch arm64" in c for c in flat)


def test_oci_publisher_insecure_disables_tls(tmp_path: Path) -> None:
    staging = tmp_path / "docker"
    _context(staging, "node_exporter", ("amd64",))
    runner = RecordingRunner()

    OciPublisher(
        registry="localhost:5000/mh",
        versions={"node_exporter": "1.9.1"},
        runner=runner,
        tls_verify=False,
    ).publish(staging)

    flat = [" ".join(c) for c in runner.calls]
    assert any("buildah manifest push --all --tls-verify=false" in c for c in flat)
    assert any("skopeo copy --src-tls-verify=false --dest-tls-verify=false" in c for c in flat)


def test_oci_publisher_raises_on_failure(tmp_path: Path) -> None:
    staging = tmp_path / "docker"
    _context(staging, "node_exporter", ("amd64",))
    runner = RecordingRunner(returncode=1, stderr="boom")

    with pytest.raises(PublishError, match="buildah failed: boom"):
        OciPublisher(registry="r", versions={"node_exporter": "1.9.1"}, runner=runner).publish(
            staging
        )
