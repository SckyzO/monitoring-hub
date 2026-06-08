"""Package-filename naming convention for rpm/deb (single source of truth).

These pure helpers encode how a built ``.rpm``/``.deb`` is named and where its
arch/codename map. ``forge.repo.builder`` (distribution trees) and
``forge.bundle.resolver`` (offline bundles) both depend on them so the
convention never diverges between the two consumers.
"""

from __future__ import annotations

from forge.domain.errors import DistributionError

# Artifact.arch is GOARCH (manifest build.archs); rpm uses the rpm arch, deb
# keeps GOARCH (amd64/arm64).
_RPM_ARCH = {"amd64": "x86_64", "arm64": "aarch64"}
_DEB_CODENAMES = {
    "ubuntu-22.04": "jammy",
    "ubuntu-24.04": "noble",
    "ubuntu-26.04": "resolute",
    "debian-12": "bookworm",
    "debian-13": "trixie",
}


def rpm_arch(arch: str | None) -> str:
    """Translate a GOARCH (``amd64``) to the rpm arch (``x86_64``)."""
    if arch not in _RPM_ARCH:
        raise DistributionError(f"no rpm arch mapping for {arch!r}")
    return _RPM_ARCH[arch]


def codename_for(target: str) -> str:
    """Map a deb target (``ubuntu-24.04``) to its apt codename (``noble``)."""
    try:
        return _DEB_CODENAMES[target]
    except KeyError as exc:
        raise DistributionError(f"no apt codename for deb target {target!r}") from exc


def rpm_filename(name: str, version: str, target: str, rpm_arch_: str) -> str:
    """The on-disk ``.rpm`` filename nfpm emits."""
    return f"{name}-{version}-1.{target}.{rpm_arch_}.rpm"


def deb_filename(name: str, version: str, arch: str) -> str:
    """The on-disk ``.deb`` filename nfpm emits (name underscores → hyphens)."""
    return f"{name.replace('_', '-')}_{version}-1_{arch}.deb"
