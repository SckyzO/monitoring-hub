"""Manifest envelope + per-kind spec discriminated union (spec §6, §7)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from forge.domain.manifest import (
    Build,
    Directory,
    FileInstall,
    Systemd,
    Upstream,
    Validation,
)


def test_systemd_defaults() -> None:
    sd = Systemd()
    assert sd.enabled is False
    assert sd.after == ["network.target"]
    assert sd.restart == "on-failure"
    assert sd.type == "simple"


def test_fileinstall_and_directory_defaults() -> None:
    fi = FileInstall(source="a.conf", dest="/etc/a.conf")
    assert fi.mode == "0644"
    assert fi.config is False
    d = Directory(path="/var/lib/x")
    assert d.mode == "0755"
    assert d.owner == "root"
    assert d.group == "root"


def test_validation_defaults() -> None:
    v = Validation()
    assert v.enabled is True
    assert v.port is None


def test_build_requires_method_and_binary_name() -> None:
    with pytest.raises(ValidationError):
        Build()  # type: ignore[call-arg]
    b = Build(method="binary_repack", binary_name="node_exporter")
    assert b.archs == ["amd64", "arm64"]


def test_upstream_github_requires_repo() -> None:
    with pytest.raises(ValidationError):
        Upstream(type="github")
    up = Upstream(type="github", repo="prometheus/node_exporter")
    assert up.strategy == "latest_release"


def test_upstream_archive_name_accepts_str_or_dict() -> None:
    assert Upstream(type="github", repo="a/b", archive_name="x-{arch}.tgz").archive_name == "x-{arch}.tgz"
    d = Upstream(type="github", repo="a/b", archive_name={"amd64": "x.tgz", "arm64": "y.tgz"})
    assert d.archive_name == {"amd64": "x.tgz", "arm64": "y.tgz"}


def test_upstream_local_requires_one_source() -> None:
    with pytest.raises(ValidationError):
        Upstream(type="local")
    with pytest.raises(ValidationError):
        Upstream(type="local", local_binary="/a", local_archive="/b.tgz")
    assert Upstream(type="local", local_binary="/usr/bin/x").type == "local"


def test_exporter_spec_packaging_defaults() -> None:
    from forge.domain.manifest import (
        DebTarget,
        DockerTarget,
        ExporterArtifacts,
        ExporterSpec,
        RpmTarget,
    )

    rpm = RpmTarget(enabled=True)
    assert rpm.targets == ["el9", "el10"]
    assert rpm.systemd.enabled is False

    deb = DebTarget(enabled=True)
    assert deb.targets == ["ubuntu-24.04", "ubuntu-26.04", "debian-12", "debian-13"]
    assert deb.section == "utils"

    docker = DockerTarget(enabled=True)
    assert docker.base_image == "registry.access.redhat.com/ubi9/ubi-minimal"

    spec = ExporterSpec(
        upstream={"type": "github", "repo": "prometheus/node_exporter"},
        build={"method": "binary_repack", "binary_name": "node_exporter"},
        artifacts=ExporterArtifacts(rpm=rpm, deb=deb, docker=docker),
    )
    assert spec.artifacts.rpm is not None
    assert spec.artifacts.rpm.targets == ["el9", "el10"]


def test_dropped_distros_still_accepted_explicitly() -> None:
    # el8 / ubuntu-22.04 are out of the AUTO defaults but remain valid manual
    # targets: the field accepts any string (spec: manual builds unaffected).
    from forge.domain.manifest import DebTarget, RpmTarget

    assert RpmTarget(enabled=True, targets=["el8"]).targets == ["el8"]
    assert DebTarget(enabled=True, targets=["ubuntu-22.04"]).targets == ["ubuntu-22.04"]
