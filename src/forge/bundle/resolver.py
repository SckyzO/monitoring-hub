"""Recipe resolution: load a BundleRecipe from YAML/JSON (spec §5.2).

SP3.0 ships the loader only; catalog resolution and flag synthesis land in SP3.1.
The loader accepts both YAML and JSON (extension-driven) and validates against
the canonical ``BundleRecipe`` model — unknown keys are rejected (extra=forbid).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import BundleError
from forge.domain.recipe import BundleRecipe, RecipeItem
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


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_selector(selector: str) -> tuple[str | None, str, str | None]:
    """Split ``[kind:]name[@version]`` into ``(kind, name, version)``."""
    kind: str | None = None
    rest = selector
    if ":" in rest:
        kind, rest = rest.split(":", 1)
    name = rest
    version: str | None = None
    if "@" in rest:
        name, version = rest.rsplit("@", 1)
    if not name:
        raise BundleError(f"invalid --item selector: {selector!r}")
    return kind or None, name, version or None


def _select_entry(
    kind: str | None,
    name: str,
    *,
    by_kind_name: dict[tuple[str, str], CatalogEntry],
    by_name: dict[str, list[CatalogEntry]],
) -> CatalogEntry:
    if kind is not None:
        entry = by_kind_name.get((kind, name))
        if entry is None:
            raise BundleError(f"item not in catalog: {kind}/{name}")
        return entry
    candidates = by_name.get(name, [])
    if not candidates:
        raise BundleError(f"item not in catalog: {name}")
    if len(candidates) > 1:
        kinds = ", ".join(sorted(c.kind for c in candidates))
        raise BundleError(f"ambiguous item {name!r} across kinds ({kinds}); qualify as kind:name")
    return candidates[0]


def recipe_from_selection(
    items: Sequence[str],
    catalog: Catalog,
    *,
    targets: Sequence[str] | None,
    arches: Sequence[str] | None,
    generated_at: str | None = None,
) -> BundleRecipe:
    """Synthesise a recipe from CLI ``[kind:]name[@version]`` selectors.

    Kind is inferred from the catalogue (qualify ``kind:name`` to disambiguate);
    version defaults to the catalogue's unless pinned. ``targets``/``arches`` are
    the global ``--target``/``--arch`` filters: ``arches`` becomes the bundle-wide
    default, ``targets`` is applied per item.
    """
    by_kind_name = {(e.kind, e.name): e for e in catalog.items}
    by_name: dict[str, list[CatalogEntry]] = {}
    for e in catalog.items:
        by_name.setdefault(e.name, []).append(e)

    recipe_items: list[RecipeItem] = []
    for selector in items:
        kind, name, version = _parse_selector(selector)
        entry = _select_entry(kind, name, by_kind_name=by_kind_name, by_name=by_name)
        recipe_items.append(
            RecipeItem(
                kind=entry.kind,
                name=entry.name,
                version=version or entry.version,
                targets=list(targets) if targets else None,
            )
        )
    return BundleRecipe(
        generated_at=generated_at or _utc_now(),
        arches=list(arches) if arches else None,
        items=recipe_items,
    )
