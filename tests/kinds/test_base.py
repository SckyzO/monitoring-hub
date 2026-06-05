"""Producer protocol + build I/O models (spec §9)."""

from __future__ import annotations

from pathlib import Path

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry
from forge.domain.manifest import Manifest
from forge.kinds.base import BuildContext, BuildResult, Producer


def test_build_context_holds_work_dir() -> None:
    ctx = BuildContext(work_dir=Path("/tmp/build"))
    assert ctx.work_dir == Path("/tmp/build")


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
