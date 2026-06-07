"""Downloader seam: protocol conformance + a gated real download."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from forge.domain.errors import SourceResolutionError
from forge.fetch.http import Downloader, HttpxDownloader
from tests.fetch.conftest import FakeDownloader


def test_httpx_downloader_satisfies_protocol() -> None:
    assert isinstance(HttpxDownloader(), Downloader)


def test_fake_downloader_satisfies_protocol() -> None:
    assert isinstance(FakeDownloader(), Downloader)


def test_download_bad_url_raises_source_error(tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError):
        HttpxDownloader(retries=1, timeout=2.0).download(
            "https://0.0.0.0/nope.tar.gz", tmp_path / "out"
        )


@pytest.mark.skipif(
    os.environ.get("FORGE_NETWORK_TESTS") != "1",
    reason="set FORGE_NETWORK_TESTS=1 to run network tests",
)
def test_real_download_writes_file(tmp_path: Path) -> None:
    url = (
        "https://github.com/prometheus/node_exporter/releases/download/"
        "v1.9.1/sha256sums.txt"
    )
    dest = HttpxDownloader().download(url, tmp_path / "sha256sums.txt")
    assert dest.is_file()
    assert dest.stat().st_size > 0
