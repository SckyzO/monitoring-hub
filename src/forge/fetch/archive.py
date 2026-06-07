"""Archive extraction + binary discovery (pure filesystem; spec §7.1).

Supports the upstream formats exporters ship: ``.tar.gz``/``.tgz``/``.tar`` and
``.zip``. Tar extraction uses the ``data`` filter (Python 3.12) and zip members
are validated to stay within the destination, so neither path can write outside
``dest`` (path traversal). A failed extraction or a missing binary is a
``BuildError`` — the op that can fail is wrapped, not the one that follows.
"""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from forge.domain.errors import BuildError

_TAR_SUFFIXES = (".tar.gz", ".tgz", ".tar")


def _extract_zip_safely(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extract a zip, refusing any member that resolves outside ``dest``."""
    dest_resolved = dest.resolve()
    for member in zf.namelist():
        target = (dest / member).resolve()
        if not target.is_relative_to(dest_resolved):
            raise BuildError(f"unsafe path in zip archive: {member}")
    # members validated above to stay within dest (path-traversal guard)
    zf.extractall(dest)  # nosec B202


def extract_archive(archive: Path, dest: Path) -> Path:
    """Extract ``archive`` into ``dest`` (created); return ``dest``."""
    dest.mkdir(parents=True, exist_ok=True)
    name = archive.name.lower()
    try:
        if name.endswith(_TAR_SUFFIXES):
            with tarfile.open(archive) as tar:
                # data filter blocks unsafe members (path traversal, devices)
                tar.extractall(dest, filter="data")
        elif name.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                _extract_zip_safely(zf, dest)
        else:
            raise BuildError(f"unsupported archive format: {archive.name}")
    except (tarfile.TarError, zipfile.BadZipFile, OSError) as exc:
        raise BuildError(f"failed to extract {archive.name}: {exc}") from exc
    return dest


def find_binary(root: Path, name: str) -> Path:
    """Return the first regular file named exactly ``name`` under ``root``."""
    for candidate in sorted(root.rglob(name)):
        if candidate.is_file():
            return candidate
    raise BuildError(f"binary {name!r} not found in extracted archive under {root}")
