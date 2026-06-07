"""Dashboard producer: registration, validation, fetch + JSON validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.errors import BuildError
from forge.domain.manifest import (
    Build,
    DashboardManifest,
    DashboardSpec,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    GrafanaSource,
    LocalSource,
    RpmTarget,
    Upstream,
    UrlSource,
)
from forge.kinds.base import BuildContext
from forge.kinds.dashboard import DashboardProducer
from forge.kinds.registry import discover, get_producer
from tests.fetch.conftest import FakeDownloader
from tests.packaging.conftest import FakeRunner


def _grafana_manifest() -> DashboardManifest:
    return DashboardManifest(
        kind="dashboard",
        name="node-overview",
        description="Node Exporter Full",
        version="39",
        spec=DashboardSpec(source=GrafanaSource(type="grafana", id=1860, revision=39)),
    )


def _exporter_manifest() -> ExporterManifest:
    return ExporterManifest(
        kind="exporter",
        name="x_exp",
        description="d",
        version="1.0.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="o/r"),
            build=Build(method="binary_repack", binary_name="x_exp"),
            artifacts=ExporterArtifacts(rpm=RpmTarget(enabled=True)),
        ),
    )


def test_dashboard_producer_registered() -> None:
    discover()
    producer = get_producer("dashboard")
    assert producer.kind == "dashboard"
    assert isinstance(producer, DashboardProducer)


def test_validate_rejects_non_dashboard() -> None:
    with pytest.raises(BuildError, match="manifest"):
        DashboardProducer().validate(_exporter_manifest())


def test_build_emits_grafana_dashboard_artifact(tmp_path: Path) -> None:
    dl = FakeDownloader(payload=b'{"title": "Node", "panels": []}')
    ctx = BuildContext(work_dir=tmp_path, downloader=dl, runner=FakeRunner())
    result = DashboardProducer().build(_grafana_manifest(), ctx)

    assert len(result.artifacts) == 1
    artifact = result.artifacts[0]
    assert isinstance(artifact, Artifact)
    assert artifact.type == "grafana-dashboard"
    assert artifact.signed is False
    assert dl.urls == ["https://grafana.com/api/dashboards/1860/revisions/39/download"]

    entry = result.entry
    assert isinstance(entry, CatalogEntry)
    assert entry.kind == "dashboard"
    assert entry.name == "node-overview"
    assert entry.version == "39"


def test_build_rejects_non_object_json(tmp_path: Path) -> None:
    dl = FakeDownloader(payload=b"[1, 2, 3]")
    ctx = BuildContext(work_dir=tmp_path, downloader=dl, runner=FakeRunner())
    with pytest.raises(BuildError, match="must be an object"):
        DashboardProducer().build(_grafana_manifest(), ctx)


def test_build_rejects_invalid_json(tmp_path: Path) -> None:
    dl = FakeDownloader(payload=b"not json{")
    ctx = BuildContext(work_dir=tmp_path, downloader=dl, runner=FakeRunner())
    with pytest.raises(BuildError, match="not valid JSON"):
        DashboardProducer().build(_grafana_manifest(), ctx)


def test_build_reads_local_source(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "dash"
    manifest_dir.mkdir()
    (manifest_dir / "node.json").write_text('{"title": "Local"}', encoding="utf-8")
    manifest = DashboardManifest(
        kind="dashboard",
        name="local-dash",
        description="d",
        version="1",
        spec=DashboardSpec(source=LocalSource(type="local", path="node.json")),
    )
    ctx = BuildContext(
        work_dir=tmp_path / "work",
        downloader=FakeDownloader(),
        runner=FakeRunner(),
        manifest_dir=manifest_dir,
    )
    result = DashboardProducer().build(manifest, ctx)
    assert result.artifacts[0].type == "grafana-dashboard"


def test_build_local_source_without_manifest_dir_raises(tmp_path: Path) -> None:
    manifest = DashboardManifest(
        kind="dashboard",
        name="local-dash",
        description="d",
        version="1",
        spec=DashboardSpec(source=LocalSource(type="local", path="node.json")),
    )
    ctx = BuildContext(work_dir=tmp_path, downloader=FakeDownloader(), runner=FakeRunner())
    with pytest.raises(BuildError, match="manifest_dir"):
        DashboardProducer().build(manifest, ctx)


def test_build_url_source(tmp_path: Path) -> None:
    manifest = DashboardManifest(
        kind="dashboard",
        name="url-dash",
        description="d",
        version="1",
        spec=DashboardSpec(source=UrlSource(type="url", url="https://example.test/d.json")),
    )
    dl = FakeDownloader(payload=b'{"ok": true}')
    ctx = BuildContext(work_dir=tmp_path, downloader=dl, runner=FakeRunner())
    DashboardProducer().build(manifest, ctx)
    assert dl.urls == ["https://example.test/d.json"]
