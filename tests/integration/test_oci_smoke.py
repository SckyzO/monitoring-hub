"""Gated OCI smoke (spec §9.3): build a multi-arch image once and push it to TWO
throwaway insecure local registries; assert skopeo resolves a multi-arch manifest
list on each. Proves build-once-push-many. Outside ``make ci`` (forge-smoke.yml).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # noqa: S404 — driving host buildah/skopeo/docker is the point
import time
from pathlib import Path

import pytest

from forge.packaging.runner import SubprocessRunner
from forge.publish.oci import OciPublisher

pytestmark = pytest.mark.skipif(
    os.environ.get("FORGE_DOCKER_TESTS") != "1"
    or any(shutil.which(t) is None for t in ("buildah", "skopeo", "docker")),
    reason="set FORGE_DOCKER_TESTS=1 with buildah+skopeo+docker",
)

_PORTS = (5000, 5001)
_NAME = "smoke_exporter"
_VERSION = "0.0.1"


def _emit_context(staging: Path) -> None:
    ctx = staging / _NAME
    ctx.mkdir(parents=True)
    (ctx / "Dockerfile").write_text(
        "FROM scratch\nARG TARGETARCH\nCOPY " + _NAME + "-${TARGETARCH} /app\n",
        encoding="utf-8",
    )
    for arch in ("amd64", "arm64"):
        (ctx / f"{_NAME}-{arch}").write_bytes(b"\x7fELF" + bytes(64))


def _start_registry(port: int) -> str:
    cid = subprocess.run(  # noqa: S603
        ["docker", "run", "-d", "-p", f"{port}:5000", "registry:2"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    time.sleep(2)
    return cid


def _resolve_arches(port: int) -> set[str]:
    raw = subprocess.run(  # noqa: S603
        [
            "skopeo",
            "inspect",
            "--tls-verify=false",
            "--raw",
            f"docker://localhost:{port}/mh/{_NAME}:{_VERSION}",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    manifest = json.loads(raw)
    return {m["platform"]["architecture"] for m in manifest.get("manifests", [])}


def test_oci_multiarch_manifest_pushes_to_each_registry(tmp_path: Path) -> None:
    staging = tmp_path / "docker"
    _emit_context(staging)
    cids = [_start_registry(p) for p in _PORTS]
    try:
        OciPublisher(
            registries=[f"localhost:{p}/mh" for p in _PORTS],
            versions={_NAME: _VERSION},
            runner=SubprocessRunner(),
            tls_verify=False,
        ).publish(staging)

        for port in _PORTS:
            arches = _resolve_arches(port)
            assert {"amd64", "arm64"} <= arches, f"port {port}: {arches}"
    finally:
        for cid in cids:
            subprocess.run(  # noqa: S603
                ["docker", "rm", "-f", cid], check=False, capture_output=True
            )
