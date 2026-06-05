"""CatalogEntry: a single item in the kind-agnostic catalog.json (spec §10).

``new`` / ``updated`` are catalog-build state (diffed against the previous
catalog.json), deliberately kept off the manifest (spec §6.2).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from forge.domain.artifact import Artifact


class CatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    name: str
    version: str
    category: str
    description: str
    artifacts: list[Artifact] = Field(default_factory=list)
    new: bool = False
    updated: bool = False
