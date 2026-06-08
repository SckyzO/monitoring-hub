"""mh bundle (SP3.0 stub): load + validate a recipe, report its contents."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from forge.cli.main import cli


def test_bundle_recipe_reports_items(tmp_path: Path) -> None:
    recipe = tmp_path / "recipe.yaml"
    recipe.write_text(
        "items:\n"
        "  - kind: exporter\n"
        "    name: node_exporter\n"
        "    version: 1.11.1\n"
        "  - kind: dashboard\n"
        "    name: node-overview\n"
        "    version: '39'\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(cli, ["bundle", "--recipe", str(recipe)])
    assert result.exit_code == 0, result.output
    assert "2 item(s)" in result.output


def test_bundle_requires_recipe() -> None:
    result = CliRunner().invoke(cli, ["bundle"])
    assert result.exit_code != 0
    assert "--recipe" in result.output


def test_bundle_invalid_recipe_errors(tmp_path: Path) -> None:
    recipe = tmp_path / "recipe.yaml"
    recipe.write_text("bogus: true\n", encoding="utf-8")
    result = CliRunner().invoke(cli, ["bundle", "--recipe", str(recipe)])
    assert result.exit_code != 0
    assert "invalid recipe" in result.output
