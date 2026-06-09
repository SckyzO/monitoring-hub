"""Per-item ``entry.json`` persistence for the build/assemble split (spec §5).

A per-item build writes its ``CatalogEntry`` to ``<dir>/<name>.entry.json``
(atomically, on success only); ``mh catalog assemble`` loads every such file and
merges them into ``catalog.json`` via ``assemble_catalog``.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from forge.domain.catalog import CatalogEntry
from forge.domain.errors import ForgeError

_SUFFIX = ".entry.json"


def write_entry(entry: CatalogEntry, out_dir: Path) -> Path:
    """Write ``entry`` to ``<out_dir>/<name>.entry.json`` atomically; return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{entry.name}{_SUFFIX}"
    payload = json.dumps(entry.model_dump(mode="json"), indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(dir=out_dir, prefix=path.name + ".", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path


def load_entries(entries_dir: Path) -> list[CatalogEntry]:
    """Load every ``*.entry.json`` under ``entries_dir`` (sorted by filename)."""
    entries: list[CatalogEntry] = []
    for path in sorted(entries_dir.glob(f"*{_SUFFIX}")):
        try:
            entries.append(CatalogEntry.model_validate_json(path.read_text(encoding="utf-8")))
        except (OSError, ValidationError, ValueError) as exc:
            raise ForgeError(f"cannot read entry {path}: {exc}") from exc
    return entries
