"""RPM repository metadata generation (spec §5.1).

``build_rpm_repo`` wraps ``createrepo_c`` with an absolute ``--location-prefix``
so the ``primary.xml`` package hrefs point at the blob host (GitHub Releases by
default) while the generated ``repodata/`` is served from GitHub Pages. The host
is a parameter, never hardcoded — the anti-lock-in guarantee (spec §2.3).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from forge.domain.errors import DistributionError
from forge.packaging.runner import CommandRunner

# Canonical RPM tail: ...-<release>.<dist>.<arch>.rpm  (e.g. .el9.x86_64.rpm).
_RPM_TAIL = re.compile(r"\.(?P<target>el\d+)\.(?P<arch>x86_64|aarch64|noarch)\.rpm$")


def group_rpms_by_target_arch(packages: list[Path]) -> dict[tuple[str, str], list[Path]]:
    """Group ``.rpm`` paths by ``(dist-target, arch)`` parsed from the filename."""
    groups: dict[tuple[str, str], list[Path]] = {}
    for pkg in packages:
        match = _RPM_TAIL.search(pkg.name)
        if match is None:
            raise DistributionError(f"cannot parse RPM target/arch from {pkg.name!r}")
        key = (match["target"], match["arch"])
        groups.setdefault(key, []).append(pkg)
    return groups


def build_rpm_repo(
    *,
    packages: list[Path],
    repodata_dir: Path,
    location_prefix: str,
    runner: CommandRunner,
) -> Path:
    """Generate ``repodata/`` for one ``(target, arch)`` group of ``.rpm``.

    The blobs are staged next to the output dir only so ``createrepo_c`` can read
    their headers, then removed: the Pages tree keeps the metadata, never the
    packages (those go to Releases). Returns ``repodata_dir``.
    """
    if not packages:
        raise DistributionError("no rpm packages to index")

    work = repodata_dir.parent
    work.mkdir(parents=True, exist_ok=True)
    staged = [Path(shutil.copy2(pkg, work / pkg.name)) for pkg in packages]

    result = runner.run(["createrepo_c", "--location-prefix", location_prefix, str(work)])
    if result.returncode != 0:
        raise DistributionError(f"createrepo_c failed: {result.stderr}")

    for blob in staged:
        blob.unlink()
    return repodata_dir
