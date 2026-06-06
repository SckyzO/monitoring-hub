"""nfpm RPM/DEB packaging adapter (spec §7.1, §16).

``build_nfpm_config`` is the pure contract core: it maps a validated
``ExporterManifest`` + per-target/arch parameters into an nfpm config mapping
(golden-tested). ``NfpmPackager`` renders the systemd unit and scriptlets,
writes the config, and invokes the ``nfpm`` binary via the runner.
"""

from __future__ import annotations

from typing import Any, Literal

from forge.domain.manifest import DebTarget, ExporterManifest, RpmTarget

_MAINTAINER = "Monitoring Hub <noreply@users.noreply.github.com>"


def _clean_version(version: str) -> str:
    return version[1:] if version.startswith("v") else version


def _file_content(dst: str, *, config: bool, mode: int) -> dict[str, Any]:
    entry: dict[str, Any] = {"dst": dst, "file_info": {"mode": mode}}
    if config:
        entry["type"] = "config"
    return entry


def build_nfpm_config(
    manifest: ExporterManifest,
    *,
    packager: Literal["rpm", "deb"],
    target: str,
    arch: str,
    binary_dst: str,
    contents_extra: list[dict[str, Any]],
    scripts: dict[str, str],
) -> dict[str, Any]:
    """Map a manifest + target/arch into an nfpm config mapping.

    The caller (``NfpmPackager``) supplies ``binary_dst`` (resolved install
    path), ``contents_extra`` (e.g. the rendered systemd unit) and ``scripts``
    (paths to rendered scriptlets); this function does no I/O.
    """
    spec = manifest.spec.artifacts
    art: RpmTarget | DebTarget
    if packager == "rpm":
        if spec.rpm is None:
            raise ValueError("manifest has no rpm artifact target")
        art = spec.rpm
        name = manifest.name
        release = f"1.{target}"
    else:
        if spec.deb is None:
            raise ValueError("manifest has no deb artifact target")
        art = spec.deb
        name = manifest.name.replace("_", "-")
        release = "1"

    config: dict[str, Any] = {
        "name": name,
        "arch": arch,
        "platform": "linux",
        "version": _clean_version(manifest.version),
        "release": release,
        "maintainer": _MAINTAINER,
        "description": manifest.description,
        "homepage": f"https://github.com/{manifest.spec.upstream.repo or ''}",
        "depends": list(art.dependencies),
        "contents": [_file_content(binary_dst, config=False, mode=0o755)],
        "scripts": dict(scripts),
    }
    if manifest.license is not None:
        config["license"] = manifest.license

    for extra_file in art.extra_files:
        config["contents"].append(
            _file_content(extra_file.dest, config=extra_file.config, mode=int(extra_file.mode, 8))
        )
    config["contents"].extend(contents_extra)

    if isinstance(art, RpmTarget):
        config["rpm"] = {"summary": art.summary or manifest.description.split("\n", 1)[0]}
    else:
        config["section"] = art.section
        config["priority"] = art.priority

    return config
