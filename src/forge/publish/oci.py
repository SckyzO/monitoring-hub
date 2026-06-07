"""OCI publisher (spec §5.7): build + push multi-arch images via buildah/skopeo.

For each ``<staging>/<name>/`` build context emitted by ``mh build`` (Dockerfile +
per-arch binaries), build one image per present arch with ``buildah bud --arch``,
assemble a manifest list, and push ``<registry>/<name>:<version>`` plus ``:latest``.
Daemonless and rootless — runs in the dev image with no docker socket. Gated in
CI (needs qemu/binfmt for cross-arch and registry auth).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from forge.domain.errors import PublishError
from forge.packaging.runner import CommandRunner

# Standard publish set; only arches whose binary is staged are actually built.
_ARCHES = ("amd64", "arm64")


class OciPublisher:
    def __init__(
        self, *, registry: str, versions: Mapping[str, str], runner: CommandRunner
    ) -> None:
        self._registry = registry
        self._versions = versions
        self._runner = runner

    def publish(self, staging: Path) -> None:
        for context in sorted(p for p in staging.iterdir() if p.is_dir()):
            self._publish_one(context)

    def _publish_one(self, context: Path) -> None:
        name = context.name
        version = self._versions[name]
        image = f"{self._registry}/{name}"
        ref = f"{image}:{version}"
        arches = [a for a in _ARCHES if any(context.glob(f"*-{a}"))]

        for arch in arches:
            self._run(["buildah", "bud", "--arch", arch, "-t", f"{ref}-{arch}", str(context)])
        self._run(["buildah", "manifest", "create", ref])
        for arch in arches:
            self._run(["buildah", "manifest", "add", ref, f"{ref}-{arch}"])
        self._run(["buildah", "manifest", "push", "--all", ref, f"docker://{ref}"])
        self._run(["skopeo", "copy", f"docker://{ref}", f"docker://{image}:latest"])

    def _run(self, args: Sequence[str]) -> None:
        result = self._runner.run(args)
        if result.returncode != 0:
            raise PublishError(f"{args[0]} failed: {result.stderr}")
