"""Artefact acquisition for the offline bundler (spec §5.3).

``ArtifactSource`` is the seam that turns a ``ResolvedArtifact`` into a placed
file. ``LocalDirSource`` copies from a prior ``mh build`` tree; ``ReleasesFetcher``
pulls published blobs (``gh release download`` for rpm/deb, ``httpx`` for the
Pages-hosted dashboards). The release tag follows the shared
``forge.repo.naming`` convention so it can never diverge from what was published.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable

from forge.bundle.resolver import ResolvedArtifact
from forge.domain.errors import BundleError
from forge.fetch.http import Downloader
from forge.packaging.runner import CommandRunner
from forge.repo.naming import codename_for, rpm_arch


@runtime_checkable
class ArtifactSource(Protocol):
    def fetch(self, artifact: ResolvedArtifact, dest: Path) -> Path: ...


class LocalDirSource:
    """Locate an artefact by filename under a local ``mh build`` tree."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def fetch(self, artifact: ResolvedArtifact, dest: Path) -> Path:
        found = next(self._root.rglob(artifact.filename), None)
        if found is None:
            raise BundleError(f"artifact not found under {self._root}: {artifact.filename}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        return Path(shutil.copy2(found, dest))


def _release_tag(artifact: ResolvedArtifact) -> str:
    art = artifact.artifact
    if art.type == "rpm":
        return f"rpm-{art.target}-{rpm_arch(art.arch)}"
    if art.type == "deb":
        return f"apt-{codename_for(str(art.target))}"
    raise BundleError(f"no release tag for artifact type {art.type!r}")


class ReleasesFetcher:
    """Fetch published artefacts: ``gh release download`` for rpm/deb, ``httpx``
    (via ``Downloader``) for Pages-hosted artefacts by ``Artifact.url``."""

    def __init__(self, *, repo: str, runner: CommandRunner, downloader: Downloader) -> None:
        self._repo = repo
        self._runner = runner
        self._downloader = downloader

    def fetch(self, artifact: ResolvedArtifact, dest: Path) -> Path:
        art = artifact.artifact
        dest.parent.mkdir(parents=True, exist_ok=True)
        if art.type in ("rpm", "deb"):
            return self._download_release(artifact, dest)
        if art.url is None:
            raise BundleError(f"no url to fetch {artifact.kind}/{artifact.name} ({art.type})")
        return self._downloader.download(art.url, dest)

    def _download_release(self, artifact: ResolvedArtifact, dest: Path) -> Path:
        tag = _release_tag(artifact)
        result = self._runner.run(
            [
                "gh",
                "release",
                "download",
                tag,
                "--pattern",
                artifact.filename,
                "--dir",
                str(dest.parent),
                "--repo",
                self._repo,
            ]
        )
        if result.returncode != 0:
            raise BundleError(f"gh release download {tag} failed: {result.stderr}")
        (dest.parent / artifact.filename).replace(dest)
        return dest
