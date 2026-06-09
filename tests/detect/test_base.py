"""detect.base: DetectedVersion value object + VersionSource contract (spec §4)."""

from __future__ import annotations

import pytest

from forge.detect.base import DetectedVersion


def test_detected_version_holds_fields() -> None:
    dv = DetectedVersion(
        item="node_exporter",
        kind="exporter",
        current="1.9.0",
        latest="1.9.1",
        latest_raw="v1.9.1",
        source_type="github-release",
        outdated=True,
    )
    assert dv.item == "node_exporter"
    assert dv.outdated is True


def test_detected_version_is_frozen() -> None:
    dv = DetectedVersion(
        item="a",
        kind="exporter",
        current="1",
        latest="1",
        latest_raw="v1",
        source_type="github-release",
        outdated=False,
    )
    with pytest.raises((AttributeError, TypeError)):
        dv.latest = "2"  # type: ignore[misc]
