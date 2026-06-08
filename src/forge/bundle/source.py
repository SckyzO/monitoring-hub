"""Artefact acquisition for the offline bundler (spec §5.3).

``ArtifactSource`` is the seam that turns a ``ResolvedArtifact`` into a placed
file. ``LocalDirSource`` copies from a prior ``mh build`` tree; the published
``ReleasesFetcher`` lands alongside it in the next increment.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable

from forge.bundle.resolver import ResolvedArtifact
from forge.domain.errors import BundleError


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
