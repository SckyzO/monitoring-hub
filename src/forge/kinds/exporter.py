"""Exporter producer (spec §7.1): fetch → repack (nfpm) → docker → sign.

Registered under ``exporter`` so ``registry.discover()`` wires it with no central
list. ``build`` orchestrates the SP1.3 packaging adapters over the target×arch
matrix behind the injected seams in ``BuildContext``: each arch is downloaded and
extracted once, then repacked into every RPM/DEB target and a Docker image.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.errors import BuildError
from forge.domain.manifest import ExporterManifest, Manifest
from forge.domain.version import clean_version
from forge.fetch.archive import extract_archive, find_binary
from forge.fetch.upstream import resolve_download_url
from forge.kinds.base import BuildContext, BuildResult
from forge.kinds.registry import register
from forge.packaging.docker import DockerBuilder
from forge.packaging.nfpm import NfpmPackager
from forge.packaging.sign import GpgSigner


@register("exporter")
class ExporterProducer:
    kind = "exporter"

    def validate(self, manifest: Manifest) -> None:
        if not isinstance(manifest, ExporterManifest):
            raise BuildError(f"exporter producer got a {manifest.kind!r} manifest")
        artifacts = manifest.spec.artifacts
        targets = [artifacts.rpm, artifacts.deb, artifacts.docker]
        if not any(t is not None and t.enabled for t in targets):
            raise BuildError(f"{manifest.name}: no enabled artifact target to build")
        build = manifest.spec.build
        if build.extra_binaries:
            raise BuildError(f"{manifest.name}: build.extra_binaries is not supported yet (SP1.4b)")
        if build.extra_sources:
            raise BuildError(f"{manifest.name}: build.extra_sources is not supported yet (SP1.4b)")

    def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult:
        self.validate(manifest)
        manifest = cast("ExporterManifest", manifest)  # validate guarantees the kind
        artifacts_spec = manifest.spec.artifacts
        nfpm = NfpmPackager(ctx.runner)
        docker_builder = DockerBuilder(ctx.runner)
        signer = GpgSigner(ctx.runner) if ctx.signing_key_id else None

        artifacts: list[Artifact] = []
        for arch in manifest.spec.build.archs:
            binary = self._fetch_binary(manifest, ctx, arch)

            if artifacts_spec.rpm is not None and artifacts_spec.rpm.enabled:
                for target in artifacts_spec.rpm.targets:
                    artifacts.append(
                        self._package(nfpm, signer, manifest, ctx, "rpm", target, arch, binary)
                    )
            if artifacts_spec.deb is not None and artifacts_spec.deb.enabled:
                for target in artifacts_spec.deb.targets:
                    artifacts.append(
                        self._package(nfpm, signer, manifest, ctx, "deb", target, arch, binary)
                    )
            if artifacts_spec.docker is not None and artifacts_spec.docker.enabled:
                work = self._workdir(ctx, "docker", arch)
                artifacts.append(
                    docker_builder.build_image(
                        manifest, arch=arch, binary_src=binary, work_dir=work
                    )
                )

        entry = CatalogEntry(
            kind=manifest.kind,
            name=manifest.name,
            version=clean_version(manifest.version),
            category=manifest.category,
            description=manifest.description,
            artifacts=artifacts,
        )
        return BuildResult(artifacts=artifacts, entry=entry)

    def _fetch_binary(self, manifest: ExporterManifest, ctx: BuildContext, arch: str) -> Path:
        url = resolve_download_url(
            manifest.spec.upstream,
            name=manifest.name,
            version=manifest.version,
            arch=arch,
        )
        arch_dir = ctx.work_dir / "src" / arch
        archive = ctx.downloader.download(url, arch_dir / Path(url).name)
        extracted = extract_archive(archive, arch_dir / "x")
        return find_binary(extracted, manifest.spec.build.binary_name)

    def _package(  # noqa: PLR0913 — locked keyword-positional contract (matches adapters)
        self,
        nfpm: NfpmPackager,
        signer: GpgSigner | None,
        manifest: ExporterManifest,
        ctx: BuildContext,
        fmt: str,
        target: str,
        arch: str,
        binary: Path,
    ) -> Artifact:
        work = self._workdir(ctx, f"{fmt}/{target}", arch)
        artifact = nfpm.package(
            manifest,
            packager=fmt,  # type: ignore[arg-type]  # fmt is "rpm"|"deb" by construction
            target=target,
            arch=arch,
            binary_src=binary,
            work_dir=work,
        )
        if signer is not None and ctx.signing_key_id is not None:
            produced = sorted(work.glob(f"*.{fmt}"))
            if len(produced) != 1:
                raise BuildError(f"expected one .{fmt} in {work}, found {len(produced)}")
            signer.sign(produced[0], packager=fmt, key_id=ctx.signing_key_id)  # type: ignore[arg-type]
            artifact = artifact.model_copy(update={"signed": True})
        return artifact

    @staticmethod
    def _workdir(ctx: BuildContext, kind: str, arch: str) -> Path:
        work = ctx.work_dir / kind / arch
        work.mkdir(parents=True, exist_ok=True)
        return work
