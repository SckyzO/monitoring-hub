"""Version policy (spec §4): pre-release filtering, numeric comparison, optional
major pin.

Pure and source-agnostic. Any ``VersionSource`` feeds candidate upstream tags
through ``select_latest`` to pick the latest acceptable version. Dependency-free
on purpose (mirrors ``forge.domain.version.clean_version``): no ``packaging``
import, numeric ordering is done on an int tuple so ``1.10.0`` correctly sorts
above ``1.9.0``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from forge.domain.version import clean_version

# Any tag carrying one of these markers is a pre-release: an auto-merging loop
# must never bump to it (spec §4). Source-agnostic: catches tags a source's own
# "prerelease" flag may have missed (e.g. a git-tags source has no such flag).
_PRERELEASE_RE = re.compile(r"(rc|beta|alpha|dev|pre)", re.IGNORECASE)


def is_prerelease(version: str) -> bool:
    """True if the tag looks like a pre-release (rc/beta/alpha/dev/pre)."""
    return bool(_PRERELEASE_RE.search(version))


def version_key(version: str) -> tuple[int, ...]:
    """Numeric ordering key: clean, dot-split, all-numeric chunks only.

    Stops at the first chunk that is not entirely digits so build/metadata
    suffixes do not corrupt the ordering (``1.2.3+build7`` → ``(1, 2)``).
    """
    parts: list[int] = []
    for chunk in clean_version(version).split("."):
        if not chunk.isdigit():
            break
        parts.append(int(chunk))
    return tuple(parts)


def is_newer(candidate: str, current: str) -> bool:
    """True if ``candidate`` is a strictly higher version than ``current``."""
    return version_key(candidate) > version_key(current)


def major_of(version: str) -> int | None:
    """Leading numeric component, or ``None`` for an unparseable version."""
    key = version_key(version)
    return key[0] if key else None


def passes_major_pin(version: str, pin: int | None) -> bool:
    """True if ``version`` is allowed under an optional major ceiling.

    ``pin is None`` (default) means no constraint. Otherwise the version must be
    on exactly that major (``pin=1`` keeps an item on the ``1.x`` line).
    """
    if pin is None:
        return True
    return major_of(version) == pin


def select_latest(candidates: Iterable[str], *, pin_major: int | None = None) -> str | None:
    """Latest acceptable tag among ``candidates`` (raw strings preserved).

    Skips pre-releases and, when ``pin_major`` is set, versions outside that
    major. Returns the raw candidate string (the caller cleans it for
    ``DetectedVersion``), or ``None`` if nothing qualifies.
    """
    acceptable = [
        tag for tag in candidates if not is_prerelease(tag) and passes_major_pin(tag, pin_major)
    ]
    if not acceptable:
        return None
    return max(acceptable, key=version_key)
