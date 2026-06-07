"""Producer protocol and build I/O models (spec §9).

A ``Producer`` validates a manifest of its kind, then builds it into a
``BuildResult`` (``[Artifact]`` + ``CatalogEntry``). Producer *implementations*
(exporter, dashboard) land in SP1.2+; this module is the contract only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.manifest import Manifest
from forge.fetch.http import Downloader
from forge.packaging.runner import CommandRunner


class BuildContext(BaseModel):
    """Per-build context with the injected I/O seams (spec §15): the network
    ``Downloader``, the subprocess ``CommandRunner`` used by the packaging
    adapters, an optional GPG ``signing_key_id`` (signing is skipped when None),
    and the working directory.

    ``manifest_dir`` is the directory the manifest was loaded from; it resolves a
    manifest's committed ``assets/`` and a custom ``docker.dockerfile`` template.
    ``None`` for manifests built programmatically (e.g. in unit tests)."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    work_dir: Path
    downloader: Downloader
    runner: CommandRunner
    signing_key_id: str | None = None
    manifest_dir: Path | None = None


class BuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifacts: list[Artifact] = Field(default_factory=list)
    entry: CatalogEntry


@runtime_checkable
class Producer(Protocol):
    kind: str

    def validate(self, manifest: Manifest) -> None: ...

    def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult: ...
