"""Fetch the published serving index into a local dir for metadata-only merge.

The published index is the durable state (spec §4): rpm ``repodata/`` lives on
Pages, the flat apt ``Packages`` lives in the ``apt-<codename>`` release. These
fetchers reconstruct a local copy so ``mergerepo_c`` / the stanza splice can run
without any package blob present. ``None`` means the coordinate is not published
yet (first build / new coordinate) — the caller falls back to a full build.
"""

from __future__ import annotations

from pathlib import Path

import defusedxml.ElementTree as ET  # hardened parser (XXE / billion-laughs safe)

from forge.fetch.http import Downloader

_NS = "{http://linux.duke.edu/metadata/repo}"


def fetch_published_repodata(*, repo_url: str, dest: Path, downloader: Downloader) -> Path | None:
    """Download ``repomd.xml`` + every referenced data file under ``dest/repodata/``.

    ``repo_url`` is the repo root (the dir that contains ``repodata/``). Returns
    ``dest`` when published, else ``None``.
    """
    if not downloader.exists(f"{repo_url}/repodata/repomd.xml"):
        return None
    repodata = dest / "repodata"
    repodata.mkdir(parents=True, exist_ok=True)
    repomd = downloader.download(f"{repo_url}/repodata/repomd.xml", repodata / "repomd.xml")
    root = ET.parse(repomd).getroot()
    if root is None:
        return dest
    for data in root.findall(f"{_NS}data"):
        location = data.find(f"{_NS}location")
        href = location.get("href") if location is not None else None
        if href:
            downloader.download(f"{repo_url}/{href}", dest / href)
    return dest


def fetch_published_packages(*, repo_url: str, dest: Path, downloader: Downloader) -> Path | None:
    """Download the flat apt ``Packages`` file into ``dest/Packages`` (or ``None``)."""
    url = f"{repo_url}/Packages"
    if not downloader.exists(url):
        return None
    return downloader.download(url, dest / "Packages")
