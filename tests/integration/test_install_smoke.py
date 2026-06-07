"""L3 install smoke-test (spec §15): build a real package, install it on the
target distro in a container, and run the binary.

Gated by FORGE_DOCKER_TESTS=1 and needs nfpm + docker + network. This runs
OUTSIDE ``make ci`` (the dev image has no docker socket); it executes on a CI
runner or a host with docker. It is the L3 floor: prove the produced RPM/DEB is
well-formed AND runnable on the real distro, not just that nfpm reported success.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404 — invoking the host docker CLI is the point of this test
from pathlib import Path

import pytest

from forge.domain.manifest import (
    Build,
    DebTarget,
    DockerTarget,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    RpmTarget,
    Systemd,
    Upstream,
)
from forge.fetch.http import HttpxDownloader
from forge.kinds.base import BuildContext
from forge.kinds.exporter import ExporterProducer
from forge.packaging.runner import SubprocessRunner

pytestmark = pytest.mark.skipif(
    os.environ.get("FORGE_DOCKER_TESTS") != "1"
    or shutil.which("nfpm") is None
    or shutil.which("docker") is None,
    reason="set FORGE_DOCKER_TESTS=1 with nfpm + docker available",
)

_VERSION = "v1.9.1"


def _manifest(*, rpm: bool, deb: bool) -> ExporterManifest:
    return ExporterManifest(
        kind="exporter",
        name="node_exporter",
        description="Prometheus exporter for hardware and OS metrics",
        category="System",
        version=_VERSION,
        license="Apache-2.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="prometheus/node_exporter"),
            build=Build(method="binary_repack", binary_name="node_exporter", archs=["amd64"]),
            artifacts=ExporterArtifacts(
                rpm=RpmTarget(
                    enabled=rpm,
                    targets=["el9"],
                    summary="Node exporter",
                    systemd=Systemd(enabled=True),
                    system_user="prometheus",
                ),
                deb=DebTarget(
                    enabled=deb,
                    targets=["ubuntu-24.04"],
                    systemd=Systemd(enabled=True),
                    system_user="prometheus",
                ),
                docker=DockerTarget(enabled=False),
            ),
        ),
    )


def _build(tmp_path: Path, *, rpm: bool = False, deb: bool = False) -> Path:
    ctx = BuildContext(work_dir=tmp_path, downloader=HttpxDownloader(), runner=SubprocessRunner())
    ExporterProducer().build(_manifest(rpm=rpm, deb=deb), ctx)
    suffix = "rpm" if rpm else "deb"
    produced = list(tmp_path.rglob(f"*.{suffix}"))
    assert len(produced) == 1, f"expected one .{suffix}, found {produced}"
    return produced[0]


def _docker_run(image: str, pkg: Path, install_cmd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 — fixed argv, no shell at the python layer
        [
            "docker", "run", "--rm", "--platform", "linux/amd64",
            "-v", f"{pkg.parent}:/pkg:ro", image,
            "sh", "-c", install_cmd,
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )


def test_el9_rpm_installs_and_runs(tmp_path: Path) -> None:
    rpm = _build(tmp_path, rpm=True)
    result = _docker_run(
        "almalinux:9",
        rpm,
        "dnf -y install /pkg/*.rpm && node_exporter --version",
    )
    assert result.returncode == 0, result.stderr
    assert "node_exporter" in result.stdout + result.stderr


def test_ubuntu2404_deb_installs_and_runs(tmp_path: Path) -> None:
    deb = _build(tmp_path, deb=True)
    result = _docker_run(
        "ubuntu:24.04",
        deb,
        "apt-get update -qq && apt-get install -y -qq /pkg/*.deb && node_exporter --version",
    )
    assert result.returncode == 0, result.stderr
    assert "node_exporter" in result.stdout + result.stderr
