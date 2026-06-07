"""Project-wide fixtures (shared across test packages)."""

from __future__ import annotations

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
