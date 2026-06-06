"""Resolve an item reference (catalogue name or path) into a typed Manifest (spec §13)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from forge.domain.errors import SourceResolutionError


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
