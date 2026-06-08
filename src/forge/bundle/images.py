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
