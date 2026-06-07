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


class Catalog(BaseModel):
    """The kind-agnostic catalog.json envelope (spec §10).

    ``generated_at`` is a plain ISO-8601 UTC string (injectable by the builder so
    golden snapshots stay deterministic). ``schema_version`` guards forward
    compatibility for the website and the offline bundler.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    generated_at: str
    items: list[CatalogEntry] = Field(default_factory=list)
