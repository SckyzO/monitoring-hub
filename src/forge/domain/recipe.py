"""BundleRecipe: a reproducible selection of catalogue items for an offline
bundle (spec §6.4).

Model placeholder only — the bundler that consumes it lands in SP3. Defining
the shape now reserves the seam so SP3 plugs in without touching the core.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RecipeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    name: str
    version: str
    overlay: str | None = None
    sha256: str | None = None
    targets: list[str] | None = None
    arches: list[str] | None = None


class BundleRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    generated_at: str | None = None
    arches: list[str] | None = None
    items: list[RecipeItem] = Field(default_factory=list)
