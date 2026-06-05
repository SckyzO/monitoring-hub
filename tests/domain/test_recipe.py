"""BundleRecipe: offline-bundle selection model (spec §6.4). SP3 seam only."""

from __future__ import annotations

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
