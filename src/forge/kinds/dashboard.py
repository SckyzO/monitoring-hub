"""Dashboard producer (spec §7.2): resolve source -> fetch JSON -> validate.

The abstraction stress test: a kind with no OS packaging. It emits a single
``grafana-dashboard`` Artifact + a CatalogEntry, proving the producer contract
generalizes beyond exporters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.errors import BuildError
from forge.domain.manifest import DashboardManifest, LocalSource, Manifest
from forge.fetch.dashboard_source import resolve_dashboard_url
from forge.kinds.base import BuildContext, BuildResult
from forge.kinds.registry import register
from forge.packaging.checksum import file_sha256


@register("dashboard")
class DashboardProducer:
    kind = "dashboard"

    def validate(self, manifest: Manifest) -> None:
        """Check the manifest is a well-formed dashboard manifest (spec §11)."""
        if not isinstance(manifest, DashboardManifest):
            raise BuildError(f"dashboard producer got a {manifest.kind!r} manifest")

    def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult:
        self.validate(manifest)
        manifest = cast("DashboardManifest", manifest)  # validate guarantees the kind

        # Land the JSON under a dashboards/ subdir so a `mh build --work-dir dist`
        # in CI produces dist/dashboards/<name>.json — the exact path `mh repo
        # build --dashboards dist/dashboards` reads at assemble time.
        dest = ctx.work_dir / "dashboards" / f"{manifest.name}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._fetch(manifest, ctx, dest)
        self._validate_json(manifest, dest)

        artifact = Artifact(type="grafana-dashboard", sha256=file_sha256(dest), signed=False)
        entry = CatalogEntry(
            kind=manifest.kind,
            name=manifest.name,
            version=manifest.version,
            category=manifest.category,
            description=manifest.description,
            artifacts=[artifact],
        )
        return BuildResult(artifacts=[artifact], entry=entry)

    def _fetch(self, manifest: DashboardManifest, ctx: BuildContext, dest: Path) -> None:
        source = manifest.spec.source
        url = resolve_dashboard_url(source)
        if url is None:
            local_source = cast("LocalSource", source)  # url is None iff source is local
            if ctx.manifest_dir is None:
                raise BuildError(
                    f"{manifest.name}: local dashboard source needs a manifest_dir to resolve"
                )
            local = ctx.manifest_dir / local_source.path
            if not local.is_file():
                raise BuildError(f"{manifest.name}: local dashboard not found: {local}")
            dest.write_bytes(local.read_bytes())
        else:
            ctx.downloader.download(url, dest)

    @staticmethod
    def _validate_json(manifest: DashboardManifest, dest: Path) -> None:
        try:
            parsed = json.loads(dest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BuildError(f"{manifest.name}: dashboard source is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise BuildError(f"{manifest.name}: dashboard JSON must be an object")
