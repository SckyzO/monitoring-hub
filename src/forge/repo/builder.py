"""Distribution builder (spec §5.4): assemble ./public + ./release from a catalog.

Orchestrates the SP2.1/SP2.2 primitives over the built packages, signs metadata
when a key is given, copies dashboards + the public key, writes the URL-populated
``catalog.json`` to the Pages tree, and returns the updated Catalog.

RPM release tags are per-``(target, arch)`` (``rpm-el9-x86_64``), not per-package:
all ``.rpm`` of one ``(target, arch)`` share a single ``repodata/`` and therefore
a single ``createrepo_c --location-prefix`` (spec §2.1, as amended). APT stays
per-codename (``apt-noble``); the codename is derived structurally from the deb
target since filenames don't encode it.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from forge.catalog.builder import write_catalog
from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import DistributionError
from forge.packaging.runner import CommandRunner
from forge.repo.deb import build_apt_repo
from forge.repo.metadata_sign import sign_apt_release, sign_repomd
from forge.repo.naming import codename_for, deb_filename, rpm_arch, rpm_filename
from forge.repo.rpm import build_rpm_repo

_ORIGIN = "monitoring-hub"


def artifact_hosted_url(
    *,
    name: str,
    version: str,
    artifact: Artifact,
    package_base_url: str,
    pages_base_url: str,
) -> str | None:
    """Hosted URL for one artifact, or ``None`` for kinds populated elsewhere.

    ``rpm``/``deb`` → blob host (``package_base_url``); ``grafana-dashboard`` →
    Pages (``pages_base_url``); ``docker`` (and any future kind) → ``None``, set
    at publish time (SP2.4).
    """
    if artifact.type == "rpm":
        arch = rpm_arch(artifact.arch)
        fn = rpm_filename(name, version, str(artifact.target), arch)
        return f"{package_base_url}/rpm-{artifact.target}-{arch}/{fn}"
    if artifact.type == "deb":
        codename = codename_for(str(artifact.target))
        fn = deb_filename(name, version, str(artifact.arch))
        return f"{package_base_url}/apt-{codename}/{fn}"
    if artifact.type == "grafana-dashboard":
        return f"{pages_base_url}/dashboards/{name}.json"
    return None


def _locate(packages_dir: Path, filename: str) -> Path:
    found = next(packages_dir.rglob(filename), None)
    if found is None:
        raise DistributionError(f"built package not found: {filename}")
    return found


def _stage_artifacts(  # noqa: PLR0913 — staging helper; params mirror build_distribution
    item: CatalogEntry,
    *,
    packages_dir: Path,
    dashboards_dir: Path,
    public_out: Path,
    release_out: Path,
    package_base_url: str,
    pages_base_url: str,
    rpm_groups: dict[tuple[str, str], list[Path]],
    deb_groups: dict[str, list[Path]],
) -> CatalogEntry:
    """Stage one item's artifacts into the trees and return it with URLs set."""
    new_artifacts: list[Artifact] = []
    for art in item.artifacts:
        url = artifact_hosted_url(
            name=item.name,
            version=item.version,
            artifact=art,
            package_base_url=package_base_url,
            pages_base_url=pages_base_url,
        )
        if art.type == "rpm":
            arch = rpm_arch(art.arch)
            fn = rpm_filename(item.name, item.version, str(art.target), arch)
            tag_dir = release_out / f"rpm-{art.target}-{arch}"
            tag_dir.mkdir(parents=True, exist_ok=True)
            staged = Path(shutil.copy2(_locate(packages_dir, fn), tag_dir / fn))
            rpm_groups.setdefault((str(art.target), arch), []).append(staged)
        elif art.type == "deb":
            fn = deb_filename(item.name, item.version, str(art.arch))
            deb_groups.setdefault(codename_for(str(art.target)), []).append(
                _locate(packages_dir, fn)
            )
        elif art.type == "grafana-dashboard":
            src = dashboards_dir / f"{item.name}.json"
            if not src.is_file():
                raise DistributionError(f"dashboard json not found: {src}")
            dash_dir = public_out / "dashboards"
            dash_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dash_dir / src.name)
        new_artifacts.append(art.model_copy(update={"url": url}) if url else art)
    return item.model_copy(update={"artifacts": new_artifacts})


def build_distribution(  # noqa: PLR0913 — orchestrator with explicit I/O params
    *,
    catalog: Catalog,
    packages_dir: Path,
    dashboards_dir: Path,
    public_out: Path,
    release_out: Path,
    package_base_url: str,
    pages_base_url: str,
    key_id: str | None = None,
    public_key: Path | None = None,
    runner: CommandRunner,
) -> Catalog:
    """Assemble the Pages (``./public``) and Releases (``./release``) trees.

    Returns the catalog with every ``Artifact.url`` populated; the same catalog is
    written to ``public_out/catalog.json``. Metadata is signed iff ``key_id`` is
    given (local dev / unit tests emit unsigned metadata).
    """
    rpm_groups: dict[tuple[str, str], list[Path]] = {}
    deb_groups: dict[str, list[Path]] = {}

    updated_items = [
        _stage_artifacts(
            item,
            packages_dir=packages_dir,
            dashboards_dir=dashboards_dir,
            public_out=public_out,
            release_out=release_out,
            package_base_url=package_base_url,
            pages_base_url=pages_base_url,
            rpm_groups=rpm_groups,
            deb_groups=deb_groups,
        )
        for item in catalog.items
    ]

    for (target, arch), pkgs in rpm_groups.items():
        repodata_dir = public_out / target / arch / "repodata"
        build_rpm_repo(
            packages=pkgs,
            repodata_dir=repodata_dir,
            location_prefix=f"{package_base_url}/rpm-{target}-{arch}/",
            runner=runner,
        )
        if key_id is not None:
            sign_repomd(repodata_dir / "repomd.xml", key_id=key_id, runner=runner)

    for codename, debs in deb_groups.items():
        repo_dir = release_out / f"apt-{codename}"
        build_apt_repo(
            packages=debs, repo_dir=repo_dir, codename=codename, origin=_ORIGIN, runner=runner
        )
        if key_id is not None:
            sign_apt_release(repo_dir / "Release", key_id=key_id, runner=runner)

    if public_key is not None:
        public_out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(public_key, public_out / "RPM-GPG-KEY-monitoring-hub")
        apt_dir = public_out / "apt"
        apt_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(public_key, apt_dir / "monitoring-hub.asc")

    updated = catalog.model_copy(update={"items": updated_items})
    write_catalog(updated, public_out / "catalog.json")
    return updated
