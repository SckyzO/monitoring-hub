"""SP3.5 gated smoke: a locally built image survives bundle → docker load → run offline.

Daemonless build (buildah, FROM scratch — no pull), exported to docker-archive, then
loaded and run with --network none to prove the air-gapped path end-to-end.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404 — driving host buildah/docker is the point
from pathlib import Path

import pytest

from forge.bundle.images import LocalImageSource
from forge.bundle.resolver import ResolvedArtifact
from forge.domain.artifact import Artifact
from forge.packaging.runner import SubprocessRunner

_TOOLS = ("buildah", "docker", "tar")
pytestmark = pytest.mark.skipif(
    os.environ.get("FORGE_DOCKER_TESTS") != "1" or any(shutil.which(t) is None for t in _TOOLS),
    reason="needs FORGE_DOCKER_TESTS=1 and buildah/docker/tar",
)


def _img() -> ResolvedArtifact:
    return ResolvedArtifact(
        kind="exporter",
        name="hello",
        version="1.0.0",
        artifact=Artifact(type="docker-image", target="hello:1.0.0", sha256="a" * 64),
        filename="hello-1.0.0.tar",
    )


def test_local_image_loads_and_runs_offline(tmp_path: Path) -> None:
    # minimal FROM scratch context: a static busybox copied in as the entrypoint
    busybox = shutil.which("busybox")
    if busybox is None:
        pytest.skip("needs a static busybox on PATH")
    ctx = tmp_path / "ctx" / "hello"
    ctx.mkdir(parents=True)
    shutil.copy2(busybox, ctx / "hello-amd64")
    (ctx / "Dockerfile").write_text(
        'FROM scratch\nCOPY hello-amd64 /bin/busybox\nENTRYPOINT ["/bin/busybox"]\n',
        encoding="utf-8",
    )

    out_dir = tmp_path / "images"
    written = LocalImageSource(contexts_root=tmp_path / "ctx", runner=SubprocessRunner()).save(
        _img(), out_dir, arches=["amd64"]
    )
    archive = written[0]
    assert archive.exists()

    subprocess.run(["docker", "load", "-i", str(archive)], check=True)  # noqa: S603
    run = subprocess.run(  # noqa: S603
        ["docker", "run", "--rm", "--network", "none", "hello:1.0.0", "echo", "ok"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert run.stdout.strip() == "ok"
    subprocess.run(["docker", "rmi", "-f", "hello:1.0.0"], check=False)  # noqa: S603
