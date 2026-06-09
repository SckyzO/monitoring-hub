"""Watch orchestration (spec §8): map manifests to sources, build DetectedVersion.

``resolve_source_type`` is the single place that ties a manifest's
``spec.upstream`` to a registered ``VersionSource`` key. ``detect_all`` calls each
resolved source and produces the read-only ``DetectedVersion`` records consumed by
``mh watch`` (and, in SP4.3, by the bump workflow). Items that are not watchable
(no upstream, local upstream, unknown strategy) or whose upstream yields no
acceptable release are silently skipped — detection is best-effort and read-only.
"""

from __future__ import annotations

from collections.abc import Iterable

from forge.detect.base import DetectedVersion
from forge.detect.policy import is_newer
from forge.detect.registry import get_source
from forge.domain.manifest import ExporterManifest, Manifest
from forge.domain.version import clean_version
from forge.packaging.runner import CommandRunner


def resolve_source_type(manifest: Manifest) -> str | None:
    """Registry key of the version source for ``manifest``, or ``None``.

    Only github-backed exporters are watchable in SP4.1. Local upstreams and
    dashboards (grafana/url/git sources) are deferred — they slot in by adding a
    branch here plus a registered source, with no other change.
    """
    if isinstance(manifest, ExporterManifest):
        upstream = manifest.spec.upstream
        if upstream.type == "github" and upstream.strategy == "latest_release":
            return "github-release"
    return None


def detect_one(manifest: Manifest, *, runner: CommandRunner) -> DetectedVersion | None:
    """Detect one manifest's latest upstream version, or ``None`` if unwatchable."""
    source_type = resolve_source_type(manifest)
    if source_type is None:
        return None
    latest_raw = get_source(source_type).latest(manifest, runner=runner)
    if latest_raw is None:
        return None
    return DetectedVersion(
        item=manifest.name,
        kind=manifest.kind,
        current=clean_version(manifest.version),
        latest=clean_version(latest_raw),
        source_type=source_type,
        outdated=is_newer(latest_raw, manifest.version),
    )


def detect_all(manifests: Iterable[Manifest], *, runner: CommandRunner) -> list[DetectedVersion]:
    """Detect every watchable manifest; skip the rest. Order is preserved."""
    detected = [detect_one(manifest, runner=runner) for manifest in manifests]
    return [item for item in detected if item is not None]
