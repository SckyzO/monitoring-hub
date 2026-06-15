"""Published-index fetchers: reconstruct a local repodata dir / Packages file."""

from __future__ import annotations

from pathlib import Path

from forge.repo.published import fetch_published_packages, fetch_published_repodata
from tests.fetch.conftest import FakeDownloader

_REPOMD = (
    '<?xml version="1.0"?>'
    '<repomd xmlns="http://linux.duke.edu/metadata/repo">'
    '<data type="primary"><location href="repodata/aaa-primary.xml.gz"/></data>'
    '<data type="filelists"><location href="repodata/bbb-filelists.xml.gz"/></data>'
    "</repomd>"
)


def test_fetch_repodata_pulls_repomd_and_referenced_files(tmp_path: Path) -> None:
    dl = FakeDownloader(payload=_REPOMD.encode())
    out = fetch_published_repodata(repo_url="https://pg/el9/x86_64", dest=tmp_path, downloader=dl)
    assert out == tmp_path
    assert (tmp_path / "repodata" / "repomd.xml").is_file()
    assert "https://pg/el9/x86_64/repodata/repomd.xml" in dl.urls
    assert "https://pg/el9/x86_64/repodata/aaa-primary.xml.gz" in dl.urls
    assert "https://pg/el9/x86_64/repodata/bbb-filelists.xml.gz" in dl.urls


def test_fetch_repodata_returns_none_when_absent(tmp_path: Path) -> None:
    dl = FakeDownloader(present=False)
    result = fetch_published_repodata(
        repo_url="https://pg/el9/x86_64", dest=tmp_path, downloader=dl
    )
    assert result is None


def test_fetch_packages_returns_path_or_none(tmp_path: Path) -> None:
    dl = FakeDownloader(payload=b"Package: x\n")
    out = fetch_published_packages(repo_url="https://rel/apt-noble", dest=tmp_path, downloader=dl)
    assert out == tmp_path / "Packages"
    assert (tmp_path / "Packages").read_bytes() == b"Package: x\n"
    assert (
        fetch_published_packages(
            repo_url="https://rel/apt-noble",
            dest=tmp_path,
            downloader=FakeDownloader(present=False),
        )
        is None
    )
