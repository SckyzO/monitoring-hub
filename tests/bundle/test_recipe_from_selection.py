"""recipe_from_selection: CLI selectors → BundleRecipe (spec §5.2)."""

from __future__ import annotations

import pytest

from forge.bundle.resolver import recipe_from_selection
from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import BundleError


def _cat() -> Catalog:
    return Catalog(
        generated_at="2026-06-08T00:00:00Z",
        items=[
            CatalogEntry(
                kind="exporter",
                name="node_exporter",
                version="1.9.1",
                category="System",
                description="n",
                artifacts=[Artifact(type="rpm", target="el9", arch="amd64", sha256="a")],
            ),
            CatalogEntry(
                kind="dashboard",
                name="node_exporter",  # same name, different kind → ambiguous
                version="39",
                category="System",
                description="d",
                artifacts=[Artifact(type="grafana-dashboard", sha256="x")],
            ),
            CatalogEntry(
                kind="exporter",
                name="blackbox_exporter",
                version="0.25.0",
                category="Network",
                description="b",
                artifacts=[Artifact(type="rpm", target="el9", arch="amd64", sha256="c")],
            ),
        ],
    )


def test_selection_defaults_version_from_catalog() -> None:
    recipe = recipe_from_selection(
        ["blackbox_exporter"],
        _cat(),
        targets=None,
        arches=None,
        generated_at="2026-06-08T00:00:00Z",
    )
    assert recipe.generated_at == "2026-06-08T00:00:00Z"
    assert [(i.kind, i.name, i.version) for i in recipe.items] == [
        ("exporter", "blackbox_exporter", "0.25.0")
    ]


def test_selection_pins_explicit_version() -> None:
    recipe = recipe_from_selection(["blackbox_exporter@0.24.0"], _cat(), targets=None, arches=None)
    assert recipe.items[0].version == "0.24.0"


def test_selection_threads_global_filters() -> None:
    recipe = recipe_from_selection(["blackbox_exporter"], _cat(), targets=["el9"], arches=["amd64"])
    assert recipe.arches == ["amd64"]
    assert recipe.items[0].targets == ["el9"]


def test_selection_kind_qualifier_resolves_ambiguity() -> None:
    recipe = recipe_from_selection(["dashboard:node_exporter"], _cat(), targets=None, arches=None)
    assert recipe.items[0].kind == "dashboard"
    assert recipe.items[0].version == "39"


def test_selection_ambiguous_bare_name_raises() -> None:
    with pytest.raises(BundleError, match="ambiguous"):
        recipe_from_selection(["node_exporter"], _cat(), targets=None, arches=None)


def test_selection_unknown_item_raises() -> None:
    with pytest.raises(BundleError, match="not in catalog"):
        recipe_from_selection(["ghost"], _cat(), targets=None, arches=None)


def test_selection_unknown_kind_qualified_raises() -> None:
    with pytest.raises(BundleError, match="not in catalog"):
        recipe_from_selection(["stack:node_exporter"], _cat(), targets=None, arches=None)


def test_selection_empty_selector_raises() -> None:
    with pytest.raises(BundleError, match="invalid"):
        recipe_from_selection(["@1.0"], _cat(), targets=None, arches=None)
