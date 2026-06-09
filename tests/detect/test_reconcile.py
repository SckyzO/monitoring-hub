"""forge.detect.reconcile: missing = expected(manifest matrix) - present(catalog) (spec §7)."""

from __future__ import annotations

from forge.detect.reconcile import Leg, expected_legs, missing_legs, present_legs
from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.manifest import Manifest, parse_manifest


def _exporter(name: str = "ex", *, archs: list[str], rpm: list[str], docker: bool) -> Manifest:
    data: dict[str, object] = {
        "kind": "exporter",
        "name": name,
        "description": "d",
        "version": "v1.0.0",
        "spec": {
            "upstream": {"type": "github", "repo": "o/r"},
            "build": {"method": "binary_repack", "binary_name": name, "archs": archs},
            "artifacts": {
                "rpm": {"enabled": True, "targets": rpm},
                "docker": {"enabled": docker},
            },
        },
    }
    return parse_manifest(data)


def _entry(name: str, artifacts: list[Artifact]) -> CatalogEntry:
    return CatalogEntry(
        kind="exporter",
        name=name,
        version="1.0.0",
        category="System",
        description="d",
        artifacts=artifacts,
    )


def test_expected_legs_enumerates_rpm_matrix_and_single_docker() -> None:
    manifest = _exporter(archs=["amd64", "arm64"], rpm=["el9", "el10"], docker=True)
    assert expected_legs(manifest) == {
        Leg("ex", "rpm", "el9", "amd64"),
        Leg("ex", "rpm", "el10", "amd64"),
        Leg("ex", "rpm", "el9", "arm64"),
        Leg("ex", "rpm", "el10", "arm64"),
        Leg("ex", "docker-image", None, None),
    }


def test_present_legs_normalizes_docker_target() -> None:
    catalog = Catalog(
        generated_at="t",
        items=[
            _entry(
                "ex",
                [
                    Artifact(type="rpm", target="el9", arch="amd64", sha256="x"),
                    Artifact(type="docker-image", target="ex:1.0.0", arch=None, sha256="y"),
                ],
            ),
        ],
    )
    assert present_legs(catalog) == {
        Leg("ex", "rpm", "el9", "amd64"),
        Leg("ex", "docker-image", None, None),
    }


def test_missing_all_present_is_empty() -> None:
    manifest = _exporter(archs=["amd64"], rpm=["el9"], docker=False)
    catalog = Catalog(
        generated_at="t",
        items=[
            _entry("ex", [Artifact(type="rpm", target="el9", arch="amd64", sha256="x")]),
        ],
    )
    assert missing_legs([manifest], catalog) == []


def test_missing_one_leg() -> None:
    manifest = _exporter(archs=["amd64", "arm64"], rpm=["el9"], docker=False)
    catalog = Catalog(
        generated_at="t",
        items=[
            _entry("ex", [Artifact(type="rpm", target="el9", arch="amd64", sha256="x")]),
        ],
    )
    assert missing_legs([manifest], catalog) == [Leg("ex", "rpm", "el9", "arm64")]


def test_missing_whole_item_when_absent_from_catalogue() -> None:
    manifest = _exporter(archs=["amd64"], rpm=["el9"], docker=True)
    assert missing_legs([manifest], None) == [
        Leg("ex", "docker-image", None, None),
        Leg("ex", "rpm", "el9", "amd64"),
    ]


def test_extra_in_catalogue_is_ignored() -> None:
    manifest = _exporter(archs=["amd64"], rpm=["el9"], docker=False)
    catalog = Catalog(
        generated_at="t",
        items=[
            _entry(
                "ex",
                [
                    Artifact(type="rpm", target="el9", arch="amd64", sha256="x"),
                    Artifact(type="rpm", target="el10", arch="amd64", sha256="z"),
                ],
            ),
        ],
    )
    assert missing_legs([manifest], catalog) == []
