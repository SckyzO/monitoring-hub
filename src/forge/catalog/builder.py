"""Assemble CatalogEntry objects into the kind-agnostic catalog.json (spec §10).

``build_catalog`` is pure: it computes per-item ``new``/``updated`` by diffing
against a previous catalog (keyed by ``(kind, name)``), keeping that build-state
in ``CatalogEntry`` and off the manifest (spec §6.2). ``generated_at`` is
injectable so golden snapshots stay deterministic.
"""

from __future__ import annotations

import json
import os
import tempfile
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


def assemble_catalog(
    entries: Iterable[CatalogEntry],
    *,
    previous: Catalog | None = None,
    generated_at: str | None = None,
) -> Catalog:
    """Merge freshly built ``entries`` over ``previous``, keeping unbuilt items.

    The built entries get new/updated computed vs ``previous`` (via
    ``build_catalog``); any previous item not rebuilt this run is carried over
    with its flags reset. This is the self-healing join (spec §5, §7): a missing
    build leg leaves the previously published version in place.
    """
    built = build_catalog(entries, previous=previous, generated_at=generated_at)
    built_keys = {(e.kind, e.name) for e in built.items}
    carried = [
        item.model_copy(update={"new": False, "updated": False})
        for item in (previous.items if previous else [])
        if (item.kind, item.name) not in built_keys
    ]
    merged = sorted(built.items + carried, key=lambda e: (e.kind, e.name))
    return Catalog(generated_at=built.generated_at, items=merged)


def write_catalog(catalog: Catalog, path: Path) -> Path:
    """Serialize ``catalog`` to indented JSON at ``path`` atomically.

    Writes a sibling temp file then ``os.replace`` (atomic on POSIX) so a crash
    mid-write never leaves a truncated ``catalog.json`` (spec §5).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(catalog.model_dump(mode="json"), indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path
