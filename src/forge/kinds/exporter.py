"""Exporter producer (spec §7.1): fetch → repack (nfpm) → docker → sign.

Registered under ``exporter`` so ``registry.discover()`` wires it with no central
list. ``build`` orchestrates the SP1.3 packaging adapters over the target×arch
matrix behind the injected seams in ``BuildContext``: each arch is downloaded and
extracted once, then repacked into every RPM/DEB target and a Docker image.
"""

from __future__ import annotations

import shutil
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
from forge.packaging.docker import emit_docker_context
from forge.packaging.nfpm import NfpmPackager
from forge.packaging.sign import GpgSigner
from forge.packaging.staging import stage_assets


@register("exporter")
class ExporterProducer:
    kind = "exporter"

    def validate(self, manifest: Manifest) -> None:
        """Check the manifest is well-formed for this kind (spec §11).

        Validates manifest semantics only (spec §11): the manifest is the right
        kind and has at least one enabled artifact target.
        """
        if not isinstance(manifest, ExporterManifest):
            raise BuildError(f"exporter producer got a {manifest.kind!r} manifest")
        artifacts = manifest.spec.artifacts
        targets = [artifacts.rpm, artifacts.deb, artifacts.docker]
        if not any(t is not None and t.enabled for t in targets):
            raise BuildError(f"{manifest.name}: no enabled artifact target to build")

    def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult:
        self.validate(manifest)
        manifest = cast("ExporterManifest", manifest)  # validate guarantees the kind
        artifacts_spec = manifest.spec.artifacts
        nfpm = NfpmPackager(ctx.runner)
        signer = GpgSigner(ctx.runner) if ctx.signing_key_id else None

        # extra_sources are config files (arch-independent); fetch once.
        extra_sources = self._download_extra_sources(manifest, ctx)

        artifacts: list[Artifact] = []
        # Docker images are multi-arch: collect each arch's binary across the loop
        # and emit a single daemonless build context afterwards (no docker at build).
        docker_binaries: dict[str, Path] = {}
        for arch in manifest.spec.build.archs:
            extracted = self._extract(manifest, ctx, arch)
            binary = find_binary(extracted, manifest.spec.build.binary_name)
            extra_binaries = {
                name: find_binary(extracted, name) for name in manifest.spec.build.extra_binaries
            }

            if artifacts_spec.rpm is not None and artifacts_spec.rpm.enabled:
                for target in artifacts_spec.rpm.targets:
                    artifacts.append(
                        self._package(
                            nfpm,
                            signer,
                            manifest,
                            ctx,
                            "rpm",
                            target,
                            arch,
                            binary,
                            extra_binaries,
                            extra_sources,
                        )
                    )
            if artifacts_spec.deb is not None and artifacts_spec.deb.enabled:
                for target in artifacts_spec.deb.targets:
                    artifacts.append(
                        self._package(
                            nfpm,
                            signer,
                            manifest,
                            ctx,
                            "deb",
                            target,
                            arch,
                            binary,
                            extra_binaries,
                            extra_sources,
                        )
                    )
            if artifacts_spec.docker is not None and artifacts_spec.docker.enabled:
                docker_binaries[arch] = binary

        if docker_binaries:
            artifacts.append(
                emit_docker_context(
                    manifest,
                    binaries=docker_binaries,
                    out_dir=ctx.work_dir / "docker" / manifest.name,
                    manifest_dir=ctx.manifest_dir,
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

    def _extract(self, manifest: ExporterManifest, ctx: BuildContext, arch: str) -> Path:
        """Download the upstream archive for ``arch`` and return its extracted dir."""
        url = resolve_download_url(
            manifest.spec.upstream,
            name=manifest.name,
            version=manifest.version,
            arch=arch,
        )
        arch_dir = ctx.work_dir / "src" / arch
        archive = ctx.downloader.download(url, arch_dir / Path(url).name)
        return extract_archive(archive, arch_dir / "x")

    def _download_extra_sources(
        self, manifest: ExporterManifest, ctx: BuildContext
    ) -> dict[str, Path]:
        """Fetch ``build.extra_sources`` (e.g. snmp.yml) once, keyed by filename."""
        base = ctx.work_dir / "extra_sources"
        return {
            es.filename: ctx.downloader.download(es.url, base / es.filename)
            for es in manifest.spec.build.extra_sources
        }

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
        extra_binaries: dict[str, Path],
        extra_sources: dict[str, Path],
    ) -> Artifact:
        work = self._workdir(ctx, f"{fmt}/{target}", arch)
        # Stage downloaded extra sources at the work-dir root so an
        # extra_files.source: <filename> entry resolves (snmp_exporter pattern).
        for filename, src in extra_sources.items():
            shutil.copy2(src, work / filename)
        artifact = nfpm.package(
            manifest,
            packager=fmt,  # type: ignore[arg-type]  # fmt is "rpm"|"deb" by construction
            target=target,
            arch=arch,
            binary_src=binary,
            work_dir=work,
            extra_binaries=extra_binaries,
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
        # Stage the manifest's committed assets/ so nfpm extra_files.source
        # (assets/<file>) and custom Dockerfile COPYs resolve from the work dir.
        stage_assets(ctx.manifest_dir, work)
        return work
