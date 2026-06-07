"""mh validate (spec §11, §14: aggregate all errors, non-zero exit)."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from forge.cli.main import cli


def test_validate_all_ok(catalog_root: Path) -> None:
    res = CliRunner().invoke(cli, ["validate", "--all", "--catalog-root", str(catalog_root)])
    assert res.exit_code == 0


def test_validate_single_ref(catalog_root: Path) -> None:
    res = CliRunner().invoke(
        cli, ["validate", "node_exporter", "--catalog-root", str(catalog_root)]
    )
    assert res.exit_code == 0


def test_validate_reports_bad_manifest(catalog_root: Path) -> None:
    bad = catalog_root / "exporters" / "broken"
    bad.mkdir()
    (bad / "manifest.yaml").write_text("kind: exporter\nname: broken\n", encoding="utf-8")
    res = CliRunner().invoke(cli, ["validate", "--all", "--catalog-root", str(catalog_root)])
    assert res.exit_code != 0
    assert "broken" in res.output


def test_validate_aggregates_not_fail_fast(catalog_root: Path) -> None:
    for name in ("brokenone", "brokentwo"):
        d = catalog_root / "exporters" / name
        d.mkdir()
        (d / "manifest.yaml").write_text(f"kind: exporter\nname: {name}\n", encoding="utf-8")
    res = CliRunner().invoke(cli, ["validate", "--all", "--catalog-root", str(catalog_root)])
    assert res.exit_code != 0
    assert "brokenone" in res.output
    assert "brokentwo" in res.output


def test_validate_requires_ref_or_all(catalog_root: Path) -> None:
    res = CliRunner().invoke(cli, ["validate", "--catalog-root", str(catalog_root)])
    assert res.exit_code != 0
