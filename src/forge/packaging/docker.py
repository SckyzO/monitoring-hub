"""Docker image adapter (spec §5.8).

``render_dockerfile`` is pure (golden-tested); ``emit_docker_context`` stages a
daemonless multi-arch build context — the rendered Dockerfile plus one binary per
arch (``<binary>-<arch>``) — for ``mh publish --oci`` (buildah/skopeo) to build
later. No docker/buildah command runs at ``mh build`` time, so the whole path is
testable in ``make ci``.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path

from forge.domain.artifact import Artifact
from forge.domain.errors import BuildError
from forge.domain.manifest import ExporterManifest
from forge.domain.version import clean_version
from forge.packaging.checksum import file_sha256
from forge.packaging.template import render_template


def _template_context(manifest: ExporterManifest) -> dict[str, object]:
    """Build the Jinja2 context for a custom Dockerfile.

    Hoists ``spec`` fields (``upstream``/``build``/``artifacts``) to the top level
    so templates read ``{{ name }}``, ``{{ build.binary_name }}`` and
    ``{{ artifacts.docker.base_image }}`` — the legacy template namespace.
    """
    return {**manifest.model_dump(), **manifest.spec.model_dump()}


def render_dockerfile(manifest: ExporterManifest) -> str:
    docker = manifest.spec.artifacts.docker
    base = (
        docker.base_image if docker is not None else "registry.access.redhat.com/ubi9/ubi-minimal"
    )
    binary = manifest.spec.build.binary_name
    # ``TARGETARCH`` is buildah's automatic per-arch build arg; declaring it lets
    # one context build every arch by copying the matching ``<binary>-<arch>``.
    lines = [
        f"FROM {base}",
        "ARG TARGETARCH",
        f"COPY {binary}-${{TARGETARCH}} /usr/bin/{binary}",
    ]
    if docker is not None and docker.entrypoint:
        lines.append(f"ENTRYPOINT {json.dumps(docker.entrypoint)}")
    if docker is not None and docker.cmd:
        lines.append(f"CMD {json.dumps(docker.cmd)}")
    return "\n".join(lines) + "\n"


def emit_docker_context(
    manifest: ExporterManifest,
    *,
    binaries: Mapping[str, Path],
    out_dir: Path,
    manifest_dir: Path | None = None,
) -> Artifact:
    """Write the multi-arch build context to ``out_dir`` and return its artifact.

    ``binaries`` maps each arch to its extracted binary; each is staged as
    ``<binary_name>-<arch>`` next to the Dockerfile. Returns a single
    ``docker-image`` artifact (``arch`` is ``None`` — the image is multi-arch);
    its ``url`` is populated at publish time.
    """
    docker = manifest.spec.artifacts.docker
    if docker is None or not docker.enabled:
        raise BuildError(f"manifest {manifest.name!r} has no enabled docker target")

    if docker.dockerfile is not None:
        if manifest_dir is None:
            raise BuildError(
                f"{manifest.name!r}: docker.dockerfile is set but no manifest_dir to resolve it"
            )
        content = render_template(manifest_dir / docker.dockerfile, _template_context(manifest))
    else:
        content = render_dockerfile(manifest)

    out_dir.mkdir(parents=True, exist_ok=True)
    dockerfile = out_dir / "Dockerfile"
    dockerfile.write_text(content, encoding="utf-8")

    binary_name = manifest.spec.build.binary_name
    for arch, src in binaries.items():
        shutil.copy2(src, out_dir / f"{binary_name}-{arch}")

    return Artifact(
        type="docker-image",
        target=f"{manifest.name}:{clean_version(manifest.version)}",
        arch=None,
        sha256=file_sha256(dockerfile),
        signed=False,
    )
