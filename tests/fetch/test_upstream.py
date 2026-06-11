"""Pure GitHub release URL resolution from the manifest upstream block."""

from __future__ import annotations

import pytest

from forge.domain.errors import SourceResolutionError
from forge.domain.manifest import Upstream
from forge.fetch.upstream import resolve_download_url


def test_default_template_uses_clean_version_and_tag() -> None:
    up = Upstream(type="github", repo="prometheus/node_exporter")
    url = resolve_download_url(up, name="node_exporter", version="v1.9.1", arch="amd64")
    assert url == (
        "https://github.com/prometheus/node_exporter/releases/download/"
        "v1.9.1/node_exporter-1.9.1.linux-amd64.tar.gz"
    )


def test_custom_string_template() -> None:
    up = Upstream(
        type="github",
        repo="o/r",
        archive_name="{name}_{clean_version}_linux_{arch}.zip",
    )
    url = resolve_download_url(up, name="thing", version="2.0.0", arch="arm64")
    assert url.endswith("/releases/download/2.0.0/thing_2.0.0_linux_arm64.zip")


def test_per_arch_dict_template() -> None:
    up = Upstream(
        type="github",
        repo="o/r",
        archive_name={"amd64": "x86.tgz", "arm64": "aarch.tgz"},
    )
    url = resolve_download_url(up, name="t", version="v1", arch="arm64")
    assert url.endswith("/releases/download/v1/aarch.tgz")


def test_per_arch_dict_value_supports_placeholders() -> None:
    # nats_exporter / ebpf_exporter: amd64 asset is x86_64-named, not amd64.
    up = Upstream(
        type="github",
        repo="o/r",
        archive_name={"amd64": "x-v{clean_version}-x86_64.tgz"},
    )
    url = resolve_download_url(up, name="x", version="v0.20.1", arch="amd64")
    assert url.endswith("/releases/download/v0.20.1/x-v0.20.1-x86_64.tgz")


def test_dict_template_missing_arch_raises() -> None:
    up = Upstream(type="github", repo="o/r", archive_name={"amd64": "x.tgz"})
    with pytest.raises(SourceResolutionError, match="no archive_name for arch 'arm64'"):
        resolve_download_url(up, name="t", version="v1", arch="arm64")


def test_unknown_placeholder_raises() -> None:
    up = Upstream(type="github", repo="o/r", archive_name="{name}-{oops}.tgz")
    with pytest.raises(SourceResolutionError, match="placeholder"):
        resolve_download_url(up, name="t", version="v1", arch="amd64")


def test_non_github_upstream_raises() -> None:
    up = Upstream(type="local", local_binary="/bin/x")
    with pytest.raises(SourceResolutionError, match="github"):
        resolve_download_url(up, name="t", version="v1", arch="amd64")
