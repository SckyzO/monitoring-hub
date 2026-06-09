"""Detection contract (spec §4).

``DetectedVersion`` is the structured result of comparing a manifest's pinned
version against its upstream. ``VersionSource`` is the per-source-type Protocol;
implementations (``github-release`` in SP4.1) register via ``detect.registry``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol, runtime_checkable

from forge.domain.manifest import Manifest
from forge.packaging.runner import CommandRunner


@dataclass(frozen=True)
class DetectedVersion:
    """One manifest's current-vs-latest comparison."""

    item: str
    kind: str
    current: str
    latest: str
    source_type: str
    outdated: bool


@runtime_checkable
class VersionSource(Protocol):
    """Resolve the latest upstream version for a manifest of a given source type."""

    type: ClassVar[str]

    def latest(self, manifest: Manifest, *, runner: CommandRunner) -> str | None: ...
