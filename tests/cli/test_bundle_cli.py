"""mh bundle CLI: recipe/item exclusivity, source dispatch, sign gate (spec §8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from click.testing import CliRunner

from forge.bundle.source import LocalDirSource, ReleasesFetcher
from forge.cli.main import cli
from forge.domain.recipe import BundleRecipe

_CATALOG = {
    "generated_at": "2026-06-08T00:00:00Z",
    "items": [
        {
            "kind": "exporter",
            "name": "node_exporter",
            "version": "1.9.1",
            "category": "System",
            "description": "Node exporter",
            "artifacts": [
                {"type": "rpm", "target": "el9", "arch": "amd64", "sha256": "a", "url": None}
            ],
        }
    ],
}


def _write_catalog(tmp_path: Path) -> Path:
    p = tmp_path / "catalog.json"
    p.write_text(json.dumps(_CATALOG), encoding="utf-8")
    return p


def _patch_build_bundle(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Replace build_bundle with a stub that records its kwargs and writes the output."""
    captured: dict[str, object] = {}

    def fake_build_bundle(**kwargs: object) -> Path:
        captured.update(kwargs)
        out = kwargs["out"]
        assert isinstance(out, Path)
        out.write_bytes(b"")
        return out

    monkeypatch.setattr("forge.cli.main.build_bundle", fake_build_bundle)
    return captured


def test_recipe_and_item_are_mutually_exclusive(tmp_path: Path) -> None:
    recipe = tmp_path / "r.yaml"
    recipe.write_text("items: []\n", encoding="utf-8")
    result = CliRunner().invoke(cli, ["bundle", "--recipe", str(recipe), "--item", "node_exporter"])
    assert result.exit_code != 0
    assert "exactly one of --recipe / --item" in result.output


def test_neither_recipe_nor_item_errors() -> None:
    result = CliRunner().invoke(cli, ["bundle"])
    assert result.exit_code != 0
    assert "exactly one of --recipe / --item" in result.output


def test_sign_without_key_id_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli,
        ["bundle", "--item", "node_exporter", "--catalog", str(_write_catalog(tmp_path)), "--sign"],
    )
    assert result.exit_code != 0
    assert "--sign requires --key-id" in result.output


def test_target_arch_with_recipe_errors(tmp_path: Path) -> None:
    recipe = tmp_path / "r.yaml"
    recipe.write_text("items: []\n", encoding="utf-8")
    result = CliRunner().invoke(cli, ["bundle", "--recipe", str(recipe), "--target", "el9"])
    assert result.exit_code != 0
    assert "--target/--arch only apply to --item" in result.output


def test_missing_catalog_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli, ["bundle", "--item", "node_exporter", "--catalog", str(tmp_path / "nope.json")]
    )
    assert result.exit_code != 0
    assert "catalog not found" in result.output


def test_item_packages_dispatches_local_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_build_bundle(**kwargs: object) -> Path:
        captured.update(kwargs)
        out = kwargs["out"]
        assert isinstance(out, Path)
        out.write_bytes(b"")
        return out

    monkeypatch.setattr("forge.cli.main.build_bundle", fake_build_bundle)
    out = tmp_path / "bundle.tar.gz"
    result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "--item",
            "node_exporter@1.9.1",
            "--catalog",
            str(_write_catalog(tmp_path)),
            "--packages",
            str(tmp_path),
            "--target",
            "el9",
            "--arch",
            "amd64",
            "-o",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert isinstance(captured["source"], LocalDirSource)
    recipe = cast("BundleRecipe", captured["recipe"])
    assert recipe.arches == ["amd64"]
    assert recipe.items[0].targets == ["el9"]


def test_item_default_source_is_releases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_build_bundle(**kwargs: object) -> Path:
        captured.update(kwargs)
        out = kwargs["out"]
        assert isinstance(out, Path)
        out.write_bytes(b"")
        return out

    monkeypatch.setattr("forge.cli.main.build_bundle", fake_build_bundle)
    result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "--item",
            "node_exporter",
            "--catalog",
            str(_write_catalog(tmp_path)),
            "-o",
            str(tmp_path / "b.tar.gz"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert isinstance(captured["source"], ReleasesFetcher)
    assert captured["image_source"] is None  # no --images → no image source


def test_bundle_images_default_uses_registry_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _patch_build_bundle(monkeypatch)
    result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "--item",
            "node_exporter",
            "--images",
            "--catalog",
            str(_write_catalog(tmp_path)),
            "-o",
            str(tmp_path / "b.tgz"),
        ],
    )
    assert result.exit_code == 0, result.output
    from forge.bundle.images import RegistryImageSource

    assert isinstance(captured["image_source"], RegistryImageSource)


def test_bundle_build_images_uses_local_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _patch_build_bundle(monkeypatch)
    (tmp_path / "dist" / "docker").mkdir(parents=True)
    result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "--item",
            "node_exporter",
            "--build-images",
            "--contexts",
            str(tmp_path / "dist" / "docker"),
            "--catalog",
            str(_write_catalog(tmp_path)),
            "-o",
            str(tmp_path / "b.tgz"),
        ],
    )
    assert result.exit_code == 0, result.output
    from forge.bundle.images import LocalImageSource

    assert isinstance(captured["image_source"], LocalImageSource)


def test_bundle_image_arch_requires_images(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "--item",
            "node_exporter",
            "--image-arch",
            "amd64",
            "--catalog",
            str(_write_catalog(tmp_path)),
        ],
    )
    assert result.exit_code != 0
    assert "--image-arch requires --images" in result.output


def test_recipe_path_loads_recipe_and_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_build_bundle(**kwargs: object) -> Path:
        captured.update(kwargs)
        out = kwargs["out"]
        assert isinstance(out, Path)
        out.write_bytes(b"")
        return out

    monkeypatch.setattr("forge.cli.main.build_bundle", fake_build_bundle)
    recipe = tmp_path / "recipe.yaml"
    recipe.write_text(
        "items:\n  - kind: exporter\n    name: node_exporter\n    version: 1.9.1\n",
        encoding="utf-8",
    )
    out = tmp_path / "bundle.tar.gz"
    result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "--recipe",
            str(recipe),
            "--catalog",
            str(_write_catalog(tmp_path)),
            "-o",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "wrote" in result.output and "1 item(s)" in result.output
    loaded = cast("BundleRecipe", captured["recipe"])
    assert [i.name for i in loaded.items] == ["node_exporter"]
