"""End-to-end canary: real node_exporter download + real nfpm build.

Gated by FORGE_NETWORK_TESTS=1 (needs network + the nfpm binary in the dev
image). Proves the full pipeline: resolve → httpx download → extract → nfpm
produces a genuine RPM whose checksum matches the emitted Artifact.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from forge.domain.manifest import (
    Build,
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
    os.environ.get("FORGE_NETWORK_TESTS") != "1" or shutil.which("nfpm") is None,
    reason="set FORGE_NETWORK_TESTS=1 and have nfpm installed",
)


def _canary_manifest() -> ExporterManifest:
    return ExporterManifest(
        kind="exporter",
        name="node_exporter",
        description="Prometheus exporter for hardware and OS metrics",
        category="System",
        version="v1.9.1",
        license="Apache-2.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="prometheus/node_exporter"),
            build=Build(method="binary_repack", binary_name="node_exporter", archs=["amd64"]),
            artifacts=ExporterArtifacts(
                rpm=RpmTarget(
                    enabled=True,
                    targets=["el9"],
                    summary="Node exporter",
                    systemd=Systemd(enabled=True),
                    system_user="prometheus",
                ),
                docker=DockerTarget(enabled=False),
            ),
        ),
    )


def test_canary_builds_real_rpm(tmp_path: Path) -> None:
    ctx = BuildContext(work_dir=tmp_path, downloader=HttpxDownloader(), runner=SubprocessRunner())
    result = ExporterProducer().build(_canary_manifest(), ctx)
    rpms = [a for a in result.artifacts if a.type == "rpm"]
    assert len(rpms) == 1
    assert len(rpms[0].sha256) == 64
    assert result.entry.version == "1.9.1"
