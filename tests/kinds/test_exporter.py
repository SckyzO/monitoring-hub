"""Exporter producer: semantic validation, registry wiring, and matrix build."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from typing import Any

import pytest

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.errors import BuildError
from forge.domain.manifest import (
    Build,
    DashboardManifest,
    DashboardSpec,
    DebTarget,
    DockerTarget,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    ExtraSource,
    RpmTarget,
    Upstream,
    UrlSource,
)
from forge.kinds.base import BuildContext
from forge.kinds.exporter import ExporterProducer
from forge.kinds.registry import discover, get_producer
from forge.packaging.runner import CommandResult
from tests.fetch.conftest import FakeDownloader
from tests.packaging.conftest import FakeRunner


def _manifest(
    *,
    rpm: RpmTarget | None = None,
    deb: DebTarget | None = None,
    docker: DockerTarget | None = None,
    build: Build | None = None,
) -> ExporterManifest:
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


def test_build_context_carries_manifest_dir(tmp_path: Path) -> None:
    ctx = BuildContext(
        work_dir=tmp_path,
        downloader=FakeDownloader(),
        runner=FakeRunner(),
        manifest_dir=tmp_path / "src",
    )
    assert ctx.manifest_dir == tmp_path / "src"


def test_validate_accepts_one_enabled_target() -> None:
    ExporterProducer().validate(_manifest(rpm=RpmTarget(enabled=True)))


def test_validate_rejects_no_enabled_target() -> None:
    with pytest.raises(BuildError, match="no enabled artifact target"):
        ExporterProducer().validate(_manifest(rpm=RpmTarget(enabled=False)))


def test_validate_accepts_extra_binaries() -> None:
    # SP1.4b features are schema-valid; they are rejected at build, not validate.
    build = Build(method="binary_repack", binary_name="x_exp", extra_binaries=["amtool"])
    ExporterProducer().validate(_manifest(rpm=RpmTarget(enabled=True), build=build))


def test_validate_accepts_extra_sources() -> None:
    build = Build(
        method="binary_repack",
        binary_name="x_exp",
        extra_sources=[
            ExtraSource(url="https://example.test/extra.tar.gz", filename="extra.tar.gz")
        ],
    )
    ExporterProducer().validate(_manifest(rpm=RpmTarget(enabled=True), build=build))


def test_build_packs_extra_binary(tmp_path: Path) -> None:
    build = Build(method="binary_repack", binary_name="x_exp", extra_binaries=["amtool"])
    ctx = BuildContext(
        work_dir=tmp_path,
        downloader=FakeDownloader(payload=_targz_bytes("x_exp", "amtool")),
        runner=_BuildRunner(),
    )
    result = ExporterProducer().build(_manifest(rpm=RpmTarget(enabled=True), build=build), ctx)
    # the extra binary is staged into the rpm work dir for nfpm to pick up
    nfpm_cfg = next(tmp_path.rglob("nfpm.yaml"))
    assert "amtool" in nfpm_cfg.read_text(encoding="utf-8")
    assert result.artifacts


def test_build_fetches_extra_sources(tmp_path: Path) -> None:
    build = Build(
        method="binary_repack",
        binary_name="x_exp",
        extra_sources=[ExtraSource(url="https://example.test/snmp.yml", filename="snmp.yml")],
    )
    downloader = FakeDownloader(payload=_targz_bytes("x_exp"))
    ctx = BuildContext(work_dir=tmp_path, downloader=downloader, runner=_BuildRunner())
    ExporterProducer().build(_manifest(rpm=RpmTarget(enabled=True), build=build), ctx)
    # the source URL was requested and the file landed in a package work dir root
    assert "https://example.test/snmp.yml" in downloader.urls
    assert next(tmp_path.rglob("rpm/**/snmp.yml"), None) is not None


def test_validate_rejects_non_exporter_manifest() -> None:
    dashboard = DashboardManifest(
        kind="dashboard",
        name="d",
        description="d",
        version="1.0.0",
        spec=DashboardSpec(source=UrlSource(type="url", url="https://example.test/d.json")),
    )
    with pytest.raises(BuildError, match="manifest"):
        ExporterProducer().validate(dashboard)


def test_producer_registered_for_exporter_kind() -> None:
    discover()
    producer = get_producer("exporter")
    assert producer.kind == "exporter"
    assert isinstance(producer, ExporterProducer)


def _targz_bytes(*members: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for member in members:
            info = tarfile.TarInfo(member)
            data = b"ELF-fake"
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class _BuildRunner(FakeRunner):
    """Fakes nfpm by materializing a package file in the -t target dir."""

    def run(
        self, args: Any, *, cwd: Any = None, env: Any = None, stdin: Any = None
    ) -> CommandResult:
        a = list(args)
        if a and a[0].endswith("nfpm"):
            fmt = a[a.index("-p") + 1]
            target_dir = Path(a[a.index("-t") + 1])
            (target_dir / f"pkg.{fmt}").write_bytes(b"pkgdata")
        return super().run(args, cwd=cwd, env=env, stdin=stdin)


def test_build_produces_full_matrix_and_catalog_entry(
    manifest: ExporterManifest, tmp_path: Path
) -> None:
    downloader = FakeDownloader(payload=_targz_bytes("node_exporter"))
    ctx = BuildContext(work_dir=tmp_path, downloader=downloader, runner=_BuildRunner())

    result = ExporterProducer().build(manifest, ctx)

    # archs = [amd64, arm64]; rpm [el9, el10] -> 4; deb [ubuntu-24.04, debian-12] -> 4; docker -> 2
    assert len(result.artifacts) == 10
    types = sorted({a.type for a in result.artifacts})
    assert types == ["deb", "docker-image", "rpm"]
    assert all(isinstance(a, Artifact) for a in result.artifacts)
    assert all(a.signed is False for a in result.artifacts)

    entry = result.entry
    assert isinstance(entry, CatalogEntry)
    assert entry.kind == "exporter"
    assert entry.name == "node_exporter"
    assert entry.version == "1.9.1"  # clean
    assert entry.category == "System"
    assert len(entry.artifacts) == 10

    # one download per arch (not per target)
    assert len(downloader.urls) == 2


def test_build_signs_rpm_deb_when_key_present(manifest: ExporterManifest, tmp_path: Path) -> None:
    ctx = BuildContext(
        work_dir=tmp_path,
        downloader=FakeDownloader(payload=_targz_bytes("node_exporter")),
        runner=_BuildRunner(),
        signing_key_id="ABCD1234",
    )
    result = ExporterProducer().build(manifest, ctx)
    by_type = {
        t: [a for a in result.artifacts if a.type == t] for t in ("rpm", "deb", "docker-image")
    }
    assert all(a.signed for a in by_type["rpm"])
    assert all(a.signed for a in by_type["deb"])
    assert all(not a.signed for a in by_type["docker-image"])


def test_build_rejects_invalid_manifest_via_validate(tmp_path: Path) -> None:
    bad = _manifest(rpm=RpmTarget(enabled=False))
    ctx = BuildContext(work_dir=tmp_path, downloader=FakeDownloader(), runner=FakeRunner())
    with pytest.raises(BuildError, match="no enabled artifact target"):
        ExporterProducer().build(bad, ctx)
