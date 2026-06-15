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
import tempfile
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


def _stanzas(text: str) -> list[str]:
    return [s.strip() for s in text.split("\n\n") if s.strip()]


def _package_name(stanza: str) -> str | None:
    for line in stanza.splitlines():
        if line.startswith("Package:"):
            return line.split(":", 1)[1].strip()
    return None


def merge_packages(*, published: str, new_stanza: str, package: str) -> str:
    """Splice ``new_stanza`` into a published ``Packages`` (spec §4.3).

    Drop every published stanza for ``package`` (mono-version), keep all others
    verbatim, append the new stanza. Pure text — no tool, no files.
    """
    kept = [s for s in _stanzas(published) if _package_name(s) != package]
    kept.append(new_stanza.strip())
    return "\n\n".join(kept) + "\n"


def merge_apt_repo(  # noqa: PLR0913
    *,
    new_package: Path,
    published_packages: Path | None,
    repo_dir: Path,
    codename: str,
    origin: str,
    runner: CommandRunner,
) -> Path:
    """Incremental flat apt index for one changed ``.deb`` (spec §4.3).

    Record the new ``.deb``'s stanza (``apt-ftparchive packages`` over a one-file
    dir), splice it into ``published_packages`` (or start fresh when ``None``),
    write ``Packages`` + ``Packages.gz`` into ``repo_dir`` next to the new ``.deb``,
    then ``apt-ftparchive release`` over the merged index. No other ``.deb`` is
    needed. Returns ``repo_dir``.
    """
    repo_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(new_package, repo_dir / new_package.name)

    one = Path(tempfile.mkdtemp(prefix="mh-deb-merge-"))
    shutil.copy2(new_package, one / new_package.name)
    rec = runner.run(["apt-ftparchive", "packages", "."], cwd=one)
    if rec.returncode != 0:
        raise DistributionError(f"apt-ftparchive packages failed: {rec.stderr}")

    package = new_package.name.split("_", 1)[0]
    base = published_packages.read_text() if published_packages is not None else ""
    merged = merge_packages(published=base, new_stanza=rec.stdout, package=package)
    (repo_dir / "Packages").write_text(merged)
    (repo_dir / "Packages.gz").write_bytes(gzip.compress(merged.encode()))

    release = runner.run(
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
    if release.returncode != 0:
        raise DistributionError(f"apt-ftparchive release failed: {release.stderr}")
    (repo_dir / "Release").write_text(release.stdout)
    return repo_dir
