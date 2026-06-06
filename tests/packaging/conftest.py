"""Shared fixtures for packaging tests: a representative exporter manifest and
an in-memory FakeRunner that records calls and returns scripted results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from forge.domain.manifest import (
    Build,
    DebTarget,
    DockerTarget,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    FileInstall,
    RpmTarget,
    Systemd,
    Upstream,
)
from forge.packaging.runner import CommandResult


class FakeRunner:
    """Records every ``run`` call; returns a queued result (default rc=0)."""

    def __init__(self, results: list[CommandResult] | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self._results = list(results or [])

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        arg_list = list(args)
        self.calls.append(
            {"args": arg_list, "cwd": cwd, "env": dict(env) if env else None, "stdin": stdin}
        )
        if self._results:
            return self._results.pop(0)
        return CommandResult(args=arg_list, returncode=0, stdout="", stderr="")


@pytest.fixture
def manifest() -> ExporterManifest:
    return ExporterManifest(
        kind="exporter",
        name="node_exporter",
        description="Prometheus exporter for hardware and OS metrics",
        category="System",
        version="v1.9.1",
        license="Apache-2.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="prometheus/node_exporter"),
            build=Build(method="binary_repack", binary_name="node_exporter"),
            artifacts=ExporterArtifacts(
                rpm=RpmTarget(
                    enabled=True,
                    targets=["el9", "el10"],
                    summary="Node exporter",
                    install_path="/usr/bin",
                    dependencies=["shadow-utils"],
                    systemd=Systemd(enabled=True, arguments=["--web.listen-address=:9100"]),
                    system_user="prometheus",
                    extra_files=[
                        FileInstall(
                            source="assets/node.conf",
                            dest="/etc/node_exporter.conf",
                            config=True,
                        )
                    ],
                ),
                deb=DebTarget(
                    enabled=True,
                    targets=["ubuntu-24.04", "debian-12"],
                    systemd=Systemd(enabled=True, arguments=["--web.listen-address=:9100"]),
                    system_user="prometheus",
                    dependencies=["adduser"],
                    section="net",
                ),
                docker=DockerTarget(enabled=True, entrypoint=["/usr/bin/node_exporter"]),
            ),
        ),
    )
