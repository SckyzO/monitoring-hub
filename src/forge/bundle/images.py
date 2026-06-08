"""Offline image acquisition (spec §5.5, SP3.5): save bundled items' OCI images
into the bundle as per-arch ``docker-archive`` tarballs (``docker load``-ready).

The build chain is daemonless: ``docker-archive`` cannot hold a multi-arch index,
so each requested arch becomes its own ``<name>-<version>-<arch>.tar``.
``RegistryImageSource`` pulls the published image (``skopeo copy``);
``LocalImageSource`` rebuilds it from an ``mh build`` context (``buildah``). Both
shell out only — they never read image bytes themselves.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from forge.bundle.resolver import ResolvedArtifact
from forge.domain.errors import BundleError
from forge.packaging.runner import CommandRunner

_DEFAULT_ARCHES = ("amd64", "arm64")


@runtime_checkable
class ImageSource(Protocol):
    def save(
        self, artifact: ResolvedArtifact, dest_dir: Path, *, arches: list[str]
    ) -> list[Path]: ...


def _archive_path(artifact: ResolvedArtifact, dest_dir: Path, arch: str) -> Path:
    return dest_dir / f"{artifact.name}-{artifact.version}-{arch}.tar"


class RegistryImageSource:
    """Pull a published image into per-arch ``docker-archive`` tarballs via skopeo."""

    def __init__(self, *, registry: str, runner: CommandRunner, tls_verify: bool = True) -> None:
        self._registry = registry
        self._runner = runner
        self._tls_verify = tls_verify

    def save(self, artifact: ResolvedArtifact, dest_dir: Path, *, arches: list[str]) -> list[Path]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        tag = str(artifact.artifact.target)  # "<name>:<version>"
        ref = f"{self._registry}/{tag}"
        written: list[Path] = []
        for arch in arches:
            out = _archive_path(artifact, dest_dir, arch)
            cmd = ["skopeo", "copy", "--override-os", "linux", "--override-arch", arch]
            if not self._tls_verify:
                cmd.append("--src-tls-verify=false")
            cmd += [f"docker://{ref}", f"docker-archive:{out}:{tag}"]
            result = self._runner.run(cmd)
            if result.returncode != 0:
                raise BundleError(f"skopeo copy {ref} ({arch}) failed: {result.stderr}")
            written.append(out)
        return written


class LocalImageSource:
    """Build an image from its ``mh build`` context (buildah, daemonless) and write
    per-arch ``docker-archive`` tarballs. Only arches with a staged binary build."""

    def __init__(self, *, contexts_root: Path, runner: CommandRunner) -> None:
        self._contexts_root = contexts_root
        self._runner = runner

    def save(self, artifact: ResolvedArtifact, dest_dir: Path, *, arches: list[str]) -> list[Path]:
        context = self._contexts_root / artifact.name
        if not context.is_dir():
            raise BundleError(f"docker context not found: {context}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        tag = str(artifact.artifact.target)  # "<name>:<version>"
        written: list[Path] = []
        for arch in arches:
            if not any(context.glob(f"*-{arch}")):
                continue
            tagged = f"{tag}-{arch}"
            bud = self._runner.run(["buildah", "bud", "--arch", arch, "-t", tagged, str(context)])
            if bud.returncode != 0:
                raise BundleError(f"buildah bud {tag} ({arch}) failed: {bud.stderr}")
            out = _archive_path(artifact, dest_dir, arch)
            push = self._runner.run(["buildah", "push", tagged, f"docker-archive:{out}:{tag}"])
            if push.returncode != 0:
                raise BundleError(f"buildah push {tag} ({arch}) failed: {push.stderr}")
            written.append(out)
        if not written:
            raise BundleError(f"no arch binaries in {context} for {arches}")
        return written


def save_images(
    resolved: list[ResolvedArtifact],
    *,
    dest_dir: Path,
    source: ImageSource,
    arches: list[str] | None,
) -> list[Path]:
    """Save every ``docker-image`` artefact in ``resolved`` via ``source``."""
    selected = arches if arches is not None else list(_DEFAULT_ARCHES)
    written: list[Path] = []
    for art in resolved:
        if art.artifact.type == "docker-image":
            written.extend(source.save(art, dest_dir, arches=selected))
    return written
