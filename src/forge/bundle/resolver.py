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
from pydantic import ValidationError

from forge.domain.errors import BundleError
from forge.domain.recipe import BundleRecipe


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
