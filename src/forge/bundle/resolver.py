"""Recipe resolution: load a BundleRecipe from YAML/JSON (spec §5.2).

SP3.0 ships the loader only; catalog resolution and flag synthesis land in SP3.1.
The loader accepts both YAML and JSON (extension-driven) and validates against
the canonical ``BundleRecipe`` model — unknown keys are rejected (extra=forbid).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import BundleError
from forge.domain.recipe import BundleRecipe
from forge.repo.naming import deb_filename, rpm_arch, rpm_filename


def load_recipe(path: Path) -> BundleRecipe:
    """Read a recipe file (``.json`` → JSON, else YAML) into a ``BundleRecipe``.

    Raises ``BundleError`` for unreadable files, syntax errors, a non-mapping
    root, or schema violations (unknown keys, wrong types).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BundleError(f"cannot read recipe {path}: {exc}") from exc

    try:
        data: Any = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise BundleError(f"invalid recipe syntax in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise BundleError(f"{path}: expected a mapping at the top level, got {type(data).__name__}")

    try:
        return BundleRecipe.model_validate(data)
    except ValidationError as exc:
        raise BundleError(f"invalid recipe {path}: {exc}") from exc


class ResolvedArtifact(BaseModel):
    """One catalogue artefact selected for a bundle, with its on-disk filename."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    name: str
    version: str
    artifact: Artifact
    filename: str


def _passes(value: str | None, allowed: list[str] | None) -> bool:
    return allowed is None or value in allowed


def _resolve_one(
    entry: CatalogEntry, art: Artifact, *, targets: list[str] | None, arches: list[str] | None
) -> ResolvedArtifact | None:
    if art.type == "rpm":
        if not (_passes(art.target, targets) and _passes(art.arch, arches)):
            return None
        filename = rpm_filename(entry.name, entry.version, str(art.target), rpm_arch(art.arch))
    elif art.type == "deb":
        if not (_passes(art.target, targets) and _passes(art.arch, arches)):
            return None
        filename = deb_filename(entry.name, entry.version, str(art.arch))
    elif art.type == "grafana-dashboard":
        filename = f"{entry.name}.json"
    else:
        return None  # docker (and any future non-offline type) → SP3.5 --images
    return ResolvedArtifact(
        kind=entry.kind, name=entry.name, version=entry.version, artifact=art, filename=filename
    )


def resolve_artifacts(recipe: BundleRecipe, catalog: Catalog) -> list[ResolvedArtifact]:
    """Expand each recipe item into the catalogue artefacts to bundle.

    Looks each item up by ``(kind, name)``; the pinned version must equal the
    catalogue version (else ``BundleError``). Filters rpm/deb by the effective
    ``(targets, arches)`` (per-item, falling back to the bundle-wide ``arches``);
    dashboards are always included; docker images are skipped (SP3.5).
    """
    index = {(e.kind, e.name): e for e in catalog.items}
    resolved: list[ResolvedArtifact] = []
    for item in recipe.items:
        entry = index.get((item.kind, item.name))
        if entry is None:
            raise BundleError(f"item not in catalog: {item.kind}/{item.name}")
        if entry.version != item.version:
            raise BundleError(
                f"version mismatch for {item.name}: recipe pins {item.version}, "
                f"catalog has {entry.version}"
            )
        arches = item.arches if item.arches is not None else recipe.arches
        for art in entry.artifacts:
            one = _resolve_one(entry, art, targets=item.targets, arches=arches)
            if one is not None:
                resolved.append(one)
    return resolved
