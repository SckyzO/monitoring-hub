"""CLI helpers: catalogue-root resolution and manifest iteration.

Kept out of ``main.py`` so the resolution logic is unit-testable without going
through Click. The catalogue root holds the manifest **data** (spec §5):
``<root>/{exporters,dashboards}/<name>/manifest.yaml``.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

_KIND_DIRS = ("exporters", "dashboards")
_MANIFEST = "manifest.yaml"
_ENV_VAR = "FORGE_CATALOG_ROOT"
_DEFAULT_ROOT = "catalog"


def resolve_catalog_root(option: str | None) -> Path:
    """Pick the catalogue root: CLI option > ``FORGE_CATALOG_ROOT`` env > ``catalog``."""
    if option:
        return Path(option)
    env = os.environ.get(_ENV_VAR)
    return Path(env) if env else Path(_DEFAULT_ROOT)


def iter_manifest_paths(root: Path, *, kind: str | None = None) -> Iterator[Path]:
    """Yield ``manifest.yaml`` paths under the catalogue, optionally one kind.

    ``kind`` is the singular kind name (``exporter``); the on-disk directory is
    its plural (``exporters``). Items are yielded in sorted name order.
    """
    dirs = (f"{kind}s",) if kind else _KIND_DIRS
    for kind_dir in dirs:
        base = root / kind_dir
        if not base.is_dir():
            continue
        for item in sorted(base.iterdir()):
            manifest = item / _MANIFEST
            if manifest.is_file():
                yield manifest
