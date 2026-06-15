"""RPM repository metadata generation (spec §5.1).

``build_rpm_repo`` wraps ``createrepo_c`` with an absolute ``--location-prefix``
so the ``primary.xml`` package hrefs point at the blob host (GitHub Releases by
default) while the generated ``repodata/`` is served from GitHub Pages. The host
is a parameter, never hardcoded — the anti-lock-in guarantee (spec §2.3).
"""

from __future__ import annotations

import re
import shutil
import tempfile
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
    location_prefix: str | None,
    runner: CommandRunner,
    keep_packages: bool = False,
) -> Path:
    """Generate ``repodata/`` for one ``(target, arch)`` group of ``.rpm``.

    Split topology (Pages): blobs are staged next to the output dir only so
    ``createrepo_c`` can read their headers, then removed; an absolute
    ``location_prefix`` points the hrefs at the blob host (Releases). Offline
    topology: pass ``location_prefix=""`` (the flag is omitted → relative hrefs)
    and ``keep_packages=True`` so the ``.rpm`` stay co-located with ``repodata/``
    for a ``file://`` repo. A package already inside the work dir is left in place
    (never copied onto itself, never removed). Returns ``repodata_dir``.
    """
    if not packages:
        raise DistributionError("no rpm packages to index")

    work = repodata_dir.parent
    work.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    for pkg in packages:
        target = work / pkg.name
        if pkg.resolve() != target.resolve():
            shutil.copy2(pkg, target)
            staged.append(target)

    cmd = ["createrepo_c"]
    if location_prefix:
        cmd += ["--location-prefix", location_prefix]
    cmd.append(str(work))
    result = runner.run(cmd)
    if result.returncode != 0:
        raise DistributionError(f"createrepo_c failed: {result.stderr}")

    if not keep_packages:
        for blob in staged:
            blob.unlink()
    return repodata_dir


def merge_rpm_repo(
    *,
    new_package: Path,
    published_parent: Path | None,
    repodata_dir: Path,
    location_prefix: str,
    runner: CommandRunner,
) -> Path:
    """Metadata-only incremental index for one changed ``.rpm`` (spec §4.2).

    Record ``new_package`` with ``build_rpm_repo`` (one-file repo, bucket
    ``location_prefix``) then ``mergerepo_c --method nvr --omit-baseurl`` it over
    ``published_parent`` (a dir containing the fetched ``repodata/``). The result
    ``repodata/`` is written at ``repodata_dir``. With ``published_parent=None``
    (coordinate not published yet) the recorded one-file repo *is* the result —
    correct, since the new package is then the only one for that coordinate.
    Returns ``repodata_dir``.
    """
    work = Path(tempfile.mkdtemp(prefix="mh-rpm-merge-"))
    new_repo = work / "new"
    build_rpm_repo(
        packages=[new_package],
        repodata_dir=new_repo / "repodata",
        location_prefix=location_prefix,
        runner=runner,
    )
    repodata_dir.parent.mkdir(parents=True, exist_ok=True)

    def _place(src: Path, dst: Path) -> None:
        """Copy a produced repodata dir into place, tolerant of FakeRunner (no files)."""
        if not src.exists():
            dst.mkdir(parents=True, exist_ok=True)
            return
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    if published_parent is None:
        _place(new_repo / "repodata", repodata_dir)
        return repodata_dir

    merged = work / "merged"
    result = runner.run(
        [
            "mergerepo_c",
            "--method",
            "nvr",
            "--omit-baseurl",
            "--repo",
            str(published_parent),
            "--repo",
            str(new_repo),
            "--outputdir",
            str(merged),
        ]
    )
    if result.returncode != 0:
        raise DistributionError(f"mergerepo_c failed: {result.stderr}")
    _place(merged / "repodata", repodata_dir)
    return repodata_dir
