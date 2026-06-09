"""OCI publisher (spec §5.7): build a multi-arch manifest once, push to each registry.

For each ``<staging>/<name>/`` build context emitted by ``mh build`` (Dockerfile +
per-arch binaries), build one image per present arch with ``buildah bud --arch``,
assemble a single manifest list tagged on the **primary** (first) registry, then
push that one local manifest to every configured registry plus a ``:latest`` copy.
Building once and pushing N times keeps the slow cross-arch ``buildah bud`` step
off the critical path for mirror registries (GHCR primary, Docker Hub mirror).
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
        self,
        *,
        registries: Sequence[str],
        versions: Mapping[str, str],
        runner: CommandRunner,
        tls_verify: bool = True,
    ) -> None:
        if not registries:
            raise ValueError("at least one registry is required")
        self._registries = tuple(registries)
        self._versions = versions
        self._runner = runner
        self._tls_verify = tls_verify

    def publish(self, staging: Path) -> None:
        for context in sorted(p for p in staging.iterdir() if p.is_dir()):
            self._publish_one(context)

    def _publish_one(self, context: Path) -> None:
        name = context.name
        version = self._versions[name]
        arches = [a for a in _ARCHES if any(context.glob(f"*-{a}"))]

        # Build once, tagged on the primary (first) registry.
        local = f"{self._registries[0]}/{name}:{version}"
        for arch in arches:
            self._run(["buildah", "bud", "--arch", arch, "-t", f"{local}-{arch}", str(context)])
        self._run(["buildah", "manifest", "create", local])
        for arch in arches:
            self._run(["buildah", "manifest", "add", local, f"{local}-{arch}"])

        # Push the single local manifest to every registry, plus :latest.
        for registry in self._registries:
            image = f"{registry}/{name}"
            ref = f"{image}:{version}"
            self._push(local, ref)
            self._copy_latest(ref, image)

    def _push(self, local: str, ref: str) -> None:
        push = ["buildah", "manifest", "push", "--all"]
        if not self._tls_verify:
            push.append("--tls-verify=false")
        self._run([*push, local, f"docker://{ref}"])

    def _copy_latest(self, ref: str, image: str) -> None:
        copy = ["skopeo", "copy"]
        if not self._tls_verify:
            copy += ["--src-tls-verify=false", "--dest-tls-verify=false"]
        self._run([*copy, f"docker://{ref}", f"docker://{image}:latest"])

    def _run(self, args: Sequence[str]) -> None:
        result = self._runner.run(args)
        if result.returncode != 0:
            raise PublishError(f"{args[0]} failed: {result.stderr}")
