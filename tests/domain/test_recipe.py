"""BundleRecipe: offline-bundle selection model (spec §5.1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from forge.domain.recipe import BundleRecipe, RecipeItem


def test_empty_recipe_defaults() -> None:
    recipe = BundleRecipe()
    assert recipe.schema_version == 1
    assert recipe.items == []


def test_recipe_with_items() -> None:
    recipe = BundleRecipe(
        items=[
            RecipeItem(kind="exporter", name="node_exporter", version="1.11.1"),
            RecipeItem(
                kind="dashboard",
                name="node-overview",
                version="39",
                overlay="x.override.yaml",
            ),
        ]
    )
    assert [item.name for item in recipe.items] == ["node_exporter", "node-overview"]
    assert recipe.items[1].overlay == "x.override.yaml"


def test_recipe_item_matrix_filters_default_none() -> None:
    item = RecipeItem(kind="exporter", name="node_exporter", version="1.11.1")
    assert item.targets is None
    assert item.arches is None


def test_recipe_item_matrix_filters_set() -> None:
    item = RecipeItem(
        kind="exporter",
        name="node_exporter",
        version="1.11.1",
        targets=["el9"],
        arches=["amd64", "arm64"],
    )
    assert item.targets == ["el9"]
    assert item.arches == ["amd64", "arm64"]


def test_recipe_bundle_wide_fields() -> None:
    recipe = BundleRecipe(generated_at="2026-06-08T00:00:00Z", arches=["amd64"])
    assert recipe.generated_at == "2026-06-08T00:00:00Z"
    assert recipe.arches == ["amd64"]


def test_recipe_generated_at_defaults_none() -> None:
    assert BundleRecipe().generated_at is None


def test_recipe_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        BundleRecipe(unexpected="x")  # type: ignore[call-arg]
