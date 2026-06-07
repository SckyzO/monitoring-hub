"""Exporter producer: semantic validation + registry wiring (build in Task 6)."""

from __future__ import annotations

import pytest

from forge.domain.errors import BuildError
from forge.domain.manifest import (
    Build,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    RpmTarget,
    Upstream,
)
from forge.kinds.exporter import ExporterProducer


def _manifest(*, rpm=None, deb=None, docker=None, build=None) -> ExporterManifest:
    return ExporterManifest(
        kind="exporter",
        name="x_exp",
        description="d",
        version="1.0.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="o/r"),
            build=build or Build(method="binary_repack", binary_name="x_exp"),
            artifacts=ExporterArtifacts(rpm=rpm, deb=deb, docker=docker),
        ),
    )


def test_validate_accepts_one_enabled_target() -> None:
    ExporterProducer().validate(_manifest(rpm=RpmTarget(enabled=True)))


def test_validate_rejects_no_enabled_target() -> None:
    with pytest.raises(BuildError, match="no enabled artifact target"):
        ExporterProducer().validate(_manifest(rpm=RpmTarget(enabled=False)))


def test_validate_rejects_extra_binaries() -> None:
    build = Build(method="binary_repack", binary_name="x_exp", extra_binaries=["amtool"])
    with pytest.raises(BuildError, match="extra_binaries"):
        ExporterProducer().validate(_manifest(rpm=RpmTarget(enabled=True), build=build))


def test_producer_registered_for_exporter_kind() -> None:
    from forge.kinds.registry import discover, get_producer

    discover()
    producer = get_producer("exporter")
    assert producer.kind == "exporter"
    assert isinstance(producer, ExporterProducer)
