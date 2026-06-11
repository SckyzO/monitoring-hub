"""Archive extraction + binary discovery (pure filesystem; spec §7.1).

Supports the upstream formats exporters ship: ``.tar.gz``/``.tgz``/``.tar``,
``.zip``, and a bare ``.gz`` (a single gzipped binary). Tar extraction uses the
``data`` filter (Python 3.12) and zip members are validated to stay within the
destination, so neither path can write outside ``dest`` (path traversal). A
failed extraction or a missing binary is a ``BuildError`` — the op that can fail
is wrapped, not the one that follows.
"""

from __future__ import annotations

import gzip
import shutil
import tarfile
import zipfile
from pathlib import Path

from forge.domain.errors import BuildError

_TAR_SUFFIXES = (".tar.gz", ".tgz", ".tar")
_GZ_SUFFIX = ".gz"


def _extract_zip_safely(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extract a zip, refusing any member that resolves outside ``dest``."""
    dest_resolved = dest.resolve()
    for member in zf.namelist():
        target = (dest / member).resolve()
        if not target.is_relative_to(dest_resolved):
            raise BuildError(f"unsafe path in zip archive: {member}")
    # members validated above to stay within dest (path-traversal guard)
    zf.extractall(dest)  # nosec B202


def extract_archive(archive: Path, dest: Path, *, single_binary_name: str | None = None) -> Path:
    """Extract ``archive`` into ``dest`` (created); return ``dest``.

    A bare ``.gz`` (a single gzipped binary, not a tarball) is decompressed to
    one executable file: ``single_binary_name`` when given, else the archive
    name without its ``.gz`` suffix. The upstream often arch-suffixes that name
    (``ha_cluster_exporter-amd64.gz``), so passing the manifest binary name lets
    ``find_binary`` locate it by its installed name.
    """
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
        elif name.endswith(_GZ_SUFFIX):
            target = dest / (single_binary_name or archive.name[: -len(_GZ_SUFFIX)])
            with gzip.open(archive, "rb") as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
            target.chmod(0o755)
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
