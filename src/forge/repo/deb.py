"""APT flat-repository metadata generation (spec §5.2).

apt has no absolute-package-URL support, so index and blobs must share one host:
the whole flat repo (no ``dists/`` tree; ``Packages`` / ``Release`` and the
``.deb`` side by side) ships to GitHub Releases (spec §2). ``apt-ftparchive`` is
stateless — it rescans the directory each run, so regeneration is cheap and needs
no prior state.
"""

from __future__ import annotations

import gzip
import shutil
from pathlib import Path

from forge.domain.errors import DistributionError
from forge.packaging.runner import CommandRunner


def build_apt_repo(
    *,
    packages: list[Path],
    repo_dir: Path,
    codename: str,
    origin: str,
    runner: CommandRunner,
) -> Path:
    """Generate a signed-ready flat APT repo for one codename. Returns ``repo_dir``."""
    if not packages:
        raise DistributionError("no deb packages to index")

    repo_dir.mkdir(parents=True, exist_ok=True)
    for pkg in packages:
        shutil.copy2(pkg, repo_dir / pkg.name)

    packages_result = runner.run(["apt-ftparchive", "packages", "."], cwd=repo_dir)
    if packages_result.returncode != 0:
        raise DistributionError(f"apt-ftparchive packages failed: {packages_result.stderr}")
    (repo_dir / "Packages").write_text(packages_result.stdout)
    (repo_dir / "Packages.gz").write_bytes(gzip.compress(packages_result.stdout.encode()))

    release_result = runner.run(
        [
            "apt-ftparchive",
            "-o",
            f"APT::FTPArchive::Release::Codename={codename}",
            "-o",
            f"APT::FTPArchive::Release::Origin={origin}",
            "release",
            ".",
        ],
        cwd=repo_dir,
    )
    if release_result.returncode != 0:
        raise DistributionError(f"apt-ftparchive release failed: {release_result.stderr}")
    (repo_dir / "Release").write_text(release_result.stdout)

    return repo_dir
