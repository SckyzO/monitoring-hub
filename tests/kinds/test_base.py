"""Producer protocol + build I/O models (spec §9)."""

from __future__ import annotations

from pathlib import Path

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.manifest import Manifest
from forge.fetch.http import HttpxDownloader
from forge.kinds.base import BuildContext, BuildResult, Producer
from forge.packaging.runner import SubprocessRunner


def test_build_context_holds_injected_seams(tmp_path: Path) -> None:
    ctx = BuildContext(
        work_dir=tmp_path,
        downloader=HttpxDownloader(),
        runner=SubprocessRunner(),
    )
    assert ctx.work_dir == tmp_path
    assert ctx.signing_key_id is None
    assert isinstance(ctx.runner, SubprocessRunner)


def test_build_context_accepts_signing_key(tmp_path: Path) -> None:
    ctx = BuildContext(
        work_dir=tmp_path,
        downloader=HttpxDownloader(),
        runner=SubprocessRunner(),
        signing_key_id="ABCD1234",
    )
    assert ctx.signing_key_id == "ABCD1234"


def test_build_result_carries_artifacts_and_entry() -> None:
    entry = CatalogEntry(
        kind="dashboard", name="x", version="1", category="System", description="d"
    )
    result = BuildResult(artifacts=[Artifact(type="grafana-dashboard", sha256="x")], entry=entry)
    assert result.entry.name == "x"
    assert result.artifacts[0].type == "grafana-dashboard"


def test_conforming_class_satisfies_protocol() -> None:
    class FakeProducer:
        kind = "fake"

        def validate(self, manifest: Manifest) -> None:
            return None

        def build(self, manifest: Manifest, ctx: BuildContext) -> BuildResult:
            entry = CatalogEntry(
                kind="fake", name="n", version="1", category="System", description="d"
            )
            return BuildResult(entry=entry)

    assert isinstance(FakeProducer(), Producer)
