"""load_recipe: YAML/JSON recipe → BundleRecipe (spec §5.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.bundle.resolver import load_recipe
from forge.domain.errors import BundleError


def test_load_recipe_yaml(tmp_path: Path) -> None:
    path = tmp_path / "recipe.yaml"
    path.write_text(
        "schema_version: 1\n"
        "arches: [amd64]\n"
        "items:\n"
        "  - kind: exporter\n"
        "    name: node_exporter\n"
        "    version: 1.11.1\n"
        "    targets: [el9]\n",
        encoding="utf-8",
    )
    recipe = load_recipe(path)
    assert recipe.arches == ["amd64"]
    assert recipe.items[0].name == "node_exporter"
    assert recipe.items[0].targets == ["el9"]


def test_load_recipe_json(tmp_path: Path) -> None:
    path = tmp_path / "recipe.json"
    path.write_text(
        '{"items": [{"kind": "exporter", "name": "node_exporter", "version": "1.11.1"}]}',
        encoding="utf-8",
    )
    recipe = load_recipe(path)
    assert recipe.items[0].version == "1.11.1"


def test_load_recipe_missing_file(tmp_path: Path) -> None:
    with pytest.raises(BundleError, match="cannot read"):
        load_recipe(tmp_path / "nope.yaml")


def test_load_recipe_unknown_key(tmp_path: Path) -> None:
    path = tmp_path / "recipe.yaml"
    path.write_text("bogus: true\n", encoding="utf-8")
    with pytest.raises(BundleError, match="invalid recipe"):
        load_recipe(path)


def test_load_recipe_non_mapping_root(tmp_path: Path) -> None:
    path = tmp_path / "recipe.yaml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(BundleError, match="mapping"):
        load_recipe(path)


def test_load_recipe_bad_json_syntax(tmp_path: Path) -> None:
    path = tmp_path / "recipe.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(BundleError, match="invalid recipe syntax"):
        load_recipe(path)
