"""Assemble CatalogEntry objects into the kind-agnostic catalog.json (spec §10).

``build_catalog`` is pure: it computes per-item ``new``/``updated`` by diffing
against a previous catalog (keyed by ``(kind, name)``), keeping that build-state
in ``CatalogEntry`` and off the manifest (spec §6.2). ``generated_at`` is
injectable so golden snapshots stay deterministic.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import ForgeError


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_catalog(
    entries: Iterable[CatalogEntry],
    *,
    previous: Catalog | None = None,
    generated_at: str | None = None,
) -> Catalog:
    """Assemble ``entries`` into a Catalog, computing new/updated vs ``previous``."""
    prior: Mapping[tuple[str, str], str] = (
        {(e.kind, e.name): e.version for e in previous.items} if previous else {}
    )
    items: list[CatalogEntry] = []
    for entry in entries:
        old_version = prior.get((entry.kind, entry.name))
        items.append(
            entry.model_copy(
                update={
                    "new": old_version is None,
                    "updated": old_version is not None and old_version != entry.version,
                }
            )
        )
    return Catalog(generated_at=generated_at or _utc_now(), items=items)


def load_catalog(path: Path) -> Catalog | None:
    """Load a previous catalog.json; return ``None`` if the file does not exist."""
    if not path.is_file():
        return None
    try:
        return Catalog.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise ForgeError(f"cannot read catalog {path}: {exc}") from exc


def write_catalog(catalog: Catalog, path: Path) -> Path:
    """Serialize ``catalog`` to indented JSON at ``path`` (creating parents)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(catalog.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return path
