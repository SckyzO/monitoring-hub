"""Upstream model: strategy Literal + optional major pin (SP4.1, spec §4)."""

from __future__ import annotations

import pytest

from forge.domain.errors import ManifestError
from forge.domain.manifest import ExporterManifest, parse_manifest


def _exporter(**upstream_extra: object) -> dict[str, object]:
    return {
        "kind": "exporter",
        "name": "demo_exporter",
        "description": "demo",
        "version": "1.0.0",
        "spec": {
            "upstream": {"type": "github", "repo": "owner/demo", **upstream_extra},
            "build": {"method": "binary_repack", "binary_name": "demo_exporter"},
            "artifacts": {},
        },
    }


def test_strategy_defaults_to_latest_release() -> None:
    manifest = parse_manifest(_exporter())
    assert manifest.kind == "exporter"
    assert manifest.spec.upstream.strategy == "latest_release"


def test_strategy_accepts_latest_release_explicitly() -> None:
    manifest = parse_manifest(_exporter(strategy="latest_release"))
    assert isinstance(manifest, ExporterManifest)
    assert manifest.spec.upstream.strategy == "latest_release"


def test_strategy_rejects_unknown_value() -> None:
    with pytest.raises(ManifestError):
        parse_manifest(_exporter(strategy="rolling"))


def test_pin_major_defaults_to_none() -> None:
    manifest = parse_manifest(_exporter())
    assert isinstance(manifest, ExporterManifest)
    assert manifest.spec.upstream.pin_major is None


def test_pin_major_accepts_int() -> None:
    manifest = parse_manifest(_exporter(pin_major=1))
    assert isinstance(manifest, ExporterManifest)
    assert manifest.spec.upstream.pin_major == 1
