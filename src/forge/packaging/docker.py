"""Docker image adapter (spec §7.1).

``render_dockerfile`` is pure (golden-tested); ``DockerBuilder`` stages the
binary + Dockerfile and shells ``docker build`` via the injected runner. The
sha256 in the artifact is the local image digest stand-in (the staged
Dockerfile) until SP2 wires registry digests.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from forge.domain.artifact import Artifact
from forge.domain.errors import BuildError
from forge.domain.manifest import ExporterManifest
from forge.domain.version import clean_version
from forge.packaging.checksum import file_sha256
from forge.packaging.runner import CommandRunner


def render_dockerfile(manifest: ExporterManifest) -> str:
    docker = manifest.spec.artifacts.docker
    base = (
        docker.base_image if docker is not None else "registry.access.redhat.com/ubi9/ubi-minimal"
    )
    binary = manifest.spec.build.binary_name
    lines = [f"FROM {base}", f"COPY {binary} /usr/bin/{binary}"]
    if docker is not None and docker.entrypoint:
        lines.append(f"ENTRYPOINT {json.dumps(docker.entrypoint)}")
    if docker is not None and docker.cmd:
        lines.append(f"CMD {json.dumps(docker.cmd)}")
    return "\n".join(lines) + "\n"


class DockerBuilder:
    def __init__(self, runner: CommandRunner) -> None:
        self._runner = runner

    def build_image(
        self, manifest: ExporterManifest, *, arch: str, binary_src: Path, work_dir: Path
    ) -> Artifact:
        docker = manifest.spec.artifacts.docker
        if docker is None or not docker.enabled:
            raise BuildError(f"manifest {manifest.name!r} has no enabled docker target")

        dockerfile = work_dir / "Dockerfile"
        dockerfile.write_text(render_dockerfile(manifest), encoding="utf-8")
        staged = work_dir / manifest.spec.build.binary_name
        if binary_src.resolve() != staged.resolve():
            shutil.copy2(binary_src, staged)

        tag = f"{manifest.name}:{clean_version(manifest.version)}"
        result = self._runner.run(
            [
                "docker",
                "build",
                "--platform",
                f"linux/{arch}",
                "-t",
                tag,
                "-f",
                str(dockerfile),
                str(work_dir),
            ],
            cwd=work_dir,
        )
        if result.returncode != 0:
            raise BuildError(f"docker build failed for {manifest.name}: {result.stderr}")

        return Artifact(
            type="docker-image",
            target=tag,
            arch=arch,
            sha256=file_sha256(dockerfile),
            signed=False,
        )
