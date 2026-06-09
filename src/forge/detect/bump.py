"""Validated atomic manifest version bump (spec §8).

``bump_manifest`` is the engine-side replacement for an unvalidated ``sed`` on
``version:``. It loads the manifest mapping, sets ``version`` to the supplied
value **verbatim** (the caller owns the tag format — the GitHub download URL is
built from the raw upstream tag), re-validates the whole manifest through
``parse_manifest`` so a bad bump fails *before* any byte is written, then writes
the YAML back atomically (temp + ``os.replace``) — mirroring
``forge.catalog.builder.write_catalog``.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from forge.domain.manifest import Manifest, parse_manifest
from forge.sources.resolver import load_yaml_mapping


def bump_manifest(path: Path, *, to: str) -> Manifest:
    """Set ``path``'s top-level ``version`` to ``to``, validating before writing.

    Returns the re-validated ``Manifest``. Raises ``SourceResolutionError`` if the
    file cannot be read/parsed and ``ManifestError`` if the bumped manifest is
    invalid (in which case the file is left untouched).
    """
    data = load_yaml_mapping(path)
    data["version"] = to
    manifest = parse_manifest(data)  # validates; raises ManifestError before any write
    payload = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    _atomic_write_text(path, payload)
    return manifest


def _atomic_write_text(path: Path, payload: str) -> None:
    """Write ``payload`` to ``path`` via a sibling temp file + ``os.replace``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
