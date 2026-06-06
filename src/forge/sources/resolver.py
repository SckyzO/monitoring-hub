"""Resolve an item reference (catalogue name or path) into a typed Manifest (spec §13)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from forge.domain.errors import SourceResolutionError

_MANIFEST_FILENAME = "manifest.yaml"
_KIND_DIRS = ("exporters", "dashboards")


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Read a YAML file and return its top-level mapping.

    Raises ``SourceResolutionError`` for unreadable files, YAML syntax errors,
    or a non-mapping document root.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceResolutionError(f"cannot read {path}: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SourceResolutionError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SourceResolutionError(
            f"{path}: expected a mapping at the top level, got {type(data).__name__}"
        )
    return data


def resolve_manifest_path(ref: str, *, catalog_root: Path) -> Path:
    """Resolve an item reference to a manifest file path.

    Resolution order: an existing file path → an existing directory containing
    ``manifest.yaml`` → a catalogue name found under
    ``catalog_root/{exporters,dashboards}/<name>/manifest.yaml``. A name found in
    more than one kind directory is ambiguous; a name found nowhere is not found.
    """
    candidate = Path(ref)
    if candidate.is_file():
        return candidate
    if candidate.is_dir():
        manifest = candidate / _MANIFEST_FILENAME
        if manifest.is_file():
            return manifest
        raise SourceResolutionError(f"no {_MANIFEST_FILENAME} in directory {candidate}")

    matches = [
        catalog_root / kind_dir / ref / _MANIFEST_FILENAME
        for kind_dir in _KIND_DIRS
        if (catalog_root / kind_dir / ref / _MANIFEST_FILENAME).is_file()
    ]
    match matches:
        case [single]:
            return single
        case []:
            raise SourceResolutionError(f"item {ref!r} not found as a path or in {catalog_root}")
        case _:
            joined = ", ".join(str(m) for m in matches)
            raise SourceResolutionError(f"ambiguous item {ref!r}: found in {joined}")
