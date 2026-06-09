"""Self-healing reconcile diff: missing = expected(manifest matrix) - present(catalog).

No mutable failure state is stored anywhere (spec §7): the legs to (re)build are
*derived* from the manifest matrix (what should exist) minus the published
catalogue (what does exist). The daily reconcile run rebuilds exactly the
difference. ``expected_legs`` mirrors ``ExporterProducer.build`` enumeration.

Only exporters have a target×arch matrix; single-artifact kinds reconcile at
whole-item granularity (a total failure blocks their bump PR, spec §7), so they
contribute no expected legs here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from forge.domain.catalog import Catalog
from forge.domain.manifest import ExporterManifest, Manifest

_DOCKER_TYPE = "docker-image"


@dataclass(frozen=True, order=True)
class Leg:
    """One build leg: an item's artifact at a (type, target, arch) coordinate.

    The multi-arch docker image is normalized to ``(item, "docker-image", None,
    None)`` on both the expected and present sides: its real ``Artifact.target``
    embeds the version, which would otherwise spuriously differ across a bump.
    """

    item: str
    type: str
    target: str | None
    arch: str | None


def expected_legs(manifest: Manifest) -> set[Leg]:
    """The legs an exporter manifest declares it should produce (matrix)."""
    if not isinstance(manifest, ExporterManifest):
        return set()
    spec = manifest.spec
    legs: set[Leg] = set()
    for arch in spec.build.archs:
        if spec.artifacts.rpm is not None and spec.artifacts.rpm.enabled:
            legs.update(Leg(manifest.name, "rpm", t, arch) for t in spec.artifacts.rpm.targets)
        if spec.artifacts.deb is not None and spec.artifacts.deb.enabled:
            legs.update(Leg(manifest.name, "deb", t, arch) for t in spec.artifacts.deb.targets)
    if spec.artifacts.docker is not None and spec.artifacts.docker.enabled:
        legs.add(Leg(manifest.name, _DOCKER_TYPE, None, None))
    return legs


def present_legs(catalog: Catalog | None) -> set[Leg]:
    """The legs currently published in ``catalog`` (docker target normalized)."""
    if catalog is None:
        return set()
    legs: set[Leg] = set()
    for item in catalog.items:
        for art in item.artifacts:
            if art.type == _DOCKER_TYPE:
                legs.add(Leg(item.name, _DOCKER_TYPE, None, None))
            else:
                legs.add(Leg(item.name, art.type, art.target, art.arch))
    return legs


def missing_legs(manifests: Iterable[Manifest], catalog: Catalog | None) -> list[Leg]:
    """Sorted ``expected − present``: the legs the next run must (re)build."""
    expected: set[Leg] = set()
    for manifest in manifests:
        expected |= expected_legs(manifest)
    return sorted(expected - present_legs(catalog))
