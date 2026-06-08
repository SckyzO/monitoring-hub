"""build_bundle: resolve → fetch → assemble → pack (spec §5.6).

The builder is an orchestrator; it is unit-tested with a FakeRunner (like the
assemble tests) so it stays in ``make ci`` without needing createrepo_c/tar. The
real end-to-end tar+install is proven by the gated offline smoke (spec §9.3).
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.bundle.builder import build_bundle
from forge.bundle.resolver import ResolvedArtifact
from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import BundleError
from forge.domain.recipe import BundleRecipe, RecipeItem
from tests.packaging.conftest import FakeRunner

_RPM = "node_exporter-1.9.1-1.el9.x86_64.rpm"


class _FakeSource:
    """Writes a stub file at dest for each requested artefact; records filenames."""

    def __init__(self, blobs: dict[str, str]) -> None:
        self._blobs = blobs
        self.fetched: list[str] = []

    def fetch(self, artifact: ResolvedArtifact, dest: Path) -> Path:
        self.fetched.append(artifact.filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(self._blobs[artifact.filename], encoding="utf-8")
        return dest


def _catalog() -> Catalog:
    return Catalog(
        generated_at="2026-06-08T00:00:00Z",
        items=[
            CatalogEntry(
                kind="exporter",
                name="node_exporter",
                version="1.9.1",
                category="System",
                description="Node exporter",
                artifacts=[Artifact(type="rpm", target="el9", arch="amd64", sha256="a" * 64)],
            )
        ],
    )


def _catalog_with_image() -> Catalog:
    return Catalog(
        generated_at="2026-06-08T00:00:00Z",
        items=[
            CatalogEntry(
                kind="exporter",
                name="node_exporter",
                version="1.9.1",
                category="System",
                description="Node exporter",
                artifacts=[
                    Artifact(type="rpm", target="el9", arch="amd64", sha256="a" * 64),
                    Artifact(type="docker-image", target="node_exporter:1.9.1", sha256="c" * 64),
                ],
            )
        ],
    )


def _recipe() -> BundleRecipe:
    return BundleRecipe(
        generated_at="2026-06-08T00:00:00Z",
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1")],
    )


class _FakeImageSource:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def save(self, artifact: ResolvedArtifact, dest_dir: Path, *, arches: list[str]) -> list[Path]:
        self.calls.append((artifact.name, arches))
        dest_dir.mkdir(parents=True, exist_ok=True)
        out = dest_dir / f"{artifact.name}-{artifact.version}-{arches[0]}.tar"
        out.write_text("IMG", encoding="utf-8")
        return [out]


def test_build_bundle_fetches_into_inputs_assembles_tree_and_packs(tmp_path: Path) -> None:
    source = _FakeSource({_RPM: "RPMDATA"})
    runner = FakeRunner()
    staging = tmp_path / "work"
    out = tmp_path / "bundle.tar.gz"

    result = build_bundle(
        recipe=_recipe(),
        catalog=_catalog(),
        source=source,
        staging=staging,
        out=out,
        runner=runner,
    )

    assert result == out
    # every resolved artefact is fetched into the throwaway inputs/ dir
    assert source.fetched == [_RPM]
    assert (staging / "inputs" / _RPM).exists()
    # assemble built the Python-side tree under tree/ (createrepo is faked away)
    assert (staging / "tree" / "recipe.json").exists()
    assert (staging / "tree" / "README.md").exists()
    # pack tars the tree/ dir — NOT staging (so inputs/ never enters the archive)
    tar_call = cast("list[str]", runner.calls[-1]["args"])
    assert tar_call == ["tar", "-czf", str(out), "-C", str(staging / "tree"), "."]


def test_build_bundle_saves_images_into_tree_and_sums_them(tmp_path: Path) -> None:
    source = _FakeSource({_RPM: "RPMDATA"})
    images = _FakeImageSource()
    staging = tmp_path / "work"
    out = tmp_path / "bundle.tar.gz"

    build_bundle(
        recipe=_recipe(),
        catalog=_catalog_with_image(),
        source=source,
        staging=staging,
        out=out,
        image_source=images,
        image_arches=["amd64"],
        runner=FakeRunner(),
    )

    assert images.calls == [("node_exporter", ["amd64"])]
    tree = staging / "tree"
    assert (tree / "images" / "node_exporter-1.9.1-amd64.tar").exists()
    sums = (tree / "SHA256SUMS").read_text(encoding="utf-8")
    assert "images/node_exporter-1.9.1-amd64.tar" in sums  # re-summed after images
    assert "## Container images" in (tree / "README.md").read_text(encoding="utf-8")


def test_build_bundle_propagates_fetch_failure(tmp_path: Path) -> None:
    class _Boom:
        def fetch(self, artifact: ResolvedArtifact, dest: Path) -> Path:
            raise BundleError("nope")

    with pytest.raises(BundleError, match="nope"):
        build_bundle(
            recipe=_recipe(),
            catalog=_catalog(),
            source=_Boom(),
            staging=tmp_path / "work",
            out=tmp_path / "b.tar.gz",
            runner=FakeRunner(),
        )
