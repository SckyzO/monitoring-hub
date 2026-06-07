"""Golden tests for the pure nfpm config mapping (the contract core)."""

from __future__ import annotations

from typing import Any

import pytest

from forge.domain.manifest import (
    Build,
    DebTarget,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    RpmTarget,
    Upstream,
)
from forge.packaging.nfpm import build_nfpm_config


def _minimal(*, rpm: RpmTarget | None = None, deb: DebTarget | None = None) -> ExporterManifest:
    return ExporterManifest(
        kind="exporter",
        name="x_exp",
        description="d",
        version="1.0.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="o/r"),
            build=Build(method="binary_repack", binary_name="x_exp"),
            artifacts=ExporterArtifacts(rpm=rpm, deb=deb),
        ),
    )


def _cfg(manifest: ExporterManifest, packager: str, target: str, arch: str) -> dict[str, Any]:
    return build_nfpm_config(
        manifest,
        packager=packager,  # type: ignore[arg-type]
        target=target,
        arch=arch,
        binary_dst="/usr/bin/node_exporter",
        contents_extra=[],
        scripts={},
    )


def test_rpm_config_core_fields(manifest: ExporterManifest) -> None:
    cfg = _cfg(manifest, "rpm", "el9", "amd64")
    assert cfg["name"] == "node_exporter"  # rpm keeps underscores
    assert cfg["arch"] == "amd64"
    assert cfg["version"] == "1.9.1"  # leading v stripped
    assert cfg["release"] == "1.el9"  # dist tag
    assert cfg["license"] == "Apache-2.0"
    assert cfg["depends"] == ["shadow-utils"]
    assert cfg["rpm"]["summary"] == "Node exporter"


def test_deb_config_normalizes_name_and_section(manifest: ExporterManifest) -> None:
    cfg = _cfg(manifest, "deb", "ubuntu-24.04", "arm64")
    assert cfg["name"] == "node-exporter"  # deb normalizes _ -> -
    assert cfg["arch"] == "arm64"
    assert cfg["release"] == "1"
    assert cfg["section"] == "net"
    assert cfg["priority"] == "optional"
    assert cfg["depends"] == ["adduser"]


def test_binary_is_first_content_with_mode_0755(manifest: ExporterManifest) -> None:
    cfg = _cfg(manifest, "rpm", "el9", "amd64")
    binary = cfg["contents"][0]
    assert binary["dst"] == "/usr/bin/node_exporter"
    assert binary["file_info"]["mode"] == 0o755


def test_extra_files_become_config_contents(manifest: ExporterManifest) -> None:
    cfg = _cfg(manifest, "rpm", "el9", "amd64")
    confs = [c for c in cfg["contents"] if c.get("type") == "config"]
    assert any(c["dst"] == "/etc/node_exporter.conf" for c in confs)


def test_contents_extra_and_scripts_are_threaded(manifest: ExporterManifest) -> None:
    cfg = build_nfpm_config(
        manifest,
        packager="rpm",
        target="el9",
        arch="amd64",
        binary_dst="/usr/bin/node_exporter",
        contents_extra=[
            {
                "src": "/w/node_exporter.service",
                "dst": "/lib/systemd/system/node_exporter.service",
            }
        ],
        scripts={"postinstall": "/w/postinstall.sh", "preremove": "/w/preremove.sh"},
    )
    assert any(c["dst"].endswith("node_exporter.service") for c in cfg["contents"])
    assert cfg["scripts"]["postinstall"] == "/w/postinstall.sh"
    assert cfg["scripts"]["preremove"] == "/w/preremove.sh"


def test_maintainer_and_homepage_present(manifest: ExporterManifest) -> None:
    cfg = _cfg(manifest, "deb", "debian-12", "amd64")
    assert cfg["maintainer"]
    assert cfg["description"].startswith("Prometheus exporter")


def test_build_config_raises_without_rpm_target() -> None:
    manifest = _minimal(deb=DebTarget(enabled=True))
    with pytest.raises(ValueError, match="no rpm"):
        build_nfpm_config(
            manifest,
            packager="rpm",
            target="el9",
            arch="amd64",
            binary_dst="/usr/bin/x_exp",
            contents_extra=[],
            scripts={},
        )


def test_build_config_raises_without_deb_target() -> None:
    manifest = _minimal(rpm=RpmTarget(enabled=True))
    with pytest.raises(ValueError, match="no deb"):
        build_nfpm_config(
            manifest,
            packager="deb",
            target="ubuntu-24.04",
            arch="amd64",
            binary_dst="/usr/bin/x_exp",
            contents_extra=[],
            scripts={},
        )
