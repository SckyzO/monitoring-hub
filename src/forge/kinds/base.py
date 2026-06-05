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


class BuildContext(BaseModel):
    """Per-build context. Injected adapters (httpx client, nfpm/docker runners)
    are added in SP1.2 when producers become real; for now it carries the
    working directory."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    work_dir: Path


class BuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifacts: list[Artifact] = Field(default_factory=list)
    entry: CatalogEntry


@runtime_checkable
class Producer(Protocol):
    kind: str

    def validate(self, manifest: Manifest) -> None: ...

    def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult: ...
