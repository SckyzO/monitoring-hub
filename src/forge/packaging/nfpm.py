"""nfpm RPM/DEB packaging adapter (spec §7.1, §16).

``build_nfpm_config`` is the pure contract core: it maps a validated
``ExporterManifest`` + per-target/arch parameters into an nfpm config mapping
(golden-tested). ``NfpmPackager`` renders the systemd unit and scriptlets,
writes the config, and invokes the ``nfpm`` binary via the runner.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Literal

import yaml

from forge.domain.artifact import Artifact
from forge.domain.errors import BuildError
from forge.domain.manifest import DebTarget, ExporterManifest, RpmTarget
from forge.domain.version import clean_version
from forge.packaging.checksum import file_sha256
from forge.packaging.runner import CommandRunner
from forge.packaging.scriptlets import render_postinstall, render_preremove
from forge.packaging.systemd import render_systemd_unit

_MAINTAINER = "Monitoring Hub <noreply@users.noreply.github.com>"
_RPM = "rpm"


def _file_content(dst: str, *, config: bool, mode: int) -> dict[str, Any]:
    entry: dict[str, Any] = {"dst": dst, "file_info": {"mode": mode}}
    if config:
        entry["type"] = "config"
    return entry


def build_nfpm_config(  # noqa: PLR0913 — locked keyword-only contract (spec §16)
    manifest: ExporterManifest,
    *,
    packager: Literal["rpm", "deb"],
    target: str,
    arch: str,
    binary_dst: str,
    contents_extra: list[dict[str, Any]],
    scripts: dict[str, str],
    extra_binary_dsts: list[str] | None = None,
) -> dict[str, Any]:
    """Map a manifest + target/arch into an nfpm config mapping.

    The caller (``NfpmPackager``) supplies ``binary_dst`` (resolved install
    path), ``contents_extra`` (e.g. the rendered systemd unit), ``scripts``
    (paths to rendered scriptlets) and ``extra_binary_dsts`` (install paths for
    ``build.extra_binaries`` shipped in the same archive); this function does no
    I/O. The packager fills the ``src`` of the binary entries afterwards.
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
        "version": clean_version(manifest.version),
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

    for dst in extra_binary_dsts or []:
        # src is filled by the packager (it holds the staged paths); pure here.
        config["contents"].append(_file_content(dst, config=False, mode=0o755))

    for extra_file in art.extra_files:
        entry = _file_content(
            extra_file.dest, config=extra_file.config, mode=int(extra_file.mode, 8)
        )
        # nfpm needs a source to read the file from; resolved relative to its cwd.
        entry["src"] = extra_file.source
        config["contents"].append(entry)
    config["contents"].extend(contents_extra)

    if isinstance(art, RpmTarget):
        config["rpm"] = {"summary": art.summary or manifest.description.split("\n", 1)[0]}
    else:
        config["section"] = art.section
        config["priority"] = art.priority

    return config


class NfpmPackager:
    """Render unit + scriptlets, write the nfpm config, invoke ``nfpm``."""

    def __init__(self, runner: CommandRunner) -> None:
        self._runner = runner

    def package(  # noqa: PLR0913 — locked keyword-only contract (spec §7.1)
        self,
        manifest: ExporterManifest,
        *,
        packager: Literal["rpm", "deb"],
        target: str,
        arch: str,
        binary_src: Path,
        work_dir: Path,
        extra_binaries: dict[str, Path] | None = None,
    ) -> Artifact:
        art = manifest.spec.artifacts.rpm if packager == _RPM else manifest.spec.artifacts.deb
        if art is None:
            raise BuildError(f"manifest {manifest.name!r} has no {packager} target")

        # nfpm runs with ``cwd=work_dir`` (below), so every file path it reads must
        # be absolute — a relative ``--work-dir`` (e.g. ``./dist`` in CI) would
        # otherwise produce src paths that resolve against the wrong directory.
        work_dir = work_dir.resolve()
        binary_src = binary_src.resolve()

        install_path = getattr(art, "install_path", None) or "/usr/bin"
        binary_dst = f"{install_path.rstrip('/')}/{manifest.spec.build.binary_name}"
        # build.extra_binaries (e.g. amtool, promtool) ship in the same archive;
        # install them next to the main binary, keyed by dst for src fill-in.
        extra_src_by_dst = {
            f"{install_path.rstrip('/')}/{name}": src.resolve()
            for name, src in (extra_binaries or {}).items()
        }

        contents_extra: list[dict[str, Any]] = []
        scripts: dict[str, str] = {}
        unit_name = manifest.name if art.systemd.enabled else None

        if art.systemd.enabled:
            unit = render_systemd_unit(
                description=manifest.description,
                exec_start=binary_dst,
                user=art.system_user,
                systemd=art.systemd,
            )
            unit_file = work_dir / f"{manifest.name}.service"
            unit_file.write_text(unit, encoding="utf-8")
            contents_extra.append(
                {"src": str(unit_file), "dst": f"/lib/systemd/system/{manifest.name}.service"}
            )

        if art.systemd.enabled or art.system_user:
            post = work_dir / "postinstall.sh"
            post.write_text(
                render_postinstall(unit_name=unit_name, system_user=art.system_user),
                encoding="utf-8",
            )
            scripts["postinstall"] = str(post)
        if unit_name:
            pre = work_dir / "preremove.sh"
            pre.write_text(render_preremove(unit_name=unit_name), encoding="utf-8")
            scripts["preremove"] = str(pre)

        for directory in art.directories:
            contents_extra.append(
                {
                    "dst": directory.path,
                    "type": "dir",
                    "file_info": {"mode": int(directory.mode, 8)},
                }
            )

        config = build_nfpm_config(
            manifest,
            packager=packager,
            target=target,
            arch=arch,
            binary_dst=binary_dst,
            contents_extra=contents_extra,
            scripts=scripts,
            extra_binary_dsts=list(extra_src_by_dst),
        )
        # nfpm reads the binary from the config "src"; point it at the staged file.
        config["contents"][0]["src"] = str(binary_src)
        for entry in config["contents"]:
            src = extra_src_by_dst.get(entry.get("dst", ""))
            if src is not None and "src" not in entry:
                entry["src"] = str(src)

        config_path = work_dir / "nfpm.yaml"
        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

        nfpm_bin = shutil.which("nfpm") or "nfpm"
        result = self._runner.run(
            [nfpm_bin, "package", "-f", str(config_path), "-p", packager, "-t", str(work_dir)],
            cwd=work_dir,
        )
        if result.returncode != 0:
            # nfpm writes its diagnostics to stdout, not stderr; surface both.
            detail = (result.stderr + "\n" + result.stdout).strip()
            raise BuildError(f"nfpm {packager} build failed for {manifest.name}: {detail}")

        produced = sorted(work_dir.glob(f"*.{packager}"))
        if not produced:
            raise BuildError(f"nfpm reported success but produced no .{packager} in {work_dir}")
        output = produced[-1]

        return Artifact(
            type=packager,
            target=target,
            arch=arch,
            sha256=file_sha256(output),
            signed=False,
        )
