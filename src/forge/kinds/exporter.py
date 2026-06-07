"""Exporter producer (spec §7.1): fetch → repack (nfpm) → docker → sign.

Registered under ``exporter`` so ``registry.discover()`` wires it with no central
list. ``build`` (Task 6) orchestrates the SP1.3 packaging adapters over the
target×arch matrix behind the injected seams in ``BuildContext``.
"""

from __future__ import annotations

from forge.domain.errors import BuildError
from forge.domain.manifest import ExporterManifest, Manifest
from forge.kinds.base import BuildContext, BuildResult
from forge.kinds.registry import register


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
            raise BuildError(
                f"{manifest.name}: build.extra_binaries is not supported yet (SP1.4b)"
            )
        if build.extra_sources:
            raise BuildError(
                f"{manifest.name}: build.extra_sources is not supported yet (SP1.4b)"
            )

    def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult:
        raise NotImplementedError  # implemented in Task 6
