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
