"""Offline bundle assembly (spec §5.4): arrange fetched artefacts into the
self-contained bundle tree (§6) and write the integrity manifest.

Network-free: blobs are located by filename in a pre-fetched ``inputs_dir`` (the
SP3.4 builder fills it via the source). Reuses the SP2 repo primitives with
offline parameters — yum co-located (relative href, blobs kept), apt flat — and
the shared ``forge.repo.naming`` convention.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from forge.bundle.resolver import ResolvedArtifact
from forge.domain.errors import BundleError
from forge.domain.recipe import BundleRecipe
from forge.packaging.checksum import file_sha256
from forge.packaging.runner import CommandRunner
from forge.packaging.template import render_template
from forge.repo.deb import build_apt_repo
from forge.repo.metadata_sign import sign_apt_release, sign_detached, sign_repomd
from forge.repo.naming import codename_for, rpm_arch
from forge.repo.rpm import build_rpm_repo

_ORIGIN = "monitoring-hub"
_KEY_NAME = "RPM-GPG-KEY-monitoring-hub"
_README_TEMPLATE = Path(__file__).parent / "templates" / "README.md.j2"


def _locate(inputs_dir: Path, filename: str) -> Path:
    found = next(inputs_dir.rglob(filename), None)
    if found is None:
        raise BundleError(f"fetched artefact not found in {inputs_dir}: {filename}")
    return found


def assemble_bundle(  # noqa: PLR0913 — orchestrator with explicit keyword-only I/O params
    resolved: list[ResolvedArtifact],
    *,
    inputs_dir: Path,
    staging: Path,
    recipe: BundleRecipe,
    key_id: str | None = None,
    public_key: Path | None = None,
    runner: CommandRunner,
) -> Path:
    """Build the bundle tree under ``staging`` from blobs in ``inputs_dir``."""
    staging.mkdir(parents=True, exist_ok=True)
    rpm_groups: dict[tuple[str, str], list[Path]] = {}
    deb_groups: dict[str, list[Path]] = {}

    for item in resolved:
        art = item.artifact
        if art.type == "rpm":
            arch = rpm_arch(art.arch)
            rpm_groups.setdefault((str(art.target), arch), []).append(
                _locate(inputs_dir, item.filename)
            )
        elif art.type == "deb":
            codename = codename_for(str(art.target))
            deb_groups.setdefault(codename, []).append(_locate(inputs_dir, item.filename))
        elif art.type == "grafana-dashboard":
            dash_dir = staging / "dashboards"
            dash_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_locate(inputs_dir, item.filename), dash_dir / item.filename)

    for (target, arch), pkgs in rpm_groups.items():
        repodata_dir = staging / "yum" / target / arch / "repodata"
        build_rpm_repo(
            packages=pkgs,
            repodata_dir=repodata_dir,
            location_prefix="",
            keep_packages=True,
            runner=runner,
        )
        if key_id is not None:
            sign_repomd(repodata_dir / "repomd.xml", key_id=key_id, runner=runner)

    for codename, debs in deb_groups.items():
        repo_dir = staging / "apt" / codename
        build_apt_repo(
            packages=debs, repo_dir=repo_dir, codename=codename, origin=_ORIGIN, runner=runner
        )
        if key_id is not None:
            sign_apt_release(repo_dir / "Release", key_id=key_id, runner=runner)

    if public_key is not None:
        shutil.copy2(public_key, staging / _KEY_NAME)

    recipe_json = staging / "recipe.json"
    recipe_json.write_text(recipe.model_dump_json(indent=2) + "\n", encoding="utf-8")
    if key_id is not None:
        sign_detached(recipe_json, key_id=key_id, runner=runner)

    _render_readme(staging, rpm_groups=rpm_groups, deb_groups=deb_groups, signed=key_id is not None)
    _write_sha256sums(staging)
    return staging


def _render_readme(
    staging: Path,
    *,
    rpm_groups: dict[tuple[str, str], list[Path]],
    deb_groups: dict[str, list[Path]],
    signed: bool,
) -> None:
    context = {
        "signed": signed,
        "rpm_targets": [{"target": t, "arch": a} for (t, a) in sorted(rpm_groups)],
        "deb_codenames": sorted(deb_groups),
    }
    (staging / "README.md").write_text(render_template(_README_TEMPLATE, context), encoding="utf-8")


def _write_sha256sums(staging: Path) -> None:
    lines: list[str] = []
    for path in sorted(p for p in staging.rglob("*") if p.is_file()):
        rel = path.relative_to(staging).as_posix()
        if rel == "SHA256SUMS":
            continue
        lines.append(f"{file_sha256(path)}  {rel}")
    (staging / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
