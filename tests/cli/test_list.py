"""mh list (spec §11)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from forge.cli.main import cli


def test_list_prints_item(catalog_root: Path) -> None:
    res = CliRunner().invoke(cli, ["list", "--catalog-root", str(catalog_root)])
    assert res.exit_code == 0
    assert "node_exporter" in res.output


def test_list_json(catalog_root: Path) -> None:
    res = CliRunner().invoke(cli, ["list", "--catalog-root", str(catalog_root), "--json"])
    assert res.exit_code == 0
    assert '"name": "node_exporter"' in res.output


def test_list_kind_filter_excludes(catalog_root: Path) -> None:
    res = CliRunner().invoke(
        cli, ["list", "--catalog-root", str(catalog_root), "--kind", "dashboard"]
    )
    assert res.exit_code == 0
    assert "node_exporter" not in res.output
