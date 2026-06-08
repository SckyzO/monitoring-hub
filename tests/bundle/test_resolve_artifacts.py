"""resolve_artifacts: BundleRecipe + Catalog → concrete artefacts (spec §5.2)."""

from __future__ import annotations

import pytest

from forge.bundle.resolver import resolve_artifacts
from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import BundleError
from forge.domain.recipe import BundleRecipe, RecipeItem


def _entry() -> CatalogEntry:
    return CatalogEntry(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        category="System",
        description="n",
        artifacts=[
            Artifact(type="rpm", target="el9", arch="amd64", sha256="a"),
            Artifact(type="rpm", target="el9", arch="arm64", sha256="b"),
            Artifact(type="deb", target="ubuntu-24.04", arch="amd64", sha256="c"),
            Artifact(type="docker-image", target="node_exporter:1.9.1", arch=None, sha256="d"),
        ],
    )


def _catalog(*entries: CatalogEntry) -> Catalog:
    return Catalog(generated_at="2026-06-08T00:00:00Z", items=list(entries))


def test_resolve_expands_and_skips_docker() -> None:
    recipe = BundleRecipe(
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1")]
    )
    resolved = resolve_artifacts(recipe, _catalog(_entry()))
    assert [(r.artifact.type, r.artifact.arch) for r in resolved] == [
        ("rpm", "amd64"),
        ("rpm", "arm64"),
        ("deb", "amd64"),
    ]
    assert resolved[0].filename == "node_exporter-1.9.1-1.el9.x86_64.rpm"
    assert resolved[2].filename == "node-exporter_1.9.1-1_amd64.deb"


def test_resolve_includes_docker_image_only_when_requested() -> None:
    recipe = BundleRecipe(
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1")]
    )
    out = resolve_artifacts(recipe, _catalog(_entry()), include_images=True)
    image = [r for r in out if r.artifact.type == "docker-image"]
    assert [r.artifact.type for r in image] == ["docker-image"]
    assert image[0].filename == "node_exporter-1.9.1.tar"


def test_resolve_image_unaffected_by_arch_filter() -> None:
    # docker-image has arch=None (multi-arch); the recipe arch filter must not drop it.
    recipe = BundleRecipe(
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1", arches=["amd64"])]
    )
    out = resolve_artifacts(recipe, _catalog(_entry()), include_images=True)
    assert any(r.artifact.type == "docker-image" for r in out)


def test_resolve_item_arch_filter() -> None:
    recipe = BundleRecipe(
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1", arches=["amd64"])]
    )
    resolved = resolve_artifacts(recipe, _catalog(_entry()))
    assert all(r.artifact.arch == "amd64" for r in resolved)
    assert [r.artifact.type for r in resolved] == ["rpm", "deb"]


def test_resolve_bundle_wide_arch_default() -> None:
    recipe = BundleRecipe(
        arches=["arm64"],
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1")],
    )
    resolved = resolve_artifacts(recipe, _catalog(_entry()))
    assert [(r.artifact.type, r.artifact.arch) for r in resolved] == [("rpm", "arm64")]


def test_resolve_item_target_filter() -> None:
    recipe = BundleRecipe(
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1", targets=["el9"])]
    )
    resolved = resolve_artifacts(recipe, _catalog(_entry()))
    assert {r.artifact.target for r in resolved} == {"el9"}  # ubuntu deb filtered out


def test_resolve_dashboard_always_included() -> None:
    dash = CatalogEntry(
        kind="dashboard",
        name="node-overview",
        version="39",
        category="System",
        description="d",
        artifacts=[Artifact(type="grafana-dashboard", sha256="x")],
    )
    recipe = BundleRecipe(
        arches=["amd64"],
        items=[RecipeItem(kind="dashboard", name="node-overview", version="39")],
    )
    resolved = resolve_artifacts(recipe, _catalog(dash))
    assert len(resolved) == 1
    assert resolved[0].filename == "node-overview.json"


def test_resolve_item_not_in_catalog() -> None:
    recipe = BundleRecipe(items=[RecipeItem(kind="exporter", name="ghost", version="1.0")])
    with pytest.raises(BundleError, match="not in catalog"):
        resolve_artifacts(recipe, _catalog(_entry()))


def test_resolve_version_mismatch() -> None:
    recipe = BundleRecipe(
        items=[RecipeItem(kind="exporter", name="node_exporter", version="9.9.9")]
    )
    with pytest.raises(BundleError, match="version mismatch"):
        resolve_artifacts(recipe, _catalog(_entry()))
